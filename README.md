# My Hebrew Dates

MyHebrewDates is a web app for sharing Hebrew dates like birthdays, anniversaries, and yartzeit. It provides a subscribable feed for your calendar app, ensuring you never miss an important Hebrew date.

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Black code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

License: MIT

## Contributors
<div align="center">
<a href="https://github.com/abe-101/myHebrewDates/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=abe-101/myHebrewDates" />
</a>
</div>

## Settings

Moved to [settings](http://cookiecutter-django.readthedocs.io/en/latest/settings.html).

## Basic Commands

## Installation

1. Clone the repository:
  ```shell
  git clone https://github.com/abe-101/myHebrewDates.git
  cd myHebrewDates
  ```

2. Create and activate a virtual environment:
  ```shell
  python3 -m venv venv
  source venv/bin/activate
  ```

3. Install the local dependencies:
  ```shell
  pip install -r requirements/local.txt
  ```

4. Pre-Commit Install:
  ```shell
  pre-commit install
  ```

5. Create Database:
  ```shell
  createdb --username=<USERNAME> my_hebrew_dates
  ```

6. Create Env Files and add these:
  ```shell
  DATABASE_URL=postgres://<USERNAME>:<PASSWORD>@127.0.0.1:5432/my_hebrew_dates
  CELERY_BROKER_URL=redis://localhost:6379/0
  ```

7. Set up the database:
  ```shell
  python manage.py makemigrations
  python manage.py migrate
  ```

8. Start the Server
  ```shell
  python manage.py runserver
  ```

### Setting Up Your Users

- To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

- To create a **superuser account**, use this command:

      $ python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

### Type checks

Running type checks with mypy:

    $ mypy my_hebrew_dates

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

#### Running tests with pytest

    $ pytest

### Live reloading and Sass CSS compilation

Moved to [Live reloading and SASS compilation](https://cookiecutter-django.readthedocs.io/en/latest/developing-locally.html#sass-compilation-live-reloading).

### Celery

This app comes with Celery.

To run a celery worker:

```bash
cd my_hebrew_dates
celery -A config.celery_app worker -l info
```

Please note: For Celery's import magic to work, it is important _where_ the celery commands are run. If you are in the same folder with _manage.py_, you should be right.

To run [periodic tasks](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html), you'll need to start the celery beat scheduler service. You can start it as a standalone process:

```bash
cd my_hebrew_dates
celery -A config.celery_app beat
```

or you can embed the beat service inside a worker with the `-B` option (not recommended for production use):

```bash
cd my_hebrew_dates
celery -A config.celery_app worker -B -l info
```

## Deployment

The following details how to deploy this application.
