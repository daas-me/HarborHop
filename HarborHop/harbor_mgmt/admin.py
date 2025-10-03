from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

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

# Unregister the default and register with customization
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)