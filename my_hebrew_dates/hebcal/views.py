import base64
import logging
from datetime import timedelta
from uuid import UUID

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.models import Site
from django.http import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_POST
from django.views.generic.edit import DeleteView

from my_hebrew_dates.hebcal.decorators import requires_htmx
from my_hebrew_dates.hebcal.forms import CalendarForm, HebrewDateForm
from my_hebrew_dates.hebcal.models import Calendar, HebrewDate, HebrewDayEnum, HebrewMonthEnum
from my_hebrew_dates.hebcal.utils import generate_ical

# Setup logger
logger = logging.getLogger(__name__)


@login_required
def calendar_list_view(request):
    user_owned_calendars = Calendar.objects.filter(owner=request.user)

    if not user_owned_calendars.exists():
        logger.info(f"{calendar_list_view.__name__}: {request.user} has no calendars. Redirecting to create calendar.")
        return redirect("hebcal:calendar_new")

    logger.info(f"{calendar_list_view.__name__}: {request.user} with calendars: {user_owned_calendars}")

    context = {"calendar_list": user_owned_calendars, "domain_name": Site.objects.get_current().domain}

    return render(request, "hebcal/calendar_list.html", context)


def calendar_detail_view(request: HttpRequest, uuid: UUID):
    calendar = get_object_or_404(Calendar, uuid=uuid)

    context = {
        "calendar": calendar,
        "domain_name": Site.objects.get_current().domain,
    }
    logger.info(
        f"{calendar_detail_view.__name__}: {request.user} for calendar: {calendar.name} ({calendar.uuid})",
    )

    return render(request, "hebcal/calendar_detail.html", context)


@login_required
def create_calendar_view(request: HttpRequest):
    if request.method == "POST":
        form = CalendarForm(request.POST)
        if form.is_valid():
            calendar = form.save(commit=False)
            calendar.owner = request.user
            calendar.save()
            messages.success(request, f"{calendar.name} created successfully.")
            logger.info(
                f"{create_calendar_view.__name__}: {request.user} created Calendar: {calendar.name} ({calendar.uuid})",
            )
            return redirect("hebcal:calendar_edit", uuid=calendar.uuid)
        else:
            messages.error(request, "Please correct the errors in the form.")
            logger.warning(
                f"{create_calendar_view.__name__}: {request.user} Error in form submission. Errors: {form.errors}"
            )
    else:
        form = CalendarForm()

    context = {
        "form": form,
    }
    logger.info(f"{create_calendar_view.__name__}: {request.user} accessed Calendar_create_view.")

    return render(request, "hebcal/calendar_new.html", context)


@login_required
def calendar_edit_view(request: HttpRequest, uuid: UUID):
    calendar = get_object_or_404(Calendar, owner=request.user, uuid=uuid)
    month_values = request.GET.getlist("month")
    day_values = request.GET.getlist("day")
    search_query = request.GET.get("search", None)
    event_type = request.GET.get("event_type", None)

    month_choices = HebrewMonthEnum.choices
    day_choices = HebrewDayEnum.choices
    event_choices = HebrewDate.EVENT_CHOICES

    sort_by = request.GET.get("sort", "day")
    order = request.GET.get("order", "asc")

    # Determine if current sort is descending
    dayDesc = sort_by == "day" and order == "desc"
    monthDesc = sort_by == "month" and order == "desc"

    # Apply sorting to your queryset
    sort_order = f"-{sort_by}" if order == "desc" else sort_by
    hebrew_dates = calendar.calendarOf.all().order_by(sort_order)

    # Filter by month if provided
    if "month" in request.GET:
        hebrew_dates = hebrew_dates.filter(month__in=month_values)

    # Filter by day if provided
    if "day" in request.GET:
        hebrew_dates = hebrew_dates.filter(day__in=day_values)

    # Additional filters can be added similarly
    if search_query:
        hebrew_dates = hebrew_dates.filter(name__icontains=search_query)

    if event_type:
        hebrew_dates = hebrew_dates.filter(event_type=event_type)

    context = {
        "calendar": calendar,
        "month_choices": month_choices,
        "day_choices": day_choices,
        "event_choices": event_choices,
        "hebrew_dates": hebrew_dates,
        "selected_months": month_values,
        "selected_days": day_values,
        "dayDesc": dayDesc,
        "monthDesc": monthDesc,
    }

    logger.info(f"{calendar_edit_view.__name__}: {request.user} for calendar: {calendar.name} ({calendar.uuid})")

    if request.htmx:
        logger.info(
            f"Search query: {search_query} | Month values: {month_values} | Day values: {day_values} | Sort: {sort_by} | Order: {order}",  # noqa E501
        )
        return render(request, "hebcal/_calendar_table.html", context)
    return render(request, "hebcal/calendar_edit.html", context)


