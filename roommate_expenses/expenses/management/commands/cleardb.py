from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Clear all data from the database and reset schema'

    def handle(self, *args, **options):
        self.stdout.write('🗑️  Clearing database...')
        
        with connection.cursor() as cursor:
            # Drop tables in correct order to avoid foreign key constraints
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
                    self.stdout.write(f'   Dropped table: {table}')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'   Could not drop {table}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS('✅ Database tables dropped! Run migrations next.'))
