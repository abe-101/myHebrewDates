# ruff: noqa: RUF001, DJ001
import uuid
import zoneinfo

from django.conf import settings
from django.db import models
from django.urls import reverse

from .hebrew_date import hebrew_to_english_dict


class HebrewMonthEnum(models.IntegerChoices):
    NISAN = 1, "ניסן"
    IYAR = 2, "אייר"
    SIVAN = 3, "סיון"
    TAMMUZ = 4, "תמוז"
    AV = 5, "אב"
    ELUL = 6, "אלול"
    TISHREI = 7, "תשרי"
    CHESHVAN = 8, "חשון"
    KISLEV = 9, "כסלו"
    TEVET = 10, "טבת"
    SHEVAT = 11, "שבט"
    ADAR_A = 12, "אדר א׳"
    ADAR_B = 13, "אדר ב׳"


class HebrewDayEnum(models.IntegerChoices):
    ALEPH = 1, "א"
    BET = 2, "ב"
    GIMEL = 3, "ג"
    DALET = 4, "ד"
    HE = 5, "ה"
    VAV = 6, "ו"
    ZAYIN = 7, "ז"
    CHET = 8, "ח"
    TET = 9, "ט"
    YUD = 10, "י"
    YUD_ALEPH = 11, "יא"
    YUD_BET = 12, "יב"
    YUD_GIMEL = 13, "יג"
    YUD_DALET = 14, "יד"
    TET_VAV = 15, "טו"
    TET_ZAYIN = 16, "טז"
    YUD_ZAYIN = 17, "יז"
    YUD_CHET = 18, "יח"
    YUD_TET = 19, "יט"
    KAF = 20, "כ"
    KAF_ALEPH = 21, "כא"
    KAF_BET = 22, "כב"
    KAF_GIMEL = 23, "כג"
    KAF_DALET = 24, "כד"
    KAF_HE = 25, "כה"
    KAF_VAV = 26, "כו"
    KAF_ZAYIN = 27, "כז"
    KAF_CHET = 28, "כח"
    KAF_TET = 29, "כט"
    LAMED = 30, "ל"


class Calendar(models.Model):
    name = models.CharField(max_length=255)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    # https://stackoverflow.com/a/70251235
    TIMEZONE_CHOICES = (
        (x, x) for x in sorted(zoneinfo.available_timezones(), key=str.lower)
    )
    timezone = models.CharField(
        "Timezone",
        choices=TIMEZONE_CHOICES,
        max_length=250,
        default="America/New_York",
        help_text="Select the timezone that matches your local time. This ensures your events show up at the correct times.",  # noqa: E501
    )
    calendar_file_str = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("hebcal:calendar_edit", kwargs={"uuid": self.uuid})


class HebrewDate(models.Model):
    name = models.CharField(
        max_length=64,
        help_text="Enter the name of the person associated with this event.",
    )
    month = models.IntegerField(
        choices=HebrewMonthEnum.choices,
        help_text="Select the month of the event according to the Hebrew calendar.",
    )
    day = models.IntegerField(
        choices=HebrewDayEnum.choices,
        help_text="Select the day of the event according to the Hebrew calendar.",
    )

    EVENT_CHOICES = [
        ("🎂", "Birthday"),
        ("💍", "Anniversary"),
        ("🕯️", "Yartzeit"),
    ]
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_CHOICES,
        help_text="Choose the type of event, such as a Birthday, Anniversary, "
        "or Yartzeit.",
    )

    calendar = models.ForeignKey(
        "hebcal.Calendar",
        on_delete=models.CASCADE,
        related_name="calendarOf",
        help_text="Select the calendar to which this event belongs.",
    )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("hebcal:calendar_edit", kwargs={"uuid": self.calendar.uuid})

    def get_hebrew_date(self):
        hebrew_month = self.get_month_display()
        hebrew_day = self.get_day_display()
        return f"{hebrew_day} {hebrew_month}"

    def get_english_dates(self):
        hebrew_str = f"{self.month}-{self.day}"
        return hebrew_to_english_dict.get(hebrew_str)

    def get_formatted_name(self):
        capitalized_date = (
            " ".join(word.capitalize() for word in self.name.split()) + "'s"
        )
        event_type = dict(self.EVENT_CHOICES).get(self.event_type)
        return capitalized_date + " " + event_type.capitalize()
