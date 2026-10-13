"""
https://github.com/encode/django-rest-framework/discussions/9503#discussioncomment-10487612
"""

import re

from django.conf import settings
from django.contrib.auth.middleware import LoginRequiredMiddleware


class CustomLoginRequiredMiddleware(LoginRequiredMiddleware):
    def __init__(self, get_response=None):
        self.get_response = get_response
        self.open_urls = [re.compile(url) for url in settings.OPEN_URLS]
        super().__init__(get_response)

    def process_view(self, request, view_func, view_args, view_kwargs):
        for url in self.open_urls:
            if url.match(request.path):
                return None  # Pass through, no login required
        return super().process_view(request, view_func, view_args, view_kwargs)
