import base64
import logging
from datetime import timedelta
from uuid import UUID

from discord import Embed
from discord import SyncWebhook
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.http import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_POST
from django.views.generic.edit import DeleteView
from django_htmx_modal_forms import HtmxModalUpdateView

from my_hebrew_dates.hebcal.decorators import requires_htmx
from my_hebrew_dates.hebcal.forms import CalendarForm
from my_hebrew_dates.hebcal.forms import HebrewDateForm
from my_hebrew_dates.hebcal.forms import WebhookInterestForm
from my_hebrew_dates.hebcal.models import Calendar
from my_hebrew_dates.hebcal.models import HebrewDate
from my_hebrew_dates.hebcal.models import HebrewDayEnum
from my_hebrew_dates.hebcal.models import HebrewMonthEnum
from my_hebrew_dates.hebcal.utils import generate_ical
from my_hebrew_dates.hebcal.utils import generate_ical_expirimental

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
    event_count = HebrewDate.objects.filter(calendar__in=user_owned_calendars).count()

    context = {
        "event_count": event_count,
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
        log_msg = (
            "user: %s attempted to create a calendar with invalid form data. ",
            "Errors: %s",
        )
        logger.warning(
            log_msg,
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


class CalendarUpdateModalView(SuccessMessageMixin, HtmxModalUpdateView):  # type: ignore[misc]
    model = Calendar
    modal_size = "md"
    form_class = CalendarForm
    detail_template_name = "hebcal/_calendar_name.html"
    success_message = "Calendar updated successfully"


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
    day_desc = sort_by == "day" and order == "desc"
    month_desc = sort_by == "month" and order == "desc"

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
        "day_desc": day_desc,
        "month_desc": month_desc,
    }

    logger.info(
        "user: %s accessed calendar_edit_view for calendar: %s (%s)",
        request.user,
        calendar.name,
        calendar.uuid,
    )

    if hasattr(request, "htmx") and request.htmx:
        log_msg = "search_query: %s | Month: %s | Day: %s | Sort: %s | Order: %s"
        logger.info(
            log_msg,
            search_query,
            month_values,
            day_values,
            sort_by,
            order,
        )
        return render(request, "hebcal/_calendar_table.html", context)
    return render(request, "hebcal/calendar_edit.html", context)


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
                "user: %s updated HebrewDate: %s (%s)",
                request.user,
                hebrew_date.name,
                pk,
            )
            messages.success(request, f"{hebrew_date.name} updated successfully.")

            return render(
                request,
                "hebcal/_hebrew_date_row.html",
                {"hebrew_date": hebrew_date},
            )
        log_msg = (
            "user: %s attempted to update HebrewDate: ",
            "%s (%s) with invalid form data. ",
        )
        logger.warning(
            log_msg,
            request.user,
            hebrew_date.name,
            pk,
            form.errors,
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
            "user: %s cancelled edit for HebrewDate: %s (%s)",
            request.user,
            hebrew_date.name,
            pk,
        )

        return render(
            request,
            "hebcal/_hebrew_date_row.html",
            {"hebrew_date": hebrew_date},
        )

    logger.info(
        "user: %s initialized edit for HebrewDate: %s (%s)",
        request.user,
        hebrew_date.name,
        pk,
    )

    return render(request, "hebcal/_hebrew_date_form.html", context)


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
                "user: %s created HebrewDate: %s (%s)",
                request.user,
                hebrew_date.name,
                hebrew_date.pk,
            )
            messages.success(request, f"{hebrew_date.name} created successfully.")

            return render(
                request,
                "hebcal/_hebrew_date_row.html",
                {"hebrew_date": hebrew_date},
            )
        messages.error(request, "Please correct the errors in the form.")
    else:
        form = HebrewDateForm()

    context = {
        "calendar": calendar,
        "form": form,
        "new": True,
    }

    logger.info(
        "user: %s initialized create for HebrewDate",
        request.user,
    )

    return render(request, "hebcal/_hebrew_date_form.html", context)


