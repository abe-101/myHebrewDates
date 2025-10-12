# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

My Hebrew Dates is a Django web application that automatically syncs recurring Hebrew calendar events (birthdays, anniversaries, yahrzeits) to digital calendars via iCalendar (.ics) format. Built with Cookiecutter Django.

## Core Architecture

### Main Components

- **hebcal app**: Core functionality for Hebrew calendar management
  - `models.py`: `Calendar` and `HebrewDate` models with Hebrew month/day enums
  - `utils.py`: iCalendar generation (`generate_ical`, `generate_ical_experimental`)
  - `views.py`: Calendar CRUD operations and iCal file serving
  - `hebrew_date.py`: Hebrew-to-English date conversion logic

- **users app**: Custom user model and authentication (Cookiecutter Django)

- **core app**: Shared utilities and `TimeStampedModel` base class

### Key Concepts

1. **Hebrew Date Model**: Stores month (1-13, includes Adar I/II), day (1-30), event type (Birthday/Anniversary/Yartzeit), and person's name. The `get_english_dates()` method converts to Gregorian dates for the next 10 years.

2. **Calendar Export**: The `generate_ical()` function creates RFC 5545 compliant iCalendar files. Google Calendar detection uses user-agent sniffing to apply UTC timezone for better compatibility.

3. **Calendar Links**: Templates like `_calendar_links.html` generate subscription URLs for Apple Calendar (webcal://), Google Calendar, Outlook, etc.

## Development Commands

### Setup
```bash
# Install dependencies
pip install -r requirements/local.txt

# Install pre-commit hooks
pre-commit install

# Database setup (requires PostgreSQL)
createdb --username=<USERNAME> my_hebrew_dates
python manage.py migrate

# Start development server
python manage.py runserver
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage
coverage run -m pytest
coverage html

# Type checking
mypy my_hebrew_dates
```

### Celery (for async tasks)
```bash
# From project root
cd my_hebrew_dates

# Worker
celery -A config.celery_app worker -l info

# Beat scheduler (periodic tasks)
celery -A config.celery_app beat
```

## Important Configuration

- **Settings Module**: `config.settings.local` (development), uses split settings pattern
- **Database**: PostgreSQL required, configured via `DATABASE_URL` in `.env`
- **Celery Broker**: Redis (configured via `CELERY_BROKER_URL`)
- **Pre-commit**: Uses ruff, djlint, and other hooks

## Template Structure

Templates use HTMX for dynamic interactions. Key patterns:
- Modal forms with `django_htmx_modal_forms`
- Collapsible calendar links (`_calendar_links.html`)
- Calendar tables with HTMX partial updates

## Frontend Development

- **Bootstrap**: Use built-in Bootstrap classes for styling
- **Theme Compatibility**: Always choose Bootstrap classes that work for both light and dark themes. Avoid hardcoding colors or using theme-specific classes that break in one mode
- **Icons**: Bootstrap Icons (`bi` classes) for consistent iconography

## iCalendar Generation Notes

- Google Calendar requires `CALSCALE:GREGORIAN`, `DTSTAMP`, `LAST-MODIFIED`, and `SEQUENCE` properties
- All-day events use `VALUE=DATE` parameter and DTEND = DTSTART + 1 day
- Alarms use `TRIGGER` with timedelta (default: -9 hours)
- Event UIDs use SHA1 hash of event details + date + domain
