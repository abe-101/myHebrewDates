import hmac

from django.conf import settings


def allauth_settings(request):
    """Expose some settings from django-allauth in templates."""
    return {
        "ACCOUNT_ALLOW_REGISTRATION": settings.ACCOUNT_ALLOW_REGISTRATION,
    }


def posthog_support_identity(request):
    secret = settings.POSTHOG_IDENTITY_SECRET
    user = getattr(request, "user", None)
    if not secret or user is None or not user.is_authenticated:
        return {}

    distinct_id = str(user.pk)
    return {
        "POSTHOG_IDENTITY_HASH": hmac.digest(
            secret.encode(),
            distinct_id.encode(),
            "sha256",
        ).hex(),
    }
