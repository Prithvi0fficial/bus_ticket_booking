from django.db import models
import uuid  # to generate unique pnr
from django.utils import timezone
from django.conf import settings

import json 
from django.utils.timezone import now 
from django.contrib.auth import get_user_model
User = get_user_model()  



# Bus model
class Bus(models.Model):
    name = models.CharField(max_length=100)
    number = models.CharField(max_length=20, unique=True)
    total_seats = models.IntegerField()
    is_ac = models.BooleanField(default=False) 
    route = models.ForeignKey('Route', on_delete=models.CASCADE)
    BUS_TYPE_CHOICES = [('AC', 'AC'), ('Non-AC', 'Non-AC')]
    type = models.CharField(max_length=10, choices=BUS_TYPE_CHOICES)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    intermediate_stops = models.JSONField(default=list)
    timing = models.TimeField(default="12:00:00")
    seat_layout = models.TextField(default=json.dumps([
        ['1', '2', 'aisle', '3', '4'],
        ['5', '6', 'aisle', '7', '8'],
        ['9', '10', 'aisle', '11', '12'],
        ['13', '14', 'aisle', '15', '16'],
        ['17', '18', 'aisle', '19', '20'],
        ['21', '22', 'aisle', '23', '24'],
    ]))

    def get_seat_layout(self):
        try:
            return json.loads(self.seat_layout)
        except json.JSONDecodeError:
            return []

    def calculate_total_seats(self):
        layout = self.get_seat_layout()
        return sum(1 for row in layout for seat in row if isinstance(seat, str) and seat.isdigit())

    def save(self, *args, **kwargs):
        self.is_ac = self.type == "AC"
        if not self.total_seats:
            self.total_seats = self.calculate_total_seats()
        super().save(*args, **kwargs)
        if Seat.objects.filter(bus=self).count() == 0:
            self.generate_seats()

    def generate_seats(self):
        layout = self.get_seat_layout()
        seat_number = 1
        for row in layout:
            for seat in row:
                if seat.isdigit():
                    Seat.objects.create(
                        bus=self,
                        seat_number=str(seat_number).zfill(2)
                    )
                    seat_number += 1
        self.total_seats = seat_number - 1
        self.save()

    def __str__(self):
        return self.name

# bus stops
class BusStop(models.Model):
    name = models.CharField(max_length=100, unique=True)
    city = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}, {self.city}"

# bus roots for bus stops
class BusRoute(models.Model):
    bus = models.OneToOneField(Bus, on_delete=models.CASCADE)

    stops = models.ManyToManyField(BusStop, through="RouteStop", related_name="routes")

    def get_starting_stop(self):
        return self.stops.order_by("routestop__order").first()

    def get_ending_stop(self):
        return self.stops.order_by("-routestop__order").first()


    def __str__(self):
        return f"{self.bus.name} - Route"

# bus route stops
class RouteStop(models.Model):
    bus_route = models.ForeignKey(BusRoute, on_delete=models.CASCADE)
    stop = models.ForeignKey(BusStop, on_delete=models.CASCADE)
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    order = models.IntegerField(default=1)

    class Meta:
        unique_together = ("bus_route", "stop")

    def __str__(self):
        return f"{self.stop.name} - Departure: {self.departure_time}, Arrival: {self.arrival_time}"


# Route model
class Route(models.Model):
    source = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    distance = models.FloatField()

    def __str__(self):
        return f"{self.source} to {self.destination}"

# Seat model
from django.utils import timezone

from datetime import timedelta
from django.utils import timezone

from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

class Seat(models.Model):
    bus = models.ForeignKey('Bus', on_delete=models.CASCADE, related_name="seats")
    seat_number = models.CharField(max_length=5)

    is_selected = models.BooleanField(default=False)
    selected_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    selected_at = models.DateTimeField(null=True, blank=True)

    is_booked = models.BooleanField(default=False)

    # NEW FIELDS FOR LOCKING
    is_locked = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('bus', 'seat_number')

    def unlock_if_expired(self):
        """Unlock the seat if it's locked for more than 1 minutes"""
        if self.is_locked and self.locked_at:
            if timezone.now() - self.locked_at > timedelta(minutes=1):
                self.is_locked = False
                self.locked_at = None
                self.is_selected = False
                self.selected_by = None
                self.selected_at = None
                self.save()

    def select_seat(self, user):
        """Select seat temporarily if not booked or locked."""
        self.unlock_if_expired()
        if not self.is_booked and not self.is_locked:
            self.is_selected = True
            self.selected_by = user
            self.selected_at = timezone.now()
            self.is_locked = True
            self.locked_at = timezone.now()
            self.save()
            return True
        return False

    def confirm_booking(self):
        """Confirm seat booking and unlock it."""
        if self.is_selected or self.is_locked:
            self.is_booked = True
            self.is_selected = False
            self.selected_by = None
            self.selected_at = None
            self.is_locked = False
            self.locked_at = None
            self.save()

    def release_selection(self):
        """Manually release seat selection (e.g., when user cancels)."""
        self.is_selected = False
        self.selected_by = None
        self.selected_at = None
        self.is_locked = False
        self.locked_at = None
        self.save()

    def cancel_booking(self):
        """Release seat if booking is cancelled."""
        self.is_booked = False
        self.is_selected = False
        self.selected_by = None
        self.selected_at = None
        self.is_locked = False
        self.locked_at = None
        self.save()

    def __str__(self):
        status = (
            "Booked" if self.is_booked else
            "Locked" if self.is_locked else
            "Selected" if self.is_selected else
            "Available"
        )
        return f"Seat {self.seat_number} - {status}"


