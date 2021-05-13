from utils.inrix_utils import *
from utils.general_utils import *


# global parameters
ref_coord = [40.443431, -79.941643]
epsilon = 2.5*1609.34
dt = 15

"""
# -------- Part I: save and filter tmc_info as df -------- ###
# columns: [tmc_code, road, direction, intersection, start_lat, start_lon, end_lat, end_lon, miles, neighbors]
tmc_file = "./inrix_data/tmc/TMC_Identification.csv"
road_list = ['FORBES AVE', '5TH AVE', 'MURRAY AVE', 'N CRAIG ST', 'SHADY AVE', 'BEELER ST',
             'CENTRE AVE', 'BIGELOW BLVD', 'WILKINS AVE']
tmc_list = filter_road(tmc_file, road_list, epsilon, ref_coord)
tmc_df = create_tmc_df(tmc_file, tmc_list)
tmc_df = append_neighbors(tmc_df)
#saveAsPickle(tmc_df, './processed_data/inrix/tmc_df.pkl')
"""


"""
# -------- Part II: save and process feature for each year, each road -------- ###
# columns: [date_time, speed, travel_time]
file_path = "./inrix_data/2019/inrix_2019.csv"
date_time_format = "%Y-%m-%d %H:%M:%S"
year = int(file_path.split('_')[-1].split('.')[0])
feat_dict = construct_inrix_feature_dict(file_path, tmc_list, dt, year)
saveAsPickle(feat_dict, './processed_data/inrix/inrix_{}.pkl'.format(year))
"""
