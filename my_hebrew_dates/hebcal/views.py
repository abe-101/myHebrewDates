import base64
import logging
from datetime import timedelta
from uuid import UUID

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.models import Site
from django.db import transaction
from django.http import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

# from django.utils.decorators import method_decorator
# from django.views.decorators.cache import cache_page
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from my_hebrew_dates.hebcal.decorators import requires_htmx
from my_hebrew_dates.hebcal.forms import CalendarForm, HebrewDateForm, HebrewDateFormSet
from my_hebrew_dates.hebcal.models import Calendar, HebrewDate, HebrewDayEnum, HebrewMonthEnum
from my_hebrew_dates.hebcal.utils import generate_ical

# Setup logger
logger = logging.getLogger(__name__)


class CalendarListView(LoginRequiredMixin, ListView):
    model = Calendar
    login_url = reverse_lazy("users:redirect")
    template_name = "hebcal/calendar_list.html"

    def get_queryset(self):
        # Retrieve the calendars belonging to the current user
        queryset = super().get_queryset()
        user_owned_calendars = queryset.filter(owner=self.request.user)

        logger.info(
            f"User {self.request.user} accessed CalendarListView. "
            f"Total calendars owned by user: {user_owned_calendars.count()}"
        )
        return user_owned_calendars

    def get_context_data(self, **kwargs):
        # Call the parent implementation to get the default context
        context = super().get_context_data(**kwargs)
        # Add the domain_name to the context
        context["domain_name"] = Site.objects.get_current().domain

        return context


class CalendarDetailView(DetailView):
    model = Calendar
    template_name = "hebcal/calendar_detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_context_data(self, **kwargs):
        # Call the parent implementation to get the default context
        context = super().get_context_data(**kwargs)

        # Log whether the user is authenticated or not
        if self.request.user.is_authenticated:
            logger.info(
                f"Authenticated user {self.request.user} accessed Calendar {self.object.uuid}: {self.object.name}"
            )
        else:
            logger.info(f"Unauthenticated user accessed calendar {self.object.uuid}: {self.object.name}")

        # Add the domain_name to the context
        context["domain_name"] = Site.objects.get_current().domain
        context["alarm_time"] = self.request.GET.get("alarm", "9")

        return context


class CalendarCreateView(LoginRequiredMixin, CreateView):
    model = Calendar
    login_url = reverse_lazy("users:redirect")
    template_name = "hebcal/calendar_edit.html"
    fields = ["name", "timezone"]

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data["hebrewDates"] = HebrewDateFormSet(self.request.POST)
            logger.info("HebrewDateFormSet initialized with POST data.")
        else:
            data["hebrewDates"] = HebrewDateFormSet()
            logger.info("New HebrewDateFormSet initialized.")
        data["domain_name"] = Site.objects.get_current().domain
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        hebrewDates = context["hebrewDates"]
        with transaction.atomic():
            self.object = form.save(commit=False)
            self.object.owner = self.request.user  # Set the owner field

            if hebrewDates.is_valid():
                self.object.save()
                hebrewDates.instance = self.object
                hebrewDates.save()
                logger.info(f"Calendar object saved: {self.object.uuid}, Owner: {self.request.user}")
            else:
                # Display error messages and rerender the form with user data
                messages.error(self.request, "Please correct the errors in the form.")
                logger.warning(f"Error in form submission by user: {self.request.user}. Errors: {hebrewDates.errors}")
                return self.render_to_response(self.get_context_data(form=form))

        generate_ical(self.object)
        logger.info(f"iCal generated for Calendar {self.object.uuid}: {self.object.name}")
        messages.success(self.request, "Calendar created successfully.")
        return super().form_valid(form)


@login_required
def create_calendar_view(request: HttpRequest):
    if request.method == "POST":
        form = CalendarForm(request.POST)
        if form.is_valid():
            calendar = form.save(commit=False)
            calendar.owner = request.user
            calendar.save()
            messages.success(request, "Calendar created successfully.")
            logger.info(
                f"Calendar created by user: {request.user} with UUID: {calendar.uuid} and name: {calendar.name}"
            )
            return redirect("hebcal:calendar_edit", uuid=calendar.uuid)
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = CalendarForm()

    context = {
        "form": form,
    }
    logger.info(f"New CalendarForm initialized by user: {request.user}")

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

    logger.info(f"Calendar edit view accessed by user: {request.user} for calendar: {calendar.name} ({calendar.uuid})")

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
            logger.info(f"HebrewDate object updated: {hebrew_date.pk}, Name: {hebrew_date.name}")
            messages.success(request, "Hebrew date updated successfully.")
            return render(request, "hebcal/_hebrew_date_row.html", {"hebrew_date": hebrew_date})
        else:
            logger.warning(f"Error in form submission by user: {request.user}. Errors: {form.errors}")
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = HebrewDateForm(instance=hebrew_date)

    context = {
        "calendar": calendar,
        "hebrew_date": hebrew_date,
        "form": form,
    }
    if cancel:
        logger.info(f"Edit HebrewDate cancelled by user: {request.user}")
        return render(request, "hebcal/_hebrew_date_row.html", {"hebrew_date": hebrew_date})

    logger.info(f"Edit HebrewDate form initialized by user: {request.user} for HebrewDate: {hebrew_date.name} ({pk})")
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
            logger.info(f"HebrewDate object created: {hebrew_date.pk}, Name: {hebrew_date.name}")
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

    logger.info(f"New HebrewDate form initialized by user: {request.user} for Calendar: {calendar.name} ({uuid})")
    return render(request, "hebcal/_hebrew_date_form.html", context)


