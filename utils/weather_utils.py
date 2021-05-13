import pandas as pd
import numpy as np
import pytz
from datetime import datetime, timedelta, date
from utils.general_utils import *


def linear_interpolate(y0, y1, num_pts):
    """linear interpolate num_pts given interval [y0, y1]"""
    res = [0 for i in range(num_pts)]
    delta_y = (y1-y0)/(num_pts+1)
    for i in range(num_pts):
        res[i] = y0 + delta_y*(i+1)
    return res


def convert_to_datetime_GMT(date_time_str):
    """read in GMT and output EST, automatically considered DST"""
    weather_time_format, standard_time_format = "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"
    gmt, est = pytz.timezone('GMT'), pytz.timezone('US/Eastern')
    date_time = datetime.strptime(date_time_str, weather_time_format)
    date_gmt = gmt.localize(date_time)
    date_est = date_gmt.astimezone(est).strftime(standard_time_format)
    # convert back to date_time format
    date_est = datetime.strptime(date_est, standard_time_format)
    return date_est


def convert_to_datetime(date_time_str):
    """str format: %Y/%m/%d %H:%M:%S"""
    standard_time_format = "%Y/%m/%d %H:%M:%S"
    return datetime.strptime(date_time_str, standard_time_format)


def fill_missing_value(df, dt):
    """on hourly base, fill with most recent record"""
    delta_row = int(60/dt)
    temp_counter, rh_counter = 0, 0
    for i in range(0, len(df.index), delta_row):
        temp_avg, rh_avg = df.loc[i]['temp_avg'], df.loc[i]['rh_avg']
        if pd.isna(temp_avg):
            df.iat[i, 1] = fill_with_nearest_value(df, i, delta_row, 1)
            temp_counter += 1
        if pd.isna(rh_avg):
            df.iat[i, 2] = fill_with_nearest_value(df, i, delta_row, 2)
            rh_counter += 1
    print('temp missing: ' + str(temp_counter))
    print('rh missing: ' + str(rh_counter))
    return df


def fill_with_nearest_value(df, i, delta_row, idx):
    diff = delta_row
    max_len = len(df.index)
    # up search
    while i-diff > 0:
        val = df.iloc[i-diff, idx]
        if pd.isna(val):
            diff += diff
        else:
            return val
    # down search
    diff = delta_row
    while i+diff < max_len:
        val = df.iloc[i+diff, idx]
        if pd.isna(val):
            diff += diff
        else:
            return val


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
    file_name = file_path.split('/')[2].split('_')[0]
    with open(file_path, 'r') as f:
        # skip headers
        for i in range(16):
            next(f)
        for line in f:
            content = line.strip().split(',')
            # skip rows with column names
            if content[0] != col_indicator:
                if file_name == 'cwop':
                    date_time_str = content[0]
                    temp_avg = float(content[1]) if content[1] else np.nan
                    rh_avg = float(content[5]) if content[5] else np.nan
                elif file_name == 'faa':
                    date_time_str = content[0]
                    temp_avg = float(content[1]) if content[1] else np.nan
                    rh_avg = float(content[7]) if content[7] else np.nan
                date_time = convert_to_datetime_GMT(date_time_str)
                offset = day_const*get_day_index(date_time, year) + get_day_offset(date_time, dt)
                if 0 <= offset < length_max:
                    df.iat[offset, 1], df.iat[offset, 2] = temp_avg, rh_avg
    return df


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


def construct_weather_feature(file_path, dt):
    """
    :param dt: time resolution in minute, default = 15
    :return: dict: key -> year, val -> df ['date_time', 'temp_avg', 'rh_avg']
    """
    feat_dict = {}
    keys = ['2017', '2018', '2019']
    for key in keys:
        df = read_weather_file(file_path, int(key), dt)
        df = fill_missing_value(df, dt)
        df = fill_interpolate(df, dt)
        feat_dict[key] = df
    return feat_dict


# ----------------------- modified from inrix_utils ----------------------- #
def get_day_index(date_time_obj, year):
    # difference (in days) between the current day and first day of the year, start from 0
    first_date = date(year, 1, 1)
    curr_date = date_time_obj.date()
    return (curr_date - first_date).days


def get_day_offset(date_time_obj, delta_t):
    # get the offset of time-in-the-day, start from 0
    curr_minute = date_time_obj.hour*60 + date_time_obj.minute
    return curr_minute//delta_t


"""
# main
file_path = '../weather_data/faa_hourly-KAGC_20170101-20190901.csv'
dt = 15
feat_dict = construct_weather_feature(file_path, dt)
saveAsPickle(feat_dict, '../processed_data/weather/faa.pkl')
"""


