import uuid

from django.test import SimpleTestCase
from django.urls import resolve
from django.urls import reverse

from my_hebrew_dates.hebcal.views import CalendarDeleteView
from my_hebrew_dates.hebcal.views import calendar_detail_view
from my_hebrew_dates.hebcal.views import calendar_edit_view
from my_hebrew_dates.hebcal.views import calendar_file
from my_hebrew_dates.hebcal.views import create_calendar_view
from my_hebrew_dates.hebcal.views import delete_hebrew_date_htmx
from my_hebrew_dates.hebcal.views import hebrew_date_form_view
from my_hebrew_dates.hebcal.views import serve_pixel
from my_hebrew_dates.hebcal.views import update_calendar_links_htmx


class TestUrls(SimpleTestCase):
    @staticmethod
    def generate_uuid():
        return str(uuid.uuid4())

    def test_calendar_edit_url(self):
        uuid = self.generate_uuid()
        url = reverse("hebcal:calendar_edit", args=[uuid])
        assert resolve(url).func == calendar_edit_view

    def test_calendar_delete_url(self):
        uuid = self.generate_uuid()
        url = reverse("hebcal:calendar_delete", args=[uuid])
        resolved = resolve(url)
        assert hasattr(resolved.func, "view_class")
        assert resolved.func.view_class == CalendarDeleteView

    def test_calendar_new_url(self):
        url = reverse("hebcal:calendar_new")
        assert resolve(url).func == create_calendar_view

    def test_calendar_detail_url(self):
        uuid = self.generate_uuid()
        url = reverse("hebcal:calendar_detail", args=[uuid])
        assert resolve(url).func == calendar_detail_view

    def test_legacy_calendar_file_url(self):
        uuid = self.generate_uuid()
        url = reverse("hebcal:legacy_calendar_file", args=[uuid])
        assert resolve(url).func == calendar_file

    def test_calendar_file_url(self):
        uuid = self.generate_uuid()
        url = reverse("hebcal:calendar_file", args=[uuid])
        assert resolve(url).func == calendar_file

    def test_hebrew_date_edit_url(self):
        uuid = self.generate_uuid()
        pk = 1  # Example primary key
        url = reverse("hebcal:hebrew_date_edit", args=[uuid, pk])
        assert resolve(url).func == hebrew_date_form_view

    def test_delete_hebrew_date_htmx_url(self):
        uuid = self.generate_uuid()
        pk = 1  # Example primary key
        url = reverse("hebcal:delete_hebrew_date_htmx", args=[uuid, pk])
        assert resolve(url).func == delete_hebrew_date_htmx

    def test_hebrew_date_new_url(self):
        uuid = self.generate_uuid()
        url = reverse("hebcal:hebrew_date_new", args=[uuid])
        assert resolve(url).func == hebrew_date_form_view

    def test_serve_pixel_url(self):
        uuid = self.generate_uuid()
        pk = 1  # Example primary key
        url = reverse("hebcal:serve_pixel", args=[uuid, pk])
        assert resolve(url).func == serve_pixel

    def test_update_calendar_links_htmx_url(self):
        uuid = self.generate_uuid()
        url = reverse("hebcal:update_calendar_links_htmx", args=[uuid])
        assert resolve(url).func == update_calendar_links_htmx
