import logging

from pyluach import dates
from pyluach.utils import _is_leap as is_leap

logger = logging.getLogger(__name__)

lengths_of_months = [0, 30, 29, 30, 29, 30, 29, 30, 30, 30, 29, 30, 30, 29]


def create_hebrew_to_english_dict():
    logger.info("Creating hebrew_to_english_dict")
    hebrew_to_english_dict = {}
    today_year = dates.HebrewDate.today().year

    for year in range(today_year, today_year + 3):  # three years
        for month in range(1, 14):
            mstring = month
            if not is_leap(year) and month == 13:
                month = month - 1
            for day in range(1, lengths_of_months[month] + 1):
                try:
                    hebrew_date = dates.HebrewDate(year, month, day)
                except ValueError:
                    hebrew_date = dates.HebrewDate(year, month, day - 1)
                english_date = hebrew_date.to_pydate()
                hebrew_to_english_dict.setdefault(f"{mstring}-{day}", []).append(english_date)

    logger.info("Finished creating hebrew_to_english_dict")
    return hebrew_to_english_dict


hebrew_to_english_dict = create_hebrew_to_english_dict()
