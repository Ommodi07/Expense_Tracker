from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Custom authentication backend that allows login with email or username
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Try to find user by email or username
            user = User.objects.get(Q(username=username) | Q(email=username))
            
            # Check password
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            # If multiple users with same email (shouldn't happen), return first
            user = User.objects.filter(Q(username=username) | Q(email=username)).first()
            if user and user.check_password(password):
                return user
        
        return None
