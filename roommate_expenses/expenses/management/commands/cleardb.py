from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from expenses.models import Group, UserProfile, Expense


class Command(BaseCommand):
    help = 'Clear all data from the database'

    def handle(self, *args, **options):
        self.stdout.write('🗑️  Clearing database...')
        
        # Delete in order to avoid foreign key constraints
        expense_count = Expense.objects.count()
        Expense.objects.all().delete()
        self.stdout.write(f'   Deleted {expense_count} expenses')
        
        profile_count = UserProfile.objects.count()
        UserProfile.objects.all().delete()
        self.stdout.write(f'   Deleted {profile_count} user profiles')
        
        group_count = Group.objects.count()
        Group.objects.all().delete()
        self.stdout.write(f'   Deleted {group_count} groups')
        
        user_count = User.objects.count()
        User.objects.all().delete()
        self.stdout.write(f'   Deleted {user_count} users')
        
        self.stdout.write(self.style.SUCCESS('✅ Database cleared successfully!'))
