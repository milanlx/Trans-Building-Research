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


def filter_road(tmc_file, road_list, epsilon, ref_coord):
    """
    - Filter and select inrix measurement given distance to the reference point
    - NOTICE: there are duplicate lines in tmc_file
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
            # account for duplicate cases
            if road in road_list:
                if dist <= epsilon:
                    if tmc_id not in tmc_list:
                        tmc_list.append(tmc_id)
    return tmc_list


def create_tmc_df(tmc_file, tmc_list):
    """
    - create dateframe with the columns:
        - [tmc_code, road, direction, intersection, start_lat, start_lon, end_lat, end_lon, miles]
    - NOTICE: there are duplicate lines in tmc_file
    - Output: pd dataframe
    """
    column_names = ["tmc_code", "road", "direction", "intersection",
               "start_lat", "start_lon", "end_lat", "end_lon", "miles"]
    df = pd.DataFrame(columns=column_names)
    temp_list = []
    with open(tmc_file, 'r') as f:
        next(f)
        for line in f:
            content = line.strip().split(',')
            tmc_code, road, direction, intersection = [str(x) for x in content[0:4]]
            start_lat, start_lon, end_lat, end_lon, miles = [float(x) for x in content[7:12]]
            if tmc_code in tmc_list:
                if tmc_code not in temp_list:
                    temp_list.append(tmc_code)
                    df.loc[len(df.index)] = [tmc_code, road, direction, intersection,
                                            start_lat, start_lon, end_lat, end_lon, miles]
    return df


def append_neighbors(tmc_df):
    """For each tmc_code, find the directed neighbors (index in the df)
    :return: modified tmc_df with "neighbor" column
    """
    n = len(tmc_df.index)
    neighbors = []
    for i in range(n):
        start_lat, start_lon = tmc_df['start_lat'][i], tmc_df['start_lon'][i]
        neighbor = tmc_df.index[(tmc_df['end_lat'] == start_lat) & (tmc_df['end_lon'] == start_lon)].tolist()
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