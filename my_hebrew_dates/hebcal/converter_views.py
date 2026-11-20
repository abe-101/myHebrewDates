from typing import TYPE_CHECKING
from typing import cast

from django.shortcuts import render
from django.utils import timezone

from my_hebrew_dates.hebcal.forms import ENGLISH_MONTH_NAMES
from my_hebrew_dates.hebcal.forms import HebrewDateLookupForm
from my_hebrew_dates.hebcal.hebrew_date import hebrew_date_from_english_input
from my_hebrew_dates.hebcal.hebrew_date import hebrew_to_english_dict
from my_hebrew_dates.hebcal.models import Calendar
from my_hebrew_dates.hebcal.models import HebrewDayEnum
from my_hebrew_dates.hebcal.models import HebrewMonthEnum

if TYPE_CHECKING:
    from collections.abc import Mapping
    from datetime import date

    from django.http import HttpRequest


def converter_view(request: HttpRequest):
    after_sunset = "after_sunset" in request.GET
    data: Mapping[str, object] | None = request.GET if "month" in request.GET else None
    from_english = hebrew_date_from_english_input(
        request.GET.get("english_date", ""),
        after_sunset=after_sunset,
    )
    if from_english:
        month, day = from_english
        data = {"day": day, "month": month}
    form = HebrewDateLookupForm(data)

    hebrew_date = ""
    english_label = ""
    upcoming = []
    if form.is_valid():
        day = form.cleaned_data["day"]
        month = form.cleaned_data["month"]
        hebrew_date = f"{HebrewDayEnum(day).label} {HebrewMonthEnum(month).label}"
        english_label = f"{day} {ENGLISH_MONTH_NAMES[month - 1]}"
        today = timezone.localdate()
        upcoming = [
            occurrence
            for occurrence in cast(
                "list[date]",
                hebrew_to_english_dict[f"{month}-{day}"],
            )
            if occurrence >= today
        ]

    calendars = Calendar.objects.none()
    if request.user.is_authenticated:
        calendars = Calendar.objects.filter(owner=request.user)

    context = {
        "form": form,
        "english_date": request.GET.get("english_date", ""),
        "after_sunset": after_sunset,
        "hebrew_date": hebrew_date,
        "english_label": english_label,
        "upcoming": upcoming,
        "calendars": calendars,
    }
    return render(request, "pages/converter.html", context)
