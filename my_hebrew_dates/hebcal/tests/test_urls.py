import uuid

from django.test import SimpleTestCase
from django.urls import resolve, reverse

from my_hebrew_dates.hebcal.views import (
    CalendarDeleteView,
    calendar_detail_view,
    calendar_edit_view,
    calendar_file,
    create_calendar_view,
)


class TestUrls(SimpleTestCase):
    @staticmethod
    def generate_uuid():
        return str(uuid.uuid4())

    def test_calendar_edit_url(self):
        uuid = self.generate_uuid()
        url = reverse("hebcal:calendar_edit", args=[uuid])
        self.assertEqual(resolve(url).func, calendar_edit_view)

    def test_calendar_delete_url(self):
        uuid = self.generate_uuid()
        url = reverse("hebcal:calendar_delete", args=[uuid])
        self.assertEqual(resolve(url).func.view_class, CalendarDeleteView)

    def test_calendar_new_url(self):
        url = reverse("hebcal:calendar_new")
        self.assertEqual(resolve(url).func, create_calendar_view)

    def test_calendar_detail_url(self):
        uuid = self.generate_uuid()
        url = reverse("hebcal:calendar_detail", args=[uuid])
        self.assertEqual(resolve(url).func, calendar_detail_view)

    def test_legacy_calendar_file_url(self):
        uuid = self.generate_uuid()
        url = reverse("hebcal:legacy_calendar_file", args=[uuid])
        self.assertEqual(resolve(url).func, calendar_file)

    def test_calendar_file_url(self):
        uuid = self.generate_uuid()
        url = reverse("hebcal:calendar_file", args=[uuid])
        self.assertEqual(resolve(url).func, calendar_file)
