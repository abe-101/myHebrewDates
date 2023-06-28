from django.test import TestCase
from django.urls import reverse

from my_hebrew_dates.hebcal.models import Calendar, HebrewDate
from my_hebrew_dates.users.models import User


class CalendarModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.calendar = Calendar.objects.create(name="Test Calendar", owner=self.user)

    def test_str_representation(self):
        self.assertEqual(str(self.calendar), "Test Calendar")

    def test_get_absolute_url(self):
        url = reverse("hebcal:calendar_edit", kwargs={"uuid": self.calendar.uuid})
        self.assertEqual(self.calendar.get_absolute_url(), url)


class HebrewDateModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.calendar = Calendar.objects.create(name="Test Calendar", owner=self.user)
        self.hebrew_date = HebrewDate.objects.create(
            name="Test Hebrew Date", month=1, day=1, event_type="🎂", calendar=self.calendar
        )

    def test_str_representation(self):
        self.assertEqual(str(self.hebrew_date), "Test Hebrew Date")

    def test_get_hebrew_date(self):
        self.assertEqual(self.hebrew_date.get_hebrew_date(), "א ניסן")

    #    def test_get_english_dates(self):
    #        self.assertEqual(self.hebrew_date.get_english_dates(), {'hebrew': '1-1', 'english': 'March 23'})

    def test_get_formatted_name(self):
        self.assertEqual(self.hebrew_date.get_formatted_name(), "Test Hebrew Date's Birthday")

    def test_get_absolute_url(self):
        url = reverse("hebcal:calendar_edit", kwargs={"uuid": self.calendar.uuid})
        self.assertEqual(self.hebrew_date.get_absolute_url(), url)
