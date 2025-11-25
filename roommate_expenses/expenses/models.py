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
        """Calculate user's net balance within a specific group"""
        if not group:
            return 0
        
        # What the user has paid for others
        expenses_paid = Expense.objects.filter(
            paid_by=self.user, 
            group=group
        )
        
        total_paid = 0
        for expense in expenses_paid:
            # Count only the portions that others should pay
            participants = expense.shared_among.count()
            if participants > 0:
                # Don't count the user's own share
                if expense.shared_among.filter(id=self.user.id).exists():
                    total_paid += expense.amount * (participants - 1) / participants
                else:
                    total_paid += expense.amount
        
        # What others have paid for the user
        user_owes = 0
        expenses_shared = Expense.objects.filter(
            shared_among=self.user,
            group=group
        ).exclude(paid_by=self.user)
        
        for expense in expenses_shared:
            participants = expense.shared_among.count()
            if participants > 0:
                user_owes += expense.amount / participants
        
        return total_paid - user_owes
    
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