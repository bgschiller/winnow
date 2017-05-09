import datetime as dt
from datetime import datetime
from datetime import timedelta

from .error import WinnowError

valid_rel_date_values = (
    "last_full_week",
    "last_two_full_weeks",
    "last_7_days",
    "last_14_days",
    "last_30_days",
    "last_45_days",
    "last_60_days",
    "next_7_days",
    "next_14_days",
    "next_30_days",
    "next_45_days",
    "next_60_days",
    'next_week',
    "current_week",
    "current_month",
    "current_and_next_month",
    "current_year",
    "last_month",
    "next_month",
    "next_year",
    "past",
    "past_and_today",
    "future",
    "future_and_today",
    "yesterday",
    "today",
    "tomorrow",
    "past_and_future",
    "two_weeks_past_end_of_month",
)


def interpret_date_range(drange):

    drange = drange.lower().replace(' ', '_')

    today = datetime.now()
    a_few_seconds = timedelta(seconds=3)
    one_day = timedelta(days=1)
    start_of_day = dt.time()
    beginning_today = datetime.combine(today.date(), start_of_day)
    end_today = beginning_today + one_day
    weekstart = datetime.combine(today.date(), start_of_day) - timedelta(days=(today.isoweekday() % 7))
    seven_days = timedelta(days=7)
    fourteen_days = timedelta(days=14)
    thirty_days = timedelta(days=30)
    fortyfive_days = timedelta(days=45)

    if drange == 'last_full_week':
        return weekstart - seven_days, weekstart
    elif drange == 'last_two_full_weeks':
        return weekstart - fourteen_days, weekstart
    elif drange == 'last_7_days':
        return today - seven_days, today + a_few_seconds
    elif drange == 'last_14_days':
        return today - fourteen_days, today + a_few_seconds
    elif drange == 'last_30_days':
        return today - thirty_days, today + a_few_seconds
    elif drange == 'last_45_days':
        return today - fortyfive_days, today + a_few_seconds
    elif drange == 'last_60_days':
        return today - (2 * thirty_days), today + a_few_seconds
    elif drange == 'next_7_days':
        return today, today + seven_days
    elif drange == 'next_14_days':
        return today, today + fourteen_days
    elif drange == 'next_30_days':
        return today, today + thirty_days
    elif drange == 'next_45_days':
        return today, today + fortyfive_days
    elif drange == 'next_60_days':
        return today, today + (2 * thirty_days)
    elif drange == 'next_week':
        return weekstart + seven_days, weekstart + seven_days + seven_days
    elif drange == 'current_week':
        return weekstart, weekstart + seven_days
    elif drange == 'current_month':
        return first_day_of_month(today), last_day_of_month(today)
    elif drange == 'current_and_next_month':
        start_of_current = first_day_of_month(today)
        return start_of_current, last_day_of_month(start_of_current + fortyfive_days)
    elif drange == 'current_and_next_year':
        next_year = last_day_of_year(today, base_month) + timedelta(days=2)
        return first_day_of_year(today, base_month), last_day_of_year(next_year, base_month)
    elif drange == 'two_weeks_past_end_of_month':
        return first_day_of_month(today), last_day_of_month(today) + fourteen_days
    elif drange == 'two_weeks_past_end_of_year':
        return first_day_of_year(today, base_month), last_day_of_year(today, base_month) + fourteen_days
    elif drange == 'current_year':
        return (datetime(year=today.year, month=1, day=1),
                datetime(year=today.year+1, month=1, day=1) - dt.datetime.resolution)
    elif drange == 'next_year':
        next_year = last_day_of_year(today, base_month=1)
        return first_day_of_year(next_year + seven_days, base_month=1), last_day_of_year(next_year + seven_days, base_month=1)
    elif drange == 'last_month':
        last_month = first_day_of_month(today) - timedelta(days=2)
        return first_day_of_month(last_month), last_day_of_month(last_month)
    elif drange == 'next_month':
        next_month = last_day_of_month(today) + timedelta(days=2)
        return first_day_of_month(next_month), last_day_of_month(next_month)
    elif drange == 'past':
        return datetime.fromtimestamp(0), beginning_today - timedelta(microseconds=1)
    elif drange == 'past_and_today':
        return datetime.fromtimestamp(0), today
    elif drange == 'future':
        return today, datetime(year=today.year+1000, month=1, day=1)
    elif drange == 'future_and_today':
        return beginning_today, datetime(year=today.year+1000, month=1, day=1)
    elif drange == 'past_and_future':
        return datetime.fromtimestamp(0), datetime(year=today.year+1000, month=1, day=1)
    elif drange == 'yesterday':
        return beginning_today - one_day, beginning_today
    elif drange == 'today':
        return beginning_today, end_today
    elif drange == 'tomorrow':
        return end_today, end_today + one_day
    else:
        raise WinnowError("unknown date description '{}'".format(drange))
