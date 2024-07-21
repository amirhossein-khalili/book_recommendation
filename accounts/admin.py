from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group

from .forms import UserChangeForm, UserCreationForm
from .models import User


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ("email", "phone_number", "is_admin")
    list_filter = ("is_admin",)
    readonly_fields = ("last_login",)

    fieldsets = (
        ("Main", {"fields": ("email", "phone_number", "user_name", "password")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_admin",
                    "is_superuser",
                    "last_login",
                    "groups",
                    "user_permissions",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "fields": (
                    "phone_number",
                    "email",
                    "user_name",
                    "password1",
                    "password2",
                )
            },
        ),
    )

    search_fields = ("email", "user_name")
    ordering = ("user_name",)
    filter_horizontal = ("groups", "user_permissions")


admin.site.unregister(Group)
admin.site.register(User, UserAdmin)
