from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML
from crispy_forms.layout import Div
from crispy_forms.layout import Field
from crispy_forms.layout import Layout
from django import forms

from .models import Calendar
from .models import HebrewDate


class CalendarForm(forms.ModelForm):
    class Meta:
        model = Calendar
        fields = ["name", "timezone"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class HebrewDateForm(forms.ModelForm):
    class Meta:
        model = HebrewDate
        fields = ["name", "month", "day", "event_type"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.label_class = "form-label small fw-semibold mb-1"

        self.fields["name"].label = "Name"
        self.fields["name"].widget.attrs["placeholder"] = "e.g. Grandma Sarah"
        self.fields["day"].label = "Hebrew Day"
        self.fields["month"].label = "Hebrew Month"
        self.fields["event_type"].label = "Event Type"

        button_div = Div(
            StrictButton(
                '<i class="bi bi-check-lg"></i>'
                '<span class="visually-hidden">Save</span>',
                type="submit",
                css_class="btn btn-success",
                title="Save",
            ),
            css_class="d-flex gap-1",
        )

        if self.instance and self.instance.pk:
            # Cancel editing: swap the row back to its display state
            cancel_button = HTML(
                '<button type="button" class="btn btn-outline-secondary" title="Cancel" aria-label="Cancel" hx-get="{% url \'hebcal:edit_hebrew_date_htmx\' uuid=hebrew_date.calendar.uuid pk=hebrew_date.pk %}?cancel=True" hx-target="closest tr" hx-swap="outerHTML settle:1s"><i class="bi bi-x-lg"></i></button>',  # noqa: E501
            )
        else:
            # Cancel adding: the row only exists client-side, just remove it
            cancel_button = HTML(
                '<button type="button" class="btn btn-outline-secondary" title="Cancel" aria-label="Cancel" onclick="this.closest(\'tr\').remove()"><i class="bi bi-x-lg"></i></button>',  # noqa: E501
            )
        button_div.append(cancel_button)

        self.helper.layout = Layout(
            Div(
                Div(Field("name", wrapper_class="mb-0"), css_class="col-12 col-md-4"),
                Div(Field("day", wrapper_class="mb-0"), css_class="col-6 col-md-2"),
                Div(Field("month", wrapper_class="mb-0"), css_class="col-6 col-md-3"),
                Div(
                    Field("event_type", wrapper_class="mb-0"),
                    css_class="col-8 col-md-2",
                ),
                Div(button_div, css_class="col-4 col-md-1 d-flex align-items-end"),
                css_class="row g-2 align-items-end",
            ),
        )