#scheduled booking
# booking/models.py

class BusSchedule(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    route = models.ForeignKey(Route, on_delete=models.CASCADE, null=True, blank=True)  # Added route
    date = models.DateField()  # Stores the date of travel
    departure_time = models.DateTimeField()  # Stores the time separately

   

    class Meta:
        unique_together = ('bus', 'date')  # Ensures a bus can have only one schedule per date

    def __str__(self):
        return f"{self.bus} - {self.date} at {self.departure_time}"



# bus model
from django.db import models
from django.conf import settings
from django.utils.timezone import now, timezone

from .models import Bus, Route, BusSchedule, Seat  # Adjust as needed
# from .utils import process_stripe_refund  # Optional: If using Stripe refunds
class Booking(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    route = models.ForeignKey(Route, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    schedule = models.ForeignKey(BusSchedule, on_delete=models.CASCADE)
    seats = models.ManyToManyField(Seat, related_name="booking_seats")
    seat_numbers = models.CharField(max_length=200, blank=True, null=True)

    date = models.DateField(default=now)
    booked_at = models.DateTimeField(auto_now_add=True)
    is_confirmed = models.BooleanField(default=False)
    

    BUS_TYPE_CHOICES = [('AC', 'AC'), ('Non-AC', 'Non-AC')]
    type = models.CharField(max_length=10, choices=BUS_TYPE_CHOICES)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    total_price = models.FloatField()

    passenger_name = models.CharField(max_length=100)
    passenger_age = models.IntegerField()
    passenger_email = models.EmailField()
    payment = models.ForeignKey('Payment', on_delete=models.CASCADE, related_name='booking_payment', null=True, blank=True)



    STATUS_CHOICES = [
        ('Booked', 'Booked'),
        ('Cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Booked')
    cancelled_at = models.DateTimeField(null=True, blank=True)
    refund_status = models.CharField(max_length=50, null=True, blank=True)  # Optional: 'Pending', 'Completed', etc.


    def confirm_booking(self):
        """Mark seats as confirmed."""
        self.is_confirmed = True
        for seat in self.seats.all():
            seat.confirm_booking()
        self.save()

    def cancel_booking(self, refund_requested=False):
        """Cancel booking, release seats, optionally initiate refund."""
        if self.status == 'Cancelled':
            return  # Already cancelled

        for seat in self.seats.all():
            seat.release_selection()  # This should release the seat back to available
        self.status = 'Cancelled'
        self.is_confirmed = False
        self.cancelled_at = timezone.now()

        # Optional: Initiate refund if needed
        # if refund_requested and hasattr(self, 'payment'):
        #     self.refund_status = process_stripe_refund(self.payment)

        self.save()
    

    def __str__(self):
        return f"Booking for {self.passenger_name} on {self.date}"


# Discountsettings
class Discount(models.Model):
    min_seats = models.IntegerField(help_text="Minimum seats required for discount")
    discount_percentage = models.FloatField(help_text="Discount percentage")

    def __str__(self):
        return f"{self.min_seats}+ Seats: {self.discount_percentage}% Discount"

# Ticket model
class Ticket(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="ticket")  # Added related_name

    def __str__(self):
        return f"Ticket for {self.booking.passenger_name}"


# routes

# display pricing
class RoutePrice(models.Model):
    route = models.ForeignKey('Route', on_delete=models.CASCADE)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    ac_increment_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def get_price(self, is_ac):
        """Calculate price dynamically based on bus type."""
        if is_ac:
            return self.base_price + (self.base_price * self.ac_increment_percentage / 100)
        return self.base_price

#---------------------------------------------------
from django.db import models
import json

class SeatBooking(models.Model):
    bus = models.ForeignKey('Bus', on_delete=models.CASCADE, related_name="booked_seats")
    seat_number = models.CharField(max_length=10)
    is_booked = models.BooleanField(default=True)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, null=True, blank=True)



    def __str__(self):
        seat_info = str(self.seat) if self.seat else "No Seat"
        passenger_name = self.booking.passenger_name if self.booking else "No Booking"
        return f"{seat_info} - {passenger_name}"

    

    #----------------------------------------------------------------------------------------
class Payment(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="payments")
    transaction_id = models.CharField(max_length=100, unique=True, blank=True, null=True)  # Store payment gateway transaction ID
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=[("Pending", "Pending"), ("Completed", "Completed"), ("Failed", "Failed")],
        default="Pending"
    )
    payment_method = models.CharField(max_length=50, choices=[("Online", "Online"), ("Cash", "Cash")], default="Online")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Payment {self.transaction_id} - {self.status}"

#feedback
from django.conf import settings
from django.db import models

class Feedback(models.Model):
    RATING_CHOICES = [
        (1, 'Sad'),
        (2, 'Neutral'),
        (3, 'Happy'),

    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    rating = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(1, 4)])  # 1-5 stars
    comment = models.TextField()
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Feedback from {self.user.username if self.user else "Guest"} - {self.rating} Stars'

