from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.authentication.models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "role", "is_active", "is_staff")
    list_filter = ("role", "is_active", "is_staff")
    fieldsets = UserAdmin.fieldsets + (
        ("AP Automation", {"fields": ("role", "department", "phone", "is_active_employee")}),
    )
