from django.shortcuts import render

# Create your views here.
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.conf import settings
from .models import CustomUser  # Make sure this points to your custom user model

def auth_view(request):
    if request.method == "POST":
        action = request.POST.get("action")

        email = request.POST.get("email")
        password = request.POST.get("password")

        if action == "signup":
            username = request.POST.get("username")
            confirm_password = request.POST.get("confirm_password")

            if password != confirm_password:
                messages.error(request, "❌ Passwords do not match.")
                return redirect("auth")

            if CustomUser.objects.filter(username=username).exists():
                messages.error(request, "❌ Username already taken.")
                return redirect("auth")

            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, "❌ Email already registered. Try logging in.")
                return redirect("auth")

            # Generate verification token
            verification_token = get_random_string(32)

            # Create user with is_verified=False
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_verified=False,
                verification_token=verification_token,
                verification_token_created_at=timezone.now()
            )
            user.save()

            # Send verification email
            verify_link = request.build_absolute_uri(
                reverse("verify_email", args=[verification_token])
            )

            send_mail(
                "Verify Your Email - NGarage",
                f"Hi {username},\n\nPlease click the link below to verify your email:\n{verify_link}\n\nThanks for registering!",
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )

            messages.success(request, "📩 Verification link sent to your email. Please verify to log in.")
            return redirect("auth")

        elif action == "login":
            username_or_email = request.POST.get("username")
            user = authenticate(request, username=username_or_email, password=password)

            if user is not None:
                if user.is_verified or user.is_superuser:
                    login(request, user)
                    if user.is_superuser:
                        return redirect("admin:index")  # Django admin panel home page
                    elif user.is_staff:
                        return redirect("admin:index")  # your custom staff dashboard URL name
                    else:
                        return redirect("home")
                else:
                    messages.error(request, "❌ Email not verified. Please check your inbox.")
            else:
                messages.error(request, "❌ Invalid email/username or password.")

        elif action == "forgot_password":
            user = CustomUser.objects.filter(email=email).first()
            if user:
                reset_token = get_random_string(32)
                user.reset_token = reset_token
                user.save()

                reset_link = f"http://127.0.0.1:8000/reset-password/{reset_token}/"
                send_mail(
                    "Password Reset Request",
                    f"Click the link below to reset your password:\n{reset_link}",
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                messages.success(request, "📩 Password reset link sent to your email.")
            else:
                messages.error(request, "❌ Email not found in our records.")

            return redirect("auth")

    return render(request, "users/auth.html")

#------------------------------------------------------------------------------------------------------------------------
# password reset    
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
import base64
import json

User = get_user_model()

def reset_password(request):
    if request.method == "POST":
        email = request.POST.get("email")
        user = User.objects.filter(email=email).first()
        
        if user:
            # Generate timestamp
            timestamp = int(now().timestamp())  # Current time in seconds

            # Encode user ID and timestamp together
            data = json.dumps({"uid": user.pk, "ts": timestamp})
            encoded_data = base64.urlsafe_b64encode(data.encode()).decode()

            # Generate token
            token = default_token_generator.make_token(user)

            # Create password reset URL
            reset_url = request.build_absolute_uri(
                reverse("password_reset_confirm", kwargs={"uidb64": encoded_data, "token": token})
            )

            # Send email
            subject = "Password Reset Request"
            message = f"Click the link below to reset your password (valid for 5 minutes):\n\n{reset_url}"
            print("Sending email to:", email)
            send_mail(subject, message, "noreply@yourdomain.com", [email])

            messages.success(request, "A reset link has been sent to your email.")
        else:
            messages.error(request, "No account found with that email.")

        return redirect("auth")  # Redirect to login page

    return render(request, 'users/reset_password.html')

#------------------------------------------------------------------------------------------------------------
# confirmation_reset time out 
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.shortcuts import render, redirect
from django.contrib import messages
import base64
import json

User = get_user_model()

def password_reset_confirm(request, uidb64, token):
    try:
        # Decode the received uidb64 (which contains user ID and timestamp)
        decoded_data = base64.urlsafe_b64decode(uidb64.encode()).decode()
        data = json.loads(decoded_data)

        user_id = data["uid"]
        timestamp = data["ts"]

        # Check if the token is expired (5-minute validity)
        current_time = int(now().timestamp())
        if current_time - timestamp > 300:  # 300 seconds = 5 minutes
            messages.error(request, "This password reset link has expired. Please request a new one.")
            return redirect("password_reset")

        # Fetch user from the database
        user = User.objects.get(pk=user_id)

        # Validate the token
        if not default_token_generator.check_token(user, token):
            messages.error(request, "Invalid reset link.")
            return redirect("password_reset")

        if request.method == "POST":
            new_password = request.POST.get("password")
            confirm_password = request.POST.get("confirm_password")

            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, "Your password has been reset successfully. You can now log in.")
                return redirect("auth")
            else:
                messages.error(request, "Passwords do not match.")

        return render(request, "set_new_password.html", {"uidb64": uidb64, "token": token})

    except Exception as e:
        messages.error(request, "Invalid request.")
        return redirect("password_reset_complete")



