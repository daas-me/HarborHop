from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/users/', views.admin_users, name='admin_users'),
    path('change-user-role/', views.change_user_role, name='change_user_role'),
    path('add-user/', views.add_user, name='add_user'),
    path('edit-user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('test-csrf/', views.test_csrf, name='test_csrf'),
    path('toggle-user-active-ajax/<int:user_id>/', views.toggle_user_active_ajax, name='toggle_user_active_ajax'),
    path('profile/', views.profile_settings, name='profile_settings'),
    path('search-trips/', views.search_trips, name='search_trips'),
    path('search-voyages/', views.search_voyages_page, name='search_voyages_page'),
    path('search-voyages-barkota/', views.search_voyages_barkota, name='search_voyages_barkota'),
    path('api/locations/', views.get_all_locations, name='get_all_locations'),
    path('update-profile-ajax/', views.update_profile_ajax, name='update_profile_ajax'),
]