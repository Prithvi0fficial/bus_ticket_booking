from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import EmailMessage
from django.db.models import Count, Q, F
from django.http import HttpResponse
from django.conf import settings

from io import BytesIO
import os
from .models import Bus, Route, Booking, Ticket

from django.http import JsonResponse
from booking.models import User

from .models import RoutePrice


from django.contrib.auth import get_user_model
User = get_user_model()  


from .models import Bus, BusRoute, RouteStop, RoutePrice, Seat, Booking, Ticket, Discount
# Home Page
def home(request):
    buses = Bus.objects.all()
    routes = Route.objects.all()
    return render(request, 'booking/home.html', {'buses': buses, 'routes': routes})

# Seat Selection  --- -- - --------------------------------------------------
import json
from django.shortcuts import render, get_object_or_404
from .models import Bus, RoutePrice, Seat
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from .models import Seat, Bus, RoutePrice

from django.shortcuts import render, get_object_or_404, redirect

from .models import Bus, Seat, RoutePrice
from django.shortcuts import render, get_object_or_404, redirect

from .models import Bus, Seat, RoutePrice

from django.shortcuts import get_object_or_404, render, redirect
from .models import Bus, Seat, RoutePrice, Discount, BusSchedule

from booking.models import BusSchedule

from datetime import datetime
from django.http import HttpResponse

from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_date

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.utils.dateparse import parse_date
from datetime import datetime
from .models import BusSchedule, Seat, RoutePrice, Discount

from decimal import Decimal
from django.utils.dateparse import parse_date
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import BusSchedule, Seat, RoutePrice, Discount

from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.utils.dateparse import parse_date
from .models import BusSchedule, Seat, RoutePrice, Discount

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.utils.dateparse import parse_date
from decimal import Decimal
from .models import BusSchedule, Seat, RoutePrice, Discount  # adjust your imports if needed

from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.utils.dateparse import parse_date
from .models import BusSchedule, Seat, RoutePrice, Discount
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.utils.dateparse import parse_date

from .models import (
    BusSchedule,
    Seat,
    Discount,
    RoutePrice
)
from django.utils.timezone import now  # Make sure this is imported

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.utils.dateparse import parse_date
from decimal import Decimal
from .models import BusSchedule, Seat, RoutePrice, Discount

from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.utils.dateparse import parse_date
from django.utils.timezone import now
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta



from .models import BusSchedule, Seat, RoutePrice, Discount

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.utils.timezone import now
from datetime import timedelta
from decimal import Decimal
from .models import BusSchedule, Seat, RoutePrice, Discount
from django.utils.dateparse import parse_date


from django.contrib.auth.decorators import login_required

# @login_required(login_url='/users/auth/') 
def home(request):
    return render(request, 'booking/home.html')
#==================================================================================

def about_page(request):
    return render(request, 'booking/about.html')

def seat_selection(request, schedule_id):
    travel_date = None

    # Step 1: Handle travel_date from POST
    if request.method == "POST":
        travel_date_str = request.POST.get("travel_date")
        if travel_date_str:
            try:
                travel_date = parse_date(travel_date_str)
            except ValueError:
                return HttpResponse("Invalid date format", status=400)

    # Step 2: Get the bus schedule
    if travel_date:
        schedule = get_object_or_404(
            BusSchedule.objects.select_related('bus__route'),
            id=schedule_id,
            date=travel_date
        )
    else:
        schedule = get_object_or_404(
            BusSchedule.objects.select_related('bus__route'),
            id=schedule_id
        )

    bus = schedule.bus

    # Step 3: Seat Layout & Normalize Seat IDs
    seat_layout = bus.get_seat_layout()
    seat_layout = [
        [seat.strip().upper() if seat != 'aisle' else 'aisle' for seat in row]
        for row in seat_layout
    ]

    # Step 4: Unlock expired seats for this schedule
    Seat.objects.filter(
        bus=bus,
        is_locked=True,
        locked_at__lt=now() - timedelta(minutes=1)
    ).update(is_locked=False, locked_at=None)

    # Step 5: Booked + Locked Seats for this schedule
    booked_seats = list(
        Seat.objects.filter(
            bus=bus,
            is_booked=True
        ).values_list("seat_number", flat=True)
    )


    locked_seats = list(
        Seat.objects.filter(
            bus=bus,
            is_locked=True
        ).values_list("seat_number", flat=True)
    )
    unavailable_seats = booked_seats + locked_seats




    # Step 6: Get dynamic seat price
    route_price = get_object_or_404(RoutePrice, route=bus.route)
    seat_price = Decimal(route_price.get_price(bus.is_ac))

    # Step 7: Handle seat selection form submission
    if request.method == "POST" and "selected_seats" in request.POST:
        selected_seats = request.POST.getlist("selected_seats")
        selected_seats = [seat.strip().upper().zfill(2) for seat in selected_seats]

        seat_count = len(selected_seats)

        # ✅ Lock selected seats if available
        seat_objects = Seat.objects.filter(
            bus=bus,
            seat_number__in=selected_seats,
            is_booked=False,
            is_locked=False
        )

        if seat_objects.count() != seat_count:
            messages.error(request, "The seats were just booked. Please select another seats.")
            return redirect("seat_selection", schedule_id=schedule.id)

        # Lock the seats temporarily
        seat_objects.update(is_locked=True, locked_at=now())

        # Apply discount
        total_price = seat_price * seat_count
        discount_applied = Decimal("0.00")
        discount = Discount.objects.filter(min_seats__lte=seat_count).order_by("-min_seats").first()
        if discount:
            discount_applied = (Decimal(discount.discount_percentage) / 100) * total_price
            total_price -= discount_applied

        # Save in session
        request.session["selected_seats"] = selected_seats
        request.session["total_price"] = str(total_price)
        request.session["discount_applied"] = str(discount_applied)
        request.session["schedule_id"] = schedule.id

        return redirect("booking_confirmation", schedule_id=schedule.id)

    # Step 8: Render seat selection page
    context = {
        "bus": bus,
        "schedule": schedule,
        "seat_layout": seat_layout,
        "booked_seats": booked_seats,
        "seat_price": seat_price,
    }
    return render(request, "booking/seat_selection.html", context)


#-----------------------------------------------------------------------------------------------------------------------------------------------------------------
from django.http import JsonResponse
from .models import Seat, Bus

def get_booked_seats(request, bus_id):
    bus = get_object_or_404(Bus, id=bus_id)
    booked_seats = list(Seat.objects.filter(bus=bus, is_booked=True).values_list("seat_number", flat=True))
    return JsonResponse({"booked_seats": booked_seats})


#------------------------------------------------------------------------------------------------------------------
# Payment Page
@login_required
def payment_page(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, "booking/payment.html", {"booking": booking})

# Payment Success (Now Sending Email Confirmation)
def payment_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    email = EmailMessage(
        subject="Bus Ticket Confirmed!",
        body=f"Hello {booking.passenger_name}, your seat {booking.seat_number} is confirmed!",
        to=[booking.email]
    )
    email.send()
    return render(request, "booking/confirmation.html", {"booking": booking})

# Dashboard (User's Bookings)
@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(email=request.user.email).order_by("-date")
    return render(request, "booking/dashboard.html", {"bookings": bookings})



# Booking Confirmation & PDF Generation -------------------------------------------------------------------------------
from django.shortcuts import render, redirect, get_object_or_404

from django.contrib import messages
from django.utils.timezone import now
from django.core.mail import send_mail
from django.conf import settings
from .models import Bus, Seat, Booking

from .models import Bus, BusSchedule

from decimal import Decimal

def booking_confirmation(request, schedule_id):
    """Confirm seat selection before payment"""
    schedule = get_object_or_404(BusSchedule, id=schedule_id)
    bus = schedule.bus

    selected_seats = request.session.get("selected_seats", [])
    total_price = request.session.get("total_price", "0")
    discount_applied = request.session.get("discount_applied", "0")

    # Convert to Decimal for calculation
    total_price = Decimal(total_price)
    discount_applied = Decimal(discount_applied)

    # Calculate original price before discount
    price_without_discount = total_price + discount_applied

    # Calculate discount percentage (safe against division by zero)
    if price_without_discount > 0 and discount_applied > 0:
        discount_percentage = round((discount_applied / price_without_discount) * 100)
    else:
        discount_percentage = 0

    if request.method == "POST":
        passenger_name = request.POST.get("passenger_name")
        passenger_age = request.POST.get("passenger_age")
        passenger_email = request.POST.get("passenger_email")

        request.session["passenger_name"] = passenger_name
        request.session["passenger_age"] = passenger_age
        request.session["passenger_email"] = passenger_email
        request.session["total_price"] = str(total_price)
        request.session.modified = True

        return redirect("process_payment", schedule_id=schedule.id)

    return render(request, 'booking/confirmation.html', {
        'bus': bus,
        'schedule': schedule,
        'seats': selected_seats,
        'price': price_without_discount,
        'total_price': total_price,
        'discount_applied': discount_applied,
        'discount_percentage': discount_percentage,
        'bus_id': bus.id,
        'bus_routes': BusRoute.objects.filter(bus=bus),
    })


