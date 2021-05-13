import pickle
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date


# -------------------------- save and load -------------------------- #
def saveAsPickle(obj, pickle_file):
    with open(pickle_file, 'wb') as handle:
        pickle.dump(obj, handle, protocol=pickle.HIGHEST_PROTOCOL)
    handle.close()


def loadFromPickle(pickle_file):
    with open(pickle_file, 'rb') as handle:
        unserialized_obj = pickle.load(handle)
    handle.close()
    return unserialized_obj


# ------------------ initialize underlying df with date_time column filled ------------------ #
def initial_df(columns, year, dt):
    num_days = 365
    if int(year)%4 == 0:
        num_days = 366
    # 2020-01-01 00:00:00 - 2021-01-01 00:00:00
    num_rows = int(num_days*24*60/dt) + 1
    start_date = convert_to_datetime("{}/01/01 00:00:00".format(year))
    df = pd.DataFrame(index=np.arange(num_rows), columns=columns)
    date_time_list = get_date_time_list(start_date, dt, num_rows)
    df[columns[0]] = date_time_list
    return df


def get_date_time_list(start_date, dt, num_rows):
    """create and auto-fill the date_time column"""
    date_time_list = []
    date_time_list.append(start_date)
    for i in range(1, num_rows):
        date_time_curr = date_time_list[i-1] + timedelta(minutes=dt)
        date_time_list.append(date_time_curr)
    return date_time_list


def convert_to_datetime(date_time_str, str_format="%Y/%m/%d %H:%M:%S"):
    """str format: %Y/%m/%d %H:%M:%S"""
    # standard_time_format = "%Y/%m/%d %H:%M:%S"
    return datetime.strptime(date_time_str, str_format)


def round_down_time(date_time_obj, delta_t):
    """Round down the time to the next delta_t epoch, i.e, 10:02 - > [10:00, 10:15]"""
    rounded = date_time_obj - (date_time_obj - datetime.min) % timedelta(minutes=delta_t) + timedelta(minutes=delta_t)
    return rounded


def get_day_index(date_time_obj, year):
    # difference (in days) between the current day and first day of the year, start from 0
    first_date = date(year, 1, 1)
    curr_date = date_time_obj.date()
    return (curr_date - first_date).days


def get_day_offset(date_time_obj, delta_t):
    # get the offset of time-in-the-day, start from 0
    curr_minute = date_time_obj.hour*60 + date_time_obj.minute
    return curr_minute//delta_t


# conversion for bus data
def convert_to_datetime_bus(date_str, time_str):
    date_time_format = "%Y-%m-%d %H:%M:%S"
    h, m, s = time_str.split(':')
    if int(h) < 24:
        date_time_str = date_str + ' ' + time_str
        date_time_obj = datetime.strptime(date_time_str, date_time_format)
    else:
        time_str = (':').join([str(int(h)-24), m, s])
        date_time_str = date_str + ' ' + time_str
        date_time_obj = datetime.strptime(date_time_str, date_time_format)
        date_time_obj += timedelta(days=1)
    return date_time_obj
