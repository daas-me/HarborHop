from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegistrationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import UserProfile


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
    if request.user.is_authenticated:
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
    # Check if user has admin access
    try:
        if not request.user.profile.is_admin_user:
            messages.error(request, "You don't have permission to access the admin dashboard.")
            return redirect('home')
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=request.user)
        messages.error(request, "You don't have permission to access the admin dashboard.")
        return redirect('home')
    
    context = {
        'user': request.user,
    }
    return render(request, 'admin_dashboard.html', context)

@login_required
def admin_users(request):
    """Admin users management page - UI only"""
    if not hasattr(request.user, 'profile') or not request.user.profile.is_admin_user:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    context = {
        'user': request.user,
    }
    return render(request, 'admin_users.html', context)