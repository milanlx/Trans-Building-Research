from csv import reader
from datetime import timedelta, datetime, date
import numpy as np
import pandas as pd
import math
from statistics import mode


def read_inrix_csv(file_path):
    """
    columns: [tmc_code,	measurement_tstamp,	speed, average_speed,
              reference_speed, travel_time_seconds, confidence_score, cvalue]
    """
    with open(file_path, 'r') as f:
        csv_reader = reader(f)
        for row in csv_reader:
            print(row)


def str_to_datetime(date_time_str, date_time_format):
    # convert string to datetime format
    # date_time_format = "%m/%d/%Y %H:%M"
    date_time_obj = datetime.strptime(date_time_str, date_time_format)
    return date_time_obj


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


def get_week_of_day(date_time_obj):
    # 0-6  <--> Monday-Sunday
    return date_time_obj.weekday()


def get_hour_index(date_time_obj):
    # get hour of the day, 0-23
    return date_time_obj.hour


def round_down_time(date_time_obj, delta_t):
    # round down the time to the last delta_t epoch
    rounded = date_time_obj - (date_time_obj - datetime.min) % timedelta(minutes=delta_t)
    return rounded


def increment_datetime(year, offset, delta_t, date_time_format="%Y-%m-%d %H:%M:%S"):
    # return datetime given start year and offset
    date_time_str = year + "-01-01" + " 00:00:00"
    date_time_obj = str_to_datetime(date_time_str, date_time_format)
    return date_time_obj + timedelta(minutes=offset*delta_t)


def filter_road(tmc_file, road_list, epsilon, ref_coord):
    """
    - Filter and select inrix measurement given distance to the reference point
    - Input:
        - tmc_file: TMC_Identification, csv
        - road_list: list of road names, str
        - epsilon: distance threshold, in meter
        - ref_coord: [lat, lon] of the reference point on campus
    - Output: list [] of tmc id
    """
    tmc_list = []
    with open(tmc_file, 'r') as f:
        next(f)
        for line in f:
            content = line.strip().split(',')
            tmc_id = str(content[0])
            road = str(content[1])
            tgt_lat = (float(content[7]) + float(content[9]))/2
            tgt_lon = (float(content[8]) + float(content[10]))/2
            dist = get_meter_distance([tgt_lat, tgt_lon], ref_coord)
            if road in road_list:
                if dist <= epsilon:
                    tmc_list.append(tmc_id)
    return tmc_list


def create_tmc_df(tmc_file, tmc_list):
    """
    - create dateframe with the columns:
        - [tmc_code, road, direction, intersection, start_lat, start_lon, end_lat, end_lon, miles]
    - Input:
    - Output: pd dataframe
    """
    column_names = ["tmc_code", "road", "direction", "intersection",
               "start_lat", "start_lon", "end_lat", "end_lon", "miles" ]
    df = pd.DataFrame(columns=column_names)
    with open(tmc_file, 'r') as f:
        next(f)
        for line in f:
            content = line.strip().split(',')
            tmc_code, road, direction, intersection = [str(x) for x in content[0:4]]
            start_lat, start_lon, end_lat, end_lon, miles = [float(x) for x in content[7:12]]
            if tmc_code in tmc_list:
                df.loc[len(df.index)] = [tmc_code, road, direction, intersection,
                                         start_lat, start_lon, end_lat, end_lon, miles]
    return df


