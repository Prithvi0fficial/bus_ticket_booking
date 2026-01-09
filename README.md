# Bus Booking System (Django)

## Description
A web-based bus ticket booking system with dynamic seat selection, Razorpay payments, and email ticket confirmation.

[Click here to view the live demo](https://bus-ticket-booking-pqjs.onrender.com)

⭐IMP:

Please select the date  Dec 31 or Jan 3 
and route Mangalore To Bangalore ONLY

## Features
- Dynamic seat booking with bus layout
- Cash on delivery & Razorpay payment
- Email ticket confirmation with PDF
- User dashboard for booking history and cancellations
- Admin panel for trip management
- Discount application

## Technologies Used
- Python (Django)
- SQLite / MySQL
- HTML, CSS, JavaScript

## Setup
1. Clone the repository
```bash
https://github.com/Prithvi0fficial/bus_ticket_booking.git
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver  



### 🛠️ Technical Challenge: SMTP Blocking & Seat Release Logic

The Problem: During deployment on Render, the default SMTP port (587) was restricted, preventing the booking confirmation emails from sending. Because the Seat Release logic was tied to the completion of the email task, any failure in the SMTP handshake caused the seat to remain "Locked" even if the booking was cancelled or failed.
