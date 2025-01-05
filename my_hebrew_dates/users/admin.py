from allauth.account.decorators import secure_admin_login
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .forms import UserAdminChangeForm
from .forms import UserAdminCreationForm
from .models import User

if settings.DJANGO_ADMIN_FORCE_ALLAUTH:
    # Force the `admin` sign in process to go through the `django-allauth` workflow:
    # https://docs.allauth.org/en/latest/common/admin.html#admin
    admin.autodiscover()
    admin.site.login = secure_admin_login(admin.site.login)  # type: ignore[method-assign]


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("name", "email")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (  # Add this section
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2"),
            },
        ),
    )

    list_display = [
        "username",
        "name",
        "email",
        "is_superuser",
        "calendar_count_link",
        "last_login",
        "date_joined",
    ]
    search_fields = ["name", "email", "username"]
    ordering = (
        "username",
        "name",
        "email",
        "is_superuser",
        "last_login",
        "date_joined",
    )

    def get_queryset(self, request):
        # Annotate each user with the count of calendars they own
        queryset = super().get_queryset(request)
        return queryset.annotate(calendar_count=Count("calendar"))

    @admin.display(description="Calendars")
    def calendar_count_link(self, obj):
        # Count is taken from the annotated _calendar_count in get_queryset
        count = obj.calendar_count
        url = (
            reverse("admin:hebcal_calendar_changelist")
            + "?"
            + f"owner__id__exact={obj.id}"
        )
        return format_html('<a href="{}">{} Calendars</a>', url, count)