##-------------------------------------------------------------------------------------------------------------------
# bus_lists
def bus_list(request):
    buses = Bus.objects.select_related('route').all()  # Optimized query
    return render(request, 'booking/bus_list.html', {'buses': buses})


from django.shortcuts import render
from django.utils.dateparse import parse_date
from .models import BusSchedule

from django.shortcuts import render
from .models import BusSchedule
from django.utils.dateparse import parse_date

def search_buses(request):
    schedules = []
    source = destination = travel_date = None

    if request.method == "POST":
        source = request.POST.get("source", "").strip().title()
        destination = request.POST.get("destination", "").strip().title()
        travel_date_raw = request.POST.get("travel_date")
        travel_date = parse_date(travel_date_raw) if travel_date_raw else None

        print(f"Source: {source}, Destination: {destination}, Travel Date: {travel_date}")

        if source and destination and travel_date:
            schedules = BusSchedule.objects.filter(
                route__source__iexact=source,
                route__destination__iexact=destination,
                date=travel_date
            ).select_related("bus", "route")

    return render(request, "booking/search_buses.html", {
        "schedules": schedules,
        "source": source,
        "destination": destination,
        "travel_date": travel_date
    })

#--------------------------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------------------------------
#payment process

from decimal import Decimal
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now
import razorpay  # Import Razorpay SDK

from .models import BusSchedule, Seat, Booking
from .utils import send_booking_email



from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.timezone import now
from booking.models import Seat, Booking, BusSchedule
from booking.utils import send_booking_email
import razorpay

# Razorpay client setup
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def process_payment(request, schedule_id):
    schedule = get_object_or_404(BusSchedule, id=schedule_id)
    bus = schedule.bus

    seats = request.session.get("selected_seats")
    total_price = request.session.get("total_price", "0")
    discount_applied = request.session.get("discount_applied", "0")
    passenger_name = request.session.get("passenger_name", "").strip()
    passenger_age = request.session.get("passenger_age", "").strip()
    passenger_email = request.session.get("passenger_email", "").strip()

    if request.method == "GET":
        if seats and total_price and passenger_email:
            try:
                total_price_decimal = Decimal(total_price)
                razorpay_order = razorpay_client.order.create({
                    "amount": int(total_price_decimal * 100),
                    "currency": "INR",
                    "payment_capture": "1"
                })
                request.session["razorpay_order_id"] = razorpay_order['id']
            except Exception as e:
                print(f"Razorpay Error (GET): {e}")
                razorpay_order = None
        else:
            razorpay_order = None

        return render(request, "booking/payment.html", {
            "bus": bus,
            "schedule": schedule,
            "seats": seats,
            "total_price": total_price,
            "discount_applied": discount_applied,
            "passenger_name": passenger_name,
            "passenger_email": passenger_email,
            "razorpay_order_id": razorpay_order["id"] if razorpay_order else None,
            "razorpay_key": settings.RAZORPAY_KEY_ID, 
        })

    payment_method = request.POST.get("payment_method")

    try:
        total_price = Decimal(total_price)
        discount_applied = Decimal(discount_applied)
    except:
        messages.error(request, "Price format error. Please try again.")
        return redirect("seat_selection", schedule_id=schedule_id)

    if not seats or total_price <= 0 or not passenger_name or not passenger_email:
        messages.error(request, "Session expired! Please select seats again.")
        return redirect("seat_selection", schedule_id=schedule_id)

    if payment_method == "cash":
        return _finalize_booking(
    request, bus, schedule, seats, total_price,
    passenger_name, passenger_age, passenger_email,
    payment_method="cash"
)


    elif payment_method == "razorpay":
        razorpay_payment_id = request.POST.get("razorpay_payment_id")
        razorpay_order_id = request.POST.get("razorpay_order_id")
        razorpay_signature = request.POST.get("razorpay_signature")

        params_dict = {
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        }

        try:
            razorpay_client.utility.verify_payment_signature(params_dict)
            return _finalize_booking(
    request, bus, schedule, seats, total_price,
    passenger_name, passenger_age, passenger_email,
    payment_method="razorpay",
    transaction_id=razorpay_payment_id
)

        except:
            messages.error(request, "Payment verification failed.")
            return redirect("seat_selection", schedule_id=schedule_id)

    messages.error(request, "Invalid payment method selected.")
    return redirect("seat_selection", schedule_id=schedule_id)

