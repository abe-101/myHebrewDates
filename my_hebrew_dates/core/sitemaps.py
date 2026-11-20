from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = "daily"
    protocol = "https"

    def get_domain(self, site=None):
        # The Site record is "MyHebrewDates.com"; canonical URLs are lowercase.
        return super().get_domain(site).lower()

    def items(self):
        return [
            "home",
            "converter",
            "guides",
            "guide_google_calendar",
            "guide_iphone",
            "guide_yahrzeit",
            "about",
        ]

    def location(self, item):
        return reverse(item)
