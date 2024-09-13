# ruff: noqa: S106
from django.contrib.auth import get_user_model
from django.test import TestCase

from my_hebrew_dates.hebcal.forms import CalendarForm
from my_hebrew_dates.hebcal.forms import HebrewDateForm
from my_hebrew_dates.hebcal.models import Calendar
from my_hebrew_dates.hebcal.models import HebrewDate

User = get_user_model()

TWO = 2
FOUR = 4


class TestCalendarForm(TestCase):
    def test_calendar_form_valid_data(self):
        form = CalendarForm(
            data={"name": "Test Calendar", "timezone": "America/New_York"},
        )
        assert form.is_valid()

    def test_calendar_form_no_data(self):
        form = CalendarForm(data={})
        assert not form.is_valid()
        assert len(form.errors) == TWO

    def test_calendar_form_invalid_timezone(self):
        form = CalendarForm(
            data={"name": "Test Calendar", "timezone": "Invalid-Timezone"},
        )
        assert not form.is_valid()
        assert "timezone" in form.errors

    def test_calendar_form_empty_name(self):
        form = CalendarForm(data={"name": "", "timezone": "America/New_York"})
        assert not form.is_valid()
        assert "name" in form.errors


class TestHebrewDateForm(TestCase):
    def test_hebrew_date_form_valid_data(self):
        form = HebrewDateForm(
            data={"name": "Test Date", "month": 1, "day": 1, "event_type": "🎂"},
        )
        assert form.is_valid()

    def test_hebrew_date_form_no_data(self):
        form = HebrewDateForm(data={})
        assert not form.is_valid()
        assert len(form.errors) == FOUR

    def test_hebrew_date_form_invalid_month(self):
        form = HebrewDateForm(
            data={"name": "Test Date", "month": 99, "day": 1, "event_type": "🎂"},
        )
        assert not form.is_valid()
        assert "month" in form.errors

    def test_hebrew_date_form_invalid_day(self):
        form = HebrewDateForm(
            data={"name": "Test Date", "month": 1, "day": 99, "event_type": "🎂"},
        )
        assert not form.is_valid()
        assert "day" in form.errors

    def test_hebrew_date_form_invalid_event_type(self):
        form = HebrewDateForm(
            data={"name": "Test Date", "month": 1, "day": 1, "event_type": "Invalid"},
        )
        assert not form.is_valid()
        assert "event_type" in form.errors

    def test_hebrew_date_form_initialization_with_instance(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
        )
        self.calendar = Calendar.objects.create(name="Test Calendar", owner=self.user)
        hebrew_date = HebrewDate.objects.create(
            calendar=self.calendar,
            name="Test Date",
            month=1,
            day=1,
            event_type="🎂",
        )
        form = HebrewDateForm(instance=hebrew_date)
        # Check if the delete button is added in the form
        assert hebrew_date.name in form.as_p()
