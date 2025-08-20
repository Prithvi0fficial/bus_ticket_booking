from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views
from django.shortcuts import redirect
from .views import get_booked_seats, get_user_favicon
from users import views as user_views  # Import from the users app
from django.conf import settings
from django.conf.urls.static import static
from .views import feedback_view

def redirect_to_login(request):
    return redirect("auth")


urlpatterns = [
    # Home Page
    path('', views.home, name='home'),

    # Booking
    path('confirmation/<int:schedule_id>/', views.booking_confirmation, name='booking_confirmation'),
    path("search-buses/", views.search_buses, name="search_buses"),
    
    path("get_booked_seats/<int:bus_id>/", get_booked_seats, name="get_booked_seats"),

    # Payment
    path("process-payment/<int:schedule_id>/", views.process_payment, name="process_payment"),
    path('ticket-success/<int:booking_id>/', views.ticket_success, name='ticket_success'),
 
    path("get-user-favicon/", get_user_favicon, name="get_user_favicon"),

    # Seat Selection
    path("seat-selection/<int:schedule_id>/", views.seat_selection, name="seat_selection"),

    path('feedback/', feedback_view, name='feedback'),
    path('thank-you/', views.thank_you_view, name='thank_you'), 
    path('about/', views.about_page, name='about'),
    # Authentication (Login, Signup, Logout)
    path('auth/', user_views.auth_view, name="auth"),

    # Dashboard & Bookings
    path("my-bookings/", login_required(views.my_bookings), name="my_bookings"),

    # Booking
    path('book/', views.seat_selection, name='booking'),

    
]

# Serve media files in development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
