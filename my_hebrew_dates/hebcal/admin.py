from django.contrib import admin

from .models import Calendar, HebrewDate


class CommentInline(admin.TabularInline):
    model = HebrewDate


@admin.register(Calendar)
class CalendarAdmin(admin.ModelAdmin):
    inlines = [CommentInline]
    list_display = ("name", "display_uuid", "timezone")
    search_fields = (
        "name",
        "uuid",
    )  # Add search functionality based on name

    @admin.display(description="UUID")
    def display_uuid(self, obj):
        return obj.uuid


@admin.register(HebrewDate)
class HebrewDateAdmin(admin.ModelAdmin):
    list_display = ("name", "month", "day", "event_type", "calendar")
    list_filter = ("month", "event_type", "calendar")  # Filter by month, event type, and calendar
    search_fields = ("name", "calendar__name")  # Search by Hebrew date name and calendar name
