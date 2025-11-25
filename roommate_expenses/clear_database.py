#!/usr/bin/env python
"""
Script to clear all data from the database
Usage: python clear_database.py
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'roommate_expenses.settings')
django.setup()

from django.contrib.auth.models import User
from expenses.models import Group, UserProfile, Expense

def clear_database():
    """Clear all data from database tables"""
    print("⚠️  WARNING: This will delete ALL data from the database!")
    confirm = input("Type 'YES' to confirm: ")
    
    if confirm != 'YES':
        print("❌ Operation cancelled.")
        return
    
    try:
        # Delete in order to avoid foreign key constraints
        print("\n🗑️  Deleting expenses...")
        expense_count = Expense.objects.count()
        Expense.objects.all().delete()
        print(f"   Deleted {expense_count} expenses")
        
        print("\n🗑️  Deleting user profiles...")
        profile_count = UserProfile.objects.count()
        UserProfile.objects.all().delete()
        print(f"   Deleted {profile_count} user profiles")
        
        print("\n🗑️  Deleting groups...")
        group_count = Group.objects.count()
        Group.objects.all().delete()
        print(f"   Deleted {group_count} groups")
        
        print("\n🗑️  Deleting users...")
        user_count = User.objects.count()
        User.objects.all().delete()
        print(f"   Deleted {user_count} users")
        
        print("\n✅ Database cleared successfully!")
        print("\nYou can now:")
        print("1. Register new users with email as primary identifier")
        print("2. Login using email or username")
        
    except Exception as e:
        print(f"\n❌ Error clearing database: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    clear_database()
