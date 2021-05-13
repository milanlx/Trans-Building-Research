import pickle
import pandas as pd
import numpy as np
from utils.bus_utils import *
from utils.general_utils import loadFromPickle, saveAsPickle


# global parameters (reused at least twice)
ref_coord = [40.443431, -79.941643]
thres = 3000
num_groups = 27
dt = 15


# -------- Part I: save stop information as df -------- ###
# columns: [stop_id, stop_name, stop_lat, stop_lon]
"""
stops_path = 'bus_data/stops/stops.txt'
stop_df = get_bus_stops_df(stops_path)
#saveAsPickle(stop_df, 'processed_data/bus/stops/ground_truth/bus_stops.pkl')
"""

# -------- Part II: save & sample bus track for each route  -------- ###
"""
file_path = "../trans_cmu_relation_analysis/files/bus_csv/1611.csv"
bus_route = labels
max_num = 500
bus_track = sample_bus_track(file_path, bus_route, max_num)
output_path = './processed_data/bus/stops/sampled_tracks/1611_bus_track.pkl'
#saveAsPickle(bus_track, output_path)
"""


# -------- Part III: save & initialize * assign stops to each group  -------- ###
# columns: [group_id, group_stops_id, connected_group_id, lat, lon, lat_means, lon_means]
"""
dirt = '1'
group_path = 'processed_data/bus/stops/ground_truth/bus_stops_groups_dir1.csv'
bus_stops_df = loadFromPickle("processed_data/bus/stops/ground_truth/bus_stops.pkl")
bus_track = loadFromPickle("processed_data/bus/stops/sampled_tracks/1903_May_bus_track.pkl")
group_df, group_dict = initialize_group_df_dict(num_groups, dirt, ref_coord, thres, group_path, bus_stops_df, bus_track)
#saveAsPickle(group_df, 'processed_data/bus/stops/ground_truth/group_df_dir1.pkl')
#saveAsPickle(group_dict, 'processed_data/bus/stops/ground_truth/group_dict_dir1.pkl')
"""


# -------- Part IV: save & update stops in each group_df  -------- ###
# columns: [group_id, group_stops_id, connected_group_id, lat, lon, lat_means, lon_means]
"""
dirt = '0'
bus_stops_df = loadFromPickle("processed_data/bus/stops/ground_truth/bus_stops.pkl")
stop_group_dict = loadFromPickle("processed_data/bus/stops/ground_truth/group_dict_dir0.pkl")
group_df = loadFromPickle("processed_data/bus/stops/ground_truth/group_df_dir0.pkl")
bus_track = loadFromPickle("processed_data/bus/stops/sampled_tracks/1611_bus_track.pkl")
group_df, stop_group_dict = update_full_group_dict(bus_stops_df, stop_group_dict, group_df, bus_track, ref_coord, thres, dirt)
#saveAsPickle(group_df, 'processed_data/bus/stops/update_ground_truth/full_group_df_dir0.pkl')
#saveAsPickle(stop_group_dict, 'processed_data/bus/stops/update_ground_truth/full_group_dict_dir0.pkl')
"""


# -------- Part V: save & process features for each group, each direction, each year  -------- ###
# feat_df, columns: [on, off, load], each is a list
"""
year = 2017
columns = ['date_time', 'on', 'off', 'load']
# read in files
group_dict_dir0 = loadFromPickle('processed_data/bus/stops/update_ground_truth/full_group_dict_dir0.pkl')
group_dict_dir1 = loadFromPickle('processed_data/bus/stops/update_ground_truth/full_group_dict_dir1.pkl')
# file path
file_path = '../trans_cmu_relation_analysis/files/bus_csv/1611.csv'

# if no such file exist, initialize 
#feat_dict_dir0 = initial_feat_dict(num_groups, columns, year, dt)
#feat_dict_dir1 = initial_feat_dict(num_groups, columns, year, dt)

feat_dict_dir0 = loadFromPickle('./processed_data/bus/features/feat_dict_dir0_{}.pkl'.format(year))
feat_dict_dir1 = loadFromPickle('./processed_data/bus/features/feat_dict_dir1_{}.pkl'.format(year))
feat_dict_dir0, feat_dict_dir1 = read_bus_file(file_path, feat_dict_dir0, feat_dict_dir1,
                                               group_dict_dir0, group_dict_dir1, year, dt)
# save file
#saveAsPickle(feat_dict_dir0, './processed_data/bus/features/feat_dict_dir0_{}.pkl'.format(year))
#saveAsPickle(feat_dict_dir1, './processed_data/bus/features/feat_dict_dir1_{}.pkl'.format(year))
"""