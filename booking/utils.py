from io import BytesIO
from datetime import time
import qrcode

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

from django.core.mail import EmailMessage
from django.conf import settings

import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
import qrcode
from django.conf import settings  # Make sure settings is imported

from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from django.conf import settings
import os
import qrcode

from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from django.conf import settings
import qrcode
import os


from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from django.conf import settings
from io import BytesIO
import qrcode
import os

from datetime import timedelta
from django.utils.timezone import now
from .models import Seat  # adjust based on your file structure

def unlock_expired_seats():
    threshold = now() - timedelta(minutes=10)
    Seat.objects.filter(is_locked=True, locked_at__lt=threshold).update(is_locked=False, locked_at=None)



def generate_ticket_pdf(passenger_name, bus, booking, seats, total_price):
    """Generates a visually enhanced branded PDF e-ticket with NGarage logo."""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    schedule = booking.schedule
    bus = schedule.bus
    route = schedule.route

    source = route.source if route else "N/A"
    destination = route.destination if route else "N/A"

    # Format full scheduled datetime
    scheduled_date = schedule.date.strftime('%B %d, %Y')
    scheduled_time = (
        schedule.departure_time.strftime('%I:%M %p')
        if schedule and schedule.departure_time
        else "N/A"
    )
    full_schedule = f"{scheduled_date} at {scheduled_time}"

    duration = f"{schedule.duration}" if hasattr(schedule, 'duration') and schedule.duration else "N/A"
    bus_type = booking.type  # 'AC' or 'Non-AC'

    # Header background
    p.setFillColor(colors.HexColor("#004080"))
    p.rect(0, 700, 600, 100, fill=True, stroke=False)

    # Add NGarage logo to header (top left corner)
    logo_path = os.path.join(settings.STATIC_ROOT, 'img', 'ngarage_logo.png')
    if os.path.exists(logo_path):
        logo = ImageReader(logo_path)
        p.drawImage(logo, 40, 715, width=60, height=60, mask='auto')

    # Add title in header
    p.setFont("Helvetica-Bold", 24)
    p.setFillColor(colors.white)
    p.drawCentredString(300, 740, "Bus Ticket - E-Ticket")

    # Ticket details
    y = 660
    line_height = 22
    p.setFillColor(colors.black)

    def draw_label_value(label, value):
        nonlocal y
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, f"{label}:")
        p.setFont("Helvetica", 12)
        p.drawString(180, y, str(value))
        y -= line_height

    draw_label_value("Passenger Name", passenger_name)
    draw_label_value("Bus Name", bus.name)
    draw_label_value("Bus Number", bus.number)
    draw_label_value("Type", bus_type)
    draw_label_value("Route", f"{source} → {destination}")
    draw_label_value("Scheduled Time", full_schedule)
    draw_label_value("Seats", ', '.join(seats))
    draw_label_value("Total Price", f"INR {float(total_price):,.2f}")
    draw_label_value("Booking Date", booking.date.strftime('%Y-%m-%d %H:%M'))

    # Horizontal separator
    p.setStrokeColor(colors.grey)
    p.setLineWidth(1)
    p.line(50, y, 550, y)
    y -= line_height + 10

    # QR Code content
    qr_data = (
        f"Ticket ID: {booking.id}\n"
        f"Passenger: {passenger_name}\n"
        f"Bus: {bus.name}\n"
        f"Route: {source} → {destination}\n"
        f"Scheduled Time: {full_schedule}\n"
        f"Seats: {', '.join(seats)}\n"
        f"Amount: ₹{total_price}"
    )

    qr = qrcode.make(qr_data)
    qr_buffer = BytesIO()
    qr.save(qr_buffer, format="PNG")
    qr_image = ImageReader(qr_buffer)
    p.drawImage(qr_image, 400, y - 10, width=100, height=100)

    # Footer message
    p.setFont("Helvetica-Oblique", 10)
    p.setFillColor(colors.black)
    p.drawString(50, y - 40, "Thank you for choosing NGarage! Have a safe journey. Contact: xxx490xxxx")

    # Add logo again at bottom right
    if os.path.exists(logo_path):
        p.drawImage(logo, 480, 40, width=70, height=70, mask='auto')

    # Finalize PDF
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

 #-------------------------------------------------------------------------------------------------------



from django.core.mail import EmailMessage
from django.conf import settings
from .utils import generate_ticket_pdf  # Make sure this import is correct

def send_booking_email(passenger_name, bus, booking, seats, total_price, passenger_email):
    """Sends the booking confirmation email with an attached e-ticket PDF."""

    # Safely access source and destination via the route
    route = booking.schedule.route
    source = route.source if route else "N/A"
    destination = route.destination if route else "N/A"

    subject = "Your Bus Ticket Confirmation"
    message = f"""
Hello {passenger_name},

Your ticket has been successfully booked. Please find your e-ticket attached.

Booking Details:
Bus: {bus.name} ({booking.type})
From: {source} To: {destination}
Date: {booking.schedule.date.strftime('%Y-%m-%d')}
Time: {
    booking.schedule.departure_time.strftime('%I:%M %p')
    if booking.schedule and booking.schedule.departure_time
    else "N/A"
}

Seats: {', '.join(seats)}
Total Paid: ₹{total_price}

Thank you for choosing our service!

Regards,
Bus Ticket Booking Team
    """

    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[passenger_email]
    )

    # Generate and attach PDF using bus info
    pdf_buffer = generate_ticket_pdf(passenger_name, bus, booking, seats, total_price)
    email.attach(f"E-Ticket_{booking.id}.pdf", pdf_buffer.getvalue(), "application/pdf")

    try:
        email.send()
        print("✅ Email sent successfully.")
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
