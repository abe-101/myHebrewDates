# ruff: noqa: S324, ERA001
from base64 import urlsafe_b64encode
from datetime import datetime
from datetime import timedelta
from hashlib import sha1
from zoneinfo import ZoneInfo

from icalendar import Alarm
from icalendar import Calendar
from icalendar import Event

from my_hebrew_dates.core.utils import get_site_url
from my_hebrew_dates.hebcal.models import Calendar as ModelCalendar

# Constants
MERGECAL_URL = "https://mergecal.org"
MYHEBREWDATES_DOMAIN = "@myhebrewdates.com"


def generate_ical(  # noqa: PLR0915
    model_calendar: ModelCalendar,
    user_agent: str = "",
    alarm_trigger: timedelta = timedelta(hours=9),
    *,
    inject_migration_prompt: bool = False,
) -> str:
    # Google Calendar works better with UTC for all-day events
    is_google = "google" in user_agent.lower()
    timezone = "UTC" if is_google else model_calendar.timezone

    newcal = Calendar()
    newcal.add("prodid", "-//MyHebrewDates.com//Hebrew Calendar Events//EN")
    newcal.add("version", "2.0")
    newcal.add("calscale", "GREGORIAN")  # Required for Google Calendar
    newcal.add("method", "PUBLISH")

    # If migration prompt is being injected, indicate this needs attention
    if inject_migration_prompt:
        calendar_name = f"⚠️ Action Needed: {model_calendar.name}"
    else:
        calendar_name = model_calendar.name

    newcal.add("x-wr-calname", calendar_name)
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

    # Inject migration prompt event if calendar has been migrated
    if inject_migration_prompt:
        migration_event = Event()
        migration_event.add(
            "summary",
            "🔒 Security Update: Migrate Your Calendar",
        )
        site_url = get_site_url()
        subscribe_url = f"{site_url}/calendars/{model_calendar.uuid}/subscribe/"
        migration_event.add(
            "description",
            f"This calendar now requires sign-in for better security.\n\n"
            f"Click here to migrate: {subscribe_url}\n\n"
            f"Each person needs their own secure subscription URL. "
            f"Visit the link above to get yours.\n\n"
            f"This ensures only authorized users can access this calendar.",
        )

        # Set to today's date so it shows immediately
        today = datetime.now(tz=ZoneInfo("UTC")).date()
        migration_event.add("dtstart", today, parameters={"value": "DATE"})
        migration_event.add(
            "dtend",
            today + timedelta(days=1),
            parameters={"value": "DATE"},
        )
        migration_event.add(
            "uid",
            f"migration-{model_calendar.uuid}{MYHEBREWDATES_DOMAIN}",
        )
        migration_event.add("dtstamp", now_utc)
        migration_event.add("transp", "TRANSPARENT")
        migration_event.add("categories", ["System Notice", "Migration"])

        # Add alarm to get user's attention
        alarm = Alarm()
        alarm.add("action", "DISPLAY")
        alarm.add(
            "description",
            "Calendar Migration Required - Click event for details",
        )
        alarm.add("trigger", timedelta(hours=0))  # Immediate alert
        migration_event.add_component(alarm)

        # Add migration event at the beginning
        events.insert(0, migration_event)

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


# ============================================================================
# EMAIL FUNCTIONS
# ============================================================================


def send_migration_notification_email(calendar):
    """
    Send migration notification email to calendar owner.

    Args:
        calendar: Calendar instance to send notification for
    """
    import logging

    from django.core.mail import send_mail

    logger = logging.getLogger(__name__)

    # Get the subscribe URL
    site_url = get_site_url()
    subscribe_url = f"{site_url}/calendars/{calendar.uuid}/subscribe/"

    # Render email content
    subject = f"Action Required: Re-subscribe to your '{calendar.name}' calendar"

    # Plain text version
    message = f"""Hello,

Your Hebrew dates calendar "{calendar.name}" has been upgraded with enhanced \
security features.

WHAT'S CHANGING:
- Each person now gets their own secure subscription link
- You can customize alarm times without changing the URL
- Better tracking and access control

WHAT YOU NEED TO DO:
1. Click this link to get your personal subscription URL: {subscribe_url}
2. Re-add the calendar to your calendar app (Apple Calendar, Google Calendar, \
etc.)
3. Remove the old calendar subscription (it will show a migration notice)

WHY THIS MATTERS:
The old public link will continue to work temporarily but will show a \
migration prompt in your calendar. To get the best experience and avoid \
seeing the migration notice, please re-subscribe using your personal link.

Questions? Reply to this email or visit {site_url}

Thanks for using My Hebrew Dates!
"""

    # HTML version (optional, but recommended)
    html_message = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #4A90E2;">Calendar Update Required</h2>

    <p>Hello,</p>

    <p>Your Hebrew dates calendar <strong>"{calendar.name}"</strong> has been \
upgraded with enhanced security features.</p>

    <h3 style="color: #4A90E2;">What's Changing:</h3>
    <ul>
        <li>Each person now gets their own secure subscription link</li>
        <li>You can customize alarm times without changing the URL</li>
        <li>Better tracking and access control</li>
    </ul>

    <h3 style="color: #4A90E2;">What You Need to Do:</h3>
    <ol>
        <li>Click this link to get your personal subscription URL: \
<a href="{subscribe_url}" style="color: #4A90E2;">{subscribe_url}</a></li>
        <li>Re-add the calendar to your calendar app (Apple Calendar, \
Google Calendar, etc.)</li>
        <li>Remove the old calendar subscription (it will show a migration \
notice)</li>
    </ol>

    <div style="background-color: #FFF3CD; border-left: 4px solid #FFC107; \
padding: 12px; margin: 20px 0;">
        <strong>Why This Matters:</strong><br>
        The old public link will continue to work temporarily but will show a \
migration prompt in your calendar.
        To get the best experience and avoid seeing the migration notice, \
please re-subscribe using your personal link.
    </div>

    <p style="margin-top: 30px;">
        Questions? Reply to this email or visit \
<a href="{site_url}" style="color: #4A90E2;">{site_url}</a>
    </p>

    <p>Thanks for using My Hebrew Dates!</p>
</body>
</html>
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=None,  # Uses DEFAULT_FROM_EMAIL from settings
            recipient_list=[calendar.owner.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(
            "Migration notification email sent: calendar=%s, owner=%s",
            calendar.name,
            calendar.owner.email,
        )
    except Exception:
        logger.exception(
            "Failed to send migration email: calendar=%s, owner=%s",
            calendar.name,
            calendar.owner.email,
        )
