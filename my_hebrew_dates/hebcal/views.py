from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.models import Site
from django.forms import inlineformset_factory
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic.edit import DeleteView

from .forms import CalendarForm, HebrewDateForm
from .models import Calendar, HebrewDate
from .utils import generate_ical


class CalendarDeleteView(LoginRequiredMixin, DeleteView):
    model = Calendar
    success_url = reverse_lazy("calendars:calendar_list")
    login_url = reverse_lazy("login")
    template_name = "calendars/calendar_confirm_delete.html"


@login_required
def calendar_list(request):
    if request.method == "POST" and "delete" in request.POST:
        calendar_id = request.POST.get("calendar_id")
        calendar = get_object_or_404(Calendar, id=calendar_id)
        if calendar.owner == request.user:
            calendar.delete()
            return redirect("hebcal:calendar_list")

    if request.method == "POST":
        form = CalendarForm(request.POST)
        if form.is_valid():
            calendar = form.save(commit=False)
            calendar.owner = request.user
            calendar.save()
            return redirect(calendar.get_absolute_url())
    else:
        calendars = Calendar.objects.filter(owner=request.user)
        form = CalendarForm()
    context = {
        "calendars": calendars,
        "form": form,
        "domain_name": Site.objects.get_current().domain,
    }

    return render(request, "hebcal/calendar_list.html", context)


@login_required
def calendar_detail(request, pk):
    calendar = get_object_or_404(Calendar, pk=pk, owner=request.user)

    # Create an inline formset for editing Hebrew dates
    HebrewDateInlineFormSet = inlineformset_factory(Calendar, HebrewDate, form=HebrewDateForm, extra=1)

    if request.method == "POST":
        calendar_form = CalendarForm(request.POST, instance=calendar)
        hebrew_date_formset = HebrewDateInlineFormSet(request.POST, instance=calendar)
        if calendar_form.is_valid() and hebrew_date_formset.is_valid():
            calendar_form.save()
            hebrew_date_formset.save()
    else:
        calendar_form = CalendarForm(instance=calendar)
        hebrew_date_formset = HebrewDateInlineFormSet(instance=calendar)

    return render(
        request,
        "hebcal/calendar_detail.html",
        {
            "calendar": calendar,
            "calendar_form": calendar_form,
            "hebrew_date_formset": hebrew_date_formset,
        },
    )


def calendar_file(request, uuid):
    calendar: Calendar = get_object_or_404(Calendar.objects.filter(uuid=uuid))
    generate_ical(calendar)
    calendar_str: str = calendar.calendar_file_str

    response = HttpResponse(calendar_str, content_type="application/octet-stream")
    response["Content-Disposition"] = f'attachment; filename="{uuid}.ical"'

    return response
