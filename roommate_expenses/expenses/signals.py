# expenses/signals.py
from django.db.models.signals import post_save, m2m_changed, pre_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import UserProfile, Expense, ExpenseShare

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    """Create a UserProfile for every new User"""
    if created:
        UserProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, created, **kwargs):
    """Update UserProfile when User is updated"""
    if created:
        # Skip for new users - create_profile signal handles this
        return
    try:
        profile = UserProfile.objects.get(user=instance)
        profile.save()
    except UserProfile.DoesNotExist:
        # Create profile if it doesn't exist
        UserProfile.objects.create(user=instance)

@receiver(m2m_changed, sender=Expense.shared_among.through)
def create_expense_shares(sender, instance, action, pk_set, **kwargs):
    """Automatically create ExpenseShare records when users are added to shared_among"""
    if action == "post_add":
        num_people = instance.shared_among.count()
        if num_people > 0:
            amount_per_person = instance.amount / num_people
            
            # Update or create shares for all users
            for user in instance.shared_among.all():
                ExpenseShare.objects.update_or_create(
                    expense=instance,
                    user=user,
                    defaults={
                        'amount': amount_per_person,
                        'is_paid': (user == instance.paid_by)
                    }
                )
    elif action == "post_remove":
        # Recalculate amounts for remaining users
        num_people = instance.shared_among.count()
        if num_people > 0:
            amount_per_person = instance.amount / num_people
            
            for share in instance.shares.all():
                share.amount = amount_per_person
                share.save()
    elif action == "post_clear":
        # Delete all shares if all users are removed
        instance.shares.all().delete()

@receiver(post_save, sender=Expense)
def update_expense_shares_on_amount_change(sender, instance, created, **kwargs):
    """Recalculate ExpenseShare amounts when expense amount or paid_by changes"""
    if not created:
        # Get all existing shares for this expense
        shares = instance.shares.all()
        num_people = shares.count()
        
        if num_people > 0:
            amount_per_person = instance.amount / num_people
            
            # Update all share amounts and payment status
            for share in shares:
                share.amount = amount_per_person
                # Only the payer should be marked as paid, others reset to unpaid
                if share.user == instance.paid_by:
                    share.is_paid = True
                else:
                    share.is_paid = False
                    share.paid_at = None
                share.save()