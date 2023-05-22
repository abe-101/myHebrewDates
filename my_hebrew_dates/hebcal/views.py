from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.models import Site
from django.db import transaction
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from .forms import HebrewDateFormSet
from .models import Calendar
from .utils import generate_ical


class CalendarListView(LoginRequiredMixin, ListView):
    model = Calendar
    login_url = reverse_lazy("login")
    template_name = "hebcal/calendar_list.html"


class CalendarCreateView(LoginRequiredMixin, CreateView):
    model = Calendar
    login_url = reverse_lazy("login")
    template_name = "hebcal/calendar_detail.html"
    fields = ["name", "timezone"]

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
            self.object = form.save()

            if hebrewDates.is_valid():
                hebrewDates.instance = self.object
                hebrewDates.save()
        return super().form_valid(form)


class CalendarUpdateView(LoginRequiredMixin, UpdateView):
    model = Calendar
    login_url = reverse_lazy("login")
    template_name = "hebcal/calendar_detail.html"
    fields = ["name", "timezone"]

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
            self.object = form.save()

            if hebrewDates.is_valid():
                hebrewDates.instance = self.object
                hebrewDates.save()
        return super().form_valid(form)


class CalendarDeleteView(LoginRequiredMixin, DeleteView):
    model = Calendar
    success_url = reverse_lazy("hebcal:calendar_list")
    login_url = reverse_lazy("login")
    template_name = "hebcal/calendar_delete.html"


def calendar_file(request, uuid):
    calendar: Calendar = get_object_or_404(Calendar.objects.filter(uuid=uuid))
    generate_ical(calendar)
    calendar_str: str = calendar.calendar_file_str

    response = HttpResponse(calendar_str, content_type="application/octet-stream")
    response["Content-Disposition"] = f'attachment; filename="{uuid}.ical"'

    return response
