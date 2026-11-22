from http import HTTPStatus

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from my_hebrew_dates.hebcal.models import Calendar
from my_hebrew_dates.hebcal.models import HebrewDate
from my_hebrew_dates.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def make_calendars(count):
    calendars = []
    for index in range(count):
        calendar = Calendar.objects.create(
            name=f"Calendar {index}",
            owner=UserFactory.create(),
        )
        HebrewDate.objects.create(
            name=f"Person {index}",
            month=7,
            day=1,
            event_type="🎂",
            calendar=calendar,
        )
        calendars.append(calendar)
    return calendars


def changelist_query_count(client, url):
    with CaptureQueriesContext(connection) as queries:
        response = client.get(url)
    assert response.status_code == HTTPStatus.OK
    return len(queries)


@pytest.mark.parametrize(
    "url_name",
    ["admin:hebcal_calendar_changelist", "admin:hebcal_hebrewdate_changelist"],
)
def test_changelist_queries_do_not_grow_with_rows(admin_client, url_name):
    url = reverse(url_name)
    make_calendars(1)
    baseline = changelist_query_count(admin_client, url)
    make_calendars(5)

    assert changelist_query_count(admin_client, url) == baseline


def test_hebrew_date_filters_do_not_list_every_calendar(admin_client):
    make_calendars(3)

    response = admin_client.get(reverse("admin:hebcal_hebrewdate_changelist"))

    assert "calendar__id__exact" not in response.content.decode()


def test_calendar_list_links_to_public_page(admin_client):
    calendar = make_calendars(1)[0]

    response = admin_client.get(reverse("admin:hebcal_calendar_changelist"))

    public_url = reverse("hebcal:calendar_detail", args=[calendar.uuid])
    assert f'href="{public_url}"' in response.content.decode()


def test_calendar_change_page_renders(admin_client):
    calendar = make_calendars(1)[0]

    response = admin_client.get(
        reverse("admin:hebcal_calendar_change", args=[calendar.pk]),
    )

    assert response.status_code == HTTPStatus.OK
    assert str(calendar.uuid) in response.content.decode()


def test_hebrew_date_change_page_renders(admin_client):
    hebrew_date = make_calendars(1)[0].calendarOf.get()

    response = admin_client.get(
        reverse("admin:hebcal_hebrewdate_change", args=[hebrew_date.pk]),
    )

    assert response.status_code == HTTPStatus.OK


def test_owner_filter_from_user_admin_still_works(admin_client):
    calendars = make_calendars(2)
    owner = calendars[0].owner

    response = admin_client.get(
        reverse("admin:hebcal_calendar_changelist"),
        {"owner__id__exact": owner.pk},
    )

    assert list(response.context["cl"].queryset) == [calendars[0]]
