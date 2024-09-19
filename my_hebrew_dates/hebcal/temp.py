# ruff: noqa: S324, ERA001
import logging
from base64 import urlsafe_b64encode
from datetime import datetime
from datetime import timedelta
from hashlib import sha1
from zoneinfo import ZoneInfo

from icalendar import Alarm
from icalendar import Calendar
from icalendar import Event
from icalendar import Timezone

from my_hebrew_dates.hebcal.models import Calendar as ModelCalendar

logger = logging.getLogger(__name__)


def generate_ical(
    model_calendar: ModelCalendar,
    user_agent: str = "",
    alarm_trigger: timedelta = timedelta(hours=9),
) -> str:
    newcal = Calendar()
    newcal.add("prodid", "-//" + model_calendar.name + "//MyHebrewDates.com//")
    newcal.add("version", "2.0")
    newcal.add("x-wr-calname", model_calendar.name)
    newcal.add(
        "x-wr-timezone",
        model_calendar.timezone,
    )  # It is good to add this as well.
    newcal.add("x-wr-caldesc", "Created by MyHebrewDates.com")

    newcal.add("method", "PUBLISH")

    newtimezone = Timezone()
    newtimezone.add("tzid", model_calendar.timezone)
    newcal.add_component(newtimezone)

    events = []

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
            + "@myhebrewdates.com"
        )
        event = Event()
        title = (
            f"{hebrew_date.get_hebrew_date()} | "
            f"{hebrew_date.event_type} {hebrew_date.name}"
        )
        event.add("summary", title)
        base_description = (
            title
            + "\n\nHebrew date automation triggers: https://myhebrewdates.com/automation"
        )
        event.add("description", base_description)

        html_description = f"""
        <html>
        <body>
            {title}<br>
            Delivered to you by: <a href='https://myhebrewdates.com'>MyHebrewDates.com</a><br>
            <img src='https://myhebrewdates.com/calendars/serve-image
            /{model_calendar.uuid}/{hebrew_date.pk}' width='1' height='1'>
        </body>
        </html>
        """
        event.add("x-alt-desc;fmttype=text/html", html_description)

        event.add(
            "dtstamp",
            datetime.now(tz=ZoneInfo(model_calendar.timezone)),
        )  # Set DTSTAMP to the current UTC time
        event.add("dtstart", eng_date)
        event.add("transp", "TRANSPARENT")
        event.add("uid", uid)
        event.add(
            "categories",
            ["Hebrew Date", str(hebrew_date.get_event_type_display())],
        )
        event.add("transp", "TRANSPARENT")
        event.add("x-microsoft-cdo-alldayevent", "TRUE")
        event.add("x-microsoft-cdo-busystatus", "FREE")

        event.add(
            "attach",
            [
                {
                    "fmttype": "image/png",
                    "value": f"https://myhebrewdates.com/calendars/serve-image/{model_calendar.uuid}/{hebrew_date.pk}",
                },
            ],
        )

        # Add alarm to the event
        alarm = Alarm()
        alarm.add("action", "DISPLAY")
        alarm.add(
            "description",
            hebrew_date.name
            + "'s "
            + hebrew_date.get_event_type_display()
            + " is today!",
        )

        alarm.add("trigger", alarm_trigger)
        event.add_component(alarm)
        next_year = hebrew_date.get_english_dates()[1]
        two_year = hebrew_date.get_english_dates()[2]

        event.add("rdate", [next_year, two_year])

        events.append(event)

    sorted_events = sorted(events, key=lambda e: e["dtstart"].dt)

    for event in sorted_events:
        newcal.add_component(event)

    cal_bye_str = newcal.to_ical()
    return cal_bye_str.decode("utf8")
