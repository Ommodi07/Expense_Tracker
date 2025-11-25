from django.contrib import admin
from .models import Group, UserProfile, Expense, ExpenseShare

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'created_by', 'created_at']
    search_fields = ['name', 'code']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user']

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['title', 'amount', 'paid_by', 'group', 'date']
    list_filter = ['group', 'date']
    search_fields = ['title']

@admin.register(ExpenseShare)
class ExpenseShareAdmin(admin.ModelAdmin):
    list_display = ['expense', 'user', 'amount', 'is_paid', 'paid_at']
    list_filter = ['is_paid', 'expense__group']
    search_fields = ['expense__title', 'user__username']
