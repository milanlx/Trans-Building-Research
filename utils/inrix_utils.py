from csv import reader
from datetime import timedelta, datetime, date
import numpy as np
import pandas as pd
import math
from statistics import mode
from utils.general_utils import *


def str_to_datetime(date_time_str, date_time_format):
    # convert string to datetime format
    # date_time_format = "%m/%d/%Y %H:%M"
    date_time_obj = datetime.strptime(date_time_str, date_time_format)
    return date_time_obj


def get_week_of_day(date_time_obj):
    # 0-6  <--> Monday-Sunday
    return date_time_obj.weekday()


def get_hour_index(date_time_obj):
    # get hour of the day, 0-23
    return date_time_obj.hour


def increment_datetime(year, offset, delta_t, date_time_format="%Y-%m-%d %H:%M:%S"):
    # return datetime given start year and offset
    date_time_str = year + "-01-01" + " 00:00:00"
    date_time_obj = str_to_datetime(date_time_str, date_time_format)
    return date_time_obj + timedelta(minutes=offset*delta_t)


def filter_road(tmc_df, thres, ref_coord):
    """
    - Filter and select inrix data point given distance to the reference point, and year of measurement
    - return: filtered tmc_df
    """
    ref_start_date = pd.to_datetime('2017-05-16')
    ref_end_date = pd.to_datetime('2019-03-17')
    n = len(tmc_df.index)
    filtered_df = pd.DataFrame(columns=tmc_df.columns.tolist())
    for i in range(n):
        tmc_code = tmc_df.loc[i, 'tmc_code']
        start_date_list = tmc_df.loc[i, 'active_start_date']
        end_date_list = tmc_df.loc[i, 'active_end_date']
        start_lat_list = tmc_df.loc[i, 'start_lat']
        start_lon_list = tmc_df.loc[i, 'start_lon']
        end_lat_list = tmc_df.loc[i, 'end_lat']
        end_lon_list = tmc_df.loc[i, 'end_lon']
        # ignore tmc_code with letters
        if not any(c.isalpha() for c in tmc_code):
            # check year of coverage 2017 - 2019
            if len(start_date_list) == 4 and len(end_date_list) == 4:
                if min(start_date_list) < ref_start_date and max(end_date_list) > ref_end_date:
                    # check distance to campus
                    n = len(start_lat_list)
                    dist_list = []
                    for j in range(n):
                        tgt_lat = (start_lat_list[j] + end_lat_list[j])/2
                        tgt_lon = (start_lon_list[j] + end_lon_list[j]) / 2
                        dist = get_meter_distance([tgt_lat, tgt_lon], ref_coord)
                        dist_list.append(dist)
                    if min(dist_list) <= thres:
                        filtered_df.loc[len(filtered_df.index)] = tmc_df.loc[i]
    return filtered_df


def create_tmc_df(tmc_file):
    """
    - create dateframe with the columns:
        - [tmc_code, road, direction, intersection, start_lat, start_lon, end_lat,
           end_lon, miles, active_start_date, active_end_date]
    - NOTICE: there are duplicate lines in tmc_file, so that for lat/lon and start/end date list is used
    - Output: pd dataframe
    """
    column_names = ['tmc_code', 'road', 'direction', 'intersection', 'start_lat', 'start_lon',
                    'end_lat', 'end_lon', 'miles', 'active_start_date', 'active_end_date']
    df = pd.DataFrame(columns=column_names)
    tmc_list = []
    with open(tmc_file, 'r') as f:
        next(f)
        for line in f:
            content = line.strip().split(',')
            tmc_code, road, direction, intersection = [str(x) for x in content[0:4]]
            start_lat, start_lon, end_lat, end_lon, miles = [float(x) for x in content[7:12]]
            start_date = str(content[16]).split(' ')[0] if content[16] else '2017-01-01'
            end_date = str(content[17]).split(' ')[0] if content[17] else start_date
            if tmc_code not in tmc_list:
                df.loc[len(df.index)] = [tmc_code, road, direction, intersection, [start_lat], [start_lon], [end_lat],
                                         [end_lon], [miles], [pd.to_datetime(start_date)], [pd.to_datetime(end_date)]]
                tmc_list.append(tmc_code)
            else:
                idx = df[df['tmc_code']==tmc_code].index.tolist()[0]
                df.loc[idx].at['start_lat'].append(start_lat)
                df.loc[idx].at['start_lon'].append(start_lon)
                df.loc[idx].at['end_lat'].append(end_lat)
                df.loc[idx].at['end_lon'].append(end_lon)
                df.loc[idx].at['miles'].append(miles)
                df.loc[idx].at['active_start_date'].append(pd.to_datetime(start_date))
                df.loc[idx].at['active_end_date'].append(pd.to_datetime(end_date))
    return df


def append_neighbors(tmc_df):
    """For each tmc_code, find the directed neighbors (index in the df)
    :return: modified tmc_df with "neighbor" column added
    """
    n = len(tmc_df.index)
    neighbors = []
    for i in range(n):
        neighbor = []
        end_lat, end_lon = tmc_df['end_lat'][i], tmc_df['end_lon'][i]
        for j in range(n):
            start_lat, start_lon = tmc_df['start_lat'][j], tmc_df['start_lon'][j]
            # without self loop
            if i != j:
                if any(item in end_lat for item in start_lat) and any(item in end_lon for item in start_lon):
                    neighbor.append(j)
        neighbors.append(neighbor)
    tmc_df['neighbors'] = neighbors
    return tmc_df


def construct_inrix_feature_dict(file_path, tmc_list, dt, year, date_time_format="%Y-%m-%d %H:%M:%S"):
    """Read in inrix measurements and create dict. The conf_score are all 30 in the files
    :return: dict, key -> tmc_code, val -> [datetime, speed, travel_time, confidence_score]
    """
    day_const = int(24*60/dt)
    list_type = type([])
    columns = ["date_time", "speed", "travel_time"]
    feat_dict = {}
    count = 0
    for tmc_code in tmc_list:
        feat_dict[tmc_code] = initial_df(columns, year, dt)
    with open(file_path, 'r') as f:
        next(f)
        for line in f:
            content = line.strip().split(',')
            tmc_code, date_time = str(content[0]), str_to_datetime(str(content[1]), date_time_format)
            # speed, travel_time
            features = [float(content[2]), float(content[5])]
            if tmc_code in tmc_list:
                length_max = len(feat_dict[tmc_code].index)
                rounded_date_time = round_down_time(date_time, dt)
                offset = day_const * get_day_index(rounded_date_time, year) + get_day_offset(rounded_date_time, dt)
                if 0 <= offset < length_max:
                    for i in range(2):
                        if type(feat_dict[tmc_code].iat[offset, i+1]) is not list_type:
                            feat_dict[tmc_code].iat[offset, i+1] = [features[i]]
                        else:
                            feat_dict[tmc_code].iat[offset, i+1].append(features[i])
            count += 1
            if count%100000 == 0:
                print('processed {} lines'.format(count))
    return feat_dict


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
