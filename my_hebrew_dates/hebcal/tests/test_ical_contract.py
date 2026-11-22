"""
Contract tests for the parts of a subscription that must never move.

Calendar clients key events off UID. If a UID changes, the client drops
the old event and adds a new one, losing anything the subscriber set on
it. The date half of a UID rolls forward with the three-year window by
design; the hashed half must stay fixed for a given person and date, so
it is pinned here independently of the rolling half.
"""

import re
from http import HTTPStatus

import pytest
from django.urls import reverse

from my_hebrew_dates.hebcal.models import Calendar
from my_hebrew_dates.hebcal.tests.conftest import LATER
from my_hebrew_dates.hebcal.utils import generate_ical

BIRTHDAY = "🎂"
ANNIVERSARY = "💍"
YARTZEIT = "🕯️"

NISAN = 1
ADAR_I = 12
ADAR_II = 13

UID_RE = re.compile(
    r"^UID:(?P<date>\d{4}-\d{2}-\d{2})(?P<digest>\S{28})@myhebrewdates\.com",
    re.MULTILINE,
)

# (event_type, name, month, day) -> the digest half of the UID.
PINNED_DIGESTS = {
    (BIRTHDAY, "Avraham", NISAN, 15): "PsOLxoVd6KQMKA0mC5tr16BlNUE=",
    (ANNIVERSARY, "Sarah and Yitzchak", NISAN, 15): "FWombKb_MpgUqy1EO8byS-e1Wmc=",
    (YARTZEIT, "Rivka", NISAN, 15): "8uAPf6haevF9yO1sfZL67hzXviU=",
    (YARTZEIT, "Adar One", ADAR_I, 10): "VAYfIYaYO_MIOAkPF-QFB-7ees4=",
    (YARTZEIT, "Adar Two", ADAR_II, 10): "o39pOhKbsczROJV9agZbjShXU1I=",
}


@pytest.mark.usefixtures("pinned_hebrew_dates")
class TestUidStability:
    @pytest.mark.parametrize(
        ("event_type", "name", "month", "day"),
        list(PINNED_DIGESTS),
    )
    def test_uid_digest_is_pinned(
        self,
        make_calendar,
        event_type,
        name,
        month,
        day,
    ):
        calendar = make_calendar(events=[(month, day, event_type, name)])
        ical = generate_ical(calendar)

        digests = {m.group("digest") for m in UID_RE.finditer(ical)}
        expected = PINNED_DIGESTS[event_type, name, month, day]
        assert digests == {expected}

    def test_uid_digest_ignores_calendar_identity(self, make_calendar):
        """
        The digest covers only event type, name and Hebrew date, so the
        same person in two calendars keeps the same digest.
        """
        events = [(NISAN, 15, BIRTHDAY, "Avraham")]
        first = make_calendar(name="One", timezone="UTC", events=events)
        second = make_calendar(
            name="Two",
            timezone="Asia/Jerusalem",
            events=events,
        )

        def digests_of(calendar):
            return {m.group("digest") for m in UID_RE.finditer(generate_ical(calendar))}

        assert digests_of(first) == digests_of(second)

    def test_uid_is_stable_across_calls(self, make_calendar):
        calendar = make_calendar(events=[(NISAN, 15, BIRTHDAY, "Avraham")])
        first = UID_RE.findall(generate_ical(calendar))
        second = UID_RE.findall(generate_ical(calendar))
        assert first == second

    def test_events_are_ordered_by_start_date(self, make_calendar):
        calendar = make_calendar(
            events=[
                (NISAN, 20, BIRTHDAY, "Later"),
                (NISAN, 1, BIRTHDAY, "Earlier"),
            ],
        )
        ical = generate_ical(calendar)
        starts = re.findall(r"^DTSTART;VALUE=DATE:(\d{8})", ical, re.MULTILINE)
        assert starts == sorted(starts)

    def test_identical_dates_keep_their_order_after_an_edit(
        self,
        make_calendar,
        frozen_clock,
    ):
        """
        Two copies of a date share a start and UID. Postgres tends to return
        an updated row last, which would reorder them and change the ETag.
        """
        calendar = make_calendar(
            events=[
                (NISAN, 15, BIRTHDAY, "Avraham"),
                (NISAN, 15, BIRTHDAY, "Avraham"),
            ],
        )
        first = calendar.calendarOf.order_by("pk").first()
        frozen_clock.move_to(LATER)
        first.save()
        calendar = Calendar.objects.prefetch_related("calendarOf").get(pk=calendar.pk)

        dtstamps = re.findall(r"^DTSTAMP:(\S+)", generate_ical(calendar), re.MULTILINE)

        assert dtstamps[:2] == ["20260915T083000Z", "20260601T120000Z"]


@pytest.mark.usefixtures("pinned_hebrew_dates")
class TestSubscriptionEndpoints:
    """
    Both URL shapes are live in subscribers' clients and must keep
    serving the same document.
    """

    @pytest.fixture
    def calendar(self, make_calendar):
        return make_calendar(
            events=[
                (NISAN, 15, BIRTHDAY, "Avraham"),
                (ADAR_I, 10, YARTZEIT, "Adar One"),
            ],
        )

    def test_ics_url_serves_calendar(self, client, calendar):
        url = reverse("hebcal:calendar_file", args=[calendar.uuid])
        response = client.get(url)

        assert response.status_code == HTTPStatus.OK
        assert response["Content-Type"] == "text/calendar"
        assert f'filename="{calendar.uuid}.ics"' in response["Content-Disposition"]
        assert response.content.startswith(b"BEGIN:VCALENDAR")
        assert response["Cache-Control"] == "max-age=3600"

    def test_legacy_ical_url_serves_same_body(self, client, calendar):
        modern = client.get(
            reverse("hebcal:calendar_file", args=[calendar.uuid]),
        )
        legacy = client.get(
            reverse("hebcal:legacy_calendar_file", args=[calendar.uuid]),
        )

        assert legacy.status_code == HTTPStatus.OK
        # The whole body, not just the UIDs: the held clock makes every
        # byte reproducible, so a header, alarm or line ending that
        # drifted on one route alone would show up here.
        assert legacy.content == modern.content

    def test_body_is_the_same_for_every_client(self, client, calendar):
        """
        Cloudflare caches the feed by URL alone, so a body that depended on the
        User-Agent would be served to whichever client asked second.
        """
        url = reverse("hebcal:calendar_file", args=[calendar.uuid])
        google = client.get(url, headers={"user-agent": "Google-Calendar-Importer"})
        apple = client.get(url, headers={"user-agent": "CalendarAgent/950.11"})

        assert google.content == apple.content

    def test_edit_shows_up_on_the_next_request(self, client, calendar):
        url = reverse("hebcal:calendar_file", args=[calendar.uuid])
        client.get(url)
        calendar.calendarOf.create(
            month=NISAN,
            day=20,
            event_type=BIRTHDAY,
            name="Zebulun",
        )

        assert "Zebulun" in client.get(url).content.decode()

    def test_unchanged_feed_answers_revalidation_with_304(self, client, calendar):
        url = reverse("hebcal:calendar_file", args=[calendar.uuid])
        etag = client.get(url)["ETag"]

        response = client.get(url, headers={"if-none-match": etag})

        assert response.status_code == HTTPStatus.NOT_MODIFIED
        assert response["Cache-Control"] == "max-age=3600"

    def test_changed_feed_answers_revalidation_with_new_body(self, client, calendar):
        url = reverse("hebcal:calendar_file", args=[calendar.uuid])
        etag = client.get(url)["ETag"]
        calendar.calendarOf.create(
            month=NISAN,
            day=20,
            event_type=BIRTHDAY,
            name="Zebulun",
        )

        response = client.get(url, headers={"if-none-match": etag})

        assert response.status_code == HTTPStatus.OK
        assert "Zebulun" in response.content.decode()

    def test_subscription_does_not_require_login(self, client, calendar):
        url = reverse("hebcal:calendar_file", args=[calendar.uuid])
        assert client.get(url).status_code == HTTPStatus.OK

    def test_unknown_calendar_is_404(self, db, client):
        url = reverse(
            "hebcal:calendar_file",
            args=["00000000-0000-0000-0000-000000000000"],
        )
        assert client.get(url).status_code == HTTPStatus.NOT_FOUND

    @pytest.mark.parametrize(
        ("alarm", "expected"),
        [("9", "PT9H"), ("1", "PT1H"), ("", "PT9H"), ("bogus", "PT9H")],
    )
    def test_alarm_query_param(self, client, calendar, alarm, expected):
        url = reverse("hebcal:calendar_file", args=[calendar.uuid])
        response = client.get(url, {"alarm": alarm})
        assert f"TRIGGER:{expected}" in response.content.decode()