@require_POST
@requires_htmx
def delete_hebrew_date_htmx(request: HttpRequest, uuid: UUID, pk: int):
    calendar = get_object_or_404(Calendar, owner=request.user, uuid=uuid)
    hebrew_date = get_object_or_404(HebrewDate, calendar=calendar, pk=pk)
    formatted_name = hebrew_date.get_formatted_name()

    if request.method == "POST":
        hebrew_date.delete()
        logger.info(
            "user: %s deleted HebrewDate: %s (%s)",
            request.user,
            hebrew_date.name,
            pk,
        )
        messages.success(request, f"{formatted_name} deleted successfully.")
        return HttpResponse()
    return None


class CalendarDeleteView(LoginRequiredMixin, DeleteView):
    model = Calendar
    success_url = reverse_lazy("hebcal:calendar_list")
    login_url = reverse_lazy("users:redirect")
    template_name = "hebcal/calendar_delete.html"
    object: Calendar  # type annotation for the object
    slug_field = "uuid"
    slug_url_kwarg = "uuid"


def serve_pixel(request, pixel_id: UUID, pk: int):
    pixel_data = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+h"
        "HgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    )

    x_forwarded_for = request.headers.get("x-forwarded-for")
    ip = (
        x_forwarded_for.split(",")[0]
        if x_forwarded_for
        else request.META.get("REMOTE_ADDR")
    )
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


@cache_page(60 * 60)  # Cache the page for 15 minutes
def calendar_file(request, uuid: UUID):
    x_forwarded_for = request.headers.get("x-forwarded-for")
    ip = (
        x_forwarded_for.split(",")[0]
        if x_forwarded_for
        else request.META.get("REMOTE_ADDR")
    )
    user_agent = request.headers.get("user-agent", "")
    alarm_trigger_hours = request.GET.get("alarm", "9")
    if alarm_trigger_hours == "":
        alarm_trigger_hours = "9"
    try:
        alarm_trigger = timedelta(hours=int(alarm_trigger_hours))
    except ValueError:
        logger.warning("Invalid alarm trigger value: %s", alarm_trigger_hours)
        alarm_trigger = timedelta(hours=9)

    calendar: Calendar = get_object_or_404(Calendar.objects.filter(uuid=uuid))

    if alarm_trigger_hours != "9":
        logger.info(
            "Calendar file requested for %s with ip %s User-Agent %s, Alarm: %s",
            calendar.name,
            ip,
            user_agent,
            alarm_trigger,
        )
    expirimental = request.GET.get("expirimental", False)
    if expirimental:
        calendar_str = generate_ical_expirimental(
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


def webhook_interest(request):
    if request.method == "POST":
        logger.info("Webhook Interest form submitted")
        form = WebhookInterestForm(request.POST)
        if form.is_valid():
            webhook_url = settings.DISCORD_WEBHOOK_URL
            webhook = SyncWebhook.from_url(webhook_url)

            embed = Embed(
                title="New Hebrew Calendar Webhook Beta Sign-up",
                color=0x00FF00,
            )
            for field, value in form.cleaned_data.items():
                embed.add_field(name=field.capitalize(), value=value, inline=False)

            webhook.send(embed=embed)
            # Send email to user
            user_email = form.cleaned_data.get("email")
            msg = f"""
                Dear {form.cleaned_data.get('name')},

                Thank you for your interest in the Hebrew Calendar Webhook Beta.
                We've received your sign-up and will keep you updated on our progress.

                Best regards,
                The My Hebrew Dates Team
            """
            send_mail(
                subject="Thank you for your interest in Hebrew Calendar Webhook Beta",
                message=msg,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email] if user_email else [],
                fail_silently=False,
            )

            messages.success(
                request,
                "Form submitted successfully. We've sent you a confirmation email.",
            )
            return redirect("webhook_interest")

    else:
        logger.info("Webhook Interest form accessed")
        form = WebhookInterestForm()

    return render(request, "hebcal/webhook_interest.html", {"form": form})
