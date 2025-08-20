from django.test import TestCase
from booking.models import Bus, Route, Booking, Seat
from django.contrib.auth.models import User
from datetime import date

class BusModelTest(TestCase):
    def test_create_bus(self):
        bus = Bus.objects.create(name="Express Bus", number="KL-07-AB-1234", total_seats=49)
        self.assertEqual(bus.name, "Express Bus")
        self.assertEqual(bus.total_seats, 49)
        self.assertEqual(str(bus), "Express Bus (KL-07-AB-1234)")

class RouteModelTest(TestCase):
    def test_create_route(self):
        route = Route.objects.create(source="Kochi", destination="Trivandrum", distance=200.5)
        self.assertEqual(route.source, "Kochi")
        self.assertEqual(route.destination, "Trivandrum")
        self.assertEqual(str(route), "Kochi to Trivandrum")

class BookingModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.bus = Bus.objects.create(name="Express Bus", number="KL-07-AB-1234", total_seats=49)
        self.route = Route.objects.create(source="Kochi", destination="Trivandrum", distance=200.5)
        self.seat1 = Seat.objects.create(bus=self.bus, seat_number="1A", is_booked=False)
        self.seat2 = Seat.objects.create(bus=self.bus, seat_number="1B", is_booked=False)

    def test_create_booking(self):
        booking = Booking.objects.create(
            bus=self.bus,
            route=self.route,
            passenger_name="John Doe",
            email="johndoe@example.com",
            date=date.today(),
            user=self.user,
            type="AC",
            price=500.00
        )
        booking.seats.add(self.seat1, self.seat2)
        self.assertEqual(booking.passenger_name, "John Doe")
        self.assertEqual(booking.price, 500.00)
        self.assertEqual(booking.seats.count(), 2)
