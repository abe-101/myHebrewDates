from django.urls import reverse

from my_hebrew_dates.hebcal.models import Calendar
from my_hebrew_dates.hebcal.models import HebrewDate
from my_hebrew_dates.hebcal.models import HebrewMonthEnum


def make_calendar(client, user):
    client.force_login(user)
    return Calendar.objects.create(name="Family", owner=user)


def test_english_date_fills_in_the_hebrew_date(client, user):
    calendar = make_calendar(client, user)

    response = client.get(
        reverse("hebcal:hebrew_date_new", args=[calendar.uuid]),
        {"english_date": "2027-01-22", "after_sunset": "on", "name": "Moshe"},
    )

    form = response.context["form"]
    assert form.initial["month"] == HebrewMonthEnum.SHEVAT
    assert form.initial["day"] == 15  # noqa: PLR2004
    assert form.initial["name"] == "Moshe"


def test_save_and_add_another_returns_to_an_empty_form(client, user):
    calendar = make_calendar(client, user)

    response = client.post(
        reverse("hebcal:hebrew_date_new", args=[calendar.uuid]),
        {
            "name": "Moshe",
            "event_type": "🎂",
            "day": 15,
            "month": 11,
            "add_another": "",
        },
    )

    assert response.url == reverse("hebcal:hebrew_date_new", args=[calendar.uuid])
    assert calendar.calendarOf.count() == 1


def test_edit_keeps_existing_values(client, user):
    calendar = make_calendar(client, user)
    hebrew_date = HebrewDate.objects.create(
        calendar=calendar,
        name="Rivka",
        event_type="🕯️",
        day=23,
        month=2,
    )

    response = client.get(
        reverse("hebcal:hebrew_date_edit", args=[calendar.uuid, hebrew_date.pk]),
    )

    assert response.context["form"]["name"].value() == "Rivka"


def test_dates_are_listed_by_next_occurrence(client, user, pinned_hebrew_dates):
    calendar = make_calendar(client, user)
    HebrewDate.objects.create(
        calendar=calendar,
        name="Later",
        event_type="🎂",
        day=23,
        month=2,
    )
    HebrewDate.objects.create(
        calendar=calendar,
        name="Sooner",
        event_type="🎂",
        day=15,
        month=11,
    )

    response = client.get(reverse("hebcal:calendar_edit", args=[calendar.uuid]))

    names = [hebrew_date.name for _, hebrew_date in response.context["hebrew_dates"]]
    assert names == ["Sooner", "Later"]


def test_a_day_the_month_never_has_is_an_error_not_a_crash(client, user):
    calendar = make_calendar(client, user)

    response = client.post(
        reverse("hebcal:hebrew_date_new", args=[calendar.uuid]),
        {"name": "Moshe", "event_type": "🎂", "day": 30, "month": HebrewMonthEnum.IYAR},
    )

    assert response.status_code == 200  # noqa: PLR2004
    assert "There is no day 30 in" in response.content.decode()
    assert not calendar.calendarOf.exists()
