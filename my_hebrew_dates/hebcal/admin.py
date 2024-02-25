from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html

from .models import Calendar, HebrewDate


class HebrewDateInline(admin.TabularInline):
    model = HebrewDate


@admin.register(Calendar)
class CalendarAdmin(admin.ModelAdmin):
    inlines = [HebrewDateInline]
    list_display = ("name", "owner_email", "display_uuid", "timezone", "events_count")
    search_fields = ("name", "uuid", "owner__email")

    def owner_email(self, obj):
        return obj.owner.email

    @admin.display(ordering="_events_count")
    def events_count(self, obj):
        return obj._events_count

    def display_uuid(self, obj):
        url = reverse("hebcal:calendar_detail", args=[obj.uuid])
        return format_html('<a href="{}">{}</a>', url, obj.uuid)

    def get_queryset(self, request):
        queryset = super().get_queryset(request).prefetch_related("owner")
        queryset = queryset.annotate(_events_count=Count("calendarOf")).order_by(
            "-_events_count"
        )  # Default descending order
        return queryset


@admin.register(HebrewDate)
class HebrewDateAdmin(admin.ModelAdmin):
    list_display = ("name", "month", "day", "event_type", "link_to_calendar", "formatted_event_date")
    list_filter = ("event_type", "calendar", "month", "day")
    search_fields = ("name", "calendar__name", "calendar__owner__email", "calendar__uuid")

    @admin.display(description="Calendar")
    def link_to_calendar(self, obj):
        # This method creates a link to the Calendar object in the admin.
        url = reverse("admin:hebcal_calendar_change", args=[obj.calendar.pk])
        return format_html('<a href="{}">{}</a>', url, obj.calendar.name)

    @admin.display(description="Formatted Event Date")
    def formatted_event_date(self, obj):
        # Assuming you have a method to format the date
        return obj.get_hebrew_date()
