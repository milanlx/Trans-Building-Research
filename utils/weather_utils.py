import pandas as pd
import numpy as np
import pytz
from datetime import datetime, timedelta, date
from weather.general_utils import *


def linear_interpolate(y0, y1, num_pts):
    """linear interpolate num_pts given interval [y0, y1]"""
    res = [0 for i in range(num_pts)]
    delta_y = (y1-y0)/(num_pts+1)
    for i in range(num_pts):
        res[i] = y0 + delta_y*(i+1)
    return res


def convert_to_datetime_GMT(date_time_str):
    """read in GMT and output EST, automatically considered DST"""
    weather_time_format = "%Y-%m-%d %H:%M:%S"
    standard_time_format = "%Y/%m/%d %H:%M:%S"
    gmt = pytz.timezone('GMT')
    est = pytz.timezone('US/Eastern')
    date = datetime.strptime(date_time_str, weather_time_format)
    date_gmt = gmt.localize(date)
    date_est = date_gmt.astimezone(est).strftime(standard_time_format)
    # convert back to date_time format
    date_est = datetime.strptime(date_est, standard_time_format)
    #date_est = date_gmt.astimezone(est)
    return date_est


def convert_to_datetime(date_time_str):
    """str format: %Y/%m/%d %H:%M:%S"""
    standard_time_format = "%Y/%m/%d %H:%M:%S"
    return datetime.strptime(date_time_str, standard_time_format)



def fill_missing_value(df, dt):
    """on hourly base, fill with most recent record"""
    delta_row = int(60/dt)
    for i in range(0, len(df.index), delta_row):
        temp_avg, rh_avg = df.loc[i]['temp_avg'], df.loc[i]['rh_avg']
        if pd.isna(temp_avg) or pd.isna(rh_avg):
            print(df.loc[i])
            df.iat[i,1] = df.iat[i-delta_row,1]
            df.iat[i,2] = df.iat[i-delta_row,2]
    return df


def fill_interpolate(df, dt):
    """fill 15, 30, 45 using linear interpolated value"""
    delta_row = int(60/dt)
    num_pts = delta_row-1
    for i in range(0, len(df.index)-delta_row, delta_row):
        temp_arr = linear_interpolate(df.loc[i]['temp_avg'], df.loc[i+delta_row]['temp_avg'], num_pts)
        rh_arr = linear_interpolate(df.loc[i]['rh_avg'], df.loc[i+delta_row]['rh_avg'], num_pts)
        for j in range(num_pts):
            df.iat[i+j+1, 1] = temp_arr[j]
            df.iat[i+j+1, 2] = rh_arr[j]
    return df



def read_weather_file(file_path, year, dt):
    day_const = int(24*60/dt)
    col_indicator = 'Date/Time (GMT)'
    columns = ['date_time', 'temp_avg', 'rh_avg']
    df = initial_df(columns, year, dt)
    length_max = len(df.index)
    with open(file_path, 'r') as f:
        # skip headers
        for i in range(16):
            next(f)
        for line in f:
            content = line.strip().split(',')
            # skip rows with column names
            if content[0] != col_indicator:
                # skip no record entry
                if content[0] and content[1] and content[5]:
                    date_time_str, temp_avg, rh_avg = content[0], float(content[1]), float(content[5])
                    date_time = convert_to_datetime_GMT(date_time_str)
                    offset = day_const*get_day_index(date_time) + get_day_offset(date_time, dt)
                    if offset <= len(df.index):
                        df.iat[offset, 1], df.iat[offset, 2] = temp_avg, rh_avg
                        #print(date_time, df.loc[offset]['date_time'], )
    return df


def initial_df(columns, year, dt):
    num_days = 365
    if int(year)%4 == 0:
        num_days = 366
    num_rows = int(num_days*24*60/dt) + 1          # 2020-01-01 00:00:00 - 2020-12-31 00:00:00
    start_date = convert_to_datetime("{}/01/01 00:00:00".format(year))
    df = pd.DataFrame(index=np.arange(num_rows), columns=columns)
    date_time_list = get_date_time_list(start_date, dt, num_rows)
    df[columns[0]] = date_time_list
    return df


# ----------------------- copied from inrix utils ----------------------- #
def get_day_index(date_time_obj):
    # difference (in days) between the current day and first day of the year, start from 0
    year = date_time_obj.year
    first_date = date(year, 1, 1)
    curr_date = date_time_obj.date()
    return (curr_date - first_date).days


def get_day_offset(date_time_obj, delta_t):
    # get the offset of time-in-the-day, start from 0
    curr_minute = date_time_obj.hour*60 + date_time_obj.minute
    return curr_minute//delta_t


def get_date_time_list(start_date, dt, num_rows):
    #standard_time_format = "%Y/%m/%d %H:%M:%S"
    date_time_list = []
    date_time_list.append(start_date)
    for i in range(1, num_rows):
        date_time_curr = date_time_list[i-1] + timedelta(minutes=dt)
        date_time_list.append(date_time_curr)
    return date_time_list


file_path = '../data/cwop_hourly-CW5882_20170101-20190901.csv'
df = read_weather_file(file_path, 2017, 15)
df = fill_missing_value(df, 15)
df = fill_interpolate(df, 15)
print(df)

