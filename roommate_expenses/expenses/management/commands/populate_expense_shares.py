from django.core.management.base import BaseCommand
from expenses.models import Expense, ExpenseShare


class Command(BaseCommand):
    help = 'Populate ExpenseShare records for existing expenses'

    def handle(self, *args, **options):
        self.stdout.write('Populating expense shares...')
        
        expenses = Expense.objects.all()
        created_count = 0
        
        for expense in expenses:
            shared_users = expense.shared_among.all()
            num_people = shared_users.count()
            
            if num_people > 0:
                amount_per_person = expense.amount / num_people
                
                for user in shared_users:
                    # Check if share already exists
                    share, created = ExpenseShare.objects.get_or_create(
                        expense=expense,
                        user=user,
                        defaults={
                            'amount': amount_per_person,
                            'is_paid': (user == expense.paid_by)
                        }
                    )
                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Created share for {user.username} on expense "{expense.title}"'
                            )
                        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} expense share records'
            )
        )
