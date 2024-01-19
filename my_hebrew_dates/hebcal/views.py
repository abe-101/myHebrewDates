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
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy

# from django.utils.decorators import method_decorator
# from django.views.decorators.cache import cache_page
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from my_hebrew_dates.hebcal.forms import HebrewDateFormSet
from my_hebrew_dates.hebcal.models import Calendar, HebrewDate, HebrewDayEnum, HebrewMonthEnum

from .decorators import requires_htmx
from .utils import generate_ical

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

    # @method_decorator(cache_page(60 * 15))  # Cache the dispatch method for 15 minutes
    # def dispatch(self, request, *args, **kwargs):
    #    return super().dispatch(request, *args, **kwargs)

    # def get_object(self, queryset=None):
    #    # Retrieve the calendar by uuid
    #    queryset = self.get_queryset()
    #    return queryset.filter(uuid=self.kwargs["uuid"]).first()

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
        # cal = icalendar.Calendar.from_ical(generate_ical(self.object))
        # # Get the current date
        # current_date = datetime.now().date()

        # # Calculate the date range for the events (from current date to one year from now)
        # one_year_from_now = current_date + timedelta(days=395)

        # events = []
        # for component in cal.walk():
        #     if component.name == "VEVENT":
        #         event = {
        #             "summary": component.get("summary"),
        #             "description": component.get("description")[:-54],
        #             "start": component.get("dtstart").dt,
        #             "end": component.get("dtend").dt,
        #         }
        #         if current_date <= event["start"] <= one_year_from_now:
        #             events.append(event)

        # # Sort events by start date and time
        # events.sort(key=lambda e: e["start"])
        # context["events"] = events
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
def calendar_edit_view(request: HttpRequest, uuid: UUID):
    calendar = get_object_or_404(Calendar, owner=request.user, uuid=uuid)
    month_values = request.GET.getlist("month")
    day_values = request.GET.getlist("day")

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
    if request.POST:
        search_query = request.POST.get("search", "")
        hebrew_dates = hebrew_dates.filter(name__icontains=search_query)

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

    if request.htmx:
        return render(request, "hebcal/_calendar_table.html", context)
    return render(request, "hebcal/calendar_edit.html", context)


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
    return render(request, "hebcal/_calendar_links.html", context)


@login_required
def calendar_detail_view(request: HttpRequest, uuid: UUID):
    # Fetch the specific calendar by UUID
    calendar = get_object_or_404(Calendar, owner=request.user, uuid=uuid)

    # if request.HTMX:
    #     form = CalendarForm2(request.POST or None, instance=calendar)
    #     if request.method == "POST":
    #         if form.is_valid():
    #             form.save()
    #             messages.success(request, "Calendar updated successfully.")
    #             return render(request, "hebcal/_calendar_detail.html", {"calendar": calendar})
    #         else:
    #             messages.error(request, "Please correct the errors in the form.")

    context = {
        "calendar": calendar,
    }

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
