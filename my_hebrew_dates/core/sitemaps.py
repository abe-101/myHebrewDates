from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages with SEO-optimized priorities."""

    def items(self):
        return [
            {"page": "home", "priority": 1.0, "changefreq": "weekly"},
            {"page": "about", "priority": 0.8, "changefreq": "monthly"},
        ]

    def location(self, item):
        return reverse(item["page"])

    def priority(self, item):
        return item["priority"]

    def changefreq(self, item):
        return item["changefreq"]
