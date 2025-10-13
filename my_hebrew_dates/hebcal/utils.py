# ruff: noqa: S324
from base64 import urlsafe_b64encode
from datetime import datetime
from datetime import timedelta
from hashlib import sha1
from zoneinfo import ZoneInfo

from icalendar import Alarm
from icalendar import Calendar
from icalendar import Event

from my_hebrew_dates.hebcal.models import Calendar as ModelCalendar

# Constants
MYHEBREWDATES_URL = "https://myhebrewdates.com"
MERGECAL_URL = "https://mergecal.org"
MYHEBREWDATES_DOMAIN = "@myhebrewdates.com"


def generate_ical(
    model_calendar: ModelCalendar,
    user_agent: str = "",
    alarm_trigger: timedelta = timedelta(hours=9),
) -> str:
    # Google Calendar works better with UTC for all-day events
    is_google = "google" in user_agent.lower()
    timezone = "UTC" if is_google else model_calendar.timezone

    newcal = Calendar()
    newcal.add("prodid", "-//MyHebrewDates.com//Hebrew Calendar Events//EN")
    newcal.add("version", "2.0")
    newcal.add("calscale", "GREGORIAN")  # Required for Google Calendar
    newcal.add("method", "PUBLISH")
    newcal.add("x-wr-calname", model_calendar.name)
    newcal.add("x-wr-timezone", timezone)
    newcal.add("x-wr-caldesc", "Hebrew calendar events created by MyHebrewDates.com")

    # Note: VTIMEZONE component not needed for all-day events
    # All-day events (VALUE=DATE) don't require timezone conversion

    events = []
    now_utc = datetime.now(tz=ZoneInfo("UTC"))

    for hebrew_date in model_calendar.calendarOf.all():
        for eng_date in hebrew_date.get_english_dates():
            event_hash = sha1(
                (
                    hebrew_date.event_type
                    + hebrew_date.name
                    + hebrew_date.get_hebrew_date()
                ).encode("utf-8"),
            ).digest()
            uid = (
                eng_date.isoformat()
                + urlsafe_b64encode(event_hash).decode("ascii")
                + MYHEBREWDATES_DOMAIN
            )
            event = Event()
            title = (
                f"{hebrew_date.get_hebrew_date()} | "
                f"{hebrew_date.event_type} {hebrew_date.name}"
            )
            event.add("summary", title)

            base_description = (
                f"{title}\n\nStop switching calendars. Merge them → {MERGECAL_URL}"
            )
            event.add("description", base_description)

            # Critical for Google Calendar: DTSTAMP, LAST-MODIFIED, and SEQUENCE
            event.add("dtstamp", now_utc)
            event.add("last-modified", hebrew_date.modified)
            event.add("sequence", 0)

            # Use VALUE=DATE to mark as all-day event (no time component)
            event.add("dtstart", eng_date, parameters={"value": "DATE"})
            # For all-day events, DTEND should be the next day (RFC 5545)
            event.add(
                "dtend",
                eng_date + timedelta(days=1),
                parameters={"value": "DATE"},
            )
            event.add("uid", uid)
            event.add("transp", "TRANSPARENT")
            event.add(
                "categories",
                ["Hebrew Date", str(hebrew_date.get_event_type_display())],
            )

            # Microsoft compatibility
            event.add("x-microsoft-cdo-alldayevent", "TRUE")
            event.add("x-microsoft-cdo-busystatus", "FREE")

            # Add alarm to the event
            alarm = Alarm()
            alarm.add("action", "DISPLAY")
            alarm_desc = (
                f"{hebrew_date.name}'s {hebrew_date.get_event_type_display()} is today!"
            )
            alarm.add("description", alarm_desc)

            alarm.add("trigger", alarm_trigger)
            event.add_component(alarm)

            events.append(event)

    sorted_events = sorted(events, key=lambda e: e["dtstart"].dt)

    for event in sorted_events:
        newcal.add_component(event)

    ical_str = newcal.to_ical()
    return ical_str.decode("utf8")


def generate_ical_experimental(
    model_calendar: ModelCalendar,
    user_agent: str = "",
    alarm_trigger: timedelta = timedelta(hours=9),
) -> str:
    # Google Calendar works better with UTC for all-day events
    is_google = "google" in user_agent.lower()
    timezone = "UTC" if is_google else model_calendar.timezone

    newcal = Calendar()
    newcal.add("prodid", "-//MyHebrewDates.com//Hebrew Calendar Events//EN")
    newcal.add("version", "2.0")
    newcal.add("calscale", "GREGORIAN")  # Required for Google Calendar
    newcal.add("method", "PUBLISH")
    newcal.add("x-wr-calname", model_calendar.name)
    newcal.add("x-wr-timezone", timezone)
    newcal.add("x-wr-caldesc", "Hebrew calendar events created by MyHebrewDates.com")

    # Note: VTIMEZONE component not needed for all-day events
    # All-day events (VALUE=DATE) don't require timezone conversion

    events = []
    now_utc = datetime.now(tz=ZoneInfo("UTC"))

    for hebrew_date in model_calendar.calendarOf.all():
        event_hash = sha1(
            (
                hebrew_date.event_type
                + hebrew_date.name
                + hebrew_date.get_hebrew_date()
            ).encode("utf-8"),
        ).digest()
        eng_date = hebrew_date.get_english_dates()[0]
        uid = (
            eng_date.isoformat()
            + urlsafe_b64encode(event_hash).decode("ascii")
            + MYHEBREWDATES_DOMAIN
        )
        event = Event()
        title = (
            f"{hebrew_date.get_hebrew_date()} | "
            f"{hebrew_date.event_type} {hebrew_date.name}"
        )
        event.add("summary", title)
        base_description = (
            f"{title}\n\nStop switching calendars. Merge them → {MERGECAL_URL}"
        )
        event.add("description", base_description)

        # Critical for Google Calendar: DTSTAMP, LAST-MODIFIED, and SEQUENCE
        event.add("dtstamp", now_utc)
        event.add("last-modified", hebrew_date.modified)
        event.add("sequence", 0)

        # Use VALUE=DATE to mark as all-day event (no time component)
        event.add("dtstart", eng_date, parameters={"value": "DATE"})
        # For all-day events, DTEND should be the next day (RFC 5545)
        event.add(
            "dtend",
            eng_date + timedelta(days=1),
            parameters={"value": "DATE"},
        )
        event.add("transp", "TRANSPARENT")
        event.add("uid", uid)
        event.add(
            "categories",
            ["Hebrew Date", str(hebrew_date.get_event_type_display())],
        )

        # Add alarm to the event
        alarm = Alarm()
        alarm.add("action", "DISPLAY")
        alarm_desc = (
            f"{hebrew_date.name}'s {hebrew_date.get_event_type_display()} is today!"
        )
        alarm.add("description", alarm_desc)

        alarm.add("trigger", alarm_trigger)
        event.add_component(alarm)
        event.add(
            "rrule",
            {
                "rscale": "hebrew",
                "freq": "yearly",
                "bymonth": hebrew_date.get_rfc7529_month(),
                "bymonthday": hebrew_date.day,
            },
        )

        events.append(event)

    sorted_events = sorted(events, key=lambda e: e["dtstart"].dt)

    for event in sorted_events:
        newcal.add_component(event)

    ical_str = newcal.to_ical()
    return ical_str.decode("utf8")
