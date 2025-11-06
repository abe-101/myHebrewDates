import os

from django.apps import AppConfig
from django.conf import settings


class CoreConfig(AppConfig):
    name = "my_hebrew_dates.core"

    def ready(self):
        if os.environ.get("DJANGO_SETTINGS_MODULE") == "config.settings.production":
            import posthog

            posthog.api_key = settings.POSTHOG_API_KEY
            posthog.host = "https://m.myhebrewdates.com"
