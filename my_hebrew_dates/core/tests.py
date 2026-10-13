"""
Tests for the test harness itself.

The clock is held still for every test by an autouse fixture, so that
nothing derived from it can pass or fail on timing. These guard that
wiring: without them the fixture could be broken or removed and only
the tests that happen to assert a timestamp would notice.
"""

import datetime as dt

import pytest
from django.utils import timezone

from my_hebrew_dates.conftest import FROZEN_NOW

HELD_INSTANT = dt.datetime.fromisoformat(
    FROZEN_NOW.replace(" +0000", "+00:00"),
)
ELSEWHERE = "2030-01-02 03:04:05 +0000"
ELSEWHERE_INSTANT = dt.datetime.fromisoformat(
    ELSEWHERE.replace(" +0000", "+00:00"),
)


def test_clock_is_held_at_the_fixed_instant():
    assert timezone.now() == HELD_INSTANT


def test_clock_does_not_advance_within_a_test():
    assert timezone.now() == timezone.now()


def test_traveller_can_move_the_clock(frozen_clock):
    frozen_clock.move_to(ELSEWHERE)

    assert timezone.now() == ELSEWHERE_INSTANT
    assert timezone.now() == timezone.now()


@pytest.mark.time_ticks
def test_time_ticks_marker_releases_the_clock():
    assert timezone.now() != HELD_INSTANT
