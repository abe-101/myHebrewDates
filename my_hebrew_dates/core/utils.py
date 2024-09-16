# core/utils.py

from django.conf import settings
from django.contrib.sites.models import Site


def get_site_url() -> str:
    """Generates the full URL of the current site based on DEBUG mode.

    Returns:
        str: The full URL of the site, including the scheme.
    """
    url_scheme = "http" if settings.DEBUG else "https"
    current_site_domain = Site.objects.get_current().domain
    return f"{url_scheme}://{current_site_domain}"
