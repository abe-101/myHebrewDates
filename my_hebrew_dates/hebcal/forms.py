from crispy_forms.bootstrap import InlineField
from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML
from crispy_forms.layout import Div
from crispy_forms.layout import Layout
from crispy_forms.layout import Row
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


class HebrewDateForm(forms.ModelForm):
    class Meta:
        model = HebrewDate
        fields = ["name", "month", "day", "event_type"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.form_class = "form-inline"

        button_div = Div(
            StrictButton(
                '<i class="bi bi-check-square"></i>',
                type="submit",
                css_class="btn btn-primary mb-0",
            ),
            css_class="d-flex",
        )

        # Conditionally add the delete button if the instance exists
        if self.instance and self.instance.pk:
            delete_button = HTML(
                '<button type="button" class="btn btn-danger mb-0 ms-1" hx-get="{% url \'hebcal:edit_hebrew_date_htmx\' uuid=hebrew_date.calendar.uuid pk=hebrew_date.pk %}?cancel=True" hx-target="closest tr" hx-swap="outerHTML settle:1s"><i class="bi bi-x-square"></i></button>',  # noqa: E501
            )
            # Append the delete button to the button div
            button_div.append(delete_button)

        # Define the full layout with all fields and the button div
        self.helper.layout = Layout(
            Row(
                Div(InlineField("name", css_class="mb-0"), css_class="col"),
                Div(InlineField("day", css_class="mb-0"), css_class="col"),
                Div(InlineField("month", css_class="mb-0"), css_class="col"),
                Div(InlineField("event_type", css_class="mb-0"), css_class="col"),
                Div(
                    button_div,
                    css_class="col",
                ),  # Place the button div in its own column
                css_class="d-flex justify-content-center",
            ),
        )

        self.helper.form_show_labels = False
