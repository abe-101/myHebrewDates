from base64 import urlsafe_b64encode
from datetime import date, datetime, timedelta
from hashlib import sha1

from icalendar import Alarm, Calendar, Event

from .models import Calendar as ModelCalendar
from .models import HebrewDate


def generate_ical(modelCalendar: ModelCalendar):
    newcal = Calendar()
    newcal.add("prodid", "-//" + modelCalendar.name + "//MyHebrewDates.com//")
    newcal.add("version", "2.0")
    newcal.add("x-wr-calname", modelCalendar.name)

    # newtimezone = Timezone()
    # newtimezone.add("tzid", modelCalendar.timezone)
    # newcal.add_component(newtimezone)

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
            event.add("summary", hebrewDate.event_type + " " + hebrewDate.name)
            event.add(
                "description",
                hebrewDate.get_hebrew_date() + "\n Create your own calendar at: https://myhebrewdates.com",
            )

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

            alarm.add("trigger", timedelta(hours=9))
            event.add_component(alarm)

            events.append(event)

    sorted_events = sorted(events, key=lambda e: e["dtstart"].dt)

    for event in sorted_events:
        newcal.add_component(event)

    cal_bye_str = newcal.to_ical()
    modelCalendar.calendar_file_str = cal_bye_str.decode("utf8")
    modelCalendar.save()
