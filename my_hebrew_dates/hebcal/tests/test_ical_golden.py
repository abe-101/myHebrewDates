"""
Byte-level contract tests for the iCalendar output.

Subscription URLs live inside calendar clients we do not control, so a
change to these bytes reaches users without any deploy of theirs. These
tests pin the whole document rather than individual fields, so that any
drift - from our own edits or from an ``icalendar``, ``pyluach``, Django
or tzdata upgrade - shows up as a diff instead of a silent change.

Regenerate after an intentional change:

    UPDATE_GOLDEN=1 pytest my_hebrew_dates/hebcal/tests/test_ical_golden.py
"""

import os
from datetime import timedelta
from pathlib import Path

import pytest

from my_hebrew_dates.hebcal.utils import generate_ical
from my_hebrew_dates.hebcal.utils import generate_ical_experimental

GOLDEN_DIR = Path(__file__).parent / "golden"

BIRTHDAY = "🎂"
ANNIVERSARY = "💍"
YARTZEIT = "🕯️"

NISAN = 1
CHESHVAN = 8
KISLEV = 9
ADAR_I = 12
ADAR_II = 13

GOOGLE_USER_AGENT = (
    "Mozilla/5.0 (compatible; Google-Calendar-Importer; "
    "+http://www.google.com/calendar)"
)
APPLE_USER_AGENT = "Mac OS X/10.15.7 (19H2) CalendarAgent/950.11"


def assert_matches_golden(name: str, actual: str) -> None:
    path = GOLDEN_DIR / f"{name}.ics"

    # newline="" keeps the CRLF endings RFC 5545 requires out of the
    # universal-newline translation that would otherwise hide them.
    # Path.open takes newline on every supported Python; Path.read_text
    # only grew it in 3.13.
    # An exact match, not merely truthy: UPDATE_GOLDEN=0 would
    # otherwise rewrite the fixtures and report a pass, turning a
    # verification run into a silent update run.
    if os.environ.get("UPDATE_GOLDEN") == "1":
        GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(actual)
        return

    assert path.exists(), (
        f"Missing golden file {path.name}. "
        f"Create it with UPDATE_GOLDEN=1 and review the diff."
    )
    with path.open(encoding="utf-8", newline="") as handle:
        expected = handle.read()
    assert actual == expected


@pytest.mark.usefixtures("pinned_hebrew_dates", "frozen_clock")
class TestGoldenOutput:
    def test_all_event_types(self, make_calendar):
        calendar = make_calendar(
            events=[
                (NISAN, 15, BIRTHDAY, "Avraham"),
                (NISAN, 15, ANNIVERSARY, "Sarah and Yitzchak"),
                (NISAN, 15, YARTZEIT, "Rivka"),
            ],
        )
        ical = generate_ical(calendar, user_agent=APPLE_USER_AGENT)
        assert_matches_golden("all_event_types", ical)

    def test_google_user_agent_uses_utc(self, make_calendar):
        calendar = make_calendar(
            events=[(NISAN, 15, BIRTHDAY, "Avraham")],
        )
        ical = generate_ical(calendar, user_agent=GOOGLE_USER_AGENT)
        assert "X-WR-TIMEZONE:UTC" in ical
        assert_matches_golden("google_user_agent", ical)

    def test_non_google_keeps_calendar_timezone(self, make_calendar):
        calendar = make_calendar(
            timezone="Asia/Jerusalem",
            events=[(NISAN, 15, BIRTHDAY, "Avraham")],
        )
        ical = generate_ical(calendar, user_agent=APPLE_USER_AGENT)
        assert "X-WR-TIMEZONE:Asia/Jerusalem" in ical
        assert_matches_golden("jerusalem_timezone", ical)

    def test_adar_leap_months(self, make_calendar):
        calendar = make_calendar(
            events=[
                (ADAR_I, 10, YARTZEIT, "Adar One"),
                (ADAR_II, 10, YARTZEIT, "Adar Two"),
            ],
        )
        ical = generate_ical(calendar, user_agent=APPLE_USER_AGENT)
        assert_matches_golden("adar_leap_months", ical)

    def test_day_thirty_in_variable_length_months(self, make_calendar):
        """
        Cheshvan and Kislev are 29 days in some years, so day 30 takes
        the fallback branch in the date table.
        """
        calendar = make_calendar(
            events=[
                (CHESHVAN, 30, BIRTHDAY, "Cheshvan Thirty"),
                (KISLEV, 30, BIRTHDAY, "Kislev Thirty"),
            ],
        )
        ical = generate_ical(calendar, user_agent=APPLE_USER_AGENT)
        assert_matches_golden("day_thirty", ical)

    def test_custom_alarm_trigger(self, make_calendar):
        calendar = make_calendar(
            events=[(NISAN, 15, BIRTHDAY, "Avraham")],
        )
        ical = generate_ical(
            calendar,
            user_agent=APPLE_USER_AGENT,
            alarm_trigger=timedelta(hours=1),
        )
        assert "TRIGGER:PT1H" in ical
        assert_matches_golden("custom_alarm", ical)

    def test_unicode_names(self, make_calendar):
        calendar = make_calendar(
            name="לוח עברי",
            events=[
                (NISAN, 15, BIRTHDAY, "אברהם"),
                (NISAN, 16, YARTZEIT, "שרה"),
            ],
        )
        ical = generate_ical(calendar, user_agent=APPLE_USER_AGENT)
        assert_matches_golden("unicode_names", ical)

    def test_empty_calendar(self, make_calendar):
        calendar = make_calendar(events=[])
        ical = generate_ical(calendar, user_agent=APPLE_USER_AGENT)
        assert "BEGIN:VEVENT" not in ical
        assert_matches_golden("empty_calendar", ical)

    def test_experimental_rrule(self, make_calendar):
        calendar = make_calendar(
            events=[
                (NISAN, 15, BIRTHDAY, "Avraham"),
                (ADAR_I, 10, YARTZEIT, "Adar One"),
            ],
        )
        ical = generate_ical_experimental(calendar, user_agent=APPLE_USER_AGENT)
        assert "RSCALE=HEBREW" in ical.upper()
        assert_matches_golden("experimental_rrule", ical)
