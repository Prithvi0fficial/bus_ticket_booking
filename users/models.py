from django.db import models

# Create your models here.
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)  # Ensure unique email
    reset_token = models.CharField(max_length=64, blank=True, null=True)    
    USERNAME_FIELD = 'email'  # Now use email instead of username
    REQUIRED_FIELDS = ['username']  # Username is still required, but not for login
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=64, blank=True, null=True)
    verification_token_created_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.email  # Display email instead of username

# users/models.py
def user_profile_upload_path(instance, filename):
    return f"profile_pics/user_{instance.user.id}/{filename}"

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=user_profile_upload_path, default='profile_pics/default.png')
    phone = models.CharField(max_length=15, blank=True)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
