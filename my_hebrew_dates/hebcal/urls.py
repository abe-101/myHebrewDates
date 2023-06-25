from django.urls import path

from .views import (
    CalendarCreateView,
    CalendarDeleteView,
    CalendarListView,
    CalendarShareView,
    CalendarUpdateView,
    calendar_file,
)

app_name = "hebcal"

urlpatterns = [
    path("<int:pk>/edit/", CalendarUpdateView.as_view(), name="calendar_edit"),
    path("<int:pk>/delete/", CalendarDeleteView.as_view(), name="calendar_delete"),
    path("new/", CalendarCreateView.as_view(), name="calendar_new"),
    path("", CalendarListView.as_view(), name="calendar_list"),
    path("<uuid:uuid>/", CalendarShareView.as_view(), name="calendar_share"),
    path("<uuid:uuid>.ical", calendar_file, name="legacy_calendar_file"),
    path("<uuid:uuid>.ics", calendar_file, name="calendar_file"),
]
