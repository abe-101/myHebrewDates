from django import forms

from .models import Calendar, HebrewDate


class CalendarForm(forms.ModelForm):
    class Meta:
        model = Calendar
        fields = ["name", "timezone"]
        labels = {
            "name": "Name",
            "timezone": "Timezone",
        }
        widgets = {
            "timezone": forms.Select(choices=Calendar.TIMEZONE_CHOICES),
        }


class HebrewDateForm(forms.ModelForm):
    class Meta:
        model = HebrewDate
        fields = ["name", "month", "day", "event_type"]
        widgets = {
            "month": forms.Select(choices=HebrewDate.MONTH_CHOICES),
            "day": forms.Select(choices=HebrewDate.DAY_CHOICES),
            "event_type": forms.Select(choices=HebrewDate.EVENT_CHOICES),
        }
