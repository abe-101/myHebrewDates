from django.urls import reverse


def test_home_canonical_url_ignores_the_query(client, db):
    response = client.get(reverse("home"), {"utm_source": "newsletter"})

    assert '<link rel="canonical" href="https://myhebrewdates.com/" />' in (
        response.content.decode()
    )
