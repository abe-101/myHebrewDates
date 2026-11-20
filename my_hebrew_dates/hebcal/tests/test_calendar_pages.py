from django.contrib.sites.models import Site
from django.urls import reverse

from my_hebrew_dates.hebcal.models import Calendar


def test_owner_sees_settings_tabs_and_sharing(client, user):
    calendar = Calendar.objects.create(name="Family", owner=user)
    client.force_login(user)

    content = client.get(
        reverse("hebcal:calendar_detail", args=[calendar.uuid]),
    ).content.decode()

    assert "Calendar settings" in content
    assert reverse("hebcal:calendar_edit", args=[calendar.uuid]) in content
    assert "Share with your family" in content


def test_family_member_sees_only_how_to_subscribe(client, user):
    calendar = Calendar.objects.create(name="Family", owner=user)

    content = client.get(
        reverse("hebcal:calendar_detail", args=[calendar.uuid]),
    ).content.decode()

    assert "Add these dates to your own calendar app" in content
    assert "Calendar settings" not in content
    assert reverse("hebcal:calendar_edit", args=[calendar.uuid]) not in content
    assert "Share with your family" not in content


def test_list_copies_the_page_family_should_open(client, user):
    calendar = Calendar.objects.create(name="Family", owner=user)
    client.force_login(user)

    content = client.get(reverse("hebcal:calendar_list")).content.decode()

    domain = Site.objects.get_current().domain.lower()
    share_url = reverse("hebcal:calendar_detail", args=[calendar.uuid])
    assert f'data-copy="https://{domain}{share_url}"' in content
