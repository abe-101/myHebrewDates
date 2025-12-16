from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html

from .models import Calendar
from .models import HebrewDate
from .models import UserCalendarSubscription
from .utils import send_migration_notification_email


class HebrewDateInline(admin.TabularInline):
    model = HebrewDate


@admin.register(Calendar)
class CalendarAdmin(admin.ModelAdmin):
    inlines = [HebrewDateInline]
    list_display = (
        "name",
        "owner_email",
        "display_uuid",
        "timezone",
        "events_count",
        "is_migrated",
        "migrated_at",
        "created",
        "modified",
    )
    search_fields = ("name", "uuid", "owner__email")
    list_filter = ("migrated_at",)
    readonly_fields = ("migrated_at",)
    actions = ["migrate_and_notify"]

    def owner_email(self, obj):
        return obj.owner.email

    @admin.display(ordering="events_count")
    def events_count(self, obj):
        return obj.events_count

    def display_uuid(self, obj):
        url = reverse("hebcal:calendar_detail", args=[obj.uuid])
        return format_html('<a href="{}">{}</a>', url, obj.uuid)

    def get_queryset(self, request):
        queryset = super().get_queryset(request).prefetch_related("owner")
        return queryset.annotate(events_count=Count("calendarOf")).order_by(
            "-events_count",
        )

    @admin.action(description="Migrate calendars and send notification email")
    def migrate_and_notify(self, request, queryset):
        """Enable migration for selected calendars and send notification emails."""
        migrated_count = 0
        email_count = 0

        for calendar in queryset:
            # Enable migration if not already migrated
            if not calendar.is_migrated:
                calendar.migrate_to_authenticated()
                migrated_count += 1

            # Send notification email (whether just migrated or already migrated)
            if calendar.is_migrated:
                send_migration_notification_email(calendar)
                email_count += 1

        self.message_user(
            request,
            f"Enabled migration for {migrated_count} calendar(s) and sent "
            f"{email_count} notification email(s). (Placeholder - check logs)",
        )


@admin.register(HebrewDate)
class HebrewDateAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "month",
        "day",
        "event_type",
        "link_to_calendar",
        "formatted_event_date",
        "created",
        "modified",
    )
    list_filter = ("event_type", "calendar", "month", "day")
    search_fields = (
        "name",
        "calendar__name",
        "calendar__owner__email",
        "calendar__uuid",
    )

    @admin.display(description="Calendar")
    def link_to_calendar(self, obj):
        # This method creates a link to the Calendar object in the admin.
        url = reverse("admin:hebcal_calendar_change", args=[obj.calendar.pk])
        return format_html('<a href="{}">{}</a>', url, obj.calendar.name)

    @admin.display(description="Formatted Event Date")
    def formatted_event_date(self, obj):
        # Assuming you have a method to format the date
        return obj.get_hebrew_date()


@admin.register(UserCalendarSubscription)
class UserCalendarSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "subscription_id",
        "user_email",
        "calendar_name",
        "calendar_owner",
        "alarm_time",
        "last_accessed",
        "created",
    )
    search_fields = (
        "subscription_id",
        "user__email",
        "calendar__name",
        "calendar__owner__email",
    )
    list_filter = ("created", "last_accessed", "alarm_time")
    readonly_fields = ("subscription_id", "created", "modified")
    raw_id_fields = ("user", "calendar")

    @admin.display(description="User")
    def user_email(self, obj):
        return obj.user.email

    @admin.display(description="Calendar")
    def calendar_name(self, obj):
        url = reverse("admin:hebcal_calendar_change", args=[obj.calendar.pk])
        return format_html('<a href="{}">{}</a>', url, obj.calendar.name)

    @admin.display(description="Calendar Owner")
    def calendar_owner(self, obj):
        return obj.calendar.owner.email

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related("user", "calendar", "calendar__owner")
