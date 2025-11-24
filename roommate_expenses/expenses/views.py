from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .forms import UserRegistrationForm, GroupCreationForm, GroupJoinForm, ExpenseForm
from .models import Group, UserProfile, Expense
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
import uuid
from datetime import timedelta

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                # Create user but don't activate yet
                user = form.save(commit=False)
                user.is_active = False  # Deactivate until email verification
                user.save()
                
                # Create user profile with verification token
                user_profile, created = UserProfile.objects.get_or_create(user=user)
                verification_token = str(uuid.uuid4())
                user_profile.verification_token = verification_token
                user_profile.token_created_at = timezone.now()
                user_profile.email_verified = False
                user_profile.save()
                
                # Send verification email
                verification_url = request.build_absolute_uri(
                    reverse('verify_email', kwargs={'token': verification_token})
                )
                
                subject = 'Verify your email - Roommate Expenses'
                message = f'''
Hello {user.username},

Thank you for registering! Please verify your email address by clicking the link below:

{verification_url}

This link will expire in 10 minutes.

If you didn't create this account, please ignore this email.

Best regards,
Roommate Expenses Team
                '''
                
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=False,
                    )
                    messages.success(request, f"Account created! Please check your email ({user.email}) to verify your account.")
                    return redirect('verification_sent')
                except Exception as email_error:
                    # If email fails, activate user anyway (for production without email configured)
                    user.is_active = True
                    user.save()
                    user_profile.email_verified = True
                    user_profile.save()
                    messages.warning(request, f"Account created but email verification is unavailable. You can log in now.")
                    return redirect('login')
                    
            except IntegrityError:
                messages.error(request, "A user profile already exists for this user.")
                return redirect('login')
            except Exception as e:
                messages.error(request, f"Error creating account. Please try again.")
                if user.id:
                    user.delete()  # Clean up if registration fails
                return redirect('register')
    else:
        form = UserRegistrationForm()
    return render(request, 'expenses/register.html', {'form': form})

def verification_sent(request):
    return render(request, 'expenses/verification_sent.html')

def verify_email(request, token):
    try:
        user_profile = UserProfile.objects.get(verification_token=token)
        
        # Check if token has expired (10 minutes)
        if user_profile.token_created_at:
            expiry_time = user_profile.token_created_at + timedelta(minutes=10)
            if timezone.now() > expiry_time:
                messages.error(request, "Verification link has expired. Please request a new one.")
                return redirect('resend_verification')
        
        # Activate user and mark email as verified
        user_profile.user.is_active = True
        user_profile.user.save()
        user_profile.email_verified = True
        user_profile.verification_token = None  # Clear token after use
        user_profile.save()
        
        messages.success(request, "Email verified successfully! You can now log in.")
        return redirect('login')
        
    except UserProfile.DoesNotExist:
        messages.error(request, "Invalid verification link.")
        return redirect('login')

def resend_verification(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email, is_active=False)
            user_profile = user.profile
            
            # Generate new token
            verification_token = str(uuid.uuid4())
            user_profile.verification_token = verification_token
            user_profile.token_created_at = timezone.now()
            user_profile.save()
            
            # Send verification email
            verification_url = request.build_absolute_uri(
                reverse('verify_email', kwargs={'token': verification_token})
            )
            
            subject = 'Verify your email - Roommate Expenses'
            message = f'''
Hello {user.username},

Here is your new verification link:

{verification_url}

This link will expire in 10 minutes.

Best regards,
Roommate Expenses Team
            '''
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
            messages.success(request, f"Verification email sent to {email}. Please check your inbox.")
            return redirect('verification_sent')
            
        except User.DoesNotExist:
            messages.error(request, "No unverified account found with this email.")
        except Exception as e:
            messages.error(request, "Error sending verification email. Please try again.")
    
    return render(request, 'expenses/resend_verification.html')

