from django.conf import settings


def support_links(request):
    """Expose the configured support/donation links to every template.

    Each option is a hosted checkout URL owned by the payment provider, so a blank
    setting is meaningful: it simply drops that option from the card. Ordering here
    is the ordering on screen, and the first option is rendered as the primary call
    to action.
    """
    options = [
        {"key": key, "label": label, "hint": hint, "icon": icon, "url": url}
        for key, label, hint, icon, url in (
            (
                "monthly",
                "Monthly",
                "Choose your amount",
                "bi-arrow-repeat",
                settings.SUPPORT_MONTHLY_URL,
            ),
            (
                "annual",
                "Yearly",
                "One charge a year",
                "bi-calendar-check",
                settings.SUPPORT_ANNUAL_URL,
            ),
            (
                "onetime",
                "One-time",
                "Give what you like",
                "bi-cup-hot",
                settings.SUPPORT_ONETIME_URL,
            ),
        )
        if url
    ]

    return {
        "support": {
            "options": options,
            "portal_url": settings.SUPPORT_PORTAL_URL,
            "enabled": bool(options),
        },
    }
