import numpy as np
import pandas as pd
from utils.inrix_utils import *
from utils.general_utils import *
import matplotlib.pyplot as plt

# check ratio of missing value for each center
group_selected = [0, 1, 2, 3, 4, 7, 8, 12, 13, 14, 15, 16, 17, 24]
"""
feat_dict = loadFromPickle('processed_data/bus/features/feat_dict_dir1_2018.pkl')
print(feat_dict[0].columns)

columns = ['group_id'] + [i for i in range(24)] + ['total_num']
missing_df = pd.DataFrame(columns=columns)

key_list = list(feat_dict.keys())
for i in range(len(key_list)):
    h_list = [0]*24
    group_id = key_list[i]
    df = feat_dict[key_list[i]]
    nan_values = df[df['on'].isna()]
    h = nan_values['date_time'].dt.hour.tolist()
    total_num = len(h)
    for item in h:
        h_list[item] += 1
    missing_df.loc[len(missing_df.index)] = [group_id] + h_list + [total_num]

missing_df.to_csv('bus_missing_dir1_2018_on.csv')
"""


df = loadFromPickle('processed_data/bus/stops/update_ground_truth/full_group_df_dir1.pkl')
print(df.columns)
df = df.loc[group_selected]
df.reset_index(drop=True, inplace=True)
print(df)
saveAsPickle(df, 'processed_data/bus/stops/update_ground_truth/full_group_df_dir1_filtered.pkl')