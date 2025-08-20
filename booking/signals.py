from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Booking, Ticket

@receiver(post_save, sender=Booking)
def create_ticket(sender, instance, created, **kwargs):
    if created:  # Only create a ticket when a new booking is created
        Ticket.objects.create(booking=instance)
