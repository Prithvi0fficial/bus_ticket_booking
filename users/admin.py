from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ("username", "email", "is_staff", "is_superuser")
    search_fields = ("email", "username")
    ordering = ("email",)

admin.site.register(CustomUser, CustomUserAdmin)