@login_required
@requires_htmx
def edit_hebrew_date_htmx(request: HttpRequest, uuid: UUID, pk: int):
    calendar = get_object_or_404(Calendar, owner=request.user, uuid=uuid)
    hebrew_date = get_object_or_404(HebrewDate, calendar=calendar, pk=pk)
    cancel = request.GET.get("cancel", False)

    if request.method == "POST":
        form = HebrewDateForm(request.POST, instance=hebrew_date)
        if form.is_valid():
            form.save()
            logger.info(
                f"{edit_hebrew_date_htmx.__name__}: {request.user} HebrewDate updated: {hebrew_date.name} ({pk})"
            )
            return render(request, "hebcal/_hebrew_date_row.html", {"hebrew_date": hebrew_date})
        else:
            logger.warning(
                f"{edit_hebrew_date_htmx.__name__}: {request.user} Error in form submission. Errors: {form.errors}",
            )
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = HebrewDateForm(instance=hebrew_date)

    context = {
        "calendar": calendar,
        "hebrew_date": hebrew_date,
        "form": form,
    }
    if cancel:
        logger.info(
            f"{edit_hebrew_date_htmx.__name__}: {request.user} HebrewDate edit cancelled: {hebrew_date.name} ({pk})"
        )
        return render(request, "hebcal/_hebrew_date_row.html", {"hebrew_date": hebrew_date})

    logger.info(
        f"{edit_hebrew_date_htmx.__name__}: {request.user} HebrewDate edit initialized: {hebrew_date.name} ({pk})"
    )
    return render(request, "hebcal/_hebrew_date_form.html", context)


@login_required
@requires_htmx
def create_hebrew_date_htmx(request: HttpRequest, uuid: UUID):
    calendar = get_object_or_404(Calendar, owner=request.user, uuid=uuid)

    if request.method == "POST":
        form = HebrewDateForm(request.POST)
        if form.is_valid():
            hebrew_date = form.save(commit=False)
            hebrew_date.calendar = calendar
            hebrew_date.save()
            logger.info(
                f"{create_hebrew_date_htmx.__name__}: {request.user} HebrewDate created: {hebrew_date.name} ({hebrew_date.pk})"  # noqa E501
            )
            return render(request, "hebcal/_hebrew_date_row.html", {"hebrew_date": hebrew_date})
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = HebrewDateForm()

    context = {
        "calendar": calendar,
        "form": form,
        "new": True,
    }

    logger.info(f"{create_hebrew_date_htmx.__name__}: {request.user} HebrewDate create initialized.")
    return render(request, "hebcal/_hebrew_date_form.html", context)


@login_required
@require_POST
@requires_htmx
def delete_hebrew_date_htmx(request: HttpRequest, uuid: UUID, pk: int):
    calendar = get_object_or_404(Calendar, owner=request.user, uuid=uuid)
    hebrew_date = get_object_or_404(HebrewDate, calendar=calendar, pk=pk)
    formatted_name = hebrew_date.get_formatted_name()

    if request.method == "POST":
        hebrew_date.delete()
        logger.info(f"{delete_hebrew_date_htmx.__name__}: {request.user} HebrewDate deleted: {formatted_name} ({pk})")
        messages.success(request, f"{formatted_name} deleted successfully.")
        return HttpResponse()


class CalendarDeleteView(LoginRequiredMixin, DeleteView):
    model = Calendar
    success_url = reverse_lazy("hebcal:calendar_list")
    login_url = reverse_lazy("users:redirect")
    template_name = "hebcal/calendar_delete.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"


def serve_pixel(request, pixel_id: UUID, pk: int):
    pixel_data = b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

    x_forwarded_for = request.headers.get("x-forwarded-for")
    ip = x_forwarded_for.split(",")[0] if x_forwarded_for else request.META.get("REMOTE_ADDR")
    user_agent = request.headers.get("user-agent", "")

    # Log the information along with the UUID
    logger.info("Pixel requested. IP: %s, User Agent: %s, UUID: %s, PK: %s", ip, user_agent, str(pixel_id), str(pk))

    return HttpResponse(base64.b64decode(pixel_data), content_type="image/png")


@cache_page(60 * 60)  # Cache the page for 15 minutes
def calendar_file(request, uuid: UUID):
    # user = request.user
    # user_info = "Anonymous user"
    # ip = request.META.get("REMOTE_ADDR", "Unknown IP")

    x_forwarded_for = request.headers.get("x-forwarded-for")
    ip = x_forwarded_for.split(",")[0] if x_forwarded_for else request.META.get("REMOTE_ADDR")
    user_agent = request.headers.get("user-agent", "")
    alarm_trigger_hours = request.GET.get("alarm", "9")
    if alarm_trigger_hours == "":
        alarm_trigger_hours = "9"
    print(alarm_trigger_hours)
    try:
        alarm_trigger = timedelta(hours=int(alarm_trigger_hours))
    except ValueError:
        logger.warning(f"Invalid alarm trigger value: {alarm_trigger_hours}")
        alarm_trigger = timedelta(hours=9)

    # if user.is_authenticated:
    #    user_info = f"user_id: {user.id}, username: {user.username}, email: {user.email}"
    calendar: Calendar = get_object_or_404(Calendar.objects.filter(uuid=uuid))

    if alarm_trigger_hours != "9":
        logger.info(
            f"Calendar file requested for {calendar.name} with ip {ip} User-Agent {user_agent}, Alarm: {alarm_trigger}"
        )
    else:
        logger.info(f"Calendar file requested for {calendar.name} with ip {ip} User-Agent {user_agent}")

    # logger.info(
    #    "calendar_file function called for uuid: %s by %s, IP: %s, User-Agent: %s", uuid, user_info, ip, user_agent
    # )

    calendar_str: str = generate_ical(modelCalendar=calendar, user_agent=user_agent, alarm_trigger=alarm_trigger)

    response = HttpResponse(calendar_str, content_type="text/calendar")
    response["Content-Disposition"] = f'attachment; filename="{uuid}.ics"'  # noqa E702

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
    logger.info(
        f"{update_calendar_links_htmx.__name__}: {request.user} for calendar: {calendar.name} ({calendar.uuid})"
    )
    return render(request, "hebcal/_calendar_links.html", context)
