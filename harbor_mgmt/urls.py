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
    path('admin/add-user/', views.add_user, name='add_user'),
    path('admin/delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
]