import pytest
from django.urls import reverse

from my_hebrew_dates.hebcal.models import Calendar
from my_hebrew_dates.hebcal.models import HebrewMonthEnum


def test_empty_page_shows_both_lookups(client, db):
    content = client.get(reverse("converter")).content.decode()

    assert "Show English dates" in content
    assert "Find the Hebrew date" in content
    assert ") falls on" not in content


def test_hebrew_date_shows_upcoming_english_dates(client, db, pinned_hebrew_dates):
    content = client.get(
        reverse("converter"),
        {"day": 15, "month": HebrewMonthEnum.SHEVAT},
    ).content.decode()

    assert "(15 Shevat) falls on" in content
    assert "Saturday, January 23, 2027" in content


def test_english_date_after_sunset_is_the_next_hebrew_day(
    client,
    db,
    pinned_hebrew_dates,
):
    content = client.get(
        reverse("converter"),
        {"english_date": "2027-01-22", "after_sunset": "on"},
    ).content.decode()

    assert "(15 Shevat) falls on" in content


def test_impossible_date_explains_itself(client, db):
    content = client.get(
        reverse("converter"),
        {"day": 30, "month": HebrewMonthEnum.IYAR},
    ).content.decode()

    assert "There is no day 30 in" in content


def test_signed_in_user_can_add_the_date_to_their_calendar(client, user):
    calendar = Calendar.objects.create(name="Family", owner=user)
    client.force_login(user)

    content = client.get(
        reverse("converter"),
        {"day": 15, "month": HebrewMonthEnum.SHEVAT},
    ).content.decode()

    add_url = reverse("hebcal:hebrew_date_new", args=[calendar.uuid])
    assert f"{add_url}?day=15&month=11" in content


def test_add_date_page_accepts_the_prefilled_date(client, user):
    calendar = Calendar.objects.create(name="Family", owner=user)
    client.force_login(user)

    response = client.get(
        reverse("hebcal:hebrew_date_new", args=[calendar.uuid]),
        {"day": 15, "month": HebrewMonthEnum.SHEVAT},
    )

    assert response.context["form"].initial["month"] == str(HebrewMonthEnum.SHEVAT)


def test_converter_is_in_the_sitemap(client, db):
    content = client.get("/sitemap.xml").content.decode()

    assert reverse("converter") in content


@pytest.mark.parametrize(
    "query",
    [
        {"english_date": "2027-02-30"},
        {"english_date": "9999-12-31", "after_sunset": "on"},
    ],
)
def test_impossible_english_dates_do_not_crash(client, user, query):
    calendar = Calendar.objects.create(name="Family", owner=user)
    client.force_login(user)

    converter = client.get(reverse("converter"), query)
    add_page = client.get(
        reverse("hebcal:hebrew_date_new", args=[calendar.uuid]),
        query,
    )

    assert converter.status_code == 200  # noqa: PLR2004
    assert add_page.status_code == 200  # noqa: PLR2004


def test_impossible_english_date_says_so(client, db):
    content = client.get(
        reverse("converter"),
        {"english_date": "2027-02-30"},
    ).content.decode()

    assert "a real date. Check the day, month, and year." in content


def test_hebrew_lookup_updates_when_a_select_changes(client, db):
    content = client.get(reverse("converter")).content.decode()

    assert 'hx-trigger="change, submit"' in content
    assert 'hx-target="#converter-result"' in content


def test_live_update_shows_an_impossible_hebrew_date_in_the_results(client, db):
    response = client.get(
        reverse("converter"),
        {"day": 30, "month": HebrewMonthEnum.IYAR},
        headers={"HX-Request": "true"},
    )

    results = response.content.decode().split('id="converter-result"')[1]
    assert "There is no day 30 in" in results


def test_live_update_stays_quiet_while_the_date_is_half_chosen(client, db):
    response = client.get(
        reverse("converter"),
        {"day": 30, "month": ""},
        headers={"HX-Request": "true"},
    )

    results = response.content.decode().split('id="converter-result"')[1]
    assert "alert" not in results.split("</main>")[0]
