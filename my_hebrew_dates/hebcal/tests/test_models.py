# ruff: noqa: S106
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from my_hebrew_dates.hebcal.models import Calendar
from my_hebrew_dates.hebcal.models import HebrewDate

User = get_user_model()


class CalendarModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
        )
        self.calendar = Calendar.objects.create(name="Test Calendar", owner=self.user)

    def test_str_representation(self):
        assert str(self.calendar) == "Test Calendar"

    def test_get_absolute_url(self):
        url = reverse("hebcal:calendar_edit", kwargs={"uuid": self.calendar.uuid})
        assert self.calendar.get_absolute_url() == url


class HebrewDateModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
        )
        self.calendar = Calendar.objects.create(name="Test Calendar", owner=self.user)
        self.hebrew_date = HebrewDate.objects.create(
            name="Test Hebrew Date",
            month=1,
            day=1,
            event_type="🎂",
            calendar=self.calendar,
        )

    def test_str_representation(self):
        assert str(self.hebrew_date) == "Test Hebrew Date"

    def test_get_hebrew_date(self):
        assert self.hebrew_date.get_hebrew_date() == "א ניסן"

    def test_get_formatted_name(self):
        assert self.hebrew_date.get_formatted_name() == "Test Hebrew Date's Birthday"

    def test_get_absolute_url(self):
        url = reverse("hebcal:calendar_edit", kwargs={"uuid": self.calendar.uuid})
        assert self.hebrew_date.get_absolute_url() == url
