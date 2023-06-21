from django import forms

from .models import Calendar, HebrewDate


class CalendarForm(forms.ModelForm):
    class Meta:
        model = Calendar
        fields = ["name"]
        labels = {
            "name": "Name",
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


HebrewDateFormSet = forms.inlineformset_factory(Calendar, HebrewDate, form=HebrewDateForm, extra=3)
