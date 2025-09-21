from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from .models import Profile
from django.contrib.auth.models import User

# Create profile when a new user is created (excluding staff/superusers)
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not instance.is_staff:
        Profile.objects.create(user=instance)

# Save profile on user save (only if it exists and is not staff)
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    if not instance.is_staff and hasattr(instance, 'profile'):
        instance.profile.save()

# Ensure old users have a profile on login (excluding staff)
@receiver(user_logged_in)
def ensure_profile_exists(sender, request, user, **kwargs):
    if not user.is_staff:
        Profile.objects.get_or_create(user=user)


# DASHBOARD
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
