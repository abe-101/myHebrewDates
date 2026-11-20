from datetime import date

from my_hebrew_dates.hebcal.hebrew_date import hebrew_date_from_english
from my_hebrew_dates.hebcal.models import HebrewMonthEnum


def test_daytime_date():
    assert hebrew_date_from_english(date(2027, 1, 23), after_sunset=False) == (
        HebrewMonthEnum.SHEVAT,
        15,
    )


def test_after_sunset_belongs_to_the_next_hebrew_day():
    assert hebrew_date_from_english(date(2027, 1, 22), after_sunset=True) == (
        HebrewMonthEnum.SHEVAT,
        15,
    )


def test_adar_in_a_year_with_one_adar_is_stored_as_adar_ii():
    assert hebrew_date_from_english(date(2026, 3, 3), after_sunset=False) == (
        HebrewMonthEnum.ADAR_B,
        14,
    )


def test_leap_year_keeps_adar_i_and_adar_ii_apart():
    assert hebrew_date_from_english(date(2027, 2, 23), after_sunset=False) == (
        HebrewMonthEnum.ADAR_A,
        16,
    )
    assert hebrew_date_from_english(date(2027, 3, 23), after_sunset=False) == (
        HebrewMonthEnum.ADAR_B,
        14,
    )
