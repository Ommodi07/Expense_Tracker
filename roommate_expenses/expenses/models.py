# expenses/models.py
from django.db import models
from django.contrib.auth.models import User
import uuid

class Group(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    members = models.ManyToManyField(User, related_name='joined_groups', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)
    
    def get_member_count(self):
        return self.members.count()

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def get_balance(self, group):
        """Calculate user's net balance within a specific group based on actual payment status"""
        if not group:
            return 0
        
        # What others owe this user (unpaid shares for expenses paid by this user)
        others_owe = ExpenseShare.objects.filter(
            expense__paid_by=self.user,
            expense__group=group,
            is_paid=False
        ).exclude(user=self.user).aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        # What this user owes to others (unpaid shares where this user is the debtor)
        user_owes = ExpenseShare.objects.filter(
            user=self.user,
            expense__group=group,
            is_paid=False
        ).exclude(expense__paid_by=self.user).aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        return others_owe - user_owes
    
    def get_all_groups(self):
        """Get all groups the user is a member of"""
        return self.user.joined_groups.all()

class Expense(models.Model):
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses_paid')
    date = models.DateField(auto_now_add=True)
    shared_among = models.ManyToManyField(User, related_name='shared_expenses')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='expenses')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} (${self.amount})"
    
    class Meta:
        ordering = ['-created_at']
    
    def get_split_amount(self):
        """Calculate amount per person"""
        num_people = self.shared_among.count()
        if num_people > 0:
            return self.amount / num_people
        return self.amount

class ExpenseShare(models.Model):
    """Tracks individual payment status for each user's share of an expense"""
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='shares')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expense_shares')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('expense', 'user')
        ordering = ['user__username']
    
    def __str__(self):
        status = "Paid" if self.is_paid else "Unpaid"
        return f"{self.user.username} - ${self.amount} ({status})"