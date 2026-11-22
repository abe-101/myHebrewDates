import re

import pytest
from django.urls import reverse

from my_hebrew_dates.hebcal.models import Calendar
from my_hebrew_dates.hebcal.models import HebrewDate
from my_hebrew_dates.hebcal.models import HebrewMonthEnum

PASSWORD = "analytics-Pa55word!"  # noqa: S105


@pytest.fixture
def captured(monkeypatch):
    events = []
    monkeypatch.setattr(
        "posthog.capture",
        lambda event, **kwargs: events.append((event, kwargs)),
    )
    return events


@pytest.mark.django_db
def test_journey_is_captured_under_the_user_id(client, mailoutbox, captured):
    client.post(
        reverse("account_signup"),
        {
            "email": "analytics@example.com",
            "username": "analytics",
            "password1": PASSWORD,
            "password2": PASSWORD,
        },
    )
    confirm_url = re.search(r"(/accounts/confirm-email/\S+/)", mailoutbox[0].body)
    assert confirm_url
    client.post(confirm_url.group(1))
    client.post(reverse("account_login"), {"login": "analytics", "password": PASSWORD})
    client.post(
        reverse("hebcal:calendar_new"),
        {"name": "Family", "timezone": "America/New_York"},
    )
    calendar = Calendar.objects.get(owner__username="analytics")
    client.post(
        reverse("hebcal:hebrew_date_new", args=[calendar.uuid]),
        {
            "name": "Moshe",
            "month": HebrewMonthEnum.SHEVAT,
            "day": 15,
            "event_type": "🎂",
        },
    )
    client.logout()
    client.get(
        reverse("hebcal:calendar_file", args=[calendar.uuid]),
        headers={"user-agent": "Google-Calendar-Importer"},
    )

    assert [event for event, _ in captured] == [
        "user_signed_up",
        "user_logged_in",
        "calendar_created",
        "hebrew_date_added",
        "feed_fetched",
    ]
    assert {kwargs["distinct_id"] for _, kwargs in captured} == {
        str(calendar.owner_id),
    }
    assert captured[0][1]["properties"] == {"method": "email"}
    assert captured[3][1]["properties"]["event_type"] == "Birthday"
    assert captured[4][1]["properties"]["client"] == "google"
    assert captured[4][1]["properties"]["date_count"] == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("user_agent", "expected"),
    [
        ("iOS/18.1 (22B83) dataaccessd/1.0", "apple"),
        ("macOS/15.1 (24B83) dataaccessd/1.0", "apple"),
        ("Microsoft Exchange (Windows NT 10.0; Win64; x64)", "outlook"),
        ("Mozilla/5.0 (X11; Linux x86_64) Firefox/130.0", "browser"),
        ("", "other"),
    ],
)
def test_feed_fetch_names_the_calendar_app(
    client, user, captured, user_agent, expected
):
    calendar = Calendar.objects.create(name="Family", owner=user)
    client.get(
        reverse("hebcal:calendar_file", args=[calendar.uuid]),
        headers={"user-agent": user_agent},
    )
    assert captured[-1][1]["properties"]["client"] == expected


@pytest.mark.django_db
def test_deleting_a_date_is_captured(client, user, captured):
    calendar = Calendar.objects.create(name="Family", owner=user)
    hebrew_date = HebrewDate.objects.create(
        calendar=calendar,
        name="Moshe",
        month=HebrewMonthEnum.SHEVAT,
        day=15,
        event_type="🕯️",
    )
    client.force_login(user)
    client.post(
        reverse("hebcal:delete_hebrew_date_htmx", args=[calendar.uuid, hebrew_date.pk]),
        headers={"hx-request": "true"},
    )
    assert captured[-1][0] == "hebrew_date_deleted"
    assert captured[-1][1]["properties"]["event_type"] == "Yartzeit"


@pytest.mark.django_db
def test_deleting_a_calendar_is_captured(client, user, captured):
    calendar = Calendar.objects.create(name="Family", owner=user)
    client.force_login(user)
    client.post(reverse("hebcal:calendar_delete", args=[calendar.uuid]))
    assert captured[-1] == (
        "calendar_deleted",
        {
            "distinct_id": str(user.pk),
            "properties": {"calendar_uuid": str(calendar.uuid)},
        },
    )
