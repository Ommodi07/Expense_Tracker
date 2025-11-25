# expenses/signals.py
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import UserProfile

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