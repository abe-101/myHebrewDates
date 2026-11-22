import posthog
from allauth.account.signals import user_logged_in
from allauth.account.signals import user_signed_up
from django.dispatch import receiver


@receiver(user_signed_up)
def capture_signup(request, user, **kwargs):
    sociallogin = kwargs.get("sociallogin")
    method = sociallogin.account.provider if sociallogin else "email"
    posthog.capture(
        "user_signed_up",
        distinct_id=str(user.pk),
        properties={"method": method},
    )


@receiver(user_logged_in)
def capture_login(request, user, **kwargs):
    sociallogin = kwargs.get("sociallogin")
    method = sociallogin.account.provider if sociallogin else "email"
    posthog.capture(
        "user_logged_in",
        distinct_id=str(user.pk),
        properties={"method": method},
    )
