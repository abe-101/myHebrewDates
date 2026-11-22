import logging

import pytest
from django.urls import reverse

from my_hebrew_dates.core.request_context import RequestContextFilter
from my_hebrew_dates.hebcal.models import Calendar

REQUEST_LOGGER = "my_hebrew_dates.core.request_context"


@pytest.fixture
def captured(caplog):
    caplog.handler.addFilter(RequestContextFilter())
    caplog.set_level(logging.INFO)
    return caplog


@pytest.fixture
def calendar(user):
    return Calendar.objects.create(name="Family", owner=user)


def test_logged_in_request_writes_one_request_line(client, user, captured):
    client.force_login(user)

    client.get(reverse("hebcal:calendar_new"), HTTP_X_RAILWAY_REQUEST_ID="rail-123")

    [line] = [r for r in captured.records if r.name == REQUEST_LOGGER]
    assert line.route == "hebcal:calendar_new"
    assert line.status == 200  # noqa: PLR2004
    assert line.user_id == user.pk
    assert line.request_id == "rail-123"


def test_unnamed_route_is_logged_by_path(client, user, captured):
    client.force_login(user)

    client.get("/favicon.png")

    [line] = [r for r in captured.records if r.name == REQUEST_LOGGER]
    assert line.route == "/favicon.png"


def test_anonymous_request_writes_no_request_line(client, db, captured):
    client.get(reverse("home"))

    assert not [r for r in captured.records if r.name == REQUEST_LOGGER]


def test_lines_from_views_carry_the_request_id(client, calendar, captured):
    client.get(
        reverse("hebcal:calendar_file", kwargs={"uuid": calendar.uuid}),
        HTTP_X_RAILWAY_REQUEST_ID="rail-456",
    )

    [line] = [r for r in captured.records if r.funcName == "calendar_file"]
    assert line.request_id == "rail-456"
    assert line.user_id is None


def test_feed_fetch_writes_a_request_line_with_its_status(client, calendar, captured):
    url = reverse("hebcal:calendar_file", kwargs={"uuid": calendar.uuid})
    etag = client.get(url).headers["ETag"]
    captured.clear()

    client.get(url, HTTP_IF_NONE_MATCH=etag)

    [line] = [r for r in captured.records if r.name == REQUEST_LOGGER]
    assert line.route == "hebcal:calendar_file"
    assert line.status == 304  # noqa: PLR2004
    assert line.user_id is None


def test_request_id_is_generated_without_the_railway_header(client, user, captured):
    client.force_login(user)

    client.get(reverse("hebcal:calendar_new"))

    [line] = [r for r in captured.records if r.name == REQUEST_LOGGER]
    assert line.request_id


def test_feed_response_does_not_vary_on_cookie(client, calendar):
    response = client.get(
        reverse("hebcal:calendar_file", kwargs={"uuid": calendar.uuid}),
    )

    assert "Cookie" not in response.headers.get("Vary", "")
