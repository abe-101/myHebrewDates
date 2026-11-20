from typing import cast

from crispy_forms.helper import FormHelper
from django import forms
from pyluach.utils import MONTH_NAMES

from .models import Calendar
from .models import HebrewDate
from .models import HebrewDayEnum
from .models import HebrewMonthEnum

# pyluach also names plain Adar, which is not one of this app's months.
ENGLISH_MONTH_NAMES = [*MONTH_NAMES[:11], *MONTH_NAMES[12:]]


class CalendarForm(forms.ModelForm):
    class Meta:
        model = Calendar
        fields = ["name", "timezone"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class HebrewDateForm(forms.ModelForm):
    class Meta:
        model = HebrewDate
        fields = ["name", "event_type", "day", "month"]
        labels = {"event_type": "What is it?"}
        help_texts = {
            "name": "As it should appear in the calendar, like “Savta Rivka”.",
            "event_type": "",
            "day": "",
            "month": "Adar I and Adar II are the same month in years with one Adar.",
        }
        widgets = {"event_type": forms.RadioSelect}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cast("forms.ChoiceField", self.fields["event_type"]).choices = [
            ("🎂", "🎂 Birthday"),
            ("💍", "💍 Anniversary"),
            ("🕯️", "🕯️ Yahrzeit"),
        ]
        cast("forms.ChoiceField", self.fields["day"]).choices = [
            ("", "Day"),
            *[(day, f"{day} ({label})") for day, label in HebrewDayEnum.choices],
        ]
        cast("forms.ChoiceField", self.fields["month"]).choices = [
            ("", "Month"),
            *[
                (month, f"{ENGLISH_MONTH_NAMES[month - 1]} ({label})")
                for month, label in HebrewMonthEnum.choices
            ],
        ]
