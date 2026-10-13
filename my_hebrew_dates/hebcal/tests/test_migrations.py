"""
Guards against the migration churn the timezone field used to cause.

``Calendar.timezone`` draws its choices from the system tz database. It
was built as an evaluated tuple, which Django froze into the migration,
so every tzdata update produced another AlterField - migrations 0004,
0007 and 0008 are all that and nothing else. The field now takes a
callable, and these tests keep it that way.

The callable is also cached, so anything that resolves it has to clear
the cache first to observe a patched tz database.
"""

import zoneinfo

from django.apps import apps
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.questioner import NonInteractiveMigrationQuestioner
from django.db.migrations.state import ProjectState

from my_hebrew_dates.hebcal.models import Calendar
from my_hebrew_dates.hebcal.models import get_timezone_choices


def detect_hebcal_changes():
    """
    Return the migrations makemigrations would write for hebcal.
    """
    loader = MigrationLoader(None, ignore_no_migrations=True)
    autodetector = MigrationAutodetector(
        loader.project_state(),
        ProjectState.from_apps(apps),
        NonInteractiveMigrationQuestioner(specified_apps=set(), dry_run=True),
    )
    return autodetector.changes(
        graph=loader.graph,
        trim_to_apps={"hebcal"},
        convert_apps={"hebcal"},
    )


def test_no_pending_migrations():
    assert detect_hebcal_changes() == {}


def test_deconstructed_choices_do_not_depend_on_tzdata(monkeypatch, request):
    """
    The whole point of the callable: a different tz database must not
    show up as a model change.

    Patching ``available_timezones`` alone would prove nothing, because
    the autodetector compares the callable reference without calling
    it. So this asserts both halves - that the patch really does change
    the resolved list, and that the serialised form is unmoved by it.
    """
    field = Calendar._meta.get_field("timezone")  # noqa: SLF001 (public Django API)
    before = field.deconstruct()[3]["choices"]

    monkeypatch.setattr(zoneinfo, "available_timezones", lambda: {"UTC"})
    get_timezone_choices.cache_clear()
    request.addfinalizer(get_timezone_choices.cache_clear)

    assert get_timezone_choices() == (("UTC", "UTC"),)
    assert field.deconstruct()[3]["choices"] is before
    assert detect_hebcal_changes() == {}


def test_choices_deconstruct_to_a_callable():
    """
    deconstruct() is what the migration writer serialises, so a callable
    here is what keeps the tz list out of the migration file. An
    evaluated tuple would reintroduce the churn.
    """
    field = Calendar._meta.get_field("timezone")  # noqa: SLF001 (public Django API)
    _, _, _, kwargs = field.deconstruct()

    assert callable(kwargs["choices"])


def test_choices_resolve_to_timezone_pairs():
    choices = get_timezone_choices()

    assert ("UTC", "UTC") in choices
    assert ("America/New_York", "America/New_York") in choices
    assert all(value == label for value, label in choices)


def test_choices_exclude_non_timezone_entries():
    values = {value for value, _ in get_timezone_choices()}

    assert "Factory" not in values
    assert "localtime" not in values


def test_default_is_a_valid_choice():
    field = Calendar._meta.get_field("timezone")  # noqa: SLF001 (public Django API)
    values = {value for value, _ in get_timezone_choices()}

    assert field.default in values


def test_choices_are_sorted_case_insensitively():
    choices = get_timezone_choices()
    values = [value for value, _ in choices]

    assert values == sorted(values, key=str.lower)
