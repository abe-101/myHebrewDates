from datetime import date, timedelta

from pyluach import dates


def create_hebrew_to_english_dict():
    hebrew_to_english_dict = {}
    first_gregorian_date = date.today()  # two years ago
    for i in range(365 * 3):  # three years
        hebrew_date = dates.HebrewDate.from_pydate(first_gregorian_date + timedelta(days=i))
        hebrew_date_str = f"{hebrew_date.month}-{hebrew_date.day}"
        english_date = hebrew_date.to_pydate()
        if hebrew_date_str not in hebrew_to_english_dict:
            hebrew_to_english_dict[hebrew_date_str] = [english_date]
        else:
            hebrew_to_english_dict[hebrew_date_str].append(english_date)
    return hebrew_to_english_dict


hebrew_to_english_dict = create_hebrew_to_english_dict()
