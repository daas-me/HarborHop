from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegistrationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import UserProfile, Booking
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth import update_session_auth_hash
from datetime import datetime, date 
from django.core.cache import cache
import json
import logging
import requests
import string
from django.conf import settings

logger = logging.getLogger(__name__)

def normalize_voyage_data(voyage_data):
    """Normalize voyage data to ensure all required fields exist"""
    if not voyage_data:
        return None
    
    # The data comes directly from JavaScript with flat structure
    return {
        'company': voyage_data.get('company', 'N/A'),
        'vessel': voyage_data.get('vessel', 'N/A'),
        'departureDate': voyage_data.get('departureDate', 'N/A'),
        'departureTime': voyage_data.get('departureTime', 'N/A'),
        'departureDateTime': voyage_data.get('departureDateTime', 'N/A'),
        'accommodationName': voyage_data.get('accommodationName', 'N/A'),
        'seatType': voyage_data.get('seatType', 'N/A'),
        'price': float(voyage_data.get('price', 0)),
        'distance': voyage_data.get('distance', 0),
        'originName': voyage_data.get('originName', ''),
        'destinationName': voyage_data.get('destinationName', ''),
    }


def home(request):
    # Ensure user has a profile if authenticated
    if request.user.is_authenticated:
        try:
            request.user.profile
        except UserProfile.DoesNotExist:
            UserProfile.objects.create(user=request.user)
    
    # Try to get routes data from cache first
    routes_data = cache.get('barkota_routes')
    
    if routes_data is None:
        # Cache miss - fetch from Barkota API
        try:
            url = "https://barkota-reseller-php-prod-4kl27j34za-uc.a.run.app/ob/routes/passageenabled"
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Referer": "https://booking.barkota.com/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            payload = {"companyId": None}
            
            logger.info("Fetching routes from Barkota API (cache miss)")
            
            # Increased timeout to 25 seconds
            response = requests.post(url, json=payload, headers=headers, timeout=25)
            response.raise_for_status()
            routes_data = response.json()
            
            # Validate that we got actual data
            if not routes_data or not isinstance(routes_data, list):
                logger.warning("Barkota API returned empty or invalid data")
                routes_data = []
            else:
                # Cache the data for 10 minutes (600 seconds)
                cache.set('barkota_routes', routes_data, 600)
                logger.info(f"Cached {len(routes_data)} routes for 10 minutes")
                
        except requests.exceptions.Timeout:
            logger.error("Barkota API request timed out")
            routes_data = []
        except requests.exceptions.RequestException as e:
            logger.error(f"Barkota API request failed: {str(e)}")
            routes_data = []
        except Exception as e:
            logger.error(f"Unexpected error fetching routes: {str(e)}")
            routes_data = []
    else:
        # Cache hit - using cached data
        logger.info(f"Using cached routes data ({len(routes_data)} routes)")
    
    today = date.today().isoformat()
    
    return render(request, 'home.html', {
        'today': today,
        'routes_data': json.dumps(routes_data) if routes_data else '[]'
    })
    
def register(request):
    """Handle user registration"""
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Save the User instance (form is a ModelForm for User)
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            # --- IMPORTANT: use the field name that matches your model ---
            dob = form.cleaned_data.get('date_of_birth')  # <-- correct field name

            # Create or get profile and store date_of_birth
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.date_of_birth = dob
            profile.save()

            # Log in and redirect
            login(request, user)
            messages.success(
                request,
                f'Welcome, {user.first_name or user.username}! Your account has been created.'
            )
            return redirect('home')
        # if form invalid, fall through to re-render template with errors
    else:
        form = UserRegistrationForm()

    return render(request, 'register.html', {'form': form})

@never_cache
def user_login(request):
    """Handle user login"""
    # Only redirect if user is authenticated AND it's a GET request (not after logout)
    if request.user.is_authenticated and request.method == 'GET':
        # Check if user is admin
        try:
            if request.user.profile.is_admin_user:
                return redirect('admin_dashboard')
        except UserProfile.DoesNotExist:
            UserProfile.objects.create(user=request.user)
        return redirect('home')
   
    next_url = request.GET.get('next', 'home')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                
                # Check if user is admin and redirect accordingly
                try:
                    if user.profile.is_admin_user:
                        return redirect('admin_dashboard')
                except UserProfile.DoesNotExist:
                    UserProfile.objects.create(user=user)
                
                return redirect(next_url)
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid login details. Please try again.")
    else:
        form = AuthenticationForm()
 
    return render(request, 'login.html', {'form': form})


