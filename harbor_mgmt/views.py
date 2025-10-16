from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegistrationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import UserProfile
from django.contrib.auth.models import User


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
    """Admin users management page - handle list, add, edit, and delete"""
    if not hasattr(request.user, 'profile') or not request.user.profile.is_admin_user:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')

    users = User.objects.all().select_related('profile')

    if request.method == "POST":
        action = request.POST.get("action")
        user_id = request.POST.get("user_id")

        # 🗑 DELETE USER
        if action == "delete":
            try:
                user_to_delete = User.objects.get(id=user_id)
                username = user_to_delete.username
                user_to_delete.delete()
                messages.success(request, f"User '{username}' has been deleted successfully.")
            except User.DoesNotExist:
                messages.error(request, "User not found.")

        # ➕ ADD USER
        elif action == "add_user":
            username = request.POST.get("username")
            email = request.POST.get("email")
            password = request.POST.get("password")
            first_name = request.POST.get("first_name")
            last_name = request.POST.get("last_name")
            role = request.POST.get("role")

            if username and email and password:
                if User.objects.filter(username=username).exists():
                    messages.error(request, "That username is already taken.")
                else:
                    new_user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name
                    )
                    profile = UserProfile.objects.create(user=new_user)
                    if role == "admin":
                        profile.is_admin_user = True
                        profile.save()
                    messages.success(request, f"User '{username}' has been created successfully.")
            else:
                messages.error(request, "Please fill out all required fields.")

        # ✏️ EDIT USER
        elif action == "edit_user" and user_id:
            try:
                user = User.objects.get(id=user_id)
                profile = user.profile
                user.first_name = request.POST.get("first_name")
                user.last_name = request.POST.get("last_name")
                user.email = request.POST.get("email")
                profile.is_admin_user = True if request.POST.get("role") == "admin" else False
                user.save()
                profile.save()
                messages.success(request, f"User '{user.username}' has been updated successfully.")
            except User.DoesNotExist:
                messages.error(request, "User not found.")

        return redirect("admin_users")

    return render(request, "admin_users.html", {"users": users})