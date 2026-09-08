from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse

from my_hebrew_dates.core.context_processors import support_links
from my_hebrew_dates.hebcal.models import Calendar

User = get_user_model()

NO_SUPPORT_URLS = {
    "SUPPORT_MONTHLY_URL": "",
    "SUPPORT_ANNUAL_URL": "",
    "SUPPORT_ONETIME_URL": "",
    "SUPPORT_PORTAL_URL": "",
}
ALL_SUPPORT_URLS = {
    "SUPPORT_MONTHLY_URL": "https://buy.stripe.com/monthly",
    "SUPPORT_ANNUAL_URL": "https://buy.stripe.com/annual",
    "SUPPORT_ONETIME_URL": "https://buy.stripe.com/onetime",
    "SUPPORT_PORTAL_URL": "https://billing.stripe.com/p/login/portal",
}
ONETIME_ONLY = {**NO_SUPPORT_URLS, "SUPPORT_ONETIME_URL": "https://example.com/tip"}
MONTHLY_ONLY = {**NO_SUPPORT_URLS, "SUPPORT_MONTHLY_URL": "https://example.com/month"}


class SupportLinksContextProcessorTest(TestCase):
    def setUp(self):
        self.request = RequestFactory().get("/")

    @override_settings(**NO_SUPPORT_URLS)
    def test_disabled_when_no_urls_configured(self):
        support = support_links(self.request)["support"]

        assert support["enabled"] is False
        assert support["options"] == []

    @override_settings(**ALL_SUPPORT_URLS)
    def test_options_are_ordered_recurring_first(self):
        support = support_links(self.request)["support"]

        assert support["enabled"] is True
        assert [option["key"] for option in support["options"]] == [
            "monthly",
            "annual",
            "onetime",
        ]
        assert support["portal_url"] == ALL_SUPPORT_URLS["SUPPORT_PORTAL_URL"]

    @override_settings(**ONETIME_ONLY)
    def test_blank_urls_are_dropped(self):
        support = support_links(self.request)["support"]

        assert [option["key"] for option in support["options"]] == ["onetime"]
        assert support["options"][0]["url"] == ONETIME_ONLY["SUPPORT_ONETIME_URL"]


class SupportCardRenderingTest(TestCase):
    """The calendar detail page is public, so the card must reach signed-out
    visitors as well as owners.
    """

    def setUp(self):
        self.owner = User.objects.create_user("owner", "owner@example.com", "password")
        self.calendar = Calendar.objects.create(name="Test Calendar", owner=self.owner)
        self.url = reverse(
            "hebcal:calendar_detail",
            kwargs={"uuid": self.calendar.uuid},
        )

    @override_settings(**ALL_SUPPORT_URLS)
    def test_card_is_shown_to_anonymous_visitors(self):
        response = self.client.get(self.url)

        assert response.status_code == HTTPStatus.OK
        self.assertTemplateUsed(response, "hebcal/_support_card.html")
        self.assertContains(response, ALL_SUPPORT_URLS["SUPPORT_MONTHLY_URL"])
        self.assertContains(response, ALL_SUPPORT_URLS["SUPPORT_PORTAL_URL"])

    @override_settings(**NO_SUPPORT_URLS)
    def test_card_is_hidden_when_unconfigured(self):
        response = self.client.get(self.url)

        assert response.status_code == HTTPStatus.OK
        self.assertNotContains(response, "Keep this calendar running")

    @override_settings(**MONTHLY_ONLY)
    def test_portal_line_hidden_without_portal_url(self):
        response = self.client.get(self.url)

        self.assertContains(response, MONTHLY_ONLY["SUPPORT_MONTHLY_URL"])
        self.assertNotContains(response, "Manage or cancel your contribution")
