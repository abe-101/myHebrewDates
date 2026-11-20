from django.urls import reverse


def test_home_canonical_url_ignores_the_query(client, db):
    response = client.get(reverse("home"), {"utm_source": "newsletter"})

    assert '<link rel="canonical" href="https://myhebrewdates.com/" />' in (
        response.content.decode()
    )


def test_user_name_cannot_break_out_of_the_analytics_script(client, user):
    user.name = 'Moshe\\" </script>'
    user.save()
    client.force_login(user)

    content = client.get(reverse("home")).content.decode()

    assert 'name: "Moshe\\u005C\\u0022 \\u003C/script\\u003E"' in content


def test_sitemap_uses_the_canonical_lowercase_https_domain(client, db):
    content = client.get("/sitemap.xml").content.decode()

    assert "<loc>https://myhebrewdates.com/</loc>" in content
    assert "MyHebrewDates.com" not in content
