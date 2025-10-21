from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserProfile, Booking

# Customize the User display in admin
class CustomUserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'date_joined', 'is_active', 'password_hash_preview')
    list_filter = ('is_active', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)
    
    def password_hash_preview(self, obj):
        """Show first 20 characters of password hash"""
        return obj.password[:20] + "..."
    password_hash_preview.short_description = 'Password Hash'

# Booking Admin
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_reference', 'user', 'origin', 'destination', 'departure_date', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'trip_type', 'shipping_line', 'created_at')
    search_fields = ('booking_reference', 'user__username', 'origin', 'destination')
    ordering = ('-created_at',)
    readonly_fields = ('booking_reference', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('booking_reference', 'user', 'status')
        }),
        ('Trip Details', {
            'fields': ('trip_type', 'origin', 'destination', 'departure_date', 'return_date', 'shipping_line')
        }),
        ('Passenger Information', {
            'fields': ('adults', 'children', 'total_price')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

# Unregister the default and register with customization
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(UserProfile)
admin.site.register(Booking, BookingAdmin)