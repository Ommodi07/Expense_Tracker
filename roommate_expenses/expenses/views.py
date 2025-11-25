from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .forms import UserRegistrationForm, GroupCreationForm, GroupJoinForm, ExpenseForm
from .models import Group, UserProfile, Expense
from django.contrib.auth.models import User
from django.db import IntegrityError

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                # Create user and activate immediately
                user = form.save()
                
                # Create user profile
                UserProfile.objects.get_or_create(user=user)
                
                # Log the user in automatically
                login(request, user)
                
                messages.success(request, f"Welcome {user.username}! Your account has been created successfully.")
                return redirect('dashboard')
                    
            except IntegrityError:
                messages.error(request, "A user with this username or email already exists.")
                return redirect('register')
            except Exception as e:
                messages.error(request, f"Error creating account. Please try again.")
                return redirect('register')
    else:
        form = UserRegistrationForm()
    return render(request, 'expenses/register.html', {'form': form})

@login_required
def dashboard(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get all groups user is member of
    user_groups = request.user.joined_groups.all()
    
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
        group_expenses = Expense.objects.filter(group=selected_group)
        
        # Get balances for all group members
        group_members = selected_group.members.all()
        member_balances = {}
        for member in group_members:
            member_profile, _ = UserProfile.objects.get_or_create(user=member)
            member_balances[member.username] = member_profile.get_balance(selected_group)
        
        # Calculate who owes whom
        debts = []
        for expense in group_expenses:
            per_person = expense.get_split_amount()
            
            for person in expense.shared_among.all():
                if person != expense.paid_by:
                    debts.append({
                        'from_user': person.username,
                        'to_user': expense.paid_by.username,
                        'amount': per_person,
                        'expense': expense.title
                    })
        
        context.update({
            'expenses': group_expenses,
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
            group = form.save(commit=False)
            group.created_by = request.user
            group.save()
            
            # Add creator as first member
            group.members.add(request.user)
            
            messages.success(request, f"Group '{group.name}' created! Share code: {group.code}")
            return redirect('dashboard')
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
    
    # Calculate individual shares
    per_person = expense.get_split_amount()
    shares = []
    for person in expense.shared_among.all():
        shares.append({
            'username': person.username,
            'amount': per_person,
            'is_payer': person == expense.paid_by
        })
    
    context = {
        'expense': expense,
        'shares': shares,
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
