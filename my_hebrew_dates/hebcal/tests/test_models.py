# ruff: noqa: S106
import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from my_hebrew_dates.hebcal.hebrew_date import is_valid_hebrew_date
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


class IsValidHebrewDateTest(TestCase):
    def test_accepts_a_real_date(self):
        assert is_valid_hebrew_date(7, 30)  # 30 Tishrei

    def test_rejects_a_day_the_month_never_has(self):
        assert not is_valid_hebrew_date(2, 30)  # Iyar has 29 days
        assert not is_valid_hebrew_date(13, 30)  # Adar II has 29 days

    def test_accepts_the_longest_length_of_a_variable_month(self):
        assert is_valid_hebrew_date(8, 30)  # Cheshvan
        assert is_valid_hebrew_date(9, 30)  # Kislev

    def test_rejects_out_of_range_values(self):
        assert not is_valid_hebrew_date(14, 1)
        assert not is_valid_hebrew_date(0, 1)
        assert not is_valid_hebrew_date(1, 0)


class HebrewDateCleanTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
        )
        self.calendar = Calendar.objects.create(name="Test Calendar", owner=self.user)

    def build(self, month: int, day: int) -> HebrewDate:
        return HebrewDate(
            name="Test Hebrew Date",
            month=month,
            day=day,
            event_type="🎂",
            calendar=self.calendar,
        )

    def test_full_clean_accepts_a_real_date(self):
        self.build(7, 4).full_clean()

    def test_full_clean_rejects_a_day_the_month_never_has(self):
        with pytest.raises(ValidationError) as excinfo:
            self.build(2, 30).full_clean()

        assert "day" in excinfo.value.message_dict

    def test_full_clean_still_reports_an_unknown_month(self):
        with pytest.raises(ValidationError) as excinfo:
            self.build(14, 1).full_clean()

        assert "month" in excinfo.value.message_dict
