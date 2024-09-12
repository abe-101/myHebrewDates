# My Hebrew Dates

Automatically sync recurring Hebrew calendar events, like birthdays and anniversaries, to your digital calendar.

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

License: GPLv3

## Contributors

<div align="center">
<a href="https://github.com/abe-101/myHebrewDates/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=abe-101/myHebrewDates" />
</a>
</div>

## Basic Commands

### Installation

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

6. Create `.env` File and add these:

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

      python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

### Type checks

Running type checks with mypy:

    mypy my_hebrew_dates

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

    coverage run -m pytest
    coverage html
    open htmlcov/index.html

#### Running tests with pytest

    pytest

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

### Email Server

In development, it is often nice to be able to see emails that are being sent from your application. If you choose to use [Mailpit](https://github.com/axllent/mailpit) when generating the project a local SMTP server with a web interface will be available.

1.  [Download the latest Mailpit release](https://github.com/axllent/mailpit/releases) for your OS.

2.  Copy the binary file to the project root.

3.  Make it executable:

        chmod +x mailpit

4.  Spin up another terminal window and start it there:

        ./mailpit

5.  Check out <http://127.0.0.1:8025/> to see how it goes.

Now you have your own mail server running locally, ready to receive whatever you send it.

### Sentry

Sentry is an error logging aggregator service. You can sign up for a free account at <https://sentry.io/signup/?code=cookiecutter> or download and host it yourself.
The system is set up with reasonable defaults, including 404 logging and integration with the WSGI application.

You must set the DSN url in production.

## Deployment

The following details how to deploy this application.
