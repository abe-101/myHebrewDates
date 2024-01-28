from django.contrib.auth import get_user_model
from django.test import TestCase

from my_hebrew_dates.hebcal.forms import CalendarForm, HebrewDateForm
from my_hebrew_dates.hebcal.models import Calendar, HebrewDate

User = get_user_model()


class TestCalendarForm(TestCase):
    def test_calendar_form_valid_data(self):
        form = CalendarForm(data={"name": "Test Calendar", "timezone": "America/New_York"})
        self.assertTrue(form.is_valid())

    def test_calendar_form_no_data(self):
        form = CalendarForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 2)

    def test_calendar_form_invalid_timezone(self):
        form = CalendarForm(data={"name": "Test Calendar", "timezone": "Invalid-Timezone"})
        self.assertFalse(form.is_valid())
        self.assertIn("timezone", form.errors)

    def test_calendar_form_empty_name(self):
        form = CalendarForm(data={"name": "", "timezone": "America/New_York"})
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)


class TestHebrewDateForm(TestCase):
    def test_hebrew_date_form_valid_data(self):
        form = HebrewDateForm(data={"name": "Test Date", "month": 1, "day": 1, "event_type": "🎂"})
        self.assertTrue(form.is_valid())

    def test_hebrew_date_form_no_data(self):
        form = HebrewDateForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 4)

    def test_hebrew_date_form_invalid_month(self):
        form = HebrewDateForm(data={"name": "Test Date", "month": 99, "day": 1, "event_type": "🎂"})
        self.assertFalse(form.is_valid())
        self.assertIn("month", form.errors)

    def test_hebrew_date_form_invalid_day(self):
        form = HebrewDateForm(data={"name": "Test Date", "month": 1, "day": 99, "event_type": "🎂"})
        self.assertFalse(form.is_valid())
        self.assertIn("day", form.errors)

    def test_hebrew_date_form_invalid_event_type(self):
        form = HebrewDateForm(data={"name": "Test Date", "month": 1, "day": 1, "event_type": "Invalid"})
        self.assertFalse(form.is_valid())
        self.assertIn("event_type", form.errors)

    def test_hebrew_date_form_initialization_with_instance(self):
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.calendar = Calendar.objects.create(name="Test Calendar", owner=self.user)
        hebrew_date = HebrewDate.objects.create(
            calendar=self.calendar, name="Test Date", month=1, day=1, event_type="🎂"
        )
        form = HebrewDateForm(instance=hebrew_date)
        # Check if the delete button is added in the form
        self.assertIn(hebrew_date.name, form.as_p())
