from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, F, Sum
from django.db import models
from .forms import UserRegistrationForm, GroupCreationForm, GroupJoinForm, ExpenseForm
from .models import Group, UserProfile, Expense, ExpenseShare
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.utils import timezone
from django.http import JsonResponse

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                # Create user and activate immediately
                user = form.save()
                
                # Ensure user profile exists (signal should create it, but just in case)
                UserProfile.objects.get_or_create(user=user)
                
                # Authenticate and log the user in
                user = authenticate(username=user.username, password=form.cleaned_data['password1'])
                if user:
                    login(request, user)
                    messages.success(request, f"Welcome {user.username}! Your account has been created successfully.")
                    return redirect('dashboard')
                else:
                    messages.error(request, "Account created but login failed. Please try logging in manually.")
                    return redirect('login')
                    
            except IntegrityError as e:
                messages.error(request, "A user with this username or email already exists.")
                return redirect('register')
            except Exception as e:
                # Log the actual error for debugging
                import logging
                logging.error(f"Registration error: {str(e)}")
                messages.error(request, f"Error creating account: {str(e)}")
                return redirect('register')
    else:
        form = UserRegistrationForm()
    return render(request, 'expenses/register.html', {'form': form})

@login_required
def dashboard(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get all groups user is member of
    user_groups = request.user.joined_groups.all()
    
    # Debug: log the groups
    import logging
    logging.info(f"User {request.user.username} has {user_groups.count()} groups: {[g.name for g in user_groups]}")
    
    # Get selected group from session or query parameter
    selected_group_id = request.GET.get('group') or request.session.get('selected_group_id')
    selected_group = None
    
    if selected_group_id:
        try:
            selected_group = user_groups.get(id=selected_group_id)
            request.session['selected_group_id'] = selected_group.id
        except Group.DoesNotExist:
            pass
    
    # If no group selected, use first group or show empty state
    if not selected_group and user_groups.exists():
        selected_group = user_groups.first()
        request.session['selected_group_id'] = selected_group.id
    
    # Initialize context
    context = {
        'user_profile': user_profile,
        'all_groups': user_groups,
        'selected_group': selected_group,
        'expenses': [],
        'member_balances': {},
        'debts': [],
    }
    
    if selected_group:
        # Get all expenses for the selected group
        group_expenses = Expense.objects.filter(group=selected_group).prefetch_related('shares')
        
        # Add payment statistics to each expense
        expenses_with_stats = []
        for expense in group_expenses:
            total_shares = expense.shares.count()
            paid_shares = expense.shares.filter(is_paid=True).count()
            expense.paid_count = paid_shares
            expense.total_count = total_shares
            expenses_with_stats.append(expense)
        
        # Get balances for all group members
        group_members = selected_group.members.all()
        member_balances = {}
        for member in group_members:
            member_profile, _ = UserProfile.objects.get_or_create(user=member)
            member_balances[member.username] = member_profile.get_balance(selected_group)
        
        # Calculate who owes whom (only unpaid shares)
        debts = []
        unpaid_shares = ExpenseShare.objects.filter(
            expense__group=selected_group,
            is_paid=False
        ).exclude(user=F('expense__paid_by')).select_related('user', 'expense')
        
        for share in unpaid_shares:
            debts.append({
                'from_user': share.user.username,
                'to_user': share.expense.paid_by.username,
                'amount': share.amount,
                'expense': share.expense.title
            })
        
        context.update({
            'expenses': expenses_with_stats,
            'member_balances': member_balances,
            'debts': debts,
        })
    
    return render(request, 'expenses/dashboard.html', context)

@login_required
def group_options(request):
    return render(request, 'expenses/group_options.html')

@login_required
def create_group(request):
    if request.method == 'POST':
        form = GroupCreationForm(request.POST)
        if form.is_valid():
            try:
                group = form.save(commit=False)
                group.created_by = request.user
                group.save()  # Must save before adding to ManyToMany
                
                # Add creator as first member
                group.members.add(request.user)
                
                messages.success(request, f"Group '{group.name}' created! Share code: {group.code}")
                return redirect('dashboard')
            except Exception as e:
                import logging
                logging.error(f"Error creating group: {str(e)}")
                messages.error(request, f"Error creating group: {str(e)}")
    else:
        form = GroupCreationForm()
    
    return render(request, 'expenses/create_group.html', {'form': form})

@login_required
def join_group(request):
    if request.method == 'POST':
        form = GroupJoinForm(request.POST)
        if form.is_valid():
            group_code = form.cleaned_data['code']
            group = Group.objects.get(code=group_code)
            
            # Check if already a member
            if request.user in group.members.all():
                messages.info(request, f"You're already a member of '{group.name}'.")
            else:
                # Add user to the group
                group.members.add(request.user)
                messages.success(request, f"You've joined the group '{group.name}'!")
            
            return redirect('dashboard')
    else:
        form = GroupJoinForm()
    
    return render(request, 'expenses/join_group.html', {'form': form})

@login_required
def add_expense(request):
    user_profile = UserProfile.objects.get(user=request.user)
    
    # Get selected group
    selected_group_id = request.GET.get('group') or request.session.get('selected_group_id')
    
    if not selected_group_id:
        messages.error(request, "Please select a group first.")
        return redirect('dashboard')
    
    try:
        selected_group = request.user.joined_groups.get(id=selected_group_id)
    except Group.DoesNotExist:
        messages.error(request, "Invalid group selected.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ExpenseForm(selected_group, request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.group = selected_group
            expense.save()
            
            # Save the many-to-many relations
            form.save_m2m()
            
            messages.success(request, f"Expense '{expense.title}' added!")
            return redirect(f'/?group={selected_group.id}')
    else:
        form = ExpenseForm(selected_group, initial={'paid_by': request.user})
    
    context = {
        'form': form,
        'selected_group': selected_group
    }
    return render(request, 'expenses/add_expense.html', context)

@login_required
def expense_detail(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    
    # Ensure the user is a member of the expense's group
    if request.user not in expense.group.members.all():
        messages.error(request, "You don't have permission to view this expense.")
        return redirect('dashboard')
    
    # Get ExpenseShare records for detailed payment status
    expense_shares = expense.shares.all()
    
    context = {
        'expense': expense,
        'expense_shares': expense_shares,
        'is_creator': expense.paid_by == request.user
    }
    return render(request, 'expenses/expense_detail.html', context)

@login_required
def edit_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    
    # Check if user created the expense
    if expense.paid_by != request.user:
        messages.error(request, "You can only edit expenses you've created.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ExpenseForm(expense.group, request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, f"Expense '{expense.title}' updated!")
            return redirect('expense_detail', pk=expense.pk)
    else:
        form = ExpenseForm(expense.group, instance=expense)
    
    return render(request, 'expenses/edit_expense.html', {'form': form, 'expense': expense})

@login_required
def delete_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    
    # Check if user created the expense
    if expense.paid_by != request.user:
        messages.error(request, "You can only delete expenses you've created.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        expense_title = expense.title
        group_id = expense.group.id
        expense.delete()
        messages.success(request, f"Expense '{expense_title}' deleted!")
        return redirect(f'/?group={group_id}')
    
    return render(request, 'expenses/delete_expense.html', {'expense': expense})

@login_required
def leave_group(request, group_id):
    try:
        group = Group.objects.get(id=group_id)
        
        if request.user not in group.members.all():
            messages.error(request, "You're not a member of this group.")
            return redirect('dashboard')
        
        if request.method == 'POST':
            group_name = group.name
            group.members.remove(request.user)
            
            # Clear session if leaving currently selected group
            if request.session.get('selected_group_id') == group_id:
                request.session.pop('selected_group_id', None)
            
            messages.success(request, f"You've left the group '{group_name}'.")
            return redirect('dashboard')
        
        return render(request, 'expenses/leave_group.html', {'group': group})
    
    except Group.DoesNotExist:
        messages.error(request, "Group not found.")
        return redirect('dashboard')

@login_required
def view_group_members(request, group_id):
    try:
        group = Group.objects.get(id=group_id)
        
        if request.user not in group.members.all():
            messages.error(request, "You're not a member of this group.")
            return redirect('dashboard')
        
        group_members = group.members.all()
        
        context = {
            'group': group,
            'members': group_members,
            'is_creator': group.created_by == request.user
        }
        return render(request, 'expenses/group_members.html', context)
    
    except Group.DoesNotExist:
        messages.error(request, "Group not found.")
        return redirect('dashboard')

@login_required
def manage_groups(request):
    """View to manage all user's groups"""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    user_groups = request.user.joined_groups.all()
    created_groups = request.user.created_groups.all()
    
    context = {
        'user_profile': user_profile,
        'user_groups': user_groups,
        'created_groups': created_groups,
    }
    return render(request, 'expenses/manage_groups.html', context)

@login_required
def toggle_payment_status(request, share_id):
    """Toggle payment status for an expense share"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        share = get_object_or_404(ExpenseShare, pk=share_id)
        
        # Ensure the user is a member of the expense's group
        if request.user not in share.expense.group.members.all():
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Toggle the payment status
        share.is_paid = not share.is_paid
        share.paid_at = timezone.now() if share.is_paid else None
        share.save()
        
        return JsonResponse({
            'success': True,
            'is_paid': share.is_paid,
            'username': share.user.username
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
