from django.db import models
from django.contrib.auth.models import User
import random
import string

class UserProfile(models.Model):
    """
    Extended user profile to store additional information
    This extends Django's built-in User model
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_admin_user = models.BooleanField(default=False, help_text="Designates whether this user can access the admin dashboard.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    photo = models.ImageField(upload_to="profile_photos/", blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'


class Booking(models.Model):
    """
    Model to store ferry booking information
    """
    TRIP_TYPE_CHOICES = [
        ('one_way', 'One Way'),
        ('round_trip', 'Round Trip'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reserved', 'Reserved'),
        ('expired', 'Expired'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    # User information
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    
    # Trip details
    trip_type = models.CharField(max_length=20, choices=TRIP_TYPE_CHOICES, default='one_way')
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    departure_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    shipping_line = models.CharField(max_length=100)
    
    # Passenger details
    adults = models.IntegerField(default=0)
    children = models.IntegerField(default=0)
    
    # Booking information
    booking_reference = models.CharField(max_length=20, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Reservation expiration
    reserved_until = models.DateTimeField(null=True, blank=True, help_text="If reserved, booking is held until this datetime.")

    # Stores passenger, pricing, and voyage metadata captured during reservation
    details = models.JSONField(blank=True, null=True, default=dict)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def generate_booking_reference(self):
        """
        Generate a random booking reference: HH-XXXXXXXX
        Example: HH-A3K9M2L5
        """
        while True:
            # Generate 8 random characters (uppercase letters and digits)
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            booking_ref = f"HH-{code}"
            
            # Check if this reference already exists
            if not Booking.objects.filter(booking_reference=booking_ref).exists():
                return booking_ref
    
    def save(self, *args, **kwargs):
        # Generate booking reference if it doesn't exist
        if not self.booking_reference:
            self.booking_reference = self.generate_booking_reference()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.booking_reference} - {self.user.username} ({self.origin} to {self.destination})"

    @property
    def is_expired(self):
        return self.status == 'expired'

    @property
    def is_confirmed(self):
        return self.status == 'confirmed'
    
    class Meta:
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
        ordering = ['-created_at']