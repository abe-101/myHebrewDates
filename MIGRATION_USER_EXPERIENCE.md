# Calendar Migration User Experience

## Overview

This document explains how users will experience the calendar migration from public URLs to authenticated, per-user subscription URLs.

## Migration Timeline & User Experience

### Phase 1: Admin Triggers Migration

**Action**: Admin runs "Migrate calendars and send notification email" action in Django admin

**What Happens**:
1. Calendar's `migrated_at` timestamp is set
2. Owner's subscription is created (if not already exists)
3. Email is sent to calendar owner

### Phase 2: User Receives Email

**Email Content**:
- Subject: "Action Required: Re-subscribe to your '[Calendar Name]' calendar"
- Explains the security improvements
- Provides personalized subscribe link
- Clear 3-step migration instructions

**User's Options**:
1. **Migrate Now**: Click link, get new subscription URL, re-add calendar
2. **Ignore**: Continue using old URL (will see prompts in calendar)

### Phase 3: Old URL Shows Migration Prompt

**When**: User's calendar app refreshes (varies by app, typically hourly/daily)

**What User Sees**:
1. **Calendar Name Changes**:
   - Old: "Family Birthdays"
   - New: "Family Birthdays (Legacy - Action Required)"

2. **New Event Appears** (Today's Date):
   - Title: "🔒 Security Update: Migrate Your Calendar"
   - Description:
     - Explains migration
     - Direct link to subscribe page
     - Immediate alarm notification

**Example Event**:
```
Title: 🔒 Security Update: Migrate Your Calendar

Description:
This calendar now requires sign-in for better security.

Click here to migrate: https://myhebrewdates.com/calendars/abc-123/subscribe/

Each person needs their own secure subscription URL. Visit the link above to get yours.

This ensures only authorized users can access this calendar.
```

### Phase 4: User Migrates

**User Journey**:

1. **Clicks Link** (from email or calendar event)
   - Goes to subscribe page: `/calendars/{uuid}/subscribe/`

2. **Signs In** (if not already)
   - Redirected to login page
   - After login, returns to subscribe page

3. **Gets Personal URL**
   - Auto-creates subscription
   - Shows personal subscription URL
   - Shows platform-specific subscribe buttons (Apple, Google, Outlook)
   - Can customize alarm time

4. **Re-adds Calendar**
   - Clicks platform button or copies URL
   - Adds new subscription to calendar app
   - Removes old subscription

5. **Done!**
   - Calendar name shows normal (no "Legacy" suffix)
   - No migration prompt event
   - Can customize alarm time anytime

## Technical Details

### Migration Prompt Event

**Injected By**: `generate_ical()` with `inject_migration_prompt=True`

**Properties**:
- **TRANSP**: TRANSPARENT (doesn't block time)
- **CATEGORIES**: System Notice, Migration
- **DATE**: Today (always current)
- **ALARM**: Immediate (0 hours) to grab attention

**Code Location**: `my_hebrew_dates/hebcal/utils.py:109-156`

### Calendar Name Change

**Old Name Display**:
- `model_calendar.name` (e.g., "Family Birthdays")

**New Name Display** (when migrated):
- `f"{model_calendar.name} (Legacy - Action Required)"`
- Example: "Family Birthdays (Legacy - Action Required)"

**Code Location**: `my_hebrew_dates/hebcal/utils.py:37-41`

### Email Sending

**Function**: `send_migration_notification_email(calendar)`

**Uses**: Django's `send_mail()` with both plain text and HTML versions

**From**: Uses `DEFAULT_FROM_EMAIL` from settings

**Code Location**: `my_hebrew_dates/hebcal/utils.py:270-372`

## Calendar App Behavior

### Refresh Frequency by App

- **Apple Calendar (iOS/macOS)**:
  - Typically every 15-60 minutes when app is open
  - Less frequent when device is asleep

- **Google Calendar**:
  - Typically every 12-24 hours for subscribed calendars
  - Can force refresh in settings

- **Outlook**:
  - Configurable, default is daily
  - Can manually refresh

### How Users See Changes

1. **First Refresh After Migration**:
   - Calendar name updates to include "(Legacy - Action Required)"
   - New migration prompt event appears at top of calendar

2. **After User Migrates**:
   - Old subscription removed by user
   - New subscription added with normal name
   - No migration prompt event
   - All dates/events identical (same UIDs)

## Backward Compatibility

### Old URLs Continue to Work

- Legacy endpoint: `/calendars/{uuid}/file/`
- Still serves calendar content
- Injects migration prompt when `calendar.is_migrated == True`
- Allows time for users to migrate
- No hard cutoff date (yet)

### Cache Considerations

- Legacy endpoint: 60 minute cache
- Migration prompt generation: Not cached (always fresh)
- Subscription endpoint: No view-level cache (tracks access)

## Communication Strategy

### Initial Email

**Sent**: When admin runs migrate action

**Goal**: Inform user of change, provide migration link

**Tone**: Helpful, explains benefits, clear action steps

### In-Calendar Notification

**Appears**: On next calendar refresh

**Goal**: Catch users who missed email

**Tone**: Urgent but helpful, direct link to migrate

**Visibility**: High (shows as event, has alarm)

## Success Metrics

Track migration progress via:

1. **Admin Panel**:
   - `migrated_at` field on Calendar model
   - Subscription count per calendar

2. **Database Queries**:
   ```python
   # Total migrated calendars
   Calendar.objects.filter(migrated_at__isnull=False).count()

   # Calendars with active subscriptions
   Calendar.objects.filter(subscriptions__isnull=False).distinct().count()

   # Users who've accessed new URL
   UserCalendarSubscription.objects.filter(last_accessed__isnull=False).count()
   ```

3. **Log Monitoring**:
   - Look for "Migration notification email sent" entries
   - Look for "Legacy access for MIGRATED calendar" warnings

## FAQs

### Will my existing events disappear?

No! The calendar content is identical. Same events, same dates, same UIDs. Only the subscription method changes.

### What if I share this calendar with family?

Each person needs to get their own subscription URL by visiting the subscribe page while logged in. The owner can share the subscribe page URL: `https://myhebrewdates.com/calendars/{uuid}/subscribe/`

### Can I change my alarm time?

Yes! With the new system, you can update your alarm preference anytime on the calendar detail page, and your subscription URL stays the same.

### What if I ignore the migration?

The calendar will continue to work, but you'll see the migration prompt and the "(Legacy - Action Required)" suffix. For the best experience, we recommend migrating.

### How long will the old URL work?

Indefinitely for now. We'll communicate well in advance if/when we plan to disable legacy URLs.