@login_required
@requires_htmx
def delete_hebrew_date_htmx(request: HttpRequest, uuid: UUID, pk: int):
    calendar = get_object_or_404(Calendar, owner=request.user, uuid=uuid)
    hebrew_date = get_object_or_404(HebrewDate, calendar=calendar, pk=pk)

    if request.method == "POST":
        hebrew_date.delete()
        logger.info(f"HebrewDate object deleted: {hebrew_date.pk}, Name: {hebrew_date.name}")
        messages.success(request, "Hebrew date deleted successfully.")
        return HttpResponse()


class CalendarUpdateView(LoginRequiredMixin, UpdateView):
    model = Calendar
    login_url = reverse_lazy("users:redirect")
    template_name = "hebcal/calendar_edit.html"
    fields = ["name", "timezone"]
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data["hebrewDates"] = HebrewDateFormSet(self.request.POST, instance=self.object)
            logger.info("HebrewDateFormSet initialized with POST data.")
        else:
            data["hebrewDates"] = HebrewDateFormSet(instance=self.object)
            logger.info("New HebrewDateFormSet initialized.")
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        hebrewDates = context["hebrewDates"]
        with transaction.atomic():
            self.object = form.save(commit=False)
            self.object.owner = self.request.user  # Set the owner field

            if hebrewDates.is_valid():
                self.object.save()
                hebrewDates.instance = self.object
                hebrewDates.save()
                logger.info(
                    f"Calendar object updated: {self.object.uuid}, "
                    f"Owner={self.request.user}, "
                    f"Name={self.object.name}, "
                    f"Timezone={self.object.timezone}"
                )
            else:
                # Display error messages and rerender the form with user data
                messages.error(self.request, "Please correct the errors in the form.")
                logger.warning(f"Form submission error by user {self.request.user}: " f"{hebrewDates.errors}")
                return self.render_to_response(self.get_context_data(form=form))

        generate_ical(self.object)
        logger.info(f"iCal generated for Calendar: {self.object.uuid}")
        messages.success(self.request, "Calendar updated successfully.")
        return super().form_valid(form)


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


# @cache_page(60 * 15)  # Cache the page for 15 minutes
def calendar_file(request, uuid: UUID):
    # user = request.user
    # user_info = "Anonymous user"
    # ip = request.META.get("REMOTE_ADDR", "Unknown IP")

    x_forwarded_for = request.headers.get("x-forwarded-for")
    ip = x_forwarded_for.split(",")[0] if x_forwarded_for else request.META.get("REMOTE_ADDR")
    user_agent = request.headers.get("user-agent", "")
    alarm_trigger_hours = request.GET.get("alarm", "9")
    try:
        alarm_trigger = timedelta(hours=int(alarm_trigger_hours))
    except ValueError:
        logger.warning(f"Invalid alarm trigger value: {alarm_trigger_hours}")

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
    logger.info(f"Calendar links updated for {calendar.name} with alarm time {alarm_time}")
    return render(request, "hebcal/_calendar_links.html", context)


def calendar_detail_view(request: HttpRequest, uuid: UUID):
    calendar = get_object_or_404(Calendar, uuid=uuid)

    context = {
        "calendar": calendar,
    }
    logger.info(
        f"Calendar detail view accessed by user: {request.user} for calendar: {calendar.name} ({calendar.uuid})"
    )

    return render(request, "hebcal/calendar_detail.html", context)


# @login_required
# @requires_htmx
# def edit_calendar_htmx(request: HttpRequest, uuid: UUID):
#     # Fetch the specific calendar by UUID
#     calendar = get_object_or_404(Calendar, user=request.user, uuid=uuid: UUID)
#     form = CalendarForm2(request.POST or None, instance=calendar)
#     if request.method == "POST":
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Calendar updated successfully.")
#             return render(request, "hebcal/_calendar_detail.html", {"calendar": calendar})
#         else:
#             messages.error(request, "Please correct the errors in the form.")
#
#     context = {
#         "calendar": calendar,
#     }
#
#     return render(request, "hebcal/_calendar_edit_form.html", context)
