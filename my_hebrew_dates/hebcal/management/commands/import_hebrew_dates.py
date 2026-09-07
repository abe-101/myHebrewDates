"""Bulk import events into an existing calendar from a CSV file.

The CSV needs the columns ``name``, ``event_type``, ``month`` and ``day``,
where ``month`` is 1 (Nisan) through 13 (Adar II) and ``day`` is 1 to 30.
See ``my_hebrew_dates/hebcal/sample_import.csv`` for an example.
"""

import csv
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db import transaction

from my_hebrew_dates.hebcal.models import Calendar
from my_hebrew_dates.hebcal.models import HebrewDate
from my_hebrew_dates.hebcal.models import HebrewDayEnum
from my_hebrew_dates.hebcal.models import HebrewMonthEnum

COLUMNS = ("name", "event_type", "month", "day")

EVENT_TYPES = {
    "birthday": "🎂",
    "anniversary": "💍",
    "yartzeit": "🕯️",
}


class RowError(Exception):
    """A CSV row that cannot be turned into a HebrewDate."""


def _as_int(value: str | None, column: str) -> int:
    text = (value or "").strip()
    if not text.isdigit():
        msg = f"{column} must be a whole number, got {text!r}"
        raise RowError(msg)
    return int(text)


def _as_event_type(value: str | None) -> str:
    text = (value or "").strip().lower()
    if text not in EVENT_TYPES:
        options = ", ".join(EVENT_TYPES)
        msg = f"event_type must be one of {options}, got {text!r}"
        raise RowError(msg)
    return EVENT_TYPES[text]


def _describe(event: HebrewDate) -> str:
    day = HebrewDayEnum(event.day).label
    month = HebrewMonthEnum(event.month).label
    return f"{event.event_type} {day} {month} - {event.name}"


class Command(BaseCommand):
    help = "Import events into a calendar from a CSV file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--calendar",
            required=True,
            help="UUID of the calendar to import into.",
        )
        parser.add_argument(
            "--file",
            required=True,
            help="Path to the CSV file to import.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate and report without writing anything.",
        )

    def handle(self, *args, **options):
        calendar = self._get_calendar(options["calendar"])
        rows = self._read_csv(Path(options["file"]))
        events, skipped, errors = self._build_events(rows, calendar)
        self._report(calendar, events, skipped, errors)

        if errors:
            msg = f"{len(errors)} row(s) are invalid, nothing was imported"
            raise CommandError(msg)
        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("Dry run, nothing was written."))
            return
        if not events:
            self.stdout.write(self.style.WARNING("Nothing to import."))
            return

        with transaction.atomic():
            for event in events:
                event.save()
        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {len(events)} event(s) into {calendar.name}.",
            ),
        )

    @staticmethod
    def _get_calendar(uuid: str) -> Calendar:
        try:
            return Calendar.objects.get(uuid=uuid)
        except (Calendar.DoesNotExist, ValidationError, ValueError) as exc:
            msg = f"no calendar with uuid {uuid!r}"
            raise CommandError(msg) from exc

    @staticmethod
    def _read_csv(path: Path) -> list[tuple[int, dict[str, str]]]:
        if not path.is_file():
            msg = f"no such file: {path}"
            raise CommandError(msg)

        # utf-8-sig so a spreadsheet's byte order mark does not end up in the
        # first column name.
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            header = [(name or "").strip().lower() for name in reader.fieldnames or []]
            missing = [column for column in COLUMNS if column not in header]
            if missing:
                msg = f"the CSV is missing column(s): {', '.join(missing)}"
                raise CommandError(msg)

            rows = []
            for record in reader:
                if not any((value or "").strip() for value in record.values()):
                    continue
                clean = {
                    (key or "").strip().lower(): value for key, value in record.items()
                }
                rows.append((reader.line_num, clean))
        return rows

    def _build_events(
        self,
        rows: list[tuple[int, dict[str, str]]],
        calendar: Calendar,
    ) -> tuple[list[HebrewDate], list[tuple[int, HebrewDate]], list[tuple[int, str]]]:
        """Validate every row before a single one is written.

        Returns the events to create, the rows already present in the calendar,
        and the rows that failed validation.
        """
        seen = set(
            HebrewDate.objects.filter(calendar=calendar).values_list(
                "name",
                "month",
                "day",
                "event_type",
            ),
        )
        events: list[HebrewDate] = []
        skipped: list[tuple[int, HebrewDate]] = []
        errors: list[tuple[int, str]] = []

        for line_number, record in rows:
            try:
                event = self._build_event(record, calendar)
            except RowError as exc:
                errors.append((line_number, str(exc)))
                continue
            except ValidationError as exc:
                errors.append((line_number, self._format_validation_error(exc)))
                continue

            key = (event.name, event.month, event.day, event.event_type)
            if key in seen:
                skipped.append((line_number, event))
                continue
            seen.add(key)
            events.append(event)

        return events, skipped, errors

    @staticmethod
    def _build_event(record: dict[str, str], calendar: Calendar) -> HebrewDate:
        event = HebrewDate(
            name=(record.get("name") or "").strip(),
            month=_as_int(record.get("month"), "month"),
            day=_as_int(record.get("day"), "day"),
            event_type=_as_event_type(record.get("event_type")),
            calendar=calendar,
        )
        # The model is the only validator: field choices, name length and the
        # month/day check in HebrewDate.clean().
        event.full_clean()
        return event

    @staticmethod
    def _format_validation_error(error: ValidationError) -> str:
        return "; ".join(
            f"{field}: {' '.join(messages)}"
            for field, messages in error.message_dict.items()
        )

    def _report(
        self,
        calendar: Calendar,
        events: list[HebrewDate],
        skipped: list[tuple[int, HebrewDate]],
        errors: list[tuple[int, str]],
    ) -> None:
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"{len(events)} event(s) for {calendar.name} ({calendar.uuid})",
            ),
        )
        for event in events:
            self.stdout.write(f"  {_describe(event)}")

        if skipped:
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING(
                    f"{len(skipped)} row(s) already in the calendar, skipped:",
                ),
            )
            for line_number, event in skipped:
                self.stdout.write(f"  line {line_number}: {_describe(event)}")

        if errors:
            self.stdout.write("")
            self.stdout.write(self.style.ERROR(f"{len(errors)} invalid row(s):"))
            for line_number, reason in errors:
                self.stdout.write(f"  line {line_number}: {reason}")
        self.stdout.write("")
