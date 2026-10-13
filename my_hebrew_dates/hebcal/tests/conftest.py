from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model

from my_hebrew_dates.hebcal import hebrew_date as hebrew_date_module
from my_hebrew_dates.hebcal.models import Calendar
from my_hebrew_dates.hebcal.models import HebrewDate

User = get_user_model()

# 5787 is a Hebrew leap year, so the three-year window starting here
# covers both Adar I and Adar II.
PINNED_HEBREW_YEAR = 5787

# A later point to travel to when a test needs modified to diverge from
# created, which the single held instant cannot show.
LATER = "2026-09-15 08:30:00 +0000"

DEFAULT_ALARM = timedelta(hours=9)


@pytest.fixture
def pinned_hebrew_dates():
    """
    Freeze the rolling three-year Hebrew-to-Gregorian window.

    Freezing the clock cannot do this: ``hebrew_to_english_dict`` is
    built at import time, so it already holds the real year by the time
    any test runs. It has to be rebuilt for a fixed year, and ``models``
    imported the dict object itself, so it is mutated in place rather
    than rebound.
    """
    pinned = hebrew_date_module.create_hebrew_to_english_dict(
        start_year=PINNED_HEBREW_YEAR,
    )
    shared = hebrew_date_module.hebrew_to_english_dict
    original = dict(shared)
    shared.clear()
    shared.update(pinned)
    yield
    shared.clear()
    shared.update(original)


@pytest.fixture
def calendar_owner(db, frozen_clock):
    return User.objects.create_user(
        username="golden-owner",
        email="golden@example.com",
    )


@pytest.fixture
def make_calendar(calendar_owner):
    """
    Build a Calendar with the given (month, day, event_type, name) events.
    """

    def _make(name="Golden Calendar", timezone="America/New_York", events=()):
        calendar = Calendar.objects.create(
            name=name,
            owner=calendar_owner,
            timezone=timezone,
        )
        for month, day, event_type, person in events:
            HebrewDate.objects.create(
                calendar=calendar,
                month=month,
                day=day,
                event_type=event_type,
                name=person,
            )
        return calendar

    return _make
