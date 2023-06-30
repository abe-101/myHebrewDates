from django.test import TestCase

from my_hebrew_dates.hebcal.forms import CalendarForm, HebrewDateForm


class TestForms(TestCase):
    def test_calendar_form_valid_data(self):
        form = CalendarForm(data={"name": "Test Calendar", "timezone": "America/New_York"})
        self.assertTrue(form.is_valid())

    def test_calendar_form_no_data(self):
        form = CalendarForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 2)

    def test_hebrew_date_form_valid_data(self):
        form = HebrewDateForm(data={"name": "Test Date", "month": 1, "day": 1, "event_type": "🎂"})
        self.assertTrue(form.is_valid())

    def test_hebrew_date_form_no_data(self):
        form = HebrewDateForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 4)
