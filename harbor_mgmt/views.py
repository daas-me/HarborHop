from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegistrationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import UserProfile
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils import timezone
import json
import logging

logger = logging.getLogger(__name__)

def home(request):
    # Ensure user has a profile if authenticated
    if request.user.is_authenticated:
        try:
            request.user.profile
        except UserProfile.DoesNotExist:
            UserProfile.objects.create(user=request.user)
    
    return render(request, 'home.html')

def register(request):
    """Handle user registration"""
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # Create UserProfile for the new user
            UserProfile.objects.create(user=user)
            
            login(request, user)
            messages.success(request, f'Welcome, {user.first_name or user.username}! Your account has been created.')
            return redirect('home')
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
    return redirect('login')

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
    total_users = User.objects.count()
    admin_users = UserProfile.objects.filter(is_admin_user=True).count()
    active_users = User.objects.filter(is_active=True).count()

    from django.utils import timezone
    from datetime import timedelta
    start_of_month = timezone.now().replace(day=1)
    new_this_month = User.objects.filter(date_joined__gte=start_of_month).count()

    context = {
        'user': request.user,
        'total_users': total_users,
        'admin_users': admin_users,
        'active_users': active_users,
        'new_this_month': new_this_month,
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
