import uuid
import zoneinfo

from django.conf import settings
from django.db import models
from django.urls import reverse

from .hebrew_date import hebrew_to_english_dict

hebrew_month_name = {
    1: "ניסן",
    2: "אייר",
    3: "סיון",
    4: "תמוז",
    5: "אב",
    6: "אלול",
    7: "תשרי",
    8: "חשון",
    9: "כסלו",
    10: "טבת",
    11: "שבט",
    12: "אדר א׳",
    13: "אדר ב׳",
}

hebrew_day_name = {
    1: "א",
    2: "ב",
    3: "ג",
    4: "ד",
    5: "ה",
    6: "ו",
    7: "ז",
    8: "ח",
    9: "ט",
    10: "י",
    11: "יא",
    12: "יב",
    13: "יג",
    14: "יד",
    15: "טו",
    16: "טז",
    17: "יז",
    18: "יח",
    19: "יט",
    20: "כ",
    21: "כא",
    22: "כב",
    23: "כג",
    24: "כד",
    25: "כה",
    26: "כו",
    27: "כז",
    28: "כח",
    29: "כט",
    30: "ל",
}


class Calendar(models.Model):
    name = models.CharField(max_length=255)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    # https://stackoverflow.com/a/70251235
    TIMEZONE_CHOICES = ((x, x) for x in sorted(zoneinfo.available_timezones(), key=str.lower))
    timezone = models.CharField("Timezone", choices=TIMEZONE_CHOICES, max_length=250, default="America/New_York")
    calendar_file_str = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("hebcal:calendar_edit", kwargs={"uuid": self.uuid})


class HebrewDate(models.Model):
    name = models.CharField(max_length=64)

    MONTH_CHOICES = [
        (1, "Nissan"),
        (2, "Iyar"),
        (3, "Sivan"),
        (4, "Tammuz"),
        (5, "Av"),
        (6, "Elul"),
        (7, "Tishrei"),
        (8, "Cheshvan"),
        (9, "Kislev"),
        (10, "Tevet"),
        (11, "Shevat"),
        (12, "Adar I"),
        (13, "Adar II"),
    ]
    month = models.PositiveSmallIntegerField(choices=MONTH_CHOICES)
    DAY_CHOICES = [(i, i) for i in range(1, 31)]
    day = models.PositiveSmallIntegerField(choices=DAY_CHOICES)
    EVENT_CHOICES = [
        ("🎂", "Birthday"),
        ("💍", "Anniversary"),
        ("🕯️", "Yartzeit"),
    ]
    event_type = models.CharField(max_length=20, choices=EVENT_CHOICES)

    calendar = models.ForeignKey("hebcal.Calendar", on_delete=models.CASCADE, related_name="calendarOf")

    def get_hebrew_date(self):
        return f"{hebrew_day_name.get(self.day)} {hebrew_month_name.get(self.month)}"

    def get_english_dates(self):
        hebrew_str = f"{self.month}-{self.day}"
        return hebrew_to_english_dict.get(hebrew_str)

    def get_formatted_name(self):
        capitalized_date = " ".join(word.capitalize() for word in self.name.split()) + "'s"
        event_type = dict(self.EVENT_CHOICES).get(self.event_type)
        formatted_event_name = capitalized_date + " " + event_type.capitalize()
        return formatted_event_name

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("hebcal:calendar_edit", kwargs={"uuid": self.calendar.uuid})