def user_logout(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully!')
    return redirect('home')

@require_POST
@login_required
def store_booking_selection(request):
    """API endpoint to store booking selections in session."""
    try:
        import json
        data = json.loads(request.body)
        selections = data.get('selections', {})
        meta = data.get('meta', {})
        total_price = data.get('total_price', 0)
        # Save selections, meta, and total_price to session
        request.session['booking_selections'] = selections
        request.session['booking_selections_meta'] = meta
        request.session['booking_selections_total_price'] = total_price
        request.session.modified = True
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def passenger_info(request):
    summary = request.session.get('passenger_info_summary')

    if not summary:
        messages.error(request, 'Please select your trips before entering passenger information.')
        return redirect('home')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Store passenger form data in session
        passenger_data = {}
        for key, value in request.POST.items():
            if key.startswith('passenger_') or key.startswith('contact_'):
                passenger_data[key] = value
        
        request.session['passenger_form_data'] = passenger_data
        
        # Get booking selections from session
        selections = request.session.get('booking_selections', {})
        outbound = selections.get('outbound', {})
        return_trip = selections.get('return', {})
        
        # Normalize the voyage data
        normalized_outbound = normalize_voyage_data(outbound) if outbound else None
        normalized_return = normalize_voyage_data(return_trip) if return_trip else None
        
        # GET ADULTS AND CHILDREN FROM SUMMARY
        adults = summary.get('adults', 1)
        children = summary.get('children', 0)
        
        # VALIDATE CHILDREN'S AGES BASED ON BIRTHDATES
        from datetime import datetime, timedelta
        from dateutil.relativedelta import relativedelta
        
        valid_children_count = 0
        invalid_children = []
        
        # Get departure date for age calculation
        dep_date_str = summary.get('departure_date_formatted', '')
        try:
            departure_date = datetime.strptime(dep_date_str, '%a, %d %b %Y').date()
        except:
            departure_date = datetime.now().date()
        
        # ==========================================
        # FIX: VALIDATE EACH CHILD PASSENGER'S AGE
        # ==========================================
        for i in range(1, children + 1):
            # Calculate the correct passenger number (adults come first)
            passenger_number = adults + i
            
            # FIX: Changed 'birthdate' to 'dob' to match HTML form field
            birthdate_str = request.POST.get(f'passenger_{passenger_number}_dob')
            
            if birthdate_str:
                try:
                    birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d').date()
                    
                    # Calculate age at time of departure
                    age_at_departure = relativedelta(departure_date, birthdate).years
                    
                    # Check if age is between 2-11 years old
                    if 2 <= age_at_departure <= 11:
                        valid_children_count += 1
                    else:
                        invalid_children.append({
                            'number': passenger_number,
                            'age': age_at_departure,
                            'name': request.POST.get(f'passenger_{passenger_number}_first_name', f'Child {i}')
                        })
                except ValueError:
                    invalid_children.append({
                        'number': passenger_number,
                        'age': 'Invalid date',
                        'name': request.POST.get(f'passenger_{passenger_number}_first_name', f'Child {i}')
                    })
            else:
                # FIX: Handle missing birthdate
                invalid_children.append({
                    'number': passenger_number,
                    'age': 'Missing birthdate',
                    'name': request.POST.get(f'passenger_{passenger_number}_first_name', f'Child {i}')
                })
        
        # If there are invalid children, show error and return
        if invalid_children:
            error_messages = []
            for child in invalid_children:
                if child['age'] == 'Invalid date':
                    error_messages.append(f"<strong>Passenger {child['number']}</strong> ({child['name']}): Invalid birthdate format")
                elif child['age'] == 'Missing birthdate':
                    error_messages.append(f"<strong>Passenger {child['number']}</strong> ({child['name']}): Birthdate is required for child discount verification")
                elif child['age'] < 2:
                    error_messages.append(f"<strong>Passenger {child['number']}</strong> ({child['name']}): Age {child['age']} years - Infants under 2 years should be marked as infants, not children")
                else:
                    error_messages.append(f"<strong>Passenger {child['number']}</strong> ({child['name']}): Age {child['age']} years - Only passengers aged 2-11 years qualify for child discount")
            
            # Use mark_safe to allow HTML in the message
            from django.utils.safestring import mark_safe
            messages.error(request, mark_safe(
                '<strong>Child Discount Validation Failed:</strong><br><br>' + 
                '<br>'.join(error_messages) +
                '<br><br><em>Please correct the birthdates or change the passenger type to Adult.</em>'
            ))
            return redirect('passenger_info')
        
        # CALCULATE PRICES WITH VALIDATED CHILDREN
        total_price = 0
        outbound_base_price = 0
        return_base_price = 0

        if normalized_outbound and isinstance(normalized_outbound.get('price'), (int, float)):
            outbound_base_price = normalized_outbound['price']
            # Calculate: (adults * full price) + (valid children * 50% price)
            outbound_total = (outbound_base_price * adults) + (outbound_base_price * valid_children_count * 0.5)
            normalized_outbound['price'] = outbound_total
            normalized_outbound['adult_price'] = outbound_base_price
            normalized_outbound['child_price'] = outbound_base_price * 0.5
            normalized_outbound['valid_children'] = valid_children_count
            total_price += outbound_total
            
        if normalized_return and isinstance(normalized_return.get('price'), (int, float)):
            return_base_price = normalized_return['price']
            # Calculate: (adults * full price) + (valid children * 50% price)
            return_total = (return_base_price * adults) + (return_base_price * valid_children_count * 0.5)
            normalized_return['price'] = return_total
            normalized_return['adult_price'] = return_base_price
            normalized_return['child_price'] = return_base_price * 0.5
            normalized_return['valid_children'] = valid_children_count
            total_price += return_total
        
        # Parse dates
        from datetime import datetime
        dep_date = summary.get('departure_date_formatted', '')
        ret_date = summary.get('return_date_formatted', None)
        
        try:
            if dep_date:
                dep_date = datetime.strptime(dep_date, '%a, %d %b %Y').date()
        except Exception:
            dep_date = None
            
        try:
            if ret_date:
                ret_date = datetime.strptime(ret_date, '%a, %d %b %Y').date()
        except Exception:
            ret_date = None
        
        # Handle "Reserve Booking" action
        if action == 'reserve':
            from django.utils.crypto import get_random_string
            from datetime import timedelta
            
            # Check 2-hour rule
            dep_time_str = normalized_outbound.get('departureDateTime') or normalized_outbound.get('departureTime')
            dep_dt = None
            
            try:
                if dep_time_str:
                    try:
                        dep_dt = datetime.fromisoformat(dep_time_str)
                    except Exception:
                        today = datetime.now().date()
                        dep_dt = datetime.strptime(str(today) + ' ' + dep_time_str, '%Y-%m-%d %I:%M %p')
            except Exception:
                dep_dt = None
            
            now = timezone.now()
            
            if dep_dt and timezone.is_naive(dep_dt):
                dep_dt = timezone.make_aware(dep_dt, timezone.get_current_timezone())
            
            if dep_dt and (dep_dt - now) < timedelta(hours=2):
                messages.error(request, 'You can only reserve if your trip is at least 2 hours away. Please proceed to payment directly.')
                return redirect('passenger_info')
            
            # Create booking with 'reserved' status
            booking_reference = get_random_string(12).upper()
            
            details = {
                'outbound': normalized_outbound,
                'return': normalized_return,
                'total_price': total_price,
                'passengers': passenger_data,
                'infants': summary.get('infants', 0),
            }
            
            booking = Booking.objects.create(
                user=request.user,
                trip_type=summary.get('trip_type', 'one_way'),
                origin=summary.get('origin_name', ''),
                destination=summary.get('destination_name', ''),
                departure_date=dep_date,
                return_date=ret_date,
                adults=summary.get('adults', 1),
                children=valid_children_count,  # FIX: Use validated children count
                booking_reference=booking_reference,
                status='reserved',
                reserved_until=now + timedelta(hours=48),
                total_price=total_price,
                details=details,
            )
            
            messages.success(request, f'Your booking has been reserved! Reference: {booking_reference}')
            return redirect('reservation_confirmation', booking_id=booking.id)
        
        # Handle "Proceed To Payment" action
        elif action == 'payment':
            from django.utils.crypto import get_random_string
            
            booking_reference = get_random_string(12).upper()
            
            details = {
                'outbound': normalized_outbound,
                'return': normalized_return,
                'total_price': total_price,
                'passengers': passenger_data,
                'infants': summary.get('infants', 0),
            }
            
            booking = Booking.objects.create(
                user=request.user,
                trip_type=summary.get('trip_type', 'one_way'),
                origin=summary.get('origin_name', ''),
                destination=summary.get('destination_name', ''),
                departure_date=dep_date,
                return_date=ret_date,
                adults=summary.get('adults', 1),
                children=valid_children_count,  # FIX: Use validated children count
                booking_reference=booking_reference,
                status='pending',
                reserved_until=None,
                total_price=total_price,
                details=details,
            )
            
            return redirect('payment', booking_id=booking.id)

    context = {
        'trip_type': summary.get('trip_type', 'one_way'),
        'origin_name': summary.get('origin_name', 'Origin'),
        'destination_name': summary.get('destination_name', 'Destination'),
        'departure_date_formatted': summary.get('departure_date_formatted', ''),
        'return_date_formatted': summary.get('return_date_formatted', ''),
        'adults': summary.get('adults', 1),
        'children': summary.get('children', 0),
    }
    return render(request, 'passenger_info.html', context)

@login_required
def reservation_confirmation(request, booking_id):
    from datetime import datetime, timedelta
    booking = Booking.objects.get(id=booking_id, user=request.user)
    # Determine if Reserve Booking is allowed (more than 2 hours before departure)
    can_reserve_booking = False
    outbound = booking.details.get('outbound') if booking.details else None
    dep_time_str = outbound.get('departureDateTime') or outbound.get('departureTime') if outbound else None
    dep_dt = None
    try:
        if dep_time_str:
            try:
                dep_dt = datetime.fromisoformat(dep_time_str)
            except Exception:
                today = datetime.now().date()
                dep_dt = datetime.strptime(str(today) + ' ' + dep_time_str, '%Y-%m-%d %I:%M %p')
    except Exception:
        dep_dt = None
    now = datetime.now()
    if dep_dt and (dep_dt - now) > timedelta(hours=2):
        can_reserve_booking = True
    context = {
        'booking': booking,
        'user': request.user,
        'can_reserve_booking': can_reserve_booking,
    }
    return render(request, 'reservation_confirmation.html', context)


@login_required
@require_POST
def cancel_reservation(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if booking.user != request.user:
        messages.error(request, "You do not have permission to modify this reservation.")
        return redirect('reservation_confirmation', booking_id=booking_id)

    if booking.status == 'cancelled':
        messages.info(request, 'This reservation is already cancelled.')
        return redirect('reservation_confirmation', booking_id=booking_id)

    booking.status = 'cancelled'
    booking.reserved_until = None
    booking.save(update_fields=['status', 'reserved_until', 'updated_at'])

    messages.success(request, 'Your reservation has been cancelled.')
    return redirect('reservation_confirmation', booking_id=booking_id)


@login_required
def reservations_view(request):
    """Display reservations separated by payment status"""
    
    # Get all active bookings (exclude cancelled and expired)
    all_reservations = (
        Booking.objects
        .filter(user=request.user)
        .exclude(status='cancelled')
        .exclude(status='expired')
        .order_by('departure_date', '-created_at')
    )
    
    # Separate into unpaid (reserved/pending) and paid (confirmed/completed)
    unpaid_bookings = all_reservations.filter(status__in=['reserved', 'pending'])
    paid_bookings = all_reservations.filter(status__in=['confirmed', 'completed'])
    
    return render(request, 'reservations.html', {
        'unpaid_bookings': unpaid_bookings,
        'paid_bookings': paid_bookings,
        'has_reservations': all_reservations.exists(),
    })
    
@login_required
def payment_confirmation(request, booking_id):
    """Display payment confirmation page after successful payment"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    # Only show confirmation for completed bookings
    if booking.status != 'completed':
        messages.warning(request, 'This booking has not been completed yet.')
        return redirect('payment', booking_id=booking_id)
    
    context = {
        'booking': booking,
        'user': request.user,
    }
    return render(request, 'payment_confirmation.html', context)


@login_required
def payment_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', '').strip() or 'unspecified'

        details = booking.details or {}
        payment_info = {
            'method': payment_method,
            'paid_at': timezone.now().isoformat(),
            'paid_at_display': timezone.localtime().strftime('%b %d, %Y %I:%M %p'),
        }
        details['payment'] = payment_info
        booking.details = details
        booking.status = 'completed'
        booking.reserved_until = None
        booking.save(update_fields=['details', 'status', 'reserved_until', 'updated_at'])

        messages.success(request, 'Payment confirmed! Your booking was added to your history.')
        return redirect('payment_confirmation', booking_id=booking.id)

    details = booking.details or {}
    distance = details.get('distance')
    if not distance:
        outbound = details.get('outbound') if isinstance(details, dict) else None
        if isinstance(outbound, dict):
            distance = outbound.get('distance')

    context = {
        'booking': booking,
        'user': request.user,
        'route_distance': distance,
        'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY,
    }
    return render(request, 'payment.html', context)


@require_POST
@login_required
def stripe_checkout(request, booking_id):
    import stripe

    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    stripe.api_key = settings.STRIPE_SECRET_KEY

    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        customer_email=request.user.email,
        line_items=[{
            "price_data": {
                "currency": "php",
                "unit_amount": int(booking.total_price * 100),
                "product_data": {"name": f"{booking.origin} - {booking.destination}"},
            },
            "quantity": 1,
        }],
        success_url=request.build_absolute_uri(
            reverse("stripe_success", args=[booking.id])
        ) + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=request.build_absolute_uri(
            reverse("payment", args=[booking.id])
        ),
    )

    details = booking.details or {}
    details["payment"] = {"method": "stripe_test", "session_id": session.id, "status": "pending"}
    booking.details = details
    booking.save(update_fields=["details", "updated_at"])

    return JsonResponse({"sessionId": session.id})


@login_required
def stripe_success(request, booking_id):
    import stripe

    session_id = request.GET.get("session_id")
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    stripe.api_key = settings.STRIPE_SECRET_KEY
    session = stripe.checkout.Session.retrieve(session_id)

    if session.payment_status == "paid":
        details = booking.details or {}
        details["payment"] = {
            "method": "stripe_test",
            "paid_at": timezone.now().isoformat(),
            "paid_at_display": timezone.localtime().strftime('%b %d, %Y %I:%M %p'),
            "session_id": session.id,
        }
        booking.details = details
        booking.status = "completed"
        booking.reserved_until = None
        booking.save(update_fields=["details", "status", "reserved_until", "updated_at"])
        messages.success(request, "Payment confirmed! Your booking was added to your history.")
    else:
        messages.error(request, "Payment not completed. Please try again.")

    return redirect('payment_confirmation', booking_id=booking.id)

@login_required
def booking_history_view(request):
    bookings = (
        Booking.objects
        .filter(user=request.user)
        .order_by('-created_at')
    )

    return render(request, 'booking_history.html', {
        'bookings': bookings,
    })

    summary = request.session.get('passenger_info_summary')

    if not summary:
        messages.error(request, 'Please select your trips before entering passenger information.')
        return redirect('home')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'reserve':
            from .models import Booking
            from django.utils.crypto import get_random_string
            from datetime import timedelta
            now = timezone.now()
            reserved_until = now + timedelta(days=1)
            # Minimal: get summary/session data for booking fields
            summary = request.session.get('passenger_info_summary', {})
            user = request.user
            booking_reference = get_random_string(12).upper()
            booking = Booking.objects.create(
                user=user,
                trip_type=summary.get('trip_type', 'one_way'),
                origin=summary.get('origin_name', ''),
                destination=summary.get('destination_name', ''),
                departure_date=summary.get('departure_date_formatted', ''),
                return_date=summary.get('return_date_formatted', None),
                adults=summary.get('adults', 1),
                children=summary.get('children', 0),
                booking_reference=booking_reference,
                status='pending',
                reserved_until=reserved_until,
                total_price=0,  # Placeholder
                details={},     # Placeholder
            )
            return redirect('reservation_confirmation', booking_id=booking.id)
        # fallback: default behavior
        form_data = {
            key: value for key, value in request.POST.items() if key != 'csrfmiddlewaretoken'
        }
        request.session['passenger_info_form'] = form_data
        request.session['passenger_info_completed'] = True
        return redirect('passenger_info')

    passenger_form_data = request.session.pop('passenger_info_form', {})
    show_booking_options = request.session.pop('passenger_info_completed', False)

    context = {
        'trip_type': summary.get('trip_type', 'one_way'),
        'origin_name': summary.get('origin_name', 'Origin'),
        'destination_name': summary.get('destination_name', 'Destination'),
        'departure_date_formatted': summary.get('departure_date_formatted', ''),
        'return_date_formatted': summary.get('return_date_formatted', ''),
        'adults': summary.get('adults', 1),
        'children': summary.get('children', 0),
        'show_booking_options': show_booking_options,
        'passenger_form_data': passenger_form_data,
    }
    return render(request, 'passenger_info.html', context)


@never_cache
@login_required
def admin_bookings(request):
    """Admin bookings management page - view all bookings"""
    # Check admin permissions
    if not hasattr(request.user, 'profile') or not request.user.profile.is_admin_user:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')

    # Get all bookings with related user
    bookings = Booking.objects.select_related('user').order_by('-created_at')

    # Booking statistics
    total_bookings = bookings.count()
    pending_bookings = bookings.filter(status='pending').count()
    reserved_bookings = bookings.filter(status='reserved').count()
    confirmed_bookings = bookings.filter(status='confirmed').count()
    cancelled_bookings = bookings.filter(status='cancelled').count()
    completed_bookings = bookings.filter(status='completed').count()

    context = {
        'bookings': bookings,
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'reserved_bookings': reserved_bookings,
        'confirmed_bookings': confirmed_bookings,
        'cancelled_bookings': cancelled_bookings,
        'completed_bookings': completed_bookings,
        'user': request.user,
    }
    return render(request, 'admin_bookings.html', context)

@never_cache
@login_required
def admin_dashboard(request):
    """Admin dashboard - only accessible to admin users"""
    try:
        if not request.user.profile.is_admin_user:
            messages.error(request, "You don't have permission to access the admin dashboard.")
            return redirect('home')
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=request.user)
        messages.error(request, "You don't have permission to access the admin dashboard.")
        return redirect('home')

    # Compute statistics
    from django.contrib.auth.models import User
    from django.db.models import Count
    from django.db.models.functions import TruncMonth
    from datetime import timedelta
    import json
    from django.utils import timezone

    total_bookings = Booking.objects.count()  # Get actual booking count
    total_users = User.objects.count()
    admin_users = UserProfile.objects.filter(is_admin_user=True).count()
    active_users = User.objects.filter(is_active=True).count()

    # Calculate new users this month
    now = timezone.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_this_month = User.objects.filter(date_joined__gte=start_of_month).count()
    
    # Get user growth data for the last 12 months
    twelve_months_ago = now - timedelta(days=365)
    
    # Query to get monthly user registrations
    monthly_users = User.objects.filter(
        date_joined__gte=twelve_months_ago
    ).annotate(
        month=TruncMonth('date_joined')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # Prepare chart data
    chart_labels = []
    chart_data = []
    
    # Fill in the data
    for entry in monthly_users:
        # Format: "Jan 2024", "Feb 2024", etc.
        month_str = entry['month'].strftime('%b %Y')
        chart_labels.append(month_str)
        chart_data.append(entry['count'])
    
    # Calculate cumulative user growth
    cumulative_data = []
    cumulative_sum = 0
    for count in chart_data:
        cumulative_sum += count
        cumulative_data.append(cumulative_sum)
    
    # Handle case when there's no data
    if not chart_labels:
        # Provide default empty data
        current_month = now.strftime('%b %Y')
        chart_labels = [current_month]
        chart_data = [0]
        cumulative_data = [0]

    context = {
        'user': request.user,
        'total_bookings': total_bookings,
        'total_users': total_users,
        'admin_users': admin_users,
        'active_users': active_users,
        'new_this_month': new_this_month,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'cumulative_data': json.dumps(cumulative_data),
    }
    return render(request, 'admin_dashboard.html', context)

@never_cache
@login_required
def admin_users(request):
    """Admin users management page - with statistics"""
    
    # Check admin permissions
    if not hasattr(request.user, 'profile') or not request.user.profile.is_admin_user:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')

    # Get all users with their profiles
    users = User.objects.all().select_related('profile').order_by('-date_joined')
    
    # Calculate statistics
    total_users = User.objects.count()
    admin_users = User.objects.filter(profile__is_admin_user=True).count()
    active_users = User.objects.filter(is_active=True).count()
    
    # Calculate new users this month
    now = timezone.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_this_month = User.objects.filter(date_joined__gte=start_of_month).count()
    
    # Handle POST requests (role changes from non-AJAX submissions)
    if request.method == "POST":
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        
        try:
            target_user = User.objects.get(id=user_id)
            profile = target_user.profile
            
            # Prevent admin from changing their own role
            if target_user.id == request.user.id:
                messages.error(request, "You cannot change your own role.")
                return redirect('admin_users')

            if action == "make_admin":
                profile.is_admin_user = True
                profile.save()
                messages.success(request, f"{target_user.username} is now an admin.")
            elif action == "remove_admin":
                profile.is_admin_user = False
                profile.save()
                messages.success(request, f"{target_user.username} is no longer an admin.")
            else:
                messages.error(request, "Invalid action.")
        
        except User.DoesNotExist:
            messages.error(request, "User not found.")
        except UserProfile.DoesNotExist:
            messages.error(request, "User profile not found.")
        
        return redirect('admin_users')
    
    # Prepare context
    context = {
        'users': users,
        'total_users': total_users,
        'admin_users': admin_users,
        'active_users': active_users,
        'new_this_month': new_this_month,
    }
    
    return render(request, 'admin_users.html', context)

@login_required
@require_POST
def toggle_user_active_ajax(request, user_id):
    if not hasattr(request.user, 'profile') or not request.user.profile.is_admin_user:
        return JsonResponse({'success': False, 'message': 'Unauthorized.'}, status=403)
    if int(user_id) == request.user.id:
        return JsonResponse({'success': False, 'message': 'Cannot change your own status.'}, status=400)
    from django.contrib.auth.models import User
    try:
        user = User.objects.get(id=user_id)
        user.is_active = not user.is_active
        user.save()
        return JsonResponse({
            'success': True,
            'new_status': user.is_active,
            'badge_html': (
                '<span class="status-badge active" style="cursor:pointer;">Active</span>'
                if user.is_active else
                '<span class="status-badge inactive" style="cursor:pointer;">Inactive</span>'
            )
        })
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found.'}, status=404)

@login_required
@require_http_methods(["POST"])
def change_user_role(request):
    """Handle role changes for users"""
    try:
        # Check if the current user is an admin
        if not hasattr(request.user, 'profile') or not request.user.profile.is_admin_user:
            return JsonResponse({
                'success': False,
                'message': 'Unauthorized. Admin privileges required.'
            }, status=403)
        
        # Parse JSON body
        data = json.loads(request.body)
        user_id = data.get('user_id')
        action = data.get('action')
        
        # Validate input
        if not user_id or not action:
            return JsonResponse({
                'success': False,
                'message': 'Missing required fields: user_id and action'
            }, status=400)
        
        # Get the user to modify
        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'User not found'
            }, status=404)
        
        # Prevent users from modifying their own role
        if target_user.id == request.user.id:
            return JsonResponse({
                'success': False,
                'message': 'You cannot modify your own role'
            }, status=400)
        
        # Ensure the user has a profile
        if not hasattr(target_user, 'profile'):
            return JsonResponse({
                'success': False,
                'message': 'User profile not found'
            }, status=404)
        
        # Perform the action
        if action == 'make_admin':
            target_user.profile.is_admin_user = True
            target_user.profile.save()
            message = f'{target_user.username} has been granted admin privileges'
        elif action == 'remove_admin':
            target_user.profile.is_admin_user = False
            target_user.profile.save()
            message = f'Admin privileges removed from {target_user.username}'
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid action specified'
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'message': message,
            'new_role': 'admin' if target_user.profile.is_admin_user else 'user'
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=500)


@require_http_methods(["POST"])
def add_user(request):
    """Add a new user - Fixed for AJAX requests with Supabase"""

    logger.info("="*50)
    logger.info("ADD USER REQUEST RECEIVED")
    logger.info(f"User authenticated: {request.user.is_authenticated}")
    logger.info(f"Method: {request.method}")
    logger.info(f"POST keys: {list(request.POST.keys())}")
    logger.info("="*50)
    
    # Manual authentication check
    if not request.user.is_authenticated:
        logger.error("User NOT authenticated!")
        return JsonResponse({
            'success': False,
            'message': 'Authentication required. Please log in.'
        }, status=401)
    
    try:
        # Check if the current user is an admin
        if not hasattr(request.user, 'profile'):
            UserProfile.objects.create(user=request.user)
            
        if not request.user.profile.is_admin_user:
            logger.warning(f"Unauthorized add_user attempt by {request.user.username}")
            return JsonResponse({
                'success': False,
                'message': 'Unauthorized. Admin privileges required.'
            }, status=403)
        
        # Get form data
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        is_admin = request.POST.get('is_admin') == 'on'
        
        logger.info(f"Attempting to create user: username={username}, email={email}")
        
        # Validate required fields
        if not username:
            return JsonResponse({
                'success': False,
                'message': 'Username is required'
            }, status=400)
            
        if not email:
            return JsonResponse({
                'success': False,
                'message': 'Email is required'
            }, status=400)
            
        if not password:
            return JsonResponse({
                'success': False,
                'message': 'Password is required'
            }, status=400)
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            logger.warning(f"Username {username} already exists")
            return JsonResponse({
                'success': False,
                'message': f'Username "{username}" already exists'
            }, status=400)
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            logger.warning(f"Email {email} already exists")
            return JsonResponse({
                'success': False,
                'message': f'Email "{email}" already exists'
            }, status=400)
        
        # Validate email format
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid email format'
            }, status=400)
        
        # Create the user
        logger.info(f"Creating user {username}...")
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        logger.info(f"User {username} created with ID {user.id}")
        
        # Verify user was actually created in database
        created_user = User.objects.filter(id=user.id).first()
        if not created_user:
            logger.error(f"User {username} was not found after creation!")
            return JsonResponse({
                'success': False,
                'message': 'User created but could not be verified in database'
            }, status=500)
        
        logger.info(f"✓ Verified user {username} exists in database")
        
        # Create profile
        profile, profile_created = UserProfile.objects.get_or_create(user=user)
        logger.info(f"Profile created: {profile_created}")
        
        # Set admin status if requested
        if is_admin:
            profile.is_admin_user = True
            profile.save()
            logger.info(f"User {username} granted admin privileges")
        
        logger.info(f"✓ User {username} created successfully!")
        
        return JsonResponse({
            'success': True,
            'message': f'User {username} created successfully',
            'user_id': user.id,
            'username': user.username
        }, status=201)
    
    except Exception as e:
        logger.error(f"Error in add_user: {str(e)}", exc_info=True)
        import traceback
        logger.error(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=500)
        

@login_required
@require_http_methods(["POST"])
def delete_user(request, user_id):
    """Delete a user"""
    try:
        # Check if the current user is an admin
        if not hasattr(request.user, 'profile') or not request.user.profile.is_admin_user:
            return JsonResponse({
                'success': False,
                'message': 'Unauthorized. Admin privileges required.'
            }, status=403)
        
        # Get the user to delete
        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'User not found'
            }, status=404)
        
        # Prevent users from deleting themselves
        if target_user.id == request.user.id:
            return JsonResponse({
                'success': False,
                'message': 'You cannot delete your own account'
            }, status=400)
        
        username = target_user.username
        target_user.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'User {username} has been deleted'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=500)
        
@login_required
@require_http_methods(["POST"])
def edit_user(request, user_id):
    """Edit an existing user"""
    
    logger.info("="*50)
    logger.info("EDIT USER REQUEST RECEIVED")
    logger.info(f"User authenticated: {request.user.is_authenticated}")
    logger.info(f"User ID to edit: {user_id}")
    logger.info("="*50)
    
    # Check authentication
    if not request.user.is_authenticated:
        logger.error("User NOT authenticated!")
        return JsonResponse({
            'success': False,
            'message': 'Authentication required. Please log in.'
        }, status=401)
    
    try:
        # Check if the current user is an admin
        if not hasattr(request.user, 'profile'):
            UserProfile.objects.create(user=request.user)
            
        if not request.user.profile.is_admin_user:
            logger.warning(f"Unauthorized edit_user attempt by {request.user.username}")
            return JsonResponse({
                'success': False,
                'message': 'Unauthorized. Admin privileges required.'
            }, status=403)
        
        # Get the user to edit
        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error(f"User with ID {user_id} not found")
            return JsonResponse({
                'success': False,
                'message': 'User not found'
            }, status=404)
        
        # Get form data
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        is_admin = request.POST.get('is_admin') == 'on'
        
        logger.info(f"Editing user: {target_user.username}")
        logger.info(f"New values - First: {first_name}, Last: {last_name}, Email: {email}, Admin: {is_admin}")
        
        # Validate email if it's being changed
        if email and email != target_user.email:
            # Check if email already exists for another user
            if User.objects.filter(email=email).exclude(id=user_id).exists():
                logger.warning(f"Email {email} already exists for another user")
                return JsonResponse({
                    'success': False,
                    'message': f'Email "{email}" is already in use by another user'
                }, status=400)
            
            # Validate email format
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError
            try:
                validate_email(email)
            except ValidationError:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid email format'
                }, status=400)
        
        # Update user fields
        target_user.first_name = first_name
        target_user.last_name = last_name
        if email:
            target_user.email = email
        target_user.save()
        
        logger.info(f"✓ User {target_user.username} basic info updated")
        
        # Update admin status (only if not editing self)
        if target_user.id != request.user.id:
            if not hasattr(target_user, 'profile'):
                UserProfile.objects.create(user=target_user)
            
            target_user.profile.is_admin_user = is_admin
            target_user.profile.save()
            logger.info(f"✓ User {target_user.username} admin status updated to {is_admin}")
        else:
            logger.info("Skipped admin status update (user editing themselves)")
        
        logger.info(f"✓ User {target_user.username} updated successfully!")
        
        return JsonResponse({
            'success': True,
            'message': f'User {target_user.username} updated successfully',
            'user_id': target_user.id,
            'username': target_user.username
        })
    
    except Exception as e:
        logger.error(f"Error in edit_user: {str(e)}", exc_info=True)
        import traceback
        logger.error(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=500)
        
@require_http_methods(["GET", "POST"])
def test_csrf(request):
    """Test endpoint to verify CSRF and authentication"""
    return JsonResponse({
        'method': request.method,
        'authenticated': request.user.is_authenticated,
        'username': request.user.username if request.user.is_authenticated else None,
        'csrf_cookie': 'csrftoken' in request.COOKIES,
        'session_key': request.session.session_key,
        'has_profile': hasattr(request.user, 'profile') if request.user.is_authenticated else False,
        'is_admin': request.user.profile.is_admin_user if (request.user.is_authenticated and hasattr(request.user, 'profile')) else False,
        'post_data': dict(request.POST) if request.method == 'POST' else None,
    })

@login_required
def profile_settings(request):
    user = request.user
    profile = getattr(user, 'profile', None)

    # Completed bookings (used by the Booking History tab)
    completed_bookings = (
        user.bookings.filter(status='completed')
        .order_by('-updated_at')
    )

    # variables used to show messages in template without redirect
    password_error = None
    password_success = None
    active_tab = request.GET.get('tab', 'personal')

    if request.method == "POST":
        # detect which form was submitted
        form_type = request.POST.get("form_type", "profile")

        # -------------------------
        # PASSWORD CHANGE SUBMIT
        # -------------------------
        if form_type == "password":
            active_tab = "security"  # remain on security tab

            current_password = request.POST.get("current_password", "")
            new_password = request.POST.get("new_password", "")
            confirm_password = request.POST.get("confirm_password", "")

            # 1) verify current password
            if not user.check_password(current_password):
                password_error = "Current password is incorrect."

            # 2) new/confirm match
            elif new_password != confirm_password:
                password_error = "New password and confirmation do not match."

            # 3) basic strength check
            elif len(new_password) < 8:
                password_error = "New password must be at least 8 characters long."

            else:
                # 4) update password and keep user logged in
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)
                password_success = "Password updated successfully!"

            # render the page with the result (no redirect so message shows on security tab)
            context = {
                'user': user,
                'profile': profile,
                'bookings': completed_bookings,
                'active_tab': active_tab,
                'password_error': password_error,
                'password_success': password_success,
            }
            return render(request, 'profile_settings.html', context)

        # -------------------------
        # PROFILE INFO SUBMIT
        # -------------------------
        else:
            active_tab = 'personal'

            # Get form data
            first_name = request.POST.get("first_name")
            last_name = request.POST.get("last_name")
            email = request.POST.get("email")
            phone = request.POST.get("phone")
            address = request.POST.get("address")
            date_of_birth_str = request.POST.get("date_of_birth")

            # ----- validate birthdate (must be in the past) -----
            dob = None
            if date_of_birth_str:
                try:
                    dob = datetime.strptime(date_of_birth_str, "%Y-%m-%d").date()
                except ValueError:
                    messages.error(request, "Invalid birthdate format. Please use YYYY-MM-DD.")
                    context = {
                        'user': user,
                        'profile': profile,
                        'bookings': completed_bookings,
                        'active_tab': 'personal',
                    }
                    return render(request, 'profile_settings.html', context)

                if dob >= date.today():
                    messages.error(request, "Birthdate cannot be today or a future date.")
                    context = {
                        'user': user,
                        'profile': profile,
                        'bookings': completed_bookings,
                        'active_tab': 'personal',
                    }
                    return render(request, 'profile_settings.html', context)

            # ----- update User fields -----
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()

            # ----- update UserProfile fields -----
            if profile:
                profile.phone = phone
                profile.address = address
                # only overwrite DOB if user actually submitted something
                if date_of_birth_str:
                    profile.date_of_birth = dob
                profile.save()

            messages.success(request, "Profile updated successfully!")
            # redirect is fine here so the change is reloaded from DB and message appears
            return redirect('profile_settings')

    # GET: render page with current values from DB
    context = {
        'user': user,
        'profile': profile,
        'bookings': completed_bookings,
        'active_tab': request.GET.get('tab', 'personal'),
        # password messages are None for GET
        'password_error': None,
        'password_success': None,
    }
    return render(request, 'profile_settings.html', context)


    # GET: render page with current values from DB
    context = {
        'user': user,
        'profile': profile,
        'bookings': completed_bookings,
        'active_tab': request.GET.get('tab', 'personal'),
    }
    return render(request, 'profile_settings.html', context)


@login_required
@require_POST
def upload_profile_photo(request):
    """Handle profile photo uploads."""
    profile = request.user.profile
    photo = request.FILES.get("photo")

    if not photo:
        return JsonResponse({"success": False, "message": "No photo uploaded."}, status=400)

    # Save new photo
    profile.photo = photo
    profile.save()

    return JsonResponse({
        "success": True,
        "message": "Photo updated successfully!",
        "photo_url": profile.photo.url
    })

@login_required
@require_POST
def delete_profile_photo(request):
    """Removes the user's profile photo and reverts to initials."""
    profile = request.user.profile

    # If user has a photo, delete it from storage
    if profile.photo:
        profile.photo.delete(save=False)
        profile.photo = None
        profile.save()
        return JsonResponse({
            "success": True,
            "message": "Profile photo removed successfully!"
        })

    return JsonResponse({
        "success": False,
        "message": "No profile photo to delete."
    }, status=400)

def search_trips(request):
    """Handle trip search using Barkota API with caching"""
    if request.method == 'POST':
        # Get form data
        trip_type = request.POST.get('trip_type', 'one_way')
        origin = request.POST.get('origin')
        destination = request.POST.get('destination')
        departure_date = request.POST.get('departure_date')
        return_date = request.POST.get('return_date') if trip_type == 'round_trip' else None
        adults = int(request.POST.get('adults', 1))
        children = int(request.POST.get('children', 0))
        
        # Calculate total passengers
        total_passengers = max(adults + children, 1)  # At least 1 passenger
        
        try:
            # First, fetch location names - use cache
            routes_data = cache.get('barkota_routes')
            
            if not routes_data:
                # Cache miss - fetch from API
                locations_url = "https://barkota-reseller-php-prod-4kl27j34za-uc.a.run.app/ob/routes/passageenabled"
                locations_headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Referer": "https://booking.barkota.com/",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                locations_payload = {"companyId": None}
                
                logger.info("Fetching routes for search (cache miss)")
                locations_response = requests.post(locations_url, json=locations_payload, headers=locations_headers, timeout=25)
                locations_response.raise_for_status()
                routes_data = locations_response.json()
                
                # Cache for 10 minutes
                cache.set('barkota_routes', routes_data, 600)
            else:
                logger.info("Using cached routes for search")
            
            # Find the location names from routes data
            origin_name = f"Origin {origin}"
            destination_name = f"Destination {destination}"
            
            # Create a dictionary of all unique locations
            locations_dict = {}
            for route in routes_data:
                if isinstance(route, dict):
                    route_origin = route.get('origin', {})
                    route_destination = route.get('destination', {})
                    
                    if isinstance(route_origin, dict) and 'id' in route_origin:
                        locations_dict[route_origin['id']] = route_origin.get('name', '')
                    
                    if isinstance(route_destination, dict) and 'id' in route_destination:
                        locations_dict[route_destination['id']] = route_destination.get('name', '')
            
            # Get the names using the dictionary
            origin_id = int(origin)
            destination_id = int(destination)
            
            if origin_id in locations_dict:
                origin_name = locations_dict[origin_id]
            
            if destination_id in locations_dict:
                destination_name = locations_dict[destination_id]
            
            logger.info(f"Location names: {origin_name} -> {destination_name}")
            
            # Create cache key for voyage search based on search parameters
            outbound_cache_key = f"voyage_{origin}_{destination}_{departure_date}_{total_passengers}"
            return_cache_key = f"voyage_{destination}_{origin}_{return_date}_{total_passengers}" if return_date else None
            
            # Search for outbound voyages - check cache first
            outbound_voyages = cache.get(outbound_cache_key)
            
            if not outbound_voyages:
                # Cache miss - fetch from API
                url = "https://barkota-reseller-php-prod-4kl27j34za-uc.a.run.app/ob/voyages/search/bylocation"
                
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/plain, */*",
                    "Origin": "https://booking.barkota.com",
                    "Referer": "https://booking.barkota.com/"
                }
                
                payload = {
                    "origin": int(origin),
                    "destination": int(destination),
                    "departureDate": departure_date,
                    "passengerCount": total_passengers,
                    "shippingCompany": None,
                    "cargoItemId": None,
                    "withDriver": 1
                }
                
                logger.info(f"Searching outbound voyages (cache miss): {payload}")
                
                response = requests.post(url, json=payload, headers=headers, timeout=25)
                response.raise_for_status()
                
                outbound_voyages = response.json()
                
                # Cache voyage results for 5 minutes (shorter than routes cache)
                cache.set(outbound_cache_key, outbound_voyages, 300)
            else:
                logger.info("Using cached outbound voyages")
            
            # If roundtrip, search for return voyages
            return_voyages = []
            if trip_type == 'round_trip' and return_date:
                return_voyages = cache.get(return_cache_key)
                
                if not return_voyages:
                    # Cache miss - fetch from API
                    return_payload = {
                        "origin": int(destination),  # Swapped
                        "destination": int(origin),  # Swapped
                        "departureDate": return_date,
                        "passengerCount": total_passengers,
                        "shippingCompany": None,
                        "cargoItemId": None,
                        "withDriver": 1
                    }
                    
                    logger.info(f"Searching return voyages (cache miss): {return_payload}")
                    
                    return_response = requests.post(url, json=return_payload, headers=headers, timeout=25)
                    return_response.raise_for_status()
                    return_voyages = return_response.json()
                    
                    # Cache for 5 minutes
                    cache.set(return_cache_key, return_voyages, 300)
                else:
                    logger.info("Using cached return voyages")
            
            # Get first voyage times for display
            departure_time = ""
            return_time = ""
            
            if outbound_voyages and len(outbound_voyages) > 0:
                first_outbound = outbound_voyages[0].get('voyage', {})
                departure_time = first_outbound.get('departureDateTime', '')
            
            if return_voyages and len(return_voyages) > 0:
                first_return = return_voyages[0].get('voyage', {})
                return_time = first_return.get('departureDateTime', '')
            
            # Format dates to "Wed, 22 Oct 2025"
            from datetime import datetime
            departure_date_formatted = departure_date
            return_date_formatted = return_date
            
            try:
                dep_date_obj = datetime.strptime(departure_date, '%Y-%m-%d')
                departure_date_formatted = dep_date_obj.strftime('%a, %d %b %Y')
            except:
                pass
            
            if return_date:
                try:
                    ret_date_obj = datetime.strptime(return_date, '%Y-%m-%d')
                    return_date_formatted = ret_date_obj.strftime('%a, %d %b %Y')
                except:
                    pass
            
            # Enforce cutoff: 1 hour 30 minutes before departure
            from datetime import timedelta
            now = timezone.now()
            cutoff_delta = timedelta(hours=1, minutes=30)

            def apply_cutoff(voyages):
                for item in voyages:
                    voyage = item.get('voyage', {})
                    dt_str = voyage.get('departureDateTime')
                    cutoff_message = None
                    if dt_str:
                        try:
                            # Handle both 'YYYY-MM-DDTHH:MM:SS' and 'YYYY-MM-DD HH:MM:SS' formats
                            dt = None
                            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"):
                                try:
                                    dt = datetime.strptime(dt_str[:16], fmt)
                                    break
                                except Exception:
                                    continue
                            if dt is not None:
                                # Assume naive datetimes are in local time
                                if timezone.is_naive(dt):
                                    dt = timezone.make_aware(dt, timezone.get_current_timezone())
                                cutoff_time = dt - cutoff_delta
                                logger.info(f"[CUTOFF DEBUG] Now: {now}, Departure: {dt}, Cutoff: {cutoff_time}, dt_str: {dt_str}")
                                if now > cutoff_time:
                                    item['accommodations'] = []
                                    cutoff_time_str = cutoff_time.strftime('%m/%d/%Y %-I:%M %p').replace('AM', 'am').replace('PM', 'pm')
                                    item['cutoff_message'] = f"Cut Off for this voyage was at {cutoff_time_str}"
                                    logger.info(f"[CUTOFF DEBUG] Set cutoff_message for voyage {dt_str}: {item['cutoff_message']}")
                                else:
                                    logger.info(f"[CUTOFF DEBUG] Booking still allowed for voyage {dt_str}")
                        except Exception as e:
                            logger.warning(f"[CUTOFF DEBUG] Exception for voyage {dt_str}: {e}")
                return voyages

            outbound_voyages = apply_cutoff(outbound_voyages)
            return_voyages = apply_cutoff(return_voyages)

            # Render results page
            context = {
                'trip_type': trip_type,
                'origin': origin,
                'destination': destination,
                'origin_name': origin_name,
                'destination_name': destination_name,
                'departure_date': departure_date,
                'return_date': return_date,
                'departure_date_formatted': departure_date_formatted,
                'return_date_formatted': return_date_formatted,
                'departure_time': departure_time,
                'return_time': return_time,
                'adults': adults,
                'children': children,
                'outbound_voyages': outbound_voyages,
                'return_voyages': return_voyages,
                'routes_data': json.dumps(routes_data) if routes_data else '[]',
                'today': date.today().isoformat(),
            }

            request.session['passenger_info_summary'] = {
                'trip_type': trip_type,
                'origin_name': origin_name,
                'destination_name': destination_name,
                'departure_date_formatted': departure_date_formatted,
                'return_date_formatted': return_date_formatted,
                'adults': adults,
                'children': children,
            }
            
            return render(request, 'available_trips_search.html', context)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Barkota API error: {str(e)}")
            messages.error(request, f'Failed to search voyages: {str(e)}')
            return redirect('home')
        except Exception as e:
            logger.error(f"Error in search_trips: {str(e)}", exc_info=True)
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('home')
    
    return redirect('home')

@login_required
def search_voyages_page(request):
    """Display the voyage search page"""
    return render(request, 'search_voyages.html')


@require_http_methods(["GET", "POST"])
def get_all_locations(request):
    """Fetch all available locations/routes from Barkota API"""
    try:
        # Barkota routes endpoint (found via DevTools - returns locations)
        url = "https://barkota-reseller-php-prod-4kl27j34za-uc.a.run.app/ob/routes/passageenabled"
        
        # Headers matching the Barkota website
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Referer": "https://booking.barkota.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        # Payload as seen in DevTools
        payload = {
            "companyId": None
        }
        
        logger.info(f"Fetching all locations from Barkota API")
        
        # Make API request with POST method and payload
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Return the API response
        return JsonResponse({
            'success': True,
            'data': response.json()
        })
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Barkota Locations API error: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'API request failed: {str(e)}'
        }, status=500)
    except Exception as e:
        logger.error(f"Error in get_all_locations: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=500)

@require_http_methods(["POST"])
def search_voyages_barkota(request):
    """Search for voyages using Barkota API"""
    try:
        # Parse request data
        data = json.loads(request.body) if request.body else {}
        
        # Get search parameters from request or use defaults
        origin = data.get('origin', 93)
        destination = data.get('destination', 96)
        departure_date = data.get('departureDate', '2025-10-22')
        passenger_count = data.get('passengerCount', 1)
        shipping_company = data.get('shippingCompany', None)
        cargo_item_id = data.get('cargoItemId', None)
        with_driver = data.get('withDriver', 1)
        
        # Barkota API endpoint
        url = "https://barkota-reseller-php-prod-4kl27j34za-uc.a.run.app/ob/voyages/search/bylocation"
        
        # Request headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://booking.barkota.com",
            "Referer": "https://booking.barkota.com/"
        }
        
        # Request payload
        payload = {
            "origin": origin,
            "destination": destination,
            "departureDate": departure_date,
            "passengerCount": passenger_count,
            "shippingCompany": shipping_company,
            "cargoItemId": cargo_item_id,
            "withDriver": with_driver
        }
        
        logger.info(f"Searching voyages with payload: {payload}")
        
        # Make API request
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Return the API response
        return JsonResponse({
            'success': True,
            'data': response.json()
        })
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Barkota API error: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'API request failed: {str(e)}'
        }, status=500)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in search_voyages_barkota: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=500)
    user = request.user
    profile = getattr(user, 'profile', None)

    if request.method == "POST":
        # Get form data
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        date_of_birth = request.POST.get("date_of_birth")

        # Update User fields
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()

        # Update UserProfile fields
        if profile:
            profile.phone = phone
            profile.address = address
            profile.date_of_birth = date_of_birth or None
            profile.save()

        messages.success(request, "Profile updated successfully!")
        return redirect('profile_settings')

    context = {
        'user': user,
        'profile': profile,
    }
    return render(request, 'profile_settings.html', context)

@login_required
@require_POST
def update_profile_ajax(request):
    """Handles updating the user profile via AJAX without page reload.
       Note: date_of_birth is intentionally ignored here to keep DOB immutable.
    """
    user = request.user
    profile = getattr(user, 'profile', None)
    if not profile:
        # defensive: ensure profile exists
        profile = UserProfile.objects.create(user=user)

    # Get fields from POST data (do NOT accept date_of_birth updates)
    first_name = request.POST.get("first_name", user.first_name)
    last_name = request.POST.get("last_name", user.last_name)
    email = request.POST.get("email", user.email)
    phone = request.POST.get("phone", profile.phone)
    address = request.POST.get("address", profile.address)

    # Update user fields
    user.first_name = first_name
    user.last_name = last_name
    user.email = email
    user.save()

    # Update profile fields (do NOT touch date_of_birth)
    profile.phone = phone
    profile.address = address
    # keep profile.date_of_birth as-is
    profile.save()

    # Return success JSON including the stored DOB for UI display
    return JsonResponse({
        "success": True,
        "message": "Profile updated successfully!",
        "updated_data": {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone": profile.phone or "",
            "address": profile.address or "",
            "date_of_birth": profile.date_of_birth.strftime("%Y-%m-%d") if profile.date_of_birth else "",
        }
    })
    

@require_http_methods(["GET"])
def get_booking_selection(request):
        booking_data = request.session.get('booking_selection', {})
        return JsonResponse(booking_data)



@login_required
@require_POST
def delete_account(request):
    """
    Permanently delete the logged-in user's account.
    Accepts AJAX (application/json) and normal form POST.
    """
    # Basic confirmation check for safety (optional)
    
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    # Optional: you may verify `request.user` password before deleting.
    

    try:
        user = request.user

        # Option A (hard delete)
        user.delete()

        # Option B (soft delete) example:
        # user.is_active = False
        # user.save()

        # Logout the session (important)
        logout(request)

        if is_ajax:
            # return JSON instructing client where to redirect
            return JsonResponse({
                "success": True,
                "message": "Account deleted successfully.",
                "redirect": "/"
            })
        else:
            # non-AJAX: redirect to homepage (logged out)
            return redirect('home')

    except Exception as e:
        # Log the exception in your real app
        if is_ajax:
            return JsonResponse({"success": False, "message": "Failed to delete account."}, status=500)
        else:
            return redirect('profile')  # or render an error page
        

def contact_us(request):
    
    return render(request, 'contact.html')

def latest_offer(request):
    return render(request, 'latest_offer.html')