#---------------------------------------------------------------------------------------------------------
from django.contrib.auth import logout

def user_logout(request):
    logout(request)
    return redirect("auth")  # Redirect to login/signup page after logout

#-------------------------------------------------------------------------------------------

# dashbord
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile  # Adjust based on app name
from booking.models import Booking  # Your Booking model
from datetime import datetime
from .forms import ProfileUpdateForm  # Optional form to update details
from django.utils import timezone
from booking.models import Booking, SeatBooking
import logging
logger = logging.getLogger(__name__)




@login_required
def user_dashboard(request):
    user = request.user
    
    # Ensure profile exists (create if missing)
    profile, created = Profile.objects.get_or_create(user=user)

    # Booking history - both past and upcoming
    bookings = Booking.objects.filter(user=user).order_by('-booked_at')
    
    context = {
        'profile': profile,
        'bookings': bookings,
        "now": timezone.now(),
    }
    return render(request, 'users/dashboard.html', context)


@login_required
def cancel_booking(request, booking_id):
    logger.error(f"CANCEL BOOKING VIEW CALLED for booking {booking_id}")

    try:
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)

        if booking.status == 'Cancelled':
            messages.warning(request, "This ticket is already cancelled.")
            return redirect('user_dashboard')

        if timezone.now() > booking.schedule.departure_time:
            messages.error(request, "Cannot cancel after departure time.")
            return redirect('user_dashboard')

        logger.error("Releasing seats...")

        # -----------------------
        # RELEASE SEATS CORRECTLY
        # -----------------------
        seat_bookings = SeatBooking.objects.filter(booking=booking)

        for sb in seat_bookings:
            seat = sb.seat
            seat.is_booked = False   # release the seat
            seat.save()
            logger.error(f"Released seat {seat.seat_number}")

        # Delete seat-booking rows
        seat_bookings.delete()

        # Update booking fields
        booking.status = 'Cancelled'
        booking.is_confirmed = False
        booking.cancelled_at = timezone.now()
        booking.save()

        logger.error("Booking cancelled and seats released.")
        messages.success(request, "Ticket cancelled successfully.")
        return redirect('user_dashboard')

    except Exception as e:
        logger.error(f"CANCEL BOOKING ERROR: {str(e)}")
        raise


@login_required
def update_profile(request):
    profile = Profile.objects.get(user=request.user)

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.info(request, "Profile updated successfully.")
            return redirect('user_dashboard')
    else:
        form = ProfileUpdateForm(instance=profile)

    return render(request, 'users/update_profile.html', {'form': form ,'profile': profile})

#----------------------------------------------------------
from datetime import timedelta
from django.utils import timezone

def verify_email(request, token):
    try:
        user = CustomUser.objects.get(verification_token=token)
    except CustomUser.DoesNotExist:
        messages.error(request, "❌ Invalid verification token.")
        return redirect("auth")

    # Check if token is expired (valid for 24 hours)
    expiry_time = user.verification_token_created_at + timedelta(hours=24)
    if timezone.now() > expiry_time:
        messages.error(request, "⏰ Verification link expired. Please resend verification email.")
        return redirect("resend_verification")  # We'll create this next

    # Mark user as verified
    user.is_verified = True
    user.verification_token = None
    user.verification_token_created_at = None
    user.save()

    messages.success(request, "✅ Email verified successfully. You can now log in.")
    return redirect("auth")
    
    #---------------------------------------------
def resend_verification(request):
    if request.method == "POST":
        email = request.POST.get("email")
        user = CustomUser.objects.filter(email=email, is_verified=False).first()

        if user:
            user.verification_token = get_random_string(32)
            user.verification_token_created_at = timezone.now()
            user.save()

            verify_link = f"http://127.0.0.1:8000/verify-email/{user.verification_token}/"
            send_mail(
                "Resend Verification - NGarage",
                f"Hi {user.username},\n\nClick to verify your email:\n{verify_link}",
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )

            messages.success(request, "📩 Verification link resent. Check your email.")
        else:
            messages.error(request, "❌ Email not found or already verified.")

    return render(request, "users/resend_verification.html")
#------------------------------------------------------------------------------------------------
#nav bar
# views.py
from django.shortcuts import render

def navbar_view(request):
    return render(request, 'booking/navbar.html')
#=====================================================================================================
from django.shortcuts import render

def terms_and_conditions(request):
    return render(request,'users/terms.html')

