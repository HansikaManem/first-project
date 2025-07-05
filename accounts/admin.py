from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = (*UserAdmin.list_display, "role")
    list_filter  = (*UserAdmin.list_filter,  "role")
    fieldsets = UserAdmin.fieldsets + (
        (None, {"fields": ("role",)}),
    )

