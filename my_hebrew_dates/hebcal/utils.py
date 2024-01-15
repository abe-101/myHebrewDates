from base64 import urlsafe_b64encode
from datetime import date, datetime, timedelta
from hashlib import sha1

from icalendar import Alarm, Calendar, Event, Timezone

from .models import Calendar as ModelCalendar
from .models import HebrewDate


def generate_ical(
    modelCalendar: ModelCalendar, user_agent: str = "", alarm_trigger: timedelta = timedelta(hours=9)
) -> str:
    newcal = Calendar()
    newcal.add("prodid", "-//" + modelCalendar.name + "//MyHebrewDates.com//")
    newcal.add("version", "2.0")
    newcal.add("x-wr-calname", modelCalendar.name)
    newcal.add("x-wr-timezone", modelCalendar.timezone)  # It is good to add this as well.
    newcal.add("x-wr-caldesc", "Created by MyHebrewDates.com")

    newcal.add("method", "PUBLISH")

    newtimezone = Timezone()
    newtimezone.add("tzid", modelCalendar.timezone)
    newcal.add_component(newtimezone)

    events = []

    for hebrewDate in modelCalendar.calendarOf.all():
        hebrewDate: HebrewDate = hebrewDate
        for engDate in hebrewDate.get_english_dates():
            engDate: date = engDate

            eventHash = sha1(
                (hebrewDate.event_type + hebrewDate.name + hebrewDate.get_hebrew_date()).encode("utf-8")
            ).digest()
            uid = engDate.isoformat() + urlsafe_b64encode(eventHash).decode("ascii") + "@myhebrewdates.com"
            event = Event()
            title = f"{hebrewDate.get_hebrew_date()} | {hebrewDate.event_type} {hebrewDate.name}"
            event.add("summary", title)
            base_description = title + "\n\nhttps://myhebrewdates.com"
            # if "Google-Calendar-Importer" in user_agent:
            # if not (user_agent == "" or "iOS" in user_agent or "macOS" in user_agent):
            #     base_description += (
            #         "\n"
            #         f"<img src='https://myhebrewdates.com/calendars/serve-ima
            # ge/{modelCalendar.uuid}/{hebrewDate.pk}' "
            #         "width='1' height='1'>"
            #     )
            event.add("description", base_description)
            html_description = (
                f"{title}<br>"
                f"Delivered to you by: <a href='https://myhebrewdates.com'>"  # noqa E231
                "MyHebrewDates.com</a><br>"
                f"<img src='https://myhebrewdates.com/calendars/serve-image/{modelCalendar.uuid}/{hebrewDate.pk}' "  # noqa E231
                "width='1' height='1'>"
            )

            event.add("x-alt-desc;fmttype=text/html", html_description)

            event.add("dtstamp", datetime.utcnow())  # Set DTSTAMP to the current UTC time
            event.add("dtstart", engDate)
            event.add("dtend", engDate + timedelta(days=1))
            event.add("uid", uid)
            event.add("categories", str(hebrewDate.get_event_type_display()))
            event.add("transp", "TRANSPARENT")
            event.add("x-microsoft-cdo-alldayevent", "TRUE")
            event.add("x-microsoft-cdo-busystatus", "FREE")

            # Add alarm to the event
            alarm = Alarm()
            alarm.add("action", "DISPLAY")
            alarm.add("description", hebrewDate.name + "'s " + hebrewDate.get_event_type_display() + " is today!")

            alarm.add("trigger", alarm_trigger)
            event.add_component(alarm)

            events.append(event)

    sorted_events = sorted(events, key=lambda e: e["dtstart"].dt)

    for event in sorted_events:
        newcal.add_component(event)

    cal_bye_str = newcal.to_ical()
    modelCalendar.calendar_file_str = cal_bye_str.decode("utf8")
    modelCalendar.save()
    return cal_bye_str.decode("utf8")
