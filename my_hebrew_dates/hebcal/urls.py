from django.urls import path
from django.views.generic import TemplateView

from .views import calendar_detail, calendar_file, calendar_list

app_name = "hebcal"

urlpatterns = [
    path(
        "instructions/",
        TemplateView.as_view(template_name="hebcal/instructions.html"),
        name="instructions",
    ),
    path("<uuid>.ical", calendar_file, name="calendar_file"),
    path("", calendar_list, name="calendar_list"),
    path("<pk>/", calendar_detail, name="calendar_detail"),
]
