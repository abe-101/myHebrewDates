# ruff: noqa: S106
import tempfile
from io import StringIO
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from my_hebrew_dates.hebcal.models import Calendar
from my_hebrew_dates.hebcal.models import HebrewDate

User = get_user_model()

ROWS_IN_VALID_CSV = 3

VALID_CSV = """name,event_type,month,day
Moshe Cohen,birthday,7,4
Yaakov and Rivka Levi,anniversary,9,15
Avraham ben Yitzchak,yartzeit,1,22
"""


class ImportHebrewDatesTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
        )
        self.calendar = Calendar.objects.create(name="Family", owner=self.user)
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)

    def call(self, csv_text: str, *args) -> str:
        path = Path(self.tmp_dir.name) / "import.csv"
        path.write_text(csv_text, encoding="utf-8")
        out = StringIO()
        call_command(
            "import_hebrew_dates",
            "--calendar",
            str(self.calendar.uuid),
            "--file",
            str(path),
            *args,
            stdout=out,
            stderr=out,
        )
        return out.getvalue()

    def test_imports_every_row(self):
        self.call(VALID_CSV)

        events = HebrewDate.objects.filter(calendar=self.calendar)
        assert events.count() == ROWS_IN_VALID_CSV
        moshe = events.get(name="Moshe Cohen")
        assert (moshe.month, moshe.day, moshe.event_type) == (7, 4, "🎂")
        assert events.get(name="Yaakov and Rivka Levi").event_type == "💍"
        assert events.get(name="Avraham ben Yitzchak").event_type == "🕯️"

    def test_dry_run_writes_nothing(self):
        output = self.call(VALID_CSV, "--dry-run")

        assert HebrewDate.objects.filter(calendar=self.calendar).count() == 0
        assert "Dry run" in output
        assert "Moshe Cohen" in output

    def test_ignores_a_spreadsheet_byte_order_mark(self):
        path = Path(self.tmp_dir.name) / "bom.csv"
        path.write_text(VALID_CSV, encoding="utf-8-sig")
        call_command(
            "import_hebrew_dates",
            "--calendar",
            str(self.calendar.uuid),
            "--file",
            str(path),
            stdout=StringIO(),
        )

        count = HebrewDate.objects.filter(calendar=self.calendar).count()
        assert count == ROWS_IN_VALID_CSV

    def test_day_that_does_not_exist_in_that_month_aborts_the_import(self):
        csv_text = (
            "name,event_type,month,day\n"
            "Moshe Cohen,birthday,7,4\n"
            "Chana Cohen,birthday,2,30\n"  # 30 Iyar, Iyar only has 29 days
        )

        with pytest.raises(CommandError):
            self.call(csv_text)

        assert HebrewDate.objects.filter(calendar=self.calendar).count() == 0

    def test_unknown_event_type_aborts_the_import(self):
        csv_text = "name,event_type,month,day\nMoshe Cohen,bar mitzvah,7,4\n"

        with pytest.raises(CommandError):
            self.call(csv_text)

        assert HebrewDate.objects.filter(calendar=self.calendar).count() == 0

    def test_non_numeric_day_aborts_the_import(self):
        csv_text = "name,event_type,month,day\nMoshe Cohen,birthday,7,fourth\n"

        with pytest.raises(CommandError):
            self.call(csv_text)

        assert HebrewDate.objects.filter(calendar=self.calendar).count() == 0

    def test_rows_already_in_the_calendar_are_skipped(self):
        self.call(VALID_CSV)
        output = self.call(VALID_CSV)

        count = HebrewDate.objects.filter(calendar=self.calendar).count()
        assert count == ROWS_IN_VALID_CSV
        assert "already in the calendar" in output

    def test_rows_repeated_within_the_file_are_skipped(self):
        csv_text = VALID_CSV + "Moshe Cohen,birthday,7,4\n"

        self.call(csv_text)

        count = HebrewDate.objects.filter(calendar=self.calendar).count()
        assert count == ROWS_IN_VALID_CSV

    def test_blank_lines_are_ignored(self):
        self.call(VALID_CSV + "\n\n")

        count = HebrewDate.objects.filter(calendar=self.calendar).count()
        assert count == ROWS_IN_VALID_CSV

    def test_missing_column_is_reported(self):
        with pytest.raises(CommandError):
            self.call("name,month,day\nMoshe Cohen,7,4\n")

    def test_unknown_calendar_is_reported(self):
        path = Path(self.tmp_dir.name) / "import.csv"
        path.write_text(VALID_CSV, encoding="utf-8")

        with pytest.raises(CommandError):
            call_command(
                "import_hebrew_dates",
                "--calendar",
                "8d2f4e6a-0000-4000-8000-000000000000",
                "--file",
                str(path),
                stdout=StringIO(),
            )

    def test_sample_file_in_the_repo_imports(self):
        sample = Path(__file__).resolve().parents[1] / "sample_import.csv"

        call_command(
            "import_hebrew_dates",
            "--calendar",
            str(self.calendar.uuid),
            "--file",
            str(sample),
            "--dry-run",
            stdout=StringIO(),
        )
