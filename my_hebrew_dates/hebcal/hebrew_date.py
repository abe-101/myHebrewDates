from datetime import date, timedelta

from pyluach import dates
from pyluach.utils import _is_leap as is_leap


def create_hebrew_to_english_dict():
    hebrew_to_english_dict = {}
    first_gregorian_date = date.today()
    for i in range(365 * 3):  # three years
        hebrew_date = dates.HebrewDate.from_pydate(first_gregorian_date + timedelta(days=i))
        english_date = hebrew_date.to_pydate()

        if is_leap(hebrew_date.year):
            if hebrew_date.month == 12:
                hebrew_date_str = f"{hebrew_date.month+1}-{hebrew_date.day}"
            elif hebrew_date.month == 13:
                hebrew_date_str = f"{hebrew_date.month-1}-{hebrew_date.day}"
            hebrew_to_english_dict.setdefault(hebrew_date_str, []).append(english_date)

        else:  # not a leap year
            if hebrew_date.month == 12:
                hebrew_date_str = f"{hebrew_date.month}-{hebrew_date.day}"
                hebrew_to_english_dict.setdefault(hebrew_date_str, []).append(english_date)
                hebrew_date_str = f"{hebrew_date.month+1}-{hebrew_date.day}"
                hebrew_to_english_dict.setdefault(hebrew_date_str, []).append(english_date)
            else:
                hebrew_date_str = f"{hebrew_date.month}-{hebrew_date.day}"
                hebrew_to_english_dict.setdefault(hebrew_date_str, []).append(english_date)
        if hebrew_date.month == 8 and hebrew_date.day == 29:
            if hebrew_date.add(days=1) == dates.HebrewDate(hebrew_date.year, 9, 1):
                hebrew_to_english_dict.setdefault("8-30", []).append(english_date)
        if hebrew_date.month == 9 and hebrew_date.day == 29:
            if hebrew_date.add(days=1) == dates.HebrewDate(hebrew_date.year, 10, 1):
                hebrew_to_english_dict.setdefault("9-30", []).append(english_date)
    return hebrew_to_english_dict


hebrew_to_english_dict = create_hebrew_to_english_dict()
