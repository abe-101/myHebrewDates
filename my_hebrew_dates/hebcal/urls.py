from django.urls import path

from .views import (
    CalendarCreateView,
    CalendarDeleteView,
    CalendarListView,
    calendar_detail_view,
    calendar_edit_view,
    calendar_file,
    serve_pixel,
    update_calendar_links_htmx,
)

app_name = "hebcal"

urlpatterns = [
    path("<uuid:uuid>/edit/", calendar_edit_view, name="calendar_edit"),
    path("<uuid:uuid>/delete/", CalendarDeleteView.as_view(), name="calendar_delete"),
    path("new/", CalendarCreateView.as_view(), name="calendar_new"),
    path("", CalendarListView.as_view(), name="calendar_list"),
    path("<uuid:uuid>/", calendar_detail_view, name="calendar_detail"),
    path("<uuid:uuid>.ical", calendar_file, name="legacy_calendar_file"),
    path("<uuid:uuid>.ics", calendar_file, name="calendar_file"),
    path("serve-image/<uuid:pixel_id>/<int:pk>", serve_pixel, name="serve_pixel"),
    path(
        "update-calendar-links-htmx/<uuid:uuid>/",
        update_calendar_links_htmx,
        name="update_calendar_links_htmx",
    ),
]
