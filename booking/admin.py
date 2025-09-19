from django.contrib import admin, messages
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from booking.models import Bus, Seat, RoutePrice, Payment, Booking, BusSchedule, Discount, Route, Feedback
from django.contrib.auth import get_user_model

User = get_user_model()


# ----------------------
# Register basic models
# ----------------------
admin.site.register(Route)
admin.site.register(Discount)


# ----------------------
# Booking Admin
# ----------------------
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'passenger_name',
        'schedule',
        'get_route',
        'date',
        'is_confirmed',
        'status',
        'price',
        'total_price',
        'booked_at',
    )
    list_filter = ('is_confirmed', 'status', 'schedule__bus', 'schedule__route', 'date')
    search_fields = ('passenger_name', 'passenger_email', 'user__username', 'schedule__bus__name')

    # ✅ FIX: ManyToMany field "seats" must use filter_horizontal
    filter_horizontal = ('seats',)
    autocomplete_fields = ['user', 'schedule']

    fieldsets = (
        ('Bus & Schedule', {
            'fields': ('schedule', 'date')
        }),
        ('Passenger Details', {
            'fields': ('user', 'passenger_name', 'passenger_age', 'passenger_email')
        }),
        ('Seat & Pricing', {
            'fields': ('seats', 'seat_numbers', 'type', 'price', 'total_price')
        }),
        ('Booking Status', {
            'fields': ('is_confirmed', 'status', 'refund_status')
        }),
        ('Timestamps', {
            'fields': ('booked_at', 'cancelled_at')
        }),
    )

    readonly_fields = ('booked_at', 'cancelled_at')
    ordering = ('-booked_at',)

    # ----------------------
    # Custom method for route display
    # ----------------------
    def get_route(self, obj):
        if obj.schedule and obj.schedule.route:
            return f"{obj.schedule.route.source} → {obj.schedule.route.destination}"
        return "-"
    get_route.short_description = 'Route'

    # ----------------------
    # Save model override
    # ----------------------
    def save_model(self, request, obj, form, change):
        # Safely set bus and route based on schedule
        if obj.schedule:
            if obj.schedule.bus:
                obj.bus = obj.schedule.bus
            if obj.schedule.route:
                obj.route = obj.schedule.route
        super().save_model(request, obj, form, change)

        # Update seat_numbers if seats changed
        if 'seats' in form.changed_data:
            seat_numbers_list = obj.seats.all().values_list('seat_number', flat=True)
            obj.seat_numbers = ", ".join(seat_numbers_list)
            obj.save()


# ----------------------
# Bus Admin
# ----------------------
@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ('name', 'number', 'type', 'timing', 'get_dynamic_price', 'reset_seats_button')
    list_filter = ('type',)
    search_fields = ('name', 'number')
    fields = ('name', 'number', 'type', 'route', 'price', 'seat_layout', 'timing')
    ordering = ['timing']

    # Custom dynamic price display
    def get_dynamic_price(self, obj):
        if not obj.route:
            return "No Route"
        route_price = RoutePrice.objects.filter(route=obj.route).first()
        if route_price:
            try:
                is_ac_bus = obj.type == "AC"
                final_price = route_price.get_price(is_ac_bus)
                return f"₹{final_price:.2f}"
            except Exception:
                return "Invalid Price"
        return "Price Not Available"
    get_dynamic_price.short_description = "Price (Dynamic)"

    # ----------------------
    # Reset seats functionality
    # ----------------------
    @csrf_exempt
    def reset_bus_seats(self, request, bus_id):
        bus = Bus.objects.filter(id=bus_id).first()
        if bus:
            updated_count = Seat.objects.filter(bus=bus).update(is_booked=False)
            messages.success(request, f"✅ {updated_count} seats for {bus.name} have been reset!")
        else:
            messages.error(request, "❌ Bus not found!")
        return redirect(request.META.get("HTTP_REFERER", "/admin/booking/bus/"))

    def reset_seats_button(self, obj):
        reset_url = reverse("admin:reset_bus_seats", args=[obj.pk])
        return format_html(
            '<a class="button" style="background: red; color: white; padding: 5px 10px; border-radius: 5px;" href="{}">Reset Seats</a>',
            reset_url
        )
    reset_seats_button.short_description = "Reset Seats"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('reset-seats/<int:bus_id>/', self.admin_site.admin_view(self.reset_bus_seats), name='reset_bus_seats'),
        ]
        return custom_urls + urls


# ----------------------
# Payment Admin
# ----------------------
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'amount', 'status', 'transaction_id')
    fields = ('booking', 'amount', 'payment_method', 'status', 'transaction_id')
    readonly_fields = ('transaction_id',)


# ----------------------
# Route Price Admin
# ----------------------
@admin.register(RoutePrice)
class RoutePriceAdmin(admin.ModelAdmin):
    list_display = ('route', 'base_price', 'ac_increment_percentage')


# ----------------------
# Seat Admin
# ----------------------
@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    search_fields = ['seat_number', 'bus__name']


# ----------------------
# Bus Schedule Admin
# ----------------------
@admin.register(BusSchedule)
class BusScheduleAdmin(admin.ModelAdmin):
    search_fields = ['bus__name', 'route__source', 'route__destination']


# ----------------------
# Feedback Admin
# ----------------------
@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'rating', 'email', 'comment', 'created_at')
    search_fields = ('user', 'email', 'comment')
    list_filter = ('rating',)
