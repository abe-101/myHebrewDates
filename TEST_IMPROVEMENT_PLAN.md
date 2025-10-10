# Test Coverage Improvement Plan

Current test coverage: **84%** (67 tests, 723 lines of test code)

## Critical Coverage Gaps (Immediate Priority)

### 1. Hebrew Calendar Utils (15% coverage) 🚨
**File:** `my_hebrew_dates/hebcal/utils.py` (94 statements, 80 missed)

**Missing Tests:**
- `generate_ical()` function - Core iCal generation logic
- Calendar timezone handling
- Event alarm generation
- Date formatting utilities

**Action Steps:**
```python
# Create: my_hebrew_dates/hebcal/tests/test_utils.py

class TestGenerateIcal(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("test", "test@example.com", "password")
        self.calendar = Calendar.objects.create(
            name="Test Calendar",
            user=self.user,
            timezone="America/New_York"
        )

    def test_generate_ical_basic_functionality(self):
        # Test basic iCal generation

    def test_generate_ical_with_alarm(self):
        # Test alarm trigger functionality

    def test_generate_ical_timezone_handling(self):
        # Test timezone conversion

    def test_generate_ical_multiple_events(self):
        # Test calendar with multiple Hebrew dates
```

### 2. Hebrew Calendar Views (54% coverage) 🚨
**File:** `my_hebrew_dates/hebcal/views.py` (215 statements, 99 missed)

**Missing Test Areas:**
- Calendar sharing functionality
- Email notifications
- HTMX modal interactions
- Error handling paths
- View permission checks

**Action Steps:**
```python
# Extend: my_hebrew_dates/hebcal/tests/test_views.py

class TestCalendarSharing(BaseTest):
    def test_calendar_sharing_enabled(self):
        # Test public calendar access

    def test_calendar_sharing_disabled(self):
        # Test private calendar protection

class TestEmailNotifications(BaseTest):
    def test_send_calendar_email(self):
        # Test email sending functionality

    def test_email_notification_failure(self):
        # Test email error handling

class TestHTMXInteractions(BaseTest):
    def test_htmx_modal_create(self):
        # Test HTMX modal calendar creation

    def test_htmx_modal_update(self):
        # Test HTMX modal calendar updates
```

## Moderate Priority Improvements

### 3. Core Models (77% coverage) ⚠️
**File:** `my_hebrew_dates/core/models.py` (22 statements, 5 missed)

**Missing Tests:**
- `SoftDeleteModel.soft_delete()` method
- `SoftDeleteModel.restore()` method
- `SoftDeleteManager` queryset filtering

**Action Steps:**
```python
# Create: my_hebrew_dates/core/tests/test_models.py

from my_hebrew_dates.core.models import SoftDeleteModel, TimeStampedModel

class TestSoftDeleteModel(TestCase):
    def test_soft_delete_functionality(self):
        # Test soft delete behavior

    def test_restore_functionality(self):
        # Test restore from soft delete

    def test_manager_excludes_deleted(self):
        # Test that objects manager excludes soft-deleted items

    def test_all_objects_includes_deleted(self):
        # Test that all_objects includes soft-deleted items
```

### 4. Hebrew Calendar Admin (75% coverage) ⚠️
**File:** `my_hebrew_dates/hebcal/admin.py` (36 statements, 9 missed)

**Missing Tests:**
- Admin interface customizations
- List display configurations
- Filter functionalities

**Action Steps:**
```python
# Create: my_hebrew_dates/hebcal/tests/test_admin.py

from django.contrib.admin.sites import AdminSite
from my_hebrew_dates.hebcal.admin import CalendarAdmin, HebrewDateAdmin

class TestCalendarAdmin(TestCase):
    def test_admin_list_display(self):
        # Test admin list view configuration

    def test_admin_search_fields(self):
        # Test search functionality

    def test_admin_filters(self):
        # Test filter options
```

### 5. Hebrew Calendar Decorators (67% coverage) ⚠️
**File:** `my_hebrew_dates/hebcal/decorators.py` (9 statements, 3 missed)

**Missing Tests:**
- HTMX request validation
- Error responses for non-HTMX requests

**Action Steps:**
```python
# Create: my_hebrew_dates/hebcal/tests/test_decorators.py

from my_hebrew_dates.hebcal.decorators import requires_htmx

class TestRequiresHtmx(TestCase):
    def test_htmx_request_allowed(self):
        # Test decorator with HTMX request

    def test_non_htmx_request_blocked(self):
        # Test decorator without HTMX headers
```

## Low Priority (Already Well Covered)

### Well-Tested Areas:
- **Hebrew Date Models (95% coverage)** ✅
- **Hebrew Calendar Forms (90% coverage)** ✅
- **User Models/Views/API (95%+ coverage)** ✅
- **URL Configurations (100% coverage)** ✅

## Implementation Strategy

### Phase 1: Critical Gaps (Week 1)
1. Create comprehensive utils tests for iCal generation
2. Expand view testing for sharing, email, and HTMX workflows

### Phase 2: Complete Coverage (Week 2)
1. Core model testing for soft delete functionality
2. Admin interface testing
3. Decorator testing for HTMX validation

### Phase 3: Integration Testing (Week 3)
1. End-to-end calendar creation workflows
2. Calendar sharing scenarios
3. Hebrew date calculation integration tests

## Testing Best Practices for This Codebase

### 1. Use Existing Test Patterns
```python
# Follow the BaseTest pattern in test_views.py
class NewTestClass(BaseTest):  # Inherits user and client setup
    def setUp(self):
        super().setUp()
        # Additional setup specific to your tests
```

### 2. Leverage Factories
```python
# Use user factories from my_hebrew_dates/users/tests/factories.py
from my_hebrew_dates.users.tests.factories import UserFactory

user = UserFactory()
```

### 3. Mock External Services
```python
# For email and external APIs
from unittest.mock import patch

@patch('my_hebrew_dates.hebcal.views.send_mail')
def test_email_notification(self, mock_send_mail):
    # Test email functionality
```

### 4. Test Hebrew Calendar Logic
```python
# Test Hebrew date calculations and conversions
from my_hebrew_dates.hebcal.models import HebrewMonthEnum, HebrewDayEnum

def test_hebrew_date_conversion(self):
    # Test Hebrew to Gregorian date conversion
```

## Expected Outcome

Following this plan should achieve:
- **90%+ overall coverage**
- **Comprehensive testing of core Hebrew calendar functionality**
- **Robust testing of iCal generation and calendar sharing**
- **Better error handling test coverage**
- **Integration test coverage for complex workflows**

## Commands for Implementation

```bash
# Run specific test file during development
pytest my_hebrew_dates/hebcal/tests/test_utils.py -v

# Run with coverage for specific app
coverage run -m pytest my_hebrew_dates/hebcal/tests/ --cov=my_hebrew_dates.hebcal

# Generate coverage report
coverage report --show-missing
coverage html
```
