# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

My Hebrew Dates is a Django application that automatically syncs recurring Hebrew calendar events (birthdays, anniversaries) to digital calendars. Built with Cookiecutter Django, it integrates Hebrew calendar calculations with modern calendar systems.

## Development Commands

### Setup and Installation
```bash
# Install local dependencies
pip install -r requirements/local.txt

# Pre-commit setup
pre-commit install

# Database setup
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### Development Server
```bash
# Start development server
python manage.py runserver
```

### Testing
```bash
# Run tests
pytest

# Run tests with coverage
coverage run -m pytest
coverage html

# Single test file
pytest my_hebrew_dates/hebcal/tests/test_models.py
```

### Code Quality
```bash
# Type checking
mypy my_hebrew_dates

# Linting (uses Ruff configuration from pyproject.toml)
ruff check .
ruff format .

# Template linting
djlint --check my_hebrew_dates/templates/
```

### Background Tasks (Celery)
```bash
# Start Celery worker
celery -A config.celery_app worker -l info

# Start Celery beat scheduler
celery -A config.celery_app beat

# Combined worker with beat (development only)
celery -A config.celery_app worker -B -l info
```

### Email Development (Mailpit)
```bash
# Start local mail server (binary should be in project root)
./mailpit
# Access web interface at http://127.0.0.1:8025/
```

## Architecture

### Django Apps Structure
- **core**: Shared models (TimeStampedModel), utilities, middleware, constants
- **users**: Custom user model, authentication, user management (built on django-allauth)
- **hebcal**: Hebrew calendar functionality, main business logic
- **contrib**: Additional utilities and extensions
- **utils**: General utility functions

### Key Models
- `Calendar` (hebcal): Represents a calendar event with Hebrew date tracking
- `HebrewDate` (hebcal): Stores Hebrew calendar dates with conversion utilities
- `User` (users): Custom user model extending Django's AbstractUser

### Settings Configuration
- **base.py**: Core Django settings
- **local.py**: Development settings (DEBUG=True, dev database)
- **production.py**: Production settings
- **test.py**: Test-specific settings
- Uses django-environ for environment variable management

### Hebrew Calendar Integration
- Hebrew month/day enums in `my_hebrew_dates/hebcal/models.py`
- Hebrew-to-English date conversion utilities in `hebrew_date.py`
- Calendar synchronization logic in hebcal app

### Background Processing
- Celery integration for asynchronous tasks
- Redis as message broker (configured via CELERY_BROKER_URL)
- Periodic tasks for calendar synchronization

## Development Guidelines

### Environment Setup
- Requires PostgreSQL database
- Redis for Celery broker
- Environment variables in `.env` file:
  - `DATABASE_URL=postgres://user:pass@host:port/db_name`
  - `CELERY_BROKER_URL=redis://localhost:6379/0`

### Testing Strategy
- Uses pytest with Django integration
- Test files follow `test_*.py` pattern
- Coverage configuration excludes migrations and test files
- Test settings use separate database configuration

### Code Style
- Ruff for linting and formatting (configured in pyproject.toml)
- mypy for type checking
- djLint for Django template linting
- Pre-commit hooks enforce code quality

### Calendar Integration
- Core functionality revolves around Hebrew calendar date calculations
- Automatic synchronization of recurring Hebrew dates to standard calendars
- Event creation and management through web interface
