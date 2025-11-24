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
    path('verification-sent/', views.verification_sent, name='verification_sent'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('login/', auth_views.LoginView.as_view(template_name='expenses/login.html'), name='login'),
    path('logout/', custom_logout, name='logout'),  # Using custom logout view
    path('group-options/', views.group_options, name='group_options'),
    path('create-group/', views.create_group, name='create_group'),
    path('join-group/', views.join_group, name='join_group'),
    path('add-expense/', views.add_expense, name='add_expense'),
    path('expense/<int:pk>/', views.expense_detail, name='expense_detail'),
    path('expense/<int:pk>/edit/', views.edit_expense, name='edit_expense'),
    path('expense/<int:pk>/delete/', views.delete_expense, name='delete_expense'),
    path('leave-group/', views.leave_group, name='leave_group'),
    path('group-members/', views.view_group_members, name='group_members'),
]