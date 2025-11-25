from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Clear all expenses data from the database'

    def handle(self, *args, **options):
        self.stdout.write('🗑️  Clearing expenses tables...')
        
        with connection.cursor() as cursor:
            # Drop expenses tables in correct order
            tables = [
                'expenses_expense_shared_among',
                'expenses_expense',
                'expenses_group_members',
                'expenses_userprofile',
                'expenses_group',
            ]
            
            for table in tables:
                try:
                    cursor.execute(f'DROP TABLE IF EXISTS {table} CASCADE;')
                    self.stdout.write(f'   ✓ Dropped: {table}')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'   ✗ Skip: {table} - {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS('✅ Tables dropped! Migrations will recreate them.'))
