from datetime import datetime, timedelta

import icalendar
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.models import Site
from django.db import transaction
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy

# from django.utils.decorators import method_decorator
# from django.views.decorators.cache import cache_page
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from .forms import HebrewDateFormSet
from .models import Calendar
from .utils import generate_ical


class CalendarListView(LoginRequiredMixin, ListView):
    model = Calendar
    login_url = reverse_lazy("login")
    template_name = "hebcal/calendar_list.html"

    def get_queryset(self):
        # Retrieve the calendars belonging to the current user
        queryset = super().get_queryset()
        return queryset.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        # Call the parent implementation to get the default context
        context = super().get_context_data(**kwargs)
        # Add the domain_name to the context
        context["domain_name"] = Site.objects.get_current().domain

        return context


class CalendarShareView(DetailView):
    model = Calendar
    template_name = "hebcal/calendar_share.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    # @method_decorator(cache_page(60 * 15))  # Cache the dispatch method for 15 minutes
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        # Retrieve the calendar by uuid
        queryset = self.get_queryset()
        return queryset.filter(uuid=self.kwargs["uuid"]).first()

    def get_context_data(self, **kwargs):
        # Call the parent implementation to get the default context
        context = super().get_context_data(**kwargs)
        # Add the domain_name to the context
        context["domain_name"] = Site.objects.get_current().domain
        cal = icalendar.Calendar.from_ical(self.object.calendar_file_str)
        # Get the current date
        current_date = datetime.now().date()

        # Calculate the date range for the events (from current date to one year from now)
        one_year_from_now = current_date + timedelta(days=365)

        events = []
        for component in cal.walk():
            if component.name == "VEVENT":
                event = {
                    "summary": component.get("summary"),
                    "description": component.get("description")[:-37],
                    "start": component.get("dtstart").dt,
                    "end": component.get("dtend").dt,
                }
                if current_date <= event["start"] <= one_year_from_now:
                    events.append(event)

        # Sort events by start date and time
        events.sort(key=lambda e: e["start"])
        context["events"] = events

        return context


class CalendarCreateView(LoginRequiredMixin, CreateView):
    model = Calendar
    login_url = reverse_lazy("login")
    template_name = "hebcal/calendar_detail.html"
    fields = ["name"]

    def get_queryset(self):
        # Retrieve the calendars belonging to the current user
        queryset = super().get_queryset()
        return queryset.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data["hebrewDates"] = HebrewDateFormSet(self.request.POST)
        else:
            data["hebrewDates"] = HebrewDateFormSet()
        data["domain_name"] = Site.objects.get_current().domain
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        hebrewDates = context["hebrewDates"]
        with transaction.atomic():
            self.object = form.save(commit=False)
            self.object.owner = self.request.user  # Set the owner field
            self.object.save()

            if hebrewDates.is_valid():
                hebrewDates.instance = self.object
                hebrewDates.save()
            else:
                # Display error messages and rerender the form with user data
                messages.error(self.request, "Please correct the errors in the form.")
                return self.render_to_response(self.get_context_data(form=form))

        generate_ical(self.object)
        messages.success(self.request, "Calendar created successfully.")
        return super().form_valid(form)


class CalendarUpdateView(LoginRequiredMixin, UpdateView):
    model = Calendar
    login_url = reverse_lazy("login")
    template_name = "hebcal/calendar_detail.html"
    fields = ["name"]

    def get_queryset(self):
        # Retrieve the calendars belonging to the current user
        queryset = super().get_queryset()
        return queryset.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data["hebrewDates"] = HebrewDateFormSet(self.request.POST, instance=self.object)
        else:
            data["hebrewDates"] = HebrewDateFormSet(instance=self.object)
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        hebrewDates = context["hebrewDates"]
        with transaction.atomic():
            self.object = form.save(commit=False)
            self.object.owner = self.request.user  # Set the owner field
            self.object.save()

            if hebrewDates.is_valid():
                hebrewDates.instance = self.object
                hebrewDates.save()
            else:
                # Display error messages and rerender the form with user data
                messages.error(self.request, "Please correct the errors in the form.")
                return self.render_to_response(self.get_context_data(form=form))

        generate_ical(self.object)
        messages.success(self.request, "Calendar updated successfully.")
        return super().form_valid(form)


class HebrewDateForm(UpdateView):
    model = Calendar
    template_name = "hebcal/hebrewdate_form.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    fields = []

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        # Retrieve the calendar by uuid
        queryset = self.get_queryset()
        return queryset.filter(uuid=self.kwargs["uuid"]).first()

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data["hebrewDates"] = HebrewDateFormSet(self.request.POST, instance=self.object)
        else:
            data["hebrewDates"] = HebrewDateFormSet()
        return data

    def get_success_url(self):
        # Replace with your success URL logic
        return reverse("hebcal:calendar_share", kwargs={"uuid": self.kwargs.get("uuid")})

    def form_valid(self, form):
        context = self.get_context_data()
        hebrewDates = context["hebrewDates"]
        with transaction.atomic():
            self.object = form.save(commit=False)
            # self.object.owner = self.request.user  # Set the owner field
            self.object.save()

            if hebrewDates.is_valid():
                hebrewDates.instance = self.object
                hebrewDates.save()
            else:
                # Display error messages and rerender the form with user data
                messages.error(self.request, "Please correct the errors in the form.")
                return self.render_to_response(self.get_context_data(form=form))

        generate_ical(self.object)
        messages.success(self.request, "Calendar updated successfully.")
        return super().form_valid(form)


class CalendarDeleteView(LoginRequiredMixin, DeleteView):
    model = Calendar
    success_url = reverse_lazy("hebcal:calendar_list")
    login_url = reverse_lazy("login")
    template_name = "hebcal/calendar_delete.html"


# @cache_page(60 * 15)  # Cache the page for 15 minutes
def calendar_file(request, uuid):
    calendar: Calendar = get_object_or_404(Calendar.objects.filter(uuid=uuid))
    generate_ical(calendar)
    calendar_str: str = calendar.calendar_file_str

    response = HttpResponse(calendar_str, content_type="text/calendar")
    response["Content-Disposition"] = f'attachment; filename="{uuid}.ics"'

    return response
