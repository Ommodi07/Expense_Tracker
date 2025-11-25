from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth import logout
from django.shortcuts import redirect
from . import views

def custom_logout(request):
    logout(request)
    request.session.flush()  # Clear all session data
    return redirect('login')

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='expenses/login.html'), name='login'),
    path('logout/', custom_logout, name='logout'),
    
    # Group management
    path('group-options/', views.group_options, name='group_options'),
    path('create-group/', views.create_group, name='create_group'),
    path('join-group/', views.join_group, name='join_group'),
    path('manage-groups/', views.manage_groups, name='manage_groups'),
    path('leave-group/<int:group_id>/', views.leave_group, name='leave_group'),
    path('group-members/<int:group_id>/', views.view_group_members, name='group_members'),
    
    # Expense management
    path('add-expense/', views.add_expense, name='add_expense'),
    path('expense/<int:pk>/', views.expense_detail, name='expense_detail'),
    path('expense/<int:pk>/edit/', views.edit_expense, name='edit_expense'),
    path('expense/<int:pk>/delete/', views.delete_expense, name='delete_expense'),
    path('toggle-payment/<int:share_id>/', views.toggle_payment_status, name='toggle_payment_status'),
]