from crispy_forms.bootstrap import InlineField
from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML
from crispy_forms.layout import Div
from crispy_forms.layout import Field
from crispy_forms.layout import Layout
from crispy_forms.layout import Row
from crispy_forms.layout import Submit
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


class WebhookInterestForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Your full name"}),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"placeholder": "your.email@example.com"}),
    )
    phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Your phone number"}),
    )
    company = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Your company name (optional)"}),
    )
    role = forms.CharField(
        max_length=100,
        required=False,
        label="Your Role (optional)",
        widget=forms.TextInput(attrs={"placeholder": "e.g., Developer, Manager, etc."}),
    )
    use_case = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "placeholder": "Describe how you plan to use Hebrew Calendar Webhooks",
                "rows": 4,
            },
        ),
        label="How do you plan to use Hebrew Calendar Webhooks?",
        required=True,
    )
    experience = forms.ChoiceField(
        choices=[
            ("beginner", "Beginner - New to webhooks"),
            ("intermediate", "Intermediate - Some experience with webhooks"),
            ("advanced", "Advanced - Extensive webhook experience"),
        ],
        label="Webhook Experience",
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Field("name"),
            Field("email"),
            Field("phone"),
            Field("company"),
            Field("role"),
            Field("use_case"),
            Field("experience"),
        )
        self.helper.add_input(
            Submit("submit", "Apply for Beta Access", css_class="btn-primary btn-lg"),
        )
