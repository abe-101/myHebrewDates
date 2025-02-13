from django.contrib.auth.decorators import login_not_required
from django.urls import path

from my_hebrew_dates.hebcal.views import CalendarDeleteView
from my_hebrew_dates.hebcal.views import CalendarUpdateModalView
from my_hebrew_dates.hebcal.views import calendar_detail_view
from my_hebrew_dates.hebcal.views import calendar_edit_view
from my_hebrew_dates.hebcal.views import calendar_file
from my_hebrew_dates.hebcal.views import calendar_list_view
from my_hebrew_dates.hebcal.views import create_calendar_view
from my_hebrew_dates.hebcal.views import create_hebrew_date_htmx
from my_hebrew_dates.hebcal.views import delete_hebrew_date_htmx
from my_hebrew_dates.hebcal.views import edit_hebrew_date_htmx
from my_hebrew_dates.hebcal.views import serve_pixel
from my_hebrew_dates.hebcal.views import update_calendar_links_htmx

app_name = "hebcal"

urlpatterns = [
    path("<uuid:uuid>/edit/", calendar_edit_view, name="calendar_edit"),
    path(
        "<uuid:uuid>/edit-hebrew-date-htmx/<int:pk>/",
        edit_hebrew_date_htmx,
        name="edit_hebrew_date_htmx",
    ),
    path(
        "<int:pk>/update-calendar-modal/",
        view=CalendarUpdateModalView.as_view(),
        name="update_calendar",
    ),
    path(
        "<uuid:uuid>/delete-hebrew-date-htmx/<int:pk>/",
        delete_hebrew_date_htmx,
        name="delete_hebrew_date_htmx",
    ),
    path(
        "<uuid:uuid>/create-hebrew-date-htmx/",
        create_hebrew_date_htmx,
        name="create_hebrew_date_htmx",
    ),
    path("<uuid:uuid>/delete/", CalendarDeleteView.as_view(), name="calendar_delete"),
    path("new/", create_calendar_view, name="calendar_new"),
    path("", calendar_list_view, name="calendar_list"),
    path(
        "<uuid:uuid>/",
        login_not_required(calendar_detail_view),
        name="calendar_detail",
    ),
    path(
        "<uuid:uuid>.ical",
        login_not_required(calendar_file),
        name="legacy_calendar_file",
    ),
    path("<uuid:uuid>.ics", login_not_required(calendar_file), name="calendar_file"),
    path(
        "serve-image/<uuid:pixel_id>/<int:pk>",
        login_not_required(serve_pixel),
        name="serve_pixel",
    ),
    path(
        "update-calendar-links-htmx/<uuid:uuid>/",
        login_not_required(update_calendar_links_htmx),
        name="update_calendar_links_htmx",
    ),
]