def create_aggregated_inrix_df(inrix_file, tmc_list, delta_t, date_time_format="%Y-%m-%d %H:%M:%S"):
    """
    - read in inrix measurements and create dict: duration is one year
        - key: tmc_code
        - value: df object, with column
            [datetime, speed, avg_speed, travel_time, confidence_score]
    - Input:
    - Output: dict
    """
    list_type = type([])
    day_len = int(24*60/delta_t)
    # initialize pd panel
    col_names = ["date_time", "speed", "avg_speed", "travel_time", "conf_score"]
    row_num = int(365*24*60/delta_t)
    data = {}
    for tmc_code in tmc_list:
        data[tmc_code] = pd.DataFrame(None, index=list(range(row_num)), columns=col_names)
    # read in file
    with open(inrix_file, 'r') as f:
        next(f)
        for line in f:
            content = line.strip().split(',')
            tmc_code, date_time, speed, avg_speed, travel_time, conf_score = \
                str(content[0]), str_to_datetime(str(content[1]), date_time_format), float(content[2]), \
                float(content[3]), float(content[5]), float(content[6])
            # check if tmc_code in selected list
            if tmc_code in tmc_list:
                feat_list = [speed, avg_speed, travel_time, conf_score]
                rounded_date = round_down_time(date_time, delta_t)
                day_idx = get_day_index(rounded_date)
                offset_idx = get_day_offset(rounded_date, delta_t)
                idx = day_idx*day_len + offset_idx
                if pd.isna(data[tmc_code].iat[idx, 0]):
                    data[tmc_code].iat[idx, 0] = rounded_date
                for i in range(len(feat_list)):
                    if type(data[tmc_code].iat[idx, i+1]) != list_type:
                        data[tmc_code].iat[idx, i+1] = [feat_list[i]]
                    else:
                        data[tmc_code].iat[idx, i+1].append(feat_list[i])
                #print(df.loc[idx, :])
    return data


def reduce_inrix_df(data, delta_t=15):
    """
    - reduce each feature by mean or mode, use -1 for missing data
    - Input:
        - data: dict of df
    - Output:
        - reduced_data: dict of reduced df
    """
    # assume columns are fixed
    list_type = type([])
    row_num = int(365 * 24 * 60 / delta_t)
    for tmc_code in data.keys():
        print(tmc_code)
        for row in range(row_num):
            for col in range(1,5):
                curr_list = data[tmc_code].iat[row, col]
                # handle missing data
                if type(curr_list) != list_type:
                    data[tmc_code].iat[row, col] = -1
                else:
                    if col != 4:
                        data[tmc_code].iat[row, col] = mean_of_list(curr_list)
                    # for conf_score, use mode
                    if col == 4:
                        if len(curr_list) < 4:
                            data[tmc_code].iat[row, col] = max(curr_list)
                        else:
                            data[tmc_code].iat[row, col] = mean_of_list(curr_list)
    return data


# ---------------------------- copied from 2019 work ---------------------------- #
def get_meter_distance(tgt_coord, ref_coord):
    """
    - Compute distance between two points in meters
    - Input:
        - tgt_coord: [lat1, lon1]
        - ref_coord: [lat2, lon2]
    - Output:
        - dist: float, distance in meters
    """
    # parameter in regression, y = a x + b
    a, b = 87758.38340014, 15.216382202612408
    # coordination distance
    x = np.sqrt(np.square(tgt_coord[0]-ref_coord[0]) + np.square(tgt_coord[1]-ref_coord[1]))
    return a*x + b


# ---------------------------- calculation ---------------------------- #
def mean_of_list(l):
    return sum(l)/len(l)


def mode_of_list(l):
    return mode(l)


def roundup_to_nearest_10(x):
    return 10*math.ceil(x/10)


# ---------------------------- appendix ---------------------------- #
def get_all_tmc_road(tmc_file):
    """
    - get all unique road name in tmc_identification file
    - Input:
    - Output: list
    """
    tmc_road = []
    with open(tmc_file, 'r') as f:
        next(f)
        for line in f:
            content = line.strip().split(',')
            road = str(content[1])
            if road not in tmc_road and len(road) > 0:
                tmc_road.append(road)
    return tmc_road


def get_closest_inrix_loc(df, ref_coord):
    row_num = len(df.index)
    c_lat = 0
    c_lon = 0
    c_dist = np.inf
    for i in range(row_num):
        cur_lat = df.iat[i, 4]
        cur_lon = df.iat[i, 5]
        tgt_coord = [cur_lat, cur_lon]
        cur_dist = get_meter_distance(tgt_coord, ref_coord)
        if cur_dist < c_dist:
            c_dist = cur_dist
            c_lat = cur_lat
            c_lon = cur_lon
    return c_lat, c_lon

