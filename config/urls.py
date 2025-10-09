# ruff: noqa
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_not_required
from django.contrib import admin
from django.urls import include, path
from django.views import defaults as default_views
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.authtoken.views import obtain_auth_token
from django.contrib.sitemaps.views import sitemap
from my_hebrew_dates.core.sitemaps import StaticViewSitemap

sitemaps = {
    "static": StaticViewSitemap,
}


urlpatterns = [
    path(
        "",
        login_not_required(TemplateView.as_view(template_name="pages/home.html")),
        name="home",
    ),
    path(
        "about/",
        login_not_required(TemplateView.as_view(template_name="pages/about.html")),
        name="about",
    ),
    path(
        "robots.txt",
        login_not_required(
            TemplateView.as_view(template_name="robots.txt", content_type="text/plain")
        ),
    ),
    path(
        "favicon.png",
        login_not_required(
            RedirectView.as_view(url="/static/images/favicon.png", permanent=True)
        ),
    ),
    path(
        "favicon.ico",
        login_not_required(
            RedirectView.as_view(
                url="static/images/favicons/favicon.ico", permanent=True
            )
        ),
    ),
    path(
        "sitemap.xml",
        login_not_required(sitemap),
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path(settings.ADMIN_URL, admin.site.urls),
    path("users/", include("my_hebrew_dates.users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),
    path("calendars/", include("my_hebrew_dates.hebcal.urls", namespace="hebcal")),
    # Media files
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]

# API URLS
urlpatterns += [
    # API base url
    path("api/", include("config.api_router")),
    # DRF auth token
    path("api/auth-token/", obtain_auth_token),
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="api-schema"),
        name="api-docs",
    ),
]

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
        path("__reload__/", include("django_browser_reload.urls")),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