def _finalize_booking(request, bus, schedule, seats, total_price, passenger_name, passenger_age, passenger_email, payment_method=None, transaction_id=None):
    seat_objects = Seat.objects.filter(
        bus=bus,
        seat_number__in=seats,
        is_locked=True,
        is_booked=False
    )

    if seat_objects.count() != len(seats):
        messages.error(request, "❌ Some seats are no longer available. Please try again.")
        return redirect("seat_selection", schedule_id=schedule.id)

    seat_numbers = ", ".join(seat_objects.values_list("seat_number", flat=True))
    booking = Booking.objects.create(
        bus=bus,
        schedule=schedule,
        route=schedule.route,
        type=bus.type,
        price=total_price / len(seats),
        total_price=total_price,
        date=now(),
        user=request.user if request.user.is_authenticated else None,
        passenger_name=passenger_name,
        passenger_age=passenger_age,
        passenger_email=passenger_email,
        is_confirmed=True,
        seat_numbers=seat_numbers
    )

    seat_objects.update(is_booked=True, is_locked=False, locked_at=None)
    booking.seats.set(seat_objects)
    from .models import Payment  # Ensure this is at the top of your file

    # ✅ Create Payment record
    Payment.objects.create(
        booking=booking,
        transaction_id=transaction_id,
        amount=total_price,
        status="Completed" if payment_method == "razorpay" else "Pending",
        payment_method="Online" if payment_method == "razorpay" else "Cash"
    )


    # ✅ Send the email
    send_booking_email(passenger_name, bus, booking, seats, total_price, passenger_email)
    # ✅ Clear selected seats and related session data
    request.session.pop("selected_seats", None)
    request.session.pop("total_price", None)
    request.session.pop("discount_applied", None)
    request.session.pop("schedule_id", None)
    request.session.pop("passenger_name", None)
    request.session.pop("passenger_age", None)
    request.session.pop("passenger_email", None)
    request.session.pop("razorpay_order_id", None)

    messages.success(request, "✅ Booking confirmed! Ticket has been emailed.")
    return redirect("ticket_success", booking_id=booking.id)

#-----------------------------------------------------------------
from django.shortcuts import render, get_object_or_404
from .models import Booking
from users.models import Profile

def ticket_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, "booking/ticket_success.html", {"booking": booking})

#----------------------------------------------------------------------------------------------
from django.http import HttpResponse
from booking.utils import send_booking_email

def download_ticket(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)  # Fetch booking details
    bus = booking.bus  # Get the bus details
    seats = booking.seats.values_list("seat_number", flat=True)  # Get seat numbers
    passenger_name = booking.passenger_name
    total_price = booking.total_price

    # Generate the e-ticket PDF
    pdf_data = generate_ticket_pdf(passenger_name, bus, booking, seats, total_price)

    # Serve the PDF as an attachment for download
    response = HttpResponse(pdf_data, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="E-Ticket_{booking.id}.pdf"'
    return response
#-----------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------------
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

@login_required
def get_user_favicon(request):
    user = request.user
    if user.is_authenticated and hasattr(user, "profile"):
        return JsonResponse({"favicon_url": user.profile.image.url})  # Profile image
    return JsonResponse({"favicon_url": "/static/favicon.ico"})  # Default favicon
#--------------------------------------------------------------------------------------------------------------------------------------------------


from django.shortcuts import render, redirect

from .forms import FeedbackForm

def feedback_view(request):
    if request.method == 'POST':
        # Get the feedback form data
        form = FeedbackForm(request.POST)
        if form.is_valid():
            # Create a new Feedback object
            feedback = form.save(commit=False)

            # If the user is authenticated, assign the user to the feedback
            if request.user.is_authenticated:
                feedback.user = request.user

            # Save the feedback to the database
            feedback.save()

            # Redirect to a thank you page after feedback is saved
            return redirect('thank_you')  # Adjust the URL name as necessary
    else:
        form = FeedbackForm()

    return render(request, 'booking/feedback.html', {'form': form})

#==========================================================================
# views.py

from django.shortcuts import render

def thank_you_view(request):
    # You can render a 'thank_you.html' template or simply return a response.
    return render(request, 'booking/thank_you.html')
