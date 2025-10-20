from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegistrationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import UserProfile
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.http import JsonResponse
import json


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


@login_required
def admin_users(request):
    """Admin users management page - list users and allow role updates"""
    if not hasattr(request.user, 'profile') or not request.user.profile.is_admin_user:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')

    users = User.objects.all().select_related('profile')

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

    return render(request, 'admin_users.html', {'users': users})


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


@login_required
@require_http_methods(["POST"])
def add_user(request):
    """Add a new user"""
    try:
        # Check if the current user is an admin
        if not hasattr(request.user, 'profile') or not request.user.profile.is_admin_user:
            return JsonResponse({
                'success': False,
                'message': 'Unauthorized. Admin privileges required.'
            }, status=403)
        
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        is_admin = request.POST.get('is_admin') == 'on'
        
        # Validate required fields
        if not all([username, email, password]):
            return JsonResponse({
                'success': False,
                'message': 'Username, email, and password are required'
            }, status=400)
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            return JsonResponse({
                'success': False,
                'message': 'Username already exists'
            }, status=400)
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'success': False,
                'message': 'Email already exists'
            }, status=400)
        
        # Create the user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Set admin status if requested
        if is_admin and hasattr(user, 'profile'):
            user.profile.is_admin_user = True
            user.profile.save()
        
        return JsonResponse({
            'success': True,
            'message': f'User {username} created successfully'
        })
    
    except Exception as e:
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