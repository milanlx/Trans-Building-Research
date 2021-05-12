import pandas as pd
import numpy as np
from utils.inrix_utils import get_meter_distance
from utils.general_utils import convert_to_datetime_bus, get_day_index, get_day_offset
from utils.weather_utils import initial_df
from datetime import timedelta, datetime


# global parameters
labels = ['611', '612', '613', '614', '67', '69', '58', '712', '714', '75']


# ---------------------------- raw data handling ---------------------------- #
def get_bus_route_dict():
    """convert bus tickers."""
    labels  = ['611', '612', '613', '614', '67', '69', '58', '712', '714', '75']
    tickers = ['61A', '61B', '61C', '61D', '67', '69', '58', '71B', '71D', '75']
    route_dict = {}
    for i, label in enumerate(labels):
        route_dict[label] = tickers[i]
    return route_dict


def get_bus_stops_df(stops_path):
    """extract stops info to dataframe.
    :return
       - df -> [stop_id, stop_name, stop_lat, stop_lon]
    """
    columns = ['stop_id', 'stop_name', 'stop_lat', 'stop_lon']
    data = pd.DataFrame(columns=columns)
    with open(stops_path, 'r') as f:
        next(f)
        next(f)
        for idx, item in enumerate(f):
            info = item.strip().split(',')
            stop_id, stop_name = info[0], info[2]
            stop_lat, stop_lon = float(info[4]), float(info[5])
            df_row = {'stop_id': stop_id, 'stop_name': stop_name,
                      'stop_lat': stop_lat, 'stop_lon': stop_lon}
            data = data.append(df_row, ignore_index=True)
    return data


def sample_bus_track(file_path, bus_route, max_num):
    """For each route, find the track (sequence of stops) for each dir from fixed number of samples
    :param:
        - bus_route: list of bus route (i.e., [611, 612])
        - max_num: maximum number of record for each route & dir
    :return:
        - dict of df: key: route+dir; value: df -> ['trip_num', 'arr_time', 'dep_time', 'stop_id']
    """
    bus_tracks = {}
    count = {}
    columns = ['trip_num', 'arr_time', 'dep_time', 'stop_id']
    for route in bus_route:
        bus_tracks[route+'+'+str(0)] = pd.DataFrame(columns=columns)
        bus_tracks[route+'+'+str(1)] = pd.DataFrame(columns=columns)
        count[route+'+'+str(0)] = 0
        count[route+'+'+str(1)] = 0
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip().split(',')
            route, dirt, stop_id = line[2], line[1], line[8].strip()
            trip_num = ' '.join([line[6], line[3]])
            arr_time = ':'.join([line[10], line[11], line[12]])
            arr_date_time = convert_to_datetime_bus(line[6], arr_time)
            dep_time = ':'.join([line[13], line[14], line[15]])
            dep_date_time = convert_to_datetime_bus(line[6], dep_time)
            key = route+'+'+dirt
            if key in bus_tracks.keys():
                if len(bus_tracks[key].index) < max_num:
                    df_row = {'trip_num': trip_num, 'arr_time': arr_date_time,
                              'dep_time': dep_date_time, 'stop_id': stop_id}
                    bus_tracks[key] = bus_tracks[key].append(df_row, ignore_index=True)
                    count[key] += 1
                else:
                    continue
                if check_full(count, max_num):
                    break
    # filter and select
    for key in bus_tracks.keys():
        bus_tracks[key] = find_bus_track(bus_tracks[key])
    return bus_tracks


def check_full(count, max_num):
    """helper: check if required number of records is attained"""
    count_list = list(count.values())
    n = len(count_list)
    if max_num*n == sum(count_list) and len(set(count_list)) == 1:
        return True
    else:
        return False


def find_bus_track(df):
    """helper: select one track"""
    most_frequent = df['trip_num'].value_counts().idxmax()
    df = df[df['trip_num']==most_frequent]
    df = df.sort_values(by='arr_time')
    return df


def get_filtered_stops(bus_stops, bus_stop_seq, ref_coord, thres):
    """For each route, only keep stops distance < thres w.r.t. campus """
    bus_filtered_stops = {}
    for key in bus_stop_seq.keys():
        stops = bus_stop_seq[key]
        bus_filtered_stops[key] = []
        for stop_id in stops:
            lat = bus_stops.loc[bus_stops['stop_id'] == stop_id, 'stop_lat'].iloc[0]
            lon = bus_stops.loc[bus_stops['stop_id'] == stop_id, 'stop_lon'].iloc[0]
            dist = get_meter_distance([lat, lon], ref_coord)
            if dist < thres:
                bus_filtered_stops[key].append(stop_id)
    return bus_filtered_stops


def get_stop_seq(bus_track, dirt):
    """
    :return: dict: key -> route+dir, val -> [stop_id]
    """
    bus_stop_seq = {}
    for key in bus_track.keys():
        if key[-1] == dirt:
            stop_seq = bus_track[key]['stop_id'].to_list()
            bus_stop_seq[key] = stop_seq
    return bus_stop_seq


def get_total_stops(bus_filtered_stops):
    """find the union stops of all route"""
    total_stops = []
    for key in bus_filtered_stops.keys():
        seq = bus_filtered_stops[key]
        for stop_id in seq:
            if stop_id not in total_stops:
                total_stops.append(stop_id)
    return total_stops


# built upon get_total_stops, but return df [stop_id, stop_lat, stop_lon]
def get_total_stops_df(total_stops, bus_stops_df):
    columns = ['stop_id', 'stop_lat', 'stop_lon']
    df = pd.DataFrame(columns=columns)
    for stop_id in total_stops:
        stop_lat = bus_stops_df.loc[bus_stops_df['stop_id'] == stop_id, 'stop_lat'].iloc[0]
        stop_lon = bus_stops_df.loc[bus_stops_df['stop_id'] == stop_id, 'stop_lon'].iloc[0]
        df_row = {'stop_id': stop_id, 'stop_lat': stop_lat, 'stop_lon': stop_lon}
        df = df.append(df_row, ignore_index=True)
    return df


# stop_id_list: stops that are not in group_df
def find_group_id(stop_id_list, bus_stops_df, group_df):
    group_id_list = []
    group_lat, group_lon = group_df['lat_means'].tolist(), group_df['lon_means'].tolist()
    group_center = np.asarray([group_lat, group_lon]).T         # n*2
    for stop_id in stop_id_list:
        stop_lat = bus_stops_df.loc[bus_stops_df['stop_id'] == stop_id, 'stop_lat'].iloc[0]
        stop_lon = bus_stops_df.loc[bus_stops_df['stop_id'] == stop_id, 'stop_lon'].iloc[0]
        stop_center = np.asarray([stop_lat, stop_lon])
        dist = np.sqrt(np.sum((group_center - stop_center)**2, axis=1))
        group_id = dist.argmin()
        # assigned to group
        group_df.loc[group_id, 'group_stops_id'].append(stop_id)
        group_df.loc[group_id, 'lat'].append(stop_lat)
        group_df.loc[group_id, 'lon'].append(stop_lon)
        # assign to list
        group_id_list.append(group_id)
    return group_id_list, group_df


# update the group_dict for the additional stops
def update_group_dict(group_df, stop_group_dict):
    group_id, group_stops = group_df['group_id'], group_df['group_stops_id']
    for idx in group_id:
        for stop in group_stops[idx]:
            if stop not in stop_group_dict.keys():
                stop_group_dict[stop] = idx
    return stop_group_dict


# ---------------------------- group assignment, adjacent matrix ---------------------------- #
def get_group_dict(group_path, total_seq):
    """
    :return: dict -> key[stop_id], val[group_num]"""
    group = {}
    group_num = 0
    with open(group_path, 'r') as f:
        next(f)
        for line in f:
            line = line.strip().split(',')
            content = line[1:]
            content = [int(x) for x in content if x]
            for idx in content:
                key = total_seq.iloc[idx]['stop_id']
                group[key] = group_num
            group_num += 1
    return group


def get_group_df(group_dict, total_seq, adj, n):
    """
    return: df [group_id, group_stops_id [list], connected_group_idx [list], [lat], [lon], lat_mean, lon_mean]
    """
    list_type = type([])
    col_names = ["group_id", "group_stops_id", "connected_group_id", "lat", "lon"]
    df = pd.DataFrame(None, index=list(range(n)), columns=col_names)
    for idx in range(n):
        df.iat[idx, 0] = idx
        connected_stop_id = [i for i, x in enumerate(adj[idx]) if x == 1]
        df.iat[idx, 2] = connected_stop_id
    for stop_id in group_dict.keys():
        group_id = group_dict[stop_id]
        lat = total_seq.loc[total_seq['stop_id'] == stop_id, 'stop_lat'].iloc[0]
        lon = total_seq.loc[total_seq['stop_id'] == stop_id, 'stop_lon'].iloc[0]
        if type(df.iat[group_id, 1]) is not list_type:
            df.loc[group_id, 'group_stops_id'] = [stop_id]
            df.loc[group_id, 'lat'] = [lat]
            df.loc[group_id, 'lon'] = [lon]
        else:
            df.loc[group_id, 'group_stops_id'].append(stop_id)
            df.loc[group_id, 'lat'].append(lat)
            df.loc[group_id, 'lon'].append(lon)
    # add mean column
    df['lat_means'] = df['lat'].apply(lambda x: sum(x)/len(x))
    df['lon_means'] = df['lon'].apply(lambda x: sum(x)/len(x))
    return df


