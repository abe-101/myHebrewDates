import re
from http import HTTPStatus

import pytest
from django.urls import reverse

from my_hebrew_dates.hebcal.models import Calendar
from my_hebrew_dates.hebcal.models import HebrewMonthEnum

PASSWORD = "journey-Pa55word!"  # noqa: S105


@pytest.mark.django_db
@pytest.mark.usefixtures("pinned_hebrew_dates")
def test_new_user_signs_up_and_subscribes_to_a_hebrew_date(client, mailoutbox):
    response = client.post(
        reverse("account_signup"),
        {
            "email": "journey@example.com",
            "username": "journey",
            "password1": PASSWORD,
            "password2": PASSWORD,
        },
    )
    assert response.status_code == HTTPStatus.FOUND

    confirm_url = re.search(
        r"https?://\S+(/accounts/confirm-email/\S+/)",
        mailoutbox[0].body,
    )
    assert confirm_url
    client.post(confirm_url.group(1))

    response = client.post(
        reverse("account_login"),
        {"login": "journey", "password": PASSWORD},
    )
    assert response.status_code == HTTPStatus.FOUND

    response = client.get(reverse("hebcal:calendar_list"))
    assert response.url == reverse("hebcal:calendar_new")

    response = client.post(
        reverse("hebcal:calendar_new"),
        {"name": "Family Dates", "timezone": "America/New_York"},
    )
    calendar = Calendar.objects.get(owner__username="journey")
    assert response.url == reverse("hebcal:calendar_edit", args=[calendar.uuid])

    response = client.post(
        reverse("hebcal:hebrew_date_new", args=[calendar.uuid]),
        {
            "name": "Grandpa Moshe",
            "month": HebrewMonthEnum.SHEVAT,
            "day": 15,
            "event_type": "🎂",
        },
    )
    assert response.url == reverse("hebcal:calendar_edit", args=[calendar.uuid])
    response = client.get(response.url)
    assert "Grandpa Moshe" in response.content.decode()

    client.logout()
    feed = client.get(
        reverse("hebcal:calendar_file", args=[calendar.uuid]),
    ).content.decode()
    assert "X-WR-CALNAME:Family Dates" in feed
    assert "| 🎂 Grandpa Moshe" in feed
    assert "DTSTART;VALUE=DATE:20270123" in feed
