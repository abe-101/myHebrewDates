# ruff: noqa: PLW2901
import logging
from datetime import date
from datetime import timedelta

from django.utils.dateparse import parse_date
from pyluach import dates
from pyluach.utils import _is_leap as is_leap

logger = logging.getLogger(__name__)

lengths_of_months = [0, 30, 29, 30, 29, 30, 29, 30, 30, 30, 29, 30, 30, 29]

ADAR_2 = 13


def create_hebrew_to_english_dict(
    start_year: int | None = None,
) -> dict[str, list[object]]:
    """
    Map "month-day" to the Gregorian dates it falls on over three years.

    ``start_year`` pins the window to a fixed Hebrew year instead of the
    current one, which keeps generated iCalendar output reproducible.
    """
    logger.info("Creating hebrew_to_english_dict")
    hebrew_to_english_dict: dict[str, list[object]] = {}
    today_year = start_year or dates.HebrewDate.today().year

    for year in range(today_year, today_year + 3):  # three years
        for month in range(1, 14):
            mstring = month
            if not is_leap(year) and month == ADAR_2:
                month = month - 1
            for day in range(1, lengths_of_months[month] + 1):
                try:
                    hebrew_date = dates.HebrewDate(year, month, day)
                except ValueError:
                    hebrew_date = dates.HebrewDate(year, month, day - 1)
                english_date = hebrew_date.to_pydate()
                hebrew_to_english_dict.setdefault(f"{mstring}-{day}", []).append(
                    english_date,
                )

    logger.info("Finished creating hebrew_to_english_dict")
    return hebrew_to_english_dict


hebrew_to_english_dict: dict[str, list[object]] = create_hebrew_to_english_dict()


def is_valid_hebrew_date(month: int, day: int) -> bool:
    """Whether the day exists in that Hebrew month in at least some years.

    Cheshvan, Kislev and Adar I vary in length by year, so their longest
    possible length is used.
    """
    if not 1 <= month <= ADAR_2:
        return False
    return 1 <= day <= lengths_of_months[month]


def hebrew_date_from_english(
    english_date: date,
    *,
    after_sunset: bool,
) -> tuple[int, int]:
    """
    Return the (month, day) of the Hebrew date for an English date.

    The Hebrew day starts at sunset. Plain Adar in a year with one Adar is
    returned as Adar II, which the calendar treats as Adar in those years.
    """
    if after_sunset:
        english_date += timedelta(days=1)
    hebrew = dates.HebrewDate.from_pydate(english_date)
    if hebrew.month == ADAR_2 - 1 and not is_leap(hebrew.year):
        return ADAR_2, hebrew.day
    return hebrew.month, hebrew.day


def hebrew_date_from_english_input(
    value: str,
    *,
    after_sunset: bool,
) -> tuple[int, int] | None:
    """
    Like hebrew_date_from_english, for a YYYY-MM-DD string from a request.

    Returns None for anything that isn't a usable date, such as 2027-02-30.
    """
    try:
        english_date = parse_date(value)
        if english_date is None:
            return None
        return hebrew_date_from_english(english_date, after_sunset=after_sunset)
    except ValueError, OverflowError:
        return None