def get_directed_adjacent_matrix(group_dict, next_stop_dict, n):
    # without self-loop, i.e., A[i][i] != 1
    adj = [[0 for j in range(n)] for i in range(n)]
    for stop_id in group_dict.keys():
        i = group_dict[stop_id]
        next_stops = next_stop_dict[stop_id]
        for next_stop in next_stops:
            if len(next_stop) > 0:
                j = group_dict[next_stop]
                adj[i][j] = 1 if j!=i else 0
    return adj


def get_next_stop_dict(per_seq, dirt):
    """For each bus stop, get the (right) next stop_id. For last stop, assign '' as its next stop
    :return: dict -> key[stop_id], val[[next_stop_id], list]
    """
    next_stop_dict = {}
    for key in per_seq.keys():
        if key[-1] == dirt:
            stops = per_seq[key]
            n = len(stops)
            for i, stop_id in enumerate(stops):
                next_stop = stops[i+1] if i!=n-1 else ''
                if stop_id not in next_stop_dict.keys():
                    next_stop_dict[stop_id] = [next_stop]
                else:
                    if next_stop not in next_stop_dict[stop_id]:
                        next_stop_dict[stop_id].append(next_stop)
    return next_stop_dict


# ---------------------------- bus feature processing ---------------------------- #
def round_down_time(date_time_obj, delta_t):
    """Round down the time to the next delta_t epoch, i.e, 10:02 - > [10:00, 10:15]"""
    rounded = date_time_obj - (date_time_obj - datetime.min) % timedelta(minutes=delta_t) + timedelta(minutes=delta_t)
    return rounded


# columns: ['date_time', 'on', 'off', 'load']
def read_bus_file(file_path, feat_dict_dir0, feat_dict_dir1, group_dict_dir0, group_dict_dir1, year, dt):
    with open(file_path, 'r') as f:
        for i, line in enumerate(f):
            line = line.strip().split(',')
            route, dirt, stop_id = line[2], line[1], line[8].strip()
            # group index
            if stop_id in group_dict_dir0.keys():
                update_df(line, feat_dict_dir0, group_dict_dir0, year, dt)
            elif stop_id in group_dict_dir1.keys():
                update_df(line, feat_dict_dir1, group_dict_dir1, year, dt)
            if i%100000 == 0:
                print(i)
    return feat_dict_dir0, feat_dict_dir1


def update_df(line, feat_dict, group_dict, year, dt):
    """
    :param line: a line from the raw file, [list]
    :param feat_dict: key -> group_id, val -> df
    :param group_dict: key -> stop_id, val -> group_id
    """
    list_type = type([])
    day_const = int(24*60/dt)
    length_max = len(feat_dict[0].index)
    stop_id = line[8].strip()
    arr_time = ':'.join([line[10], line[11], line[12]])
    arr_date_time = convert_to_datetime_bus(line[6], arr_time)
    dep_time = ':'.join([line[13], line[14], line[15]])
    dep_date_time = convert_to_datetime_bus(line[6], dep_time)
    # on, off, load
    features = line[16:19]
    features = [float(i) for i in features]
    # date_time index
    date_time = round_down_time(dep_date_time, dt)
    offset = day_const * get_day_index(date_time, year) + get_day_offset(date_time, dt)
    # group idx
    group_id = group_dict[stop_id]
    if 0 <= offset < length_max:
        if (dep_date_time - arr_date_time).total_seconds() / 60.0 < 30.0:
            for i in range(3):
                # does not account for zero
                if features[i] > 0:
                    if type(feat_dict[group_id].iat[offset, i + 1]) is not list_type:
                        feat_dict[group_id].iat[offset, i + 1] = [features[i]]
                    else:
                        feat_dict[group_id].iat[offset, i + 1].append(features[i])
        #print(feat_dict[group_id].loc[offset]['date_time'], feat_dict[group_id].loc[offset]['on'],
        #      feat_dict[group_id].loc[offset]['off'], feat_dict[group_id].loc[offset]['load'])
    return 0


def initial_feat_dict(num_groups, columns, year, dt):
    """return: dict, key -> group_id, value -> df ['date_time', 'on', 'off', 'load']"""
    feat_dict = {}
    for i in range(num_groups):
        feat_dict[i] = initial_df(columns, year, dt)
    return feat_dict