@login_required
def dashboard(request):
    user_profile = UserProfile.objects.get(user=request.user)
    
    # Check if user is in a group
    if not user_profile.group:
        messages.info(request, "Please create or join a group first.")
        return redirect('group_options')
    
    # Get all expenses for the user's group
    group_expenses = Expense.objects.filter(group=user_profile.group)
    
    # Get balances for all group members
    group_members = UserProfile.objects.filter(group=user_profile.group)
    member_balances = {profile.user.username: profile.get_balance() for profile in group_members}
    
    # Calculate who owes whom
    debts = []
    for expense in group_expenses:
        per_person = expense.get_split_amount()
        
        # For each person that shared the expense
        for person in expense.shared_among.all():
            # If the person is not the one who paid
            if person != expense.paid_by:
                debts.append({
                    'from_user': person.username,
                    'to_user': expense.paid_by.username,
                    'amount': per_person,
                    'expense': expense.title
                })
    
    context = {
        'user_profile': user_profile,
        'group': user_profile.group,
        'expenses': group_expenses,
        'member_balances': member_balances,
        'debts': debts,
    }
    return render(request, 'expenses/dashboard.html', context)

@login_required
def group_options(request):
    return render(request, 'expenses/group_options.html')

@login_required
def create_group(request):
    if request.method == 'POST':
        form = GroupCreationForm(request.POST)
        if form.is_valid():
            group = form.save()
            
            # Add user to the group
            user_profile = UserProfile.objects.get(user=request.user)
            user_profile.group = group
            user_profile.save()
            
            messages.success(request, f"Group '{group.name}' created! Your group code is {group.code}")
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
            
            # Add user to the group
            user_profile = UserProfile.objects.get(user=request.user)
            user_profile.group = group
            user_profile.save()
            
            messages.success(request, f"You've joined the group '{group.name}'!")
            return redirect('dashboard')
    else:
        form = GroupJoinForm()
    
    return render(request, 'expenses/join_group.html', {'form': form})

@login_required
def add_expense(request):
    user_profile = UserProfile.objects.get(user=request.user)
    
    # Check if user is in a group
    if not user_profile.group:
        messages.error(request, "You need to be in a group to add expenses.")
        return redirect('group_options')
    
    if request.method == 'POST':
        form = ExpenseForm(user_profile.group, request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.group = user_profile.group
            expense.save()
            
            # Save the many-to-many relations
            form.save_m2m()
            
            messages.success(request, f"Expense '{expense.title}' added!")
            return redirect('dashboard')
    else:
        form = ExpenseForm(user_profile.group, initial={'paid_by': request.user})
    
    return render(request, 'expenses/add_expense.html', {'form': form})

@login_required
def expense_detail(request, pk):
    user_profile = UserProfile.objects.get(user=request.user)
    expense = get_object_or_404(Expense, pk=pk)
    
    # Ensure the expense belongs to user's group
    if expense.group != user_profile.group:
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
    user_profile = UserProfile.objects.get(user=request.user)
    expense = get_object_or_404(Expense, pk=pk)
    
    # Check if user created the expense
    if expense.paid_by != request.user:
        messages.error(request, "You can only edit expenses you've created.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ExpenseForm(user_profile.group, request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, f"Expense '{expense.title}' updated!")
            return redirect('expense_detail', pk=expense.pk)
    else:
        form = ExpenseForm(user_profile.group, instance=expense)
    
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
        expense.delete()
        messages.success(request, f"Expense '{expense_title}' deleted!")
        return redirect('dashboard')
    
    return render(request, 'expenses/delete_expense.html', {'expense': expense})

@login_required
def leave_group(request):
    user_profile = UserProfile.objects.get(user=request.user)
    
    if not user_profile.group:
        messages.error(request, "You're not in any group.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        group_name = user_profile.group.name
        user_profile.group = None
        user_profile.save()
        messages.success(request, f"You've left the group '{group_name}'.")
        return redirect('group_options')
    
    return render(request, 'expenses/leave_group.html')

@login_required
def view_group_members(request):
    user_profile = UserProfile.objects.get(user=request.user)
    
    if not user_profile.group:
        messages.error(request, "You're not in any group.")
        return redirect('group_options')
    
    group_members = UserProfile.objects.filter(group=user_profile.group)
    
    context = {
        'group': user_profile.group,
        'members': group_members
    }
    return render(request, 'expenses/group_members.html', context)