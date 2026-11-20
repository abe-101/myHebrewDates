import pytest
from django.urls import reverse

GUIDES = [
    "guides",
    "guide_google_calendar",
    "guide_iphone",
    "guide_outlook",
    "guide_yahrzeit",
    "guide_anniversary",
]


@pytest.mark.parametrize("name", GUIDES)
def test_guide_is_public_and_in_the_sitemap(client, db, name):
    response = client.get(reverse(name))

    assert response.status_code == 200  # noqa: PLR2004
    assert reverse(name) in client.get("/sitemap.xml").content.decode()


@pytest.mark.parametrize("name", GUIDES[1:])
def test_guide_has_breadcrumb_markup(client, db, name):
    content = client.get(reverse(name)).content.decode()

    assert '"@type": "BreadcrumbList"' in content
    assert f"https://myhebrewdates.com{reverse(name)}" in content
