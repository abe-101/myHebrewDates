import base64
import logging
from datetime import date
from datetime import timedelta
from typing import TYPE_CHECKING
from typing import cast

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.sites.models import Site
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_POST
from django.views.generic.edit import DeleteView
from django_htmx_modal_forms import HtmxModalUpdateView

from my_hebrew_dates.hebcal.decorators import requires_htmx
from my_hebrew_dates.hebcal.forms import CalendarForm
from my_hebrew_dates.hebcal.forms import HebrewDateForm
from my_hebrew_dates.hebcal.hebrew_date import hebrew_date_from_english_input
from my_hebrew_dates.hebcal.models import Calendar
from my_hebrew_dates.hebcal.models import HebrewDate
from my_hebrew_dates.hebcal.utils import generate_ical
from my_hebrew_dates.hebcal.utils import generate_ical_experimental

if TYPE_CHECKING:
    from uuid import UUID

    from django.http import HttpRequest

    from my_hebrew_dates.users.models import User

# Setup logger
logger = logging.getLogger(__name__)


def calendar_list_view(request):
    user_owned_calendars = Calendar.objects.filter(owner=request.user)

    if not user_owned_calendars.exists():
        return redirect("hebcal:calendar_new")

    logger.info(
        "Calendar list view called for user: %s with calendars: %s",
        request.user,
        user_owned_calendars,
    )
    context = {
        "calendar_list": user_owned_calendars,
        "domain_name": Site.objects.get_current().domain,
    }

    return render(request, "hebcal/calendar_list.html", context)


def calendar_detail_view(request: HttpRequest, uuid: UUID):
    calendar = get_object_or_404(Calendar, uuid=uuid)

    context = {
        "calendar": calendar,
        "domain_name": Site.objects.get_current().domain,
        "alarm_time": 9,
    }
    logger.info(
        "user: %s accessed Calendar_detail_view for calendar: %s (%s)",
        request.user,
        calendar.name,
        calendar.uuid,
    )

    return render(request, "hebcal/calendar_detail.html", context)


def create_calendar_view(request: HttpRequest):
    if request.method == "POST":
        form = CalendarForm(request.POST)
        if form.is_valid():
            calendar = form.save(commit=False)
            calendar.owner = request.user
            calendar.save()
            messages.success(request, f"{calendar.name} created successfully.")
            logger.info(
                "user: %s created Calendar: %s (%s)",
                request.user,
                calendar.name,
                calendar.uuid,
            )
            return redirect("hebcal:calendar_edit", uuid=calendar.uuid)
        messages.error(request, "Please correct the errors in the form.")
        logger.warning(
            "user: %s attempted to create a calendar with invalid form data. "
            "Errors: %s",
            request.user,
            form.errors,
        )
    else:
        form = CalendarForm()

    context = {
        "form": form,
    }
    logger.info(
        "user: %s accessed create_calendar_view",
        request.user,
    )

    return render(request, "hebcal/calendar_new.html", context)


class CalendarUpdateModalView(  # type: ignore[misc]
    LoginRequiredMixin,
    SuccessMessageMixin,
    HtmxModalUpdateView,
):
    model = Calendar
    modal_size = "md"
    form_class = CalendarForm
    detail_template_name = "hebcal/_calendar_name.html"
    modal_title = "Calendar settings"
    success_message = "Calendar settings saved"
    login_url = reverse_lazy("users:redirect")

    def get_queryset(self):
        return Calendar.objects.filter(owner=cast("User", self.request.user))


def calendar_edit_view(request: HttpRequest, uuid: UUID):
    calendar = get_object_or_404(Calendar, owner=request.user, uuid=uuid)
    search_query = request.GET.get("search", "")

    hebrew_dates = calendar.calendarOf.all()
    if search_query:
        hebrew_dates = hebrew_dates.filter(name__icontains=search_query)

    today = timezone.localdate()
    upcoming = []
    for hebrew_date in hebrew_dates:
        english_dates = hebrew_date.get_english_dates() or []
        next_date = next(
            (english_date for english_date in english_dates if english_date >= today),
            None,
        )
        upcoming.append((next_date, hebrew_date))
    upcoming.sort(key=lambda pair: pair[0] or date.max)

    context = {
        "calendar": calendar,
        "hebrew_dates": upcoming,
        "search_query": search_query,
    }
    logger.info(
        "user: %s accessed calendar_edit_view for calendar: %s (%s)",
        request.user,
        calendar.name,
        calendar.uuid,
    )
    return render(request, "hebcal/calendar_edit.html", context)


def hebrew_date_form_view(request: HttpRequest, uuid: UUID, pk: int | None = None):
    calendar = get_object_or_404(Calendar, owner=request.user, uuid=uuid)
    hebrew_date = None
    if pk is not None:
        hebrew_date = get_object_or_404(HebrewDate, calendar=calendar, pk=pk)

    if request.method == "POST":
        form = HebrewDateForm(request.POST, instance=hebrew_date)
        if form.is_valid():
            saved = form.save(commit=False)
            saved.calendar = calendar
            saved.save()
            logger.info(
                "user: %s saved HebrewDate: %s (%s)",
                request.user,
                saved.name,
                saved.pk,
            )
            if hebrew_date is None:
                messages.success(request, f"Added {saved.get_formatted_name()}.")
            else:
                messages.success(request, f"Saved {saved.get_formatted_name()}.")
            if "add_another" in request.POST:
                return redirect("hebcal:hebrew_date_new", uuid=calendar.uuid)
            return redirect("hebcal:calendar_edit", uuid=calendar.uuid)
    else:
        initial: dict[str, object] = {
            field: request.GET[field]
            for field in ("name", "event_type", "day", "month")
            if field in request.GET
        }
        from_english = hebrew_date_from_english_input(
            request.GET.get("english_date", ""),
            after_sunset="after_sunset" in request.GET,
        )
        if from_english:
            month, day = from_english
            initial.update({"month": month, "day": day})
        form = HebrewDateForm(instance=hebrew_date, initial=initial)

    context = {
        "calendar": calendar,
        "hebrew_date": hebrew_date,
        "form": form,
        "english_date": request.GET.get("english_date", ""),
        "after_sunset": "after_sunset" in request.GET,
    }
    return render(request, "hebcal/hebrew_date_form.html", context)


@require_POST
@requires_htmx
def delete_hebrew_date_htmx(request: HttpRequest, uuid: UUID, pk: int):
    calendar = get_object_or_404(Calendar, owner=request.user, uuid=uuid)
    hebrew_date = get_object_or_404(HebrewDate, calendar=calendar, pk=pk)
    formatted_name = hebrew_date.get_formatted_name()
    hebrew_date.delete()
    logger.info(
        "user: %s deleted HebrewDate: %s (%s)",
        request.user,
        hebrew_date.name,
        pk,
    )
    messages.success(request, f"Removed {formatted_name}.")
    return HttpResponse()


class CalendarDeleteView(LoginRequiredMixin, DeleteView):
    model = Calendar
    success_url = reverse_lazy("hebcal:calendar_list")
    login_url = reverse_lazy("users:redirect")
    template_name = "hebcal/calendar_delete.html"
    object: Calendar  # type annotation for the object
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        return Calendar.objects.filter(owner=cast("User", self.request.user))


def client_ip(request: HttpRequest) -> str | None:
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]
    return request.META.get("REMOTE_ADDR")


def serve_pixel(request, pixel_id: UUID, pk: int):
    pixel_data = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+h"
        "HgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    )

    ip = client_ip(request)
    user_agent = request.headers.get("user-agent", "")

    # Log the information along with the UUID
    logger.info(
        "Pixel requested. IP: %s, User Agent: %s, UUID: %s, PK: %s",
        ip,
        user_agent,
        str(pixel_id),
        str(pk),
    )

    return HttpResponse(base64.b64decode(pixel_data), content_type="image/png")


@cache_page(60 * 60)
def calendar_file(request, uuid: UUID):
    ip = client_ip(request)
    user_agent = request.headers.get("user-agent", "")
    alarm_trigger_hours = request.GET.get("alarm") or "9"
    try:
        alarm_trigger = timedelta(hours=int(alarm_trigger_hours))
    except ValueError:
        logger.warning("Invalid alarm trigger value: %s", alarm_trigger_hours)
        alarm_trigger = timedelta(hours=9)

    calendar: Calendar = get_object_or_404(
        Calendar.objects.filter(uuid=uuid).prefetch_related("calendarOf"),
    )

    logger.info(
        "Calendar file requested for %s with ip %s User-Agent %s, Alarm: %s",
        calendar.name,
        ip,
        user_agent,
        alarm_trigger,
    )
    experimental = request.GET.get("experimental", False)
    if experimental:
        calendar_str = generate_ical_experimental(
            model_calendar=calendar,
            user_agent=user_agent,
            alarm_trigger=alarm_trigger,
        )
    else:
        calendar_str = generate_ical(
            model_calendar=calendar,
            user_agent=user_agent,
            alarm_trigger=alarm_trigger,
        )

    response = HttpResponse(calendar_str, content_type="text/calendar")
    response["Content-Disposition"] = f'attachment; filename="{uuid}.ics"'

    return response


@requires_htmx
def update_calendar_links_htmx(request: HttpRequest, uuid: UUID):
    alarm_time = request.GET.get("alarm", "9")  # Default to 9 AM

    # Fetch the specific calendar by UUID
    calendar = get_object_or_404(Calendar, uuid=uuid)
    domain_name = Site.objects.get_current().domain

    context = {
        "calendar": calendar,
        "domain_name": domain_name,
        "alarm_time": alarm_time,
    }
    messages.success(request, "Calendar alarm set to " + alarm_time)
    logger.info(
        "update_calendar_links_htmx: %s for calendar: %s (%s)",
        request.user,
        calendar.name,
        calendar.uuid,
    )

    return render(request, "hebcal/_calendar_links.html", context)
