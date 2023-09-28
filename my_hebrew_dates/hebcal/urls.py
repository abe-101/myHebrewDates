from django.urls import path

from .views import (
    CalendarCreateView,
    CalendarDeleteView,
    CalendarDetailView,
    CalendarListView,
    CalendarUpdateView,
    calendar_file,
    serve_pixel,
)

app_name = "hebcal"

urlpatterns = [
    path("<uuid:uuid>/edit/", CalendarUpdateView.as_view(), name="calendar_edit"),
    path("<uuid:uuid>/delete/", CalendarDeleteView.as_view(), name="calendar_delete"),
    path("new/", CalendarCreateView.as_view(), name="calendar_new"),
    path("", CalendarListView.as_view(), name="calendar_list"),
    path("<uuid:uuid>/", CalendarDetailView.as_view(), name="calendar_detail"),
    path("<uuid:uuid>.ical", calendar_file, name="legacy_calendar_file"),
    path("<uuid:uuid>.ics", calendar_file, name="calendar_file"),
    path("serve-image/<uuid:pixel_id>/<int:pk>", serve_pixel, name="serve_pixel"),
]
