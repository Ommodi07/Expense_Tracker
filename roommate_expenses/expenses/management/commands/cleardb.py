from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Clear database tables'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Drop ALL tables including Django default tables',
        )

    def handle(self, *args, **options):
        drop_all = options.get('all', False)
        
        if drop_all:
            self.stdout.write('🗑️  Clearing ALL tables...')
            with connection.cursor() as cursor:
                # Get all tables in public schema
                cursor.execute("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname='public' 
                    ORDER BY tablename;
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                for table in tables:
                    try:
                        cursor.execute(f'DROP TABLE IF EXISTS {table} CASCADE;')
                        self.stdout.write(f'   ✓ Dropped: {table}')
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'   ✗ Skip: {table} - {str(e)}'))
            self.stdout.write(self.style.SUCCESS('✅ All tables dropped! Run migrate to recreate them.'))
        else:
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
