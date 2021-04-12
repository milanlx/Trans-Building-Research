import pandas as pd
import numpy as np
import pytz
from datetime import datetime, timedelta



def linear_interpolate(y0, y1, num_pts):
    """linear interpolate num_pts given interval [y0, y1]"""
    res = [0 for i in range(num_pts)]
    delta_y = (y1-y0)/(num_pts+1)
    for i in range(num_pts):
        res[i] = y0 + delta_y*(i+1)
    return res


def convert_to_datetime(date_time_str):
    """read in GMT and output EST, automatically considered DST"""
    # date_str: i.e., '11/6/17 5:00'
    weather_time_format = "%Y/%m/%d %H:%M:%S"
    standard_time_format = "%Y/%m/%d %H:%M:%S"
    gmt = pytz.timezone('GMT')
    est = pytz.timezone('US/Eastern')
    date = datetime.strptime(date_time_str, weather_time_format)
    date_gmt = gmt.localize(date)
    date_est = date_gmt.astimezone(est).strftime(standard_time_format)
    return date_est



def fill_missing_value():
    pass


def read_weather_file(file_path, year, dt):
    col_indicator = 'Date/Time (GMT)'
    columns = ['date_time', 'temp_avg', 'rh_avg']
    df = initial_df(columns, year, dt)
    res = []
    with open(file_path, 'r') as f:
        # skip headers
        for i in range(16):
            next(f)
        for line in f:
            content = line.strip().split(',')
            # skip rows with column names
            if content[0] != col_indicator:
                date_time_str, temp_avg, rh_avg = content[0], float(content[1]), float(content[5])
                date_time = convert_to_datetime(date_time_str)
    return res


def initial_df(columns, year, dt):
    num_days = 365
    if int(year)%4 == 0:
        num_days = 366
    num_rows = int(num_days*60/dt)
    df = pd.DataFrame(index=np.arange(num_rows), columns=columns)
    # fill the date_time column
    return df



file_path = '../data/cwop_hourly-CW5882_20170101-20190901.csv'
#res = read_weather_file(file_path)
#print(res)


columns = ['date_time', 'temp_avg', 'rh_avg']
df = pd.DataFrame(index=np.arange(10), columns=columns)
#print(df)
df.iat[0,0] = '09/18/2020'
df.iat[0,1] = [1,2,3]
print(df.loc[0])

