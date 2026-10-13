# Codebase Guidelines

## Architecture

- My Hebrew Dates syncs recurring Hebrew calendar events (birthdays, anniversaries, yahrzeits) to digital calendars
  through iCalendar (.ics) subscription feeds.
- This is a Django project generated from Cookiecutter Django, running on Python 3.12.
- User authentication uses `django-allauth`.
- The front end is standard Django views and templates, with HTMX for dynamic interactions and
  `django_htmx_modal_forms` for modal forms.
- The front end uses Bootstrap 5 and Bootstrap Icons. There is no JavaScript build step.
- The main database is Postgres.
- Celery is used for background jobs and scheduled tasks, with Redis as the broker.

### Apps

- `hebcal`: the core app. `Calendar` and `HebrewDate` models, iCalendar generation in `utils.py`, calendar views and
  the `.ics` feed.
- `users`: the custom user model and authentication.
- `core`: shared code, including the `TimeStampedModel` base class.

### iCalendar gotchas

- Google Calendar is detected by user-agent sniffing and gets UTC timezones for better compatibility.
- Google Calendar requires `CALSCALE:GREGORIAN`, `DTSTAMP`, `LAST-MODIFIED` and `SEQUENCE`.
- All-day events use `VALUE=DATE`, and DTEND is DTSTART + 1 day.
- Alarms use `TRIGGER` with a timedelta (default: -9 hours).
- Event UIDs are a SHA1 hash of the event details, date and domain. Changing what goes into the hash changes every
  UID, which makes subscribed calendars drop and re-create their events.

## Commands you can run

The app runs natively. Postgres and Redis run as local services, and Python runs from the virtualenv in `venv/`
(`source venv/bin/activate`).

### First-time Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements/local.txt
pre-commit install
createdb my_hebrew_dates
python manage.py migrate
```

### Running the app

```bash
python manage.py runserver                                     # http://localhost:8000
celery -A config.celery_app worker -l info                     # Celery worker, from the project root
celery -A config.celery_app beat                               # Celery beat scheduler
```

### Testing and checks

```bash
pytest                                                         # Run all tests
pytest my_hebrew_dates/hebcal/tests/test_views.py              # Run one file
python manage.py makemigrations --check --settings=config.settings.test   # CI fails on missing migrations
mypy my_hebrew_dates                                           # Type checking
pre-commit run --all-files                                     # ruff, ruff-format, djlint and other hooks
```

## General Coding Preferences

- Always prefer simple solutions.
- Avoid duplication of code whenever possible, which means checking for other areas of the codebase that might already
  have similar code and functionality.
- Only make changes that are requested or that you are confident are well understood and related to the change being
  requested.
- When fixing an issue or bug, do not introduce a new pattern or technology without first exhausting all options for
  the existing implementation. If you finally do this, remove the old implementation afterwards so there is no
  duplicate logic.
- Keep the codebase clean and organized.
- Avoid writing scripts in files if possible, especially if the script is likely only to be run once.
- Try to avoid having files over 200-300 lines of code. Refactor at that point.
- Don't ever add mock data to functions. Only add mocks to tests or utilities that are only used by tests.
- Always think about what other areas of code might be affected by any changes made.
- Never overwrite the `.env` file without first asking and confirming.
- Avoid code comments. Only add one when there is something important a reader can't learn from the code itself.
- Write code that reads top to bottom. Prefer plain `if X: raise Y` / `return Z` over lookup dicts, context managers,
  or other indirection.
- Keep code inline. Only extract a helper function once the same code has two callers.

## Planning Work

- Keep it lean. Build only what the next milestone needs, and leave everything else out until real usage shows it's
  needed.
- Work in small PRs, one step at a time. Each PR is reviewed and merged before the next one starts.
- Allow for real-world cases in the design, even when the first version is basic. For example, the same user doing the
  same thing again later.

## Git Workflow

- All work is done on a new branch and merged through a pull request. Never commit directly to `main`.
- Every commit must be atomic: one logical change that stands on its own.
- History on a feature branch may be rewritten (rebase, squash, reorder, amend) to keep commits atomic before merging.
- Commit messages and PR descriptions explain *why* the change was made, not *what* changed — the diff already shows
  what.

## Django Template Guidelines

- Indent templates with two spaces (djlint enforced).
- For multi-line comments, use `{% comment %}...{% endcomment %}`. The `{# ... #}` syntax is single-line only and does
  NOT work across multiple lines.
- Break re-usable pieces into partial templates prefixed with `_` (e.g. `hebcal/_calendar_links.html`) and pull them
  in with `{% include %}`. HTMX endpoints usually render one of these partials.
- Use built-in Bootstrap classes for styling, and Bootstrap Icons (`bi` classes) for icons.
- Always choose Bootstrap classes that work in both light and dark themes. Avoid hardcoded colors or theme-specific
  classes that break in one mode.
- Avoid inline `<script>` tags where possible.
- When using HTMX, follow progressive enhancement patterns.
