import hmac

import pytest
from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string

from my_hebrew_dates.users.context_processors import posthog_support_identity
from my_hebrew_dates.users.models import User

IDENTITY_SECRET = "test-support-signing-key"  # noqa: S105


@pytest.mark.parametrize(
    ("authenticated", "configured"),
    [(True, True), (True, False), (False, True)],
)
def test_posthog_support_identity(rf, settings, authenticated, configured):
    request = rf.get("/")
    request.user = User(pk=123, username="tester") if authenticated else AnonymousUser()
    settings.POSTHOG_IDENTITY_SECRET = IDENTITY_SECRET if configured else ""
    settings.COMPRESS_ENABLED = False
    settings.COMPRESS_PRECOMPILERS = ()

    context = posthog_support_identity(request)
    html = render_to_string("base.html", request=request)

    if authenticated and configured:
        expected_hash = hmac.new(IDENTITY_SECRET.encode(), b"123", "sha256").hexdigest()
        assert context == {"POSTHOG_IDENTITY_HASH": expected_hash}
        assert "identity_distinct_id: '123'" in html
        assert f"identity_hash: '{expected_hash}'" in html
    else:
        assert context == {}
        assert "identity_distinct_id:" not in html
        assert "identity_hash:" not in html

    assert IDENTITY_SECRET not in html
    if authenticated:
        assert "posthog.identify('123'" in html
        assert "ph.clearIdentity" not in html
    else:
        assert "ph.clearIdentity?.()" in html
        assert "ph.reset()" in html
