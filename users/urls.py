from django.urls import path, include
from . import views

from django.contrib.auth.views import (
    PasswordResetView,  #  Added this for handling password reset
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetCompleteView,
)
from .views import auth_view,user_logout
urlpatterns = [
    # User authentication (Login & Signup)
    path("auth/", auth_view, name="auth"),
    path("login/", auth_view, name="login"),  



    path('navbar/', views.navbar_view, name='navbar'),      
    # Dashboard & User Settings
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('cancel-booking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('update-profile/', views.update_profile, name='update_profile'),
    
    # Verification
    path("resend-verification/", views.resend_verification, name="resend_verification"),
    path("verify-email/<str:token>/", views.verify_email, name="verify_email"),

    #  Password Reset using Django's built-in views
    path("reset-password/", PasswordResetView.as_view(template_name="users/reset_password.html"), name="reset_password"),
    path("reset-password/done/", PasswordResetDoneView.as_view(template_name="users/password_reset_done.html"), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", PasswordResetConfirmView.as_view(template_name="users/password_reset_confirm.html"), name="password_reset_confirm"),
    path("reset/done/", PasswordResetCompleteView.as_view(template_name="users/password_reset_complete.html"), name="password_reset_complete"),
    path("logout/", user_logout, name="user_logout"),
    #cancel ticket
    path('cancel-booking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    #terms
    path('terms/',views.terms_and_conditions,name='terms_and_conditions'),
    

    # Social Authentication (allauth)
    path("accounts/", include("allauth.urls")),

]
