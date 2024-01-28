from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from my_hebrew_dates.hebcal.models import Calendar, HebrewDate

User = get_user_model()


class BaseTest(TestCase):
    def setUp(self):
        # Common setup tasks
        self.client = Client()
        self.user = User.objects.create_user("testuser", "test@example.com", "password")


class CalendarListViewTest(BaseTest):
    def setUp(self):
        super().setUp()
        self.url = reverse("hebcal:calendar_list")

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, "/accounts/login/?next=/calendars/")

    def test_logged_in_uses_correct_template(self):
        self.client.login(username="testuser", password="password")
        self.calendar = Calendar.objects.create(name="Test Calendar", owner=self.user)
        response = self.client.get(self.url)

        self.assertContains(response, self.calendar.name)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "hebcal/calendar_list.html")

    def test_no_calendars_redirects_to_create(self):
        self.client.login(username="testuser", password="password")
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("hebcal:calendar_new"))

    def test_only_user_owned_calendars_are_listed(self):
        self.client.login(username="testuser", password="password")
        other_user = User.objects.create_user("otheruser", "other@example.com", "password")
        Calendar.objects.create(name="Other User's Calendar", owner=other_user)
        self.calendar = Calendar.objects.create(name="Test Calendar", owner=self.user)

        response = self.client.get(self.url)
        self.assertContains(response, self.calendar.name)
        self.assertNotContains(response, "Other User's Calendar")


class CreateCalendarViewTest(BaseTest):
    def setUp(self):
        super().setUp()
        self.client.login(username="testuser", password="password")
        self.url = reverse("hebcal:calendar_new")

    def test_get_create_calendar_form(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "hebcal/calendar_new.html")

    def test_valid_calendar_creation(self):
        data = {"name": "New Test Calendar", "timezone": "America/New_York"}
        response = self.client.post(self.url, data)
        self.assertEqual(Calendar.objects.count(), 1)
        self.assertRedirects(
            response, expected_url=reverse("hebcal:calendar_edit", args=[Calendar.objects.first().uuid])
        )

    def test_invalid_calendar_creation(self):
        data = {"name": "", "timezone": "America/New_York"}
        response = self.client.post(self.url, data)
        self.assertEqual(Calendar.objects.count(), 0)
        self.assertFormError(response.context["form"], "name", "This field is required.")


class CalendarDetailViewTest(BaseTest):
    def setUp(self):
        super().setUp()
        self.client.login(username="testuser", password="password")
        self.calendar = Calendar.objects.create(name="Test Calendar", owner=self.user)
        self.url = reverse("hebcal:calendar_detail", args=[self.calendar.uuid])

    def test_calendar_detail_view_with_valid_uuid(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.calendar.name)

    def test_calendar_detail_view_with_invalid_uuid(self):
        non_existent_uuid = uuid4()
        invalid_url = reverse("hebcal:calendar_detail", args=[non_existent_uuid])
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 404)


class CalendarEditViewTest(BaseTest):
    def setUp(self):
        super().setUp()
        self.client.login(username="testuser", password="password")
        self.calendar = Calendar.objects.create(name="Test Calendar", owner=self.user)
        self.url = reverse("hebcal:calendar_edit", args=[self.calendar.uuid])
        self.hebrew_date1 = HebrewDate.objects.create(
            name="Test Hebrew Date 1", month=1, day=1, event_type="🎂", calendar=self.calendar
        )
        self.hebrew_date2 = HebrewDate.objects.create(
            name="Test Hebrew Date 2", month=2, day=2, event_type="🎂", calendar=self.calendar
        )
        self.hebrew_date3 = HebrewDate.objects.create(
            name="Test Hebrew Date 3", month=3, day=3, event_type="🕯️", calendar=self.calendar
        )

    def test_access_to_view(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_unauthorized_access(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        # redirect to login page
        self.assertRedirects(response, f"/accounts/login/?next=/calendars/{self.calendar.uuid}/edit/")

    def test_view_renders_correctly(self):
        response = self.client.get(self.url)
        self.assertContains(response, "Manage Your Calendar")

    def test_filter_by_month(self):
        response = self.client.get(self.url, {"month": "1"})
        self.assertContains(response, self.hebrew_date1.name)  # Adjust based on how months are displayed

    def test_filter_by_day(self):
        response = self.client.get(self.url, {"day": "2"})
        self.assertContains(response, self.hebrew_date2.name)

    def test_filter_by_event_type(self):
        response = self.client.get(self.url, {"event_type": "🕯️"})
        self.assertContains(response, self.hebrew_date3.name)

    def test_search_functionality(self):
        response = self.client.get(self.url, {"search": "Test Hebrew Date "})
        self.assertContains(response, self.hebrew_date1.name)
        self.assertContains(response, self.hebrew_date2.name)
        self.assertContains(response, self.hebrew_date3.name)
