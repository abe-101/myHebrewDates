from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html

from .models import Calendar
from .models import HebrewDate


class HebrewDateInline(admin.TabularInline):
    model = HebrewDate
    fields = ("name", "event_type", "month", "day")
    extra = 0


@admin.register(Calendar)
class CalendarAdmin(admin.ModelAdmin):
    inlines = [HebrewDateInline]
    list_display = (
        "name",
        "owner_link",
        "public_page",
        "events_count",
        "timezone",
        "created",
        "modified",
    )
    list_select_related = ("owner",)
    search_fields = ("name", "uuid", "owner__email")
    date_hierarchy = "created"
    ordering = ("-created",)
    autocomplete_fields = ("owner",)
    fields = ("name", "owner", "timezone", "public_page", "created", "modified")
    readonly_fields = ("public_page", "created", "modified")

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(events_count=Count("calendarOf"))

    @admin.display(description="Owner", ordering="owner__email")
    def owner_link(self, obj):
        url = reverse("admin:users_user_change", args=[obj.owner.pk])
        return format_html('<a href="{}">{}</a>', url, obj.owner.email)

    @admin.display(description="Events", ordering="events_count")
    def events_count(self, obj):
        return obj.events_count

    @admin.display(description="Public page")
    def public_page(self, obj):
        url = reverse("hebcal:calendar_detail", args=[obj.uuid])
        return format_html('<a href="{}">{}</a>', url, obj.uuid)


@admin.register(HebrewDate)
class HebrewDateAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "event_type",
        "hebrew_date",
        "calendar_link",
        "owner_email",
        "created",
    )
    list_select_related = ("calendar__owner",)
    list_filter = ("event_type",)
    search_fields = ("name", "calendar__name", "calendar__owner__email")
    ordering = ("-created",)
    autocomplete_fields = ("calendar",)

    @admin.display(description="Date", ordering="month")
    def hebrew_date(self, obj):
        return obj.get_hebrew_date()

    @admin.display(description="Calendar", ordering="calendar__name")
    def calendar_link(self, obj):
        url = reverse("admin:hebcal_calendar_change", args=[obj.calendar.pk])
        return format_html('<a href="{}">{}</a>', url, obj.calendar.name)

    @admin.display(description="Owner", ordering="calendar__owner__email")
    def owner_email(self, obj):
        return obj.calendar.owner.email
