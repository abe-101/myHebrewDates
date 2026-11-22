# ruff: noqa: S324
from base64 import urlsafe_b64encode
from datetime import datetime
from datetime import timedelta
from hashlib import sha1
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from icalendar import Alarm
from icalendar import Calendar
from icalendar import Event
from icalendar import vDuration

if TYPE_CHECKING:
    from my_hebrew_dates.hebcal.models import Calendar as ModelCalendar

# Constants
MYHEBREWDATES_URL = "https://myhebrewdates.com"
CHARJ_URL = "https://charj.cc"
MYHEBREWDATES_DOMAIN = "@myhebrewdates.com"
# The feed view caches for an hour, so asking clients to come back sooner is pointless
FEED_REFRESH_INTERVAL = timedelta(hours=6)


def new_feed_calendar(model_calendar: ModelCalendar) -> Calendar:
    newcal = Calendar.new(
        prodid="-//MyHebrewDates.com//Hebrew Calendar Events//EN",
        calscale="GREGORIAN",  # Required for Google Calendar
        method="PUBLISH",
        name=model_calendar.name,
        description="Hebrew calendar events created by MyHebrewDates.com",
        color="royalblue",
    )
    # Calendar.new() always adds a random UID, which would change on every fetch
    del newcal["UID"]
    # Calendar.new(refresh_interval=...) omits the VALUE=DURATION that RFC 7986 requires
    newcal.add(
        "refresh-interval",
        FEED_REFRESH_INTERVAL,
        parameters={"value": "DURATION"},
    )
    # Outlook and Apple Calendar read the older X-PUBLISHED-TTL, not REFRESH-INTERVAL
    newcal.add("x-published-ttl", vDuration(FEED_REFRESH_INTERVAL))
    # No VTIMEZONE needed: all-day events (VALUE=DATE) have no time component
    newcal.add("x-wr-timezone", model_calendar.timezone)
    return newcal


def generate_ical(
    model_calendar: ModelCalendar,
    alarm_trigger: timedelta = timedelta(hours=9),
) -> str:
    newcal = new_feed_calendar(model_calendar)

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
                f"{title}\n\n"
                f"Keep your credit cards active. Prevent closures → {CHARJ_URL}"
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

            alarm_desc = (
                f"{hebrew_date.name}'s {hebrew_date.get_event_type_display()} is today!"
            )
            alarm = Alarm.new_display(
                description=alarm_desc,
                trigger=alarm_trigger,
            )
            event.add_component(alarm)

            events.append(event)

    sorted_events = sorted(events, key=lambda e: e.start)

    for event in sorted_events:
        newcal.add_component(event)

    ical_str = newcal.to_ical()
    return ical_str.decode("utf8")


def generate_ical_experimental(
    model_calendar: ModelCalendar,
    alarm_trigger: timedelta = timedelta(hours=9),
) -> str:
    newcal = new_feed_calendar(model_calendar)

    events = []
    now_utc = datetime.now(tz=ZoneInfo("UTC"))

    for hebrew_date in model_calendar.calendarOf.all():
        event_hash = sha1(
            (
                hebrew_date.event_type
                + hebrew_date.name
                + hebrew_date.get_hebrew_date()
                + "rrule"
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
            f"{title}\n\nKeep your credit cards active. Prevent closures → {CHARJ_URL}"
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

        # Microsoft compatibility
        event.add("x-microsoft-cdo-alldayevent", "TRUE")
        event.add("x-microsoft-cdo-busystatus", "FREE")

        alarm_desc = (
            f"{hebrew_date.name}'s {hebrew_date.get_event_type_display()} is today!"
        )
        alarm = Alarm.new_display(
            description=alarm_desc,
            trigger=alarm_trigger,
        )
        event.add_component(alarm)
        rrule = {
            "rscale": "hebrew",
            "freq": "yearly",
            "bymonth": hebrew_date.get_rfc7529_month(),
            "bymonthday": hebrew_date.day,
        }
        skip = hebrew_date.get_rfc7529_skip()
        if skip:
            rrule["skip"] = skip
        event.add("rrule", rrule)

        events.append(event)

    sorted_events = sorted(events, key=lambda e: e.start)

    for event in sorted_events:
        newcal.add_component(event)

    ical_str = newcal.to_ical()
    return ical_str.decode("utf8")
