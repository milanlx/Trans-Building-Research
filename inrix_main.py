import numpy as np
import pandas as pd
from utils.inrix_utils import *
from utils.general_utils import *
import matplotlib.pyplot as plt


# global parameters
ref_coord = [40.443431, -79.941643]
thres = 2.5*1609.34
dt = 15


# -------- Part I: save and filter tmc_info as df -------- ###
"""
tmc_file = "./inrix_data/tmc/TMC_Identification.csv"
tmc_df = create_tmc_df(tmc_file)
tmc_df = filter_road(tmc_df, thres, ref_coord)
print(len(tmc_df.index))
#tmc_df.to_csv('tmc.csv')
tmc_df = append_neighbors(tmc_df)
# save
saveAsPickle(tmc_df, 'tmc_df.pkl')
"""

# -------- Part II: save and process feature for each year, each road -------- ###
"""
# columns: [date_time, speed, travel_time]
file_path = "./inrix_data/2019/inrix_2019.csv"
date_time_format = "%Y-%m-%d %H:%M:%S"
year = int(file_path.split('_')[-1].split('.')[0])
tmc_df = loadFromPickle('tmc_df.pkl')
tmc_list = tmc_df['tmc_code'].tolist()
feat_dict = construct_inrix_feature_dict(file_path, tmc_list, dt, year)
saveAsPickle(feat_dict, 'inrix_{}.pkl'.format(year))
"""


feat_dict = loadFromPickle('processed_data/inrix/inrix_2019.pkl')
columns = ['tmc_code'] + [i for i in range(24)] + ['total_num']
missing_df = pd.DataFrame(columns=columns)

key_list = list(feat_dict.keys())
for i in range(len(key_list)):
    h_list = [0]*24
    tmc_code = key_list[i]
    df = feat_dict[key_list[i]]
    nan_values = df[df['speed'].isna()]
    h = nan_values['date_time'].dt.hour.tolist()
    total_num = len(h)
    for item in h:
        h_list[item] += 1
    missing_df.loc[len(missing_df.index)] = [tmc_code] + h_list + [total_num]

missing_df.to_csv('inrix_missing_2019.csv')
