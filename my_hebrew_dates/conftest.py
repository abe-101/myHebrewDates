import pytest
import time_machine

from my_hebrew_dates.users.models import User
from my_hebrew_dates.users.tests.factories import UserFactory

# Tests run at one fixed instant so that anything derived from the
# clock - DTSTAMP, auto_now columns, token expiry - is reproducible.
FROZEN_NOW = "2026-06-01 12:00:00 +0000"


@pytest.fixture(autouse=True)
def frozen_clock(request):
    """
    Stop the clock for every test.

    tick=False holds the instant rather than letting it run on from the
    destination, so a test cannot pass or fail on how long it took.
    Request this fixture by name to move_to another point mid-test, or
    mark a test with ``time_ticks`` when it genuinely needs time to
    pass.
    """
    if "time_ticks" in request.keywords:
        yield None
        return
    with time_machine.travel(FROZEN_NOW, tick=False) as traveller:
        yield traveller


@pytest.fixture(autouse=True)
def _media_storage(settings, tmpdir) -> None:
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user(db) -> User:
    return UserFactory.create()