@pytest.mark.usefixtures("pinned_hebrew_dates")
class TestTimestampFields:
    """
    A single frozen instant makes created and modified identical, so it
    cannot show which one LAST-MODIFIED reads. Travelling forward and
    saving again separates them.
    """

    def test_last_modified_follows_modified_not_created(
        self,
        make_calendar,
        frozen_clock,
    ):
        calendar = make_calendar(events=[(NISAN, 15, BIRTHDAY, "Avraham")])
        hebrew_date = calendar.calendarOf.get()
        assert hebrew_date.created == hebrew_date.modified

        frozen_clock.move_to(LATER)
        hebrew_date.save()
        hebrew_date.refresh_from_db()
        assert hebrew_date.created != hebrew_date.modified

        ical = generate_ical(calendar)
        last_modified = re.findall(r"^LAST-MODIFIED:(.*)$", ical, re.MULTILINE)

        expected = hebrew_date.modified.strftime("%Y%m%dT%H%M%SZ")
        unexpected = hebrew_date.created.strftime("%Y%m%dT%H%M%SZ")
        assert {value.strip() for value in last_modified} == {expected}
        assert unexpected not in {value.strip() for value in last_modified}

    def test_calendar_last_modified_moves_when_a_date_is_deleted(
        self,
        client,
        make_calendar,
        frozen_clock,
    ):
        calendar = make_calendar(events=[(NISAN, 15, BIRTHDAY, "Avraham")])
        hebrew_date = calendar.calendarOf.get()
        frozen_clock.move_to(LATER)
        client.force_login(calendar.owner)
        client.post(
            reverse(
                "hebcal:delete_hebrew_date_htmx",
                args=[calendar.uuid, hebrew_date.pk],
            ),
            headers={"HX-Request": "true"},
        )
        calendar.refresh_from_db()

        assert "LAST-MODIFIED:20260915T083000Z" in generate_ical(calendar)

    def test_calendar_last_modified_moves_on_a_bulk_delete(
        self,
        make_calendar,
        frozen_clock,
    ):
        """The admin's bulk delete action deletes through a queryset."""
        calendar = make_calendar(events=[(NISAN, 15, BIRTHDAY, "Avraham")])

        frozen_clock.move_to(LATER)
        calendar.calendarOf.all().delete()
        calendar.refresh_from_db()

        assert "LAST-MODIFIED:20260915T083000Z" in generate_ical(calendar)

    def test_calendar_with_dates_can_still_be_deleted(self, make_calendar):
        calendar = make_calendar(events=[(NISAN, 15, BIRTHDAY, "Avraham")])

        calendar.delete()

        assert not Calendar.objects.filter(pk=calendar.pk).exists()

    def test_body_does_not_change_while_the_data_does_not(
        self,
        make_calendar,
        frozen_clock,
    ):
        """
        An unchanged body keeps its ETag, so a client or Cloudflare that
        revalidates gets a 304 instead of the whole feed again.
        """
        calendar = make_calendar(events=[(NISAN, 15, BIRTHDAY, "Avraham")])
        before = generate_ical(calendar)

        frozen_clock.move_to(LATER)

        assert generate_ical(calendar) == before
