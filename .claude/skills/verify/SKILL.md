# Verify: run and drive My Hebrew Dates locally

Recipe for exercising UI changes end-to-end in a headless environment
(worked in Claude Code remote sessions; adapt paths as needed).

## Build / launch

```bash
uv venv .venv && uv pip install -r requirements/local.txt
service postgresql start                    # or pg_ctlcluster <ver> main start
sudo -u postgres createuser -s "$USER"; createdb my_hebrew_dates
DATABASE_URL="postgres://$USER@/my_hebrew_dates" \
  .venv/bin/python manage.py migrate
DATABASE_URL="postgres://$USER@/my_hebrew_dates" \
  DJANGO_SETTINGS_MODULE=config.settings.local \
  .venv/bin/python manage.py runserver 8123 --noreload
```

Gotchas:
- `--noreload` means restart the server after **any Python change**
  (forms.py, views.py). Templates reload per request.
- Seed users need a non-empty unique `username`, or the navbar's
  `users:detail` reverse 500s every page.
- Seed login needs a verified `allauth.account.models.EmailAddress`
  row, plus `Site.objects` domain if links matter.
- django-debug-toolbar intercepts clicks in Playwright; disable with a
  wrapper settings module: `DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda r: False}`.

## Drive (Playwright, sandboxed network)

The base template loads Bootstrap/SweetAlert/FullCalendar/popper from
CDNs. If the sandbox blocks CDNs (agent proxy 403), `npm pack` the same
versions (npm registry is usually allowed), extract, and serve them via
`context.route()` interception; also strip `integrity="..."` attributes
from GET document responses (fulfill with rewritten body — GET only,
POSTs must `route.continue()` or login breaks). Block analytics hosts
with 204s. htmx is vendored locally at `static/js/htmx.min.js` — no
interception needed.

Chromium executable: `ls /opt/pw-browsers/` for the real path
(e.g. `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`).

## Flows worth driving

- Login: `/accounts/login/` (`input[name=login]`, `input[name=password]`).
- Calendar list `/calendars/`, manage page `/calendars/<uuid>/edit/`:
  filter bar (HTMX swaps `#calendar-table`), inline add/edit/delete
  rows (SweetAlert intercepts `htmx:confirm`), rename modal
  (django_htmx_modal_forms swaps `_calendar_name.html` back).
- Detail `/calendars/<uuid>/` is public; alarm select re-renders the
  subscribe links partial.
- Check both themes (`document.documentElement.dataset.bsTheme = 'dark'`)
  and a ~375px viewport (assert zero horizontal overflow).

## Tests

```bash
DATABASE_URL="postgres://$USER@/my_hebrew_dates" .venv/bin/pytest my_hebrew_dates/hebcal/tests/ -q
```
