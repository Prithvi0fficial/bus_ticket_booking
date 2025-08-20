from django.test import TestCase
from django.urls import reverse
from booking.models import Bus

class BusListViewTest(TestCase):
    def setUp(self):
        Bus.objects.create(name="Express Bus", number="KL-07-AB-1234", total_seats=49)
        Bus.objects.create(name="City Bus", number="KL-07-XY-5678", total_seats=40)

    def test_bus_list_view(self):
        response = self.client.get(reverse("bus_list"))  # Ensure your urls.py has the 'bus_list' name
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Express Bus")
        self.assertContains(response, "City Bus")
