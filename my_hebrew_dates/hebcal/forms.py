from crispy_forms.bootstrap import Div, InlineField, StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Layout
from django import forms

from .models import Calendar, HebrewDate, HebrewDayEnum, HebrewMonthEnum


class CalendarForm(forms.ModelForm):
    class Meta:
        model = Calendar
        fields = ["name", "timezone"]
        labels = {
            "name": "Name",
            "timezone": "Timezone",
        }
        widgets = {
            "timezone": forms.Select(choices=Calendar.TIMEZONE_CHOICES),
        }


class OldHebrewDateForm(forms.ModelForm):
    class Meta:
        model = HebrewDate
        fields = ["name", "month", "day", "event_type"]
        widgets = {
            "month": forms.Select(choices=HebrewMonthEnum),
            "day": forms.Select(choices=HebrewDayEnum),
            "event_type": forms.Select(choices=HebrewDate.EVENT_CHOICES),
        }


class CalendarForm2(forms.ModelForm):
    class Meta:
        model = Calendar
        fields = ["name", "timezone"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "form-inline"
        self.helper.field_template = "bootstrap5/layout/inline_field.html"
        self.helper.layout = Layout(
            InlineField("name", wrapper_class="col-md-6"),
            InlineField("timezone", wrapper_class="col-md-6"),
            Div(
                StrictButton('<i class="bi bi-check-square"></i>', type="submit", css_class="btn btn-primary"),
                css_class="mt-3",
            ),
        )


class HebrewDateForm(forms.ModelForm):
    class Meta:
        model = HebrewDate
        fields = ["name", "month", "day", "event_type"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.form_class = "form-inline"
        # Start building the layout
        layout = [
            HTML("<td>"),
            InlineField("name", css_class="mb-0"),
            HTML("</td><td>"),
            InlineField("day", css_class="mb-0"),
            HTML("</td><td>"),
            InlineField("month", css_class="mb-0"),
            HTML("</td><td>"),
            InlineField("event_type", css_class="mb-0"),
            HTML("</td><td>"),
            StrictButton('<i class="bi bi-check-square"></i>', type="submit", css_class="btn btn-primary mb-0 ms-1"),
        ]

        # Add conditional element
        if self.instance and self.instance.pk:
            cancel_button = HTML(
                '<button type="button" class="btn btn-danger mb-0 ms-1" hx-get="{% url \'hebcal:edit_hebrew_date_htmx\' uuid=hebrew_date.calendar.uuid pk=hebrew_date.pk %}?cancel=True" hx-target="closest tr" hx-swap="outerHTML settle:1s"><i class="bi bi-x-square"></i></button>'  # noqa E501
            )
            layout.append(cancel_button)

        layout.append(HTML("</td>"))

        # Set the layout to the form helper
        self.helper.layout = Layout(*layout)
        self.helper.form_show_labels = False


HebrewDateFormSet = forms.inlineformset_factory(Calendar, HebrewDate, form=HebrewDateForm, extra=3)
