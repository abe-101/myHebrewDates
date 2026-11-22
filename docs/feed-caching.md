# Calendar feed caching

This page gives the key facts about how Cloudflare caches the `.ics` subscription feed, and why. Some of these facts
are not in the code. They are in the Cloudflare dashboard, or they came from tests with real requests. Read this
page before you change how Django serves the feed or how Cloudflare caches it.

## The setup

```
calendar app ──▶ Cloudflare edge (cache) ──▶ Django feed view (no cache)
```

- Cloudflare is the only cache. It keeps each feed URL for the time that the view's `Cache-Control` header gives.
- Django does not cache the feed. A request that passes Cloudflare always receives current data.
- The feed URL contains the calendar's `uuid`. The `uuid` is the only secret. Anyone with the URL can read the feed.

## The rule that keeps the cache correct

Cloudflare uses the full URL, with its query string, as the cache key. Thus the feed body must depend on the URL
only. It must not depend on the User-Agent, cookies, or any other header. If it does, the first app that fetches a URL
decides the body that all apps receive until the cached copy expires. A contract test checks this rule.

## The Cloudflare rule

The cache rule **calendar mhd** (Caching → Cache Rules) controls the feed cache:

- It applies to `.ics` and `.ical` URLs.
- It takes the edge lifetime from our `Cache-Control` header, and it does not cache a response without that header.
- It does not cache requests that come from our own calendar pages or from mergecal.org, based on the Referer. Thus a
  user who opens the feed from our site sees their change immediately.

Calendar apps fetch the feed from their own servers and do not send that Referer. Thus subscribers always receive the
cached copy.

## When a subscriber sees a change

A subscriber sees a change after two delays:

1. The Cloudflare copy expires.
2. The subscriber's app fetches the feed again.

The app controls the second delay. Google Calendar uses its own schedule and ignores the refresh interval in the feed.
Nothing on our side makes Google show a change immediately.

## Decisions and their reasons

- **The same feed for every app.** The feed once used a different time zone for Google, based on the User-Agent.
  That broke the rule above. Every event is all-day with a date only, so the time zone never moved an event.
- **No Django cache.** A Django cache kept an old copy for an hour, and nothing could delete it after a change. That
  copy also stopped the Referer exception from working.
- **An ETag on every feed.** The body changes only when the calendar's data changes, so the view sends an `ETag` and
  answers a matching `If-None-Match` with `304 Not Modified`. Cloudflare and calendar apps that revalidate then skip
  the download. Keep the body free of anything that changes on each request, such as the current time in `DTSTAMP`.
  The view sends no `Last-Modified` header: a deleted date changes the body but would not move that date.
- **No purge after a change, for now.** Cloudflare can purge every feed URL for one calendar with one API call. With
  purges, a much longer edge lifetime is possible. We did not add purges, because the load is low and we want no
  Cloudflare API integration.

## How to check the cache from outside

A fetch puts that exact URL into the Cloudflare cache. Add a temporary query parameter, so that your check does not
replace the copy that real subscribers receive:

```bash
U="https://myhebrewdates.com/calendars/<uuid>.ics?t=check$RANDOM"
curl -sI "$U" | grep -i cf-cache-status   # MISS
curl -sI "$U" | grep -i cf-cache-status   # HIT
curl -sI -e "https://myhebrewdates.com/calendars/<uuid>/" "$U" | grep -i cf-cache-status   # DYNAMIC
```
