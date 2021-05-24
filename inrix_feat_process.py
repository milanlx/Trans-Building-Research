import numpy as np
import pandas as pd
from utils.general_utils import loadFromPickle, saveAsPickle

# global parameters
max_dict = {'speed': 85.0, 'travel_time': 43.34}
min_dict = {'speed': 1.00, 'travel_time': 0.030}
hours_selected = [i for i in range(7, 20)]


def min_max_normalization(df, col_name, min_val, max_val):
    """column-wise normalization, modified in position"""
    df[col_name] = df[col_name].apply(lambda x: (x-min_val)/(max_val-min_val))
    return 0


def impute_missing_value(df, col_name, val):
    """impute missing value in place"""
    df[col_name] = df[col_name].fillna(val)
    return 0


def segment_feat(feat_list):
    """find the mean of first 1/3, second 1/3 and last 1/3 in time"""
    n = len(feat_list)
    if n == 1:
        return [feat_list[0], feat_list[0], feat_list[0]]
    elif n == 2:
        return [feat_list[0], feat_list[0], feat_list[1]]
    else:
        one_third, two_third = int(n/3), int(2*n/3)
        return [np.mean(feat_list[0:one_third]),
                np.mean(feat_list[one_third:two_third]),
                np.mean(feat_list[two_third:])]


def construct_feat_df(feat_df):
    list_type = type([])
    columns = ['date_time', 'speed_0', 'speed_1', 'speed_2', 'travel_time_0', 'travel_time_1', 'travel_time_2']
    num_rows = len(feat_df.index)
    df = pd.DataFrame(index=np.arange(num_rows), columns=columns)
    for i in range(num_rows):
        date_time, speed, travel_time = feat_df.loc[i]
        speed_feat = segment_feat(speed) if type(speed) == list_type else [np.nan] * 3
        travel_time_feat = segment_feat(travel_time) if type(travel_time) == list_type else [np.nan] * 3
        df.iloc[i] = [date_time] + speed_feat + travel_time_feat
    return df


def construct_inrix_feat_dict(feat_dict, tmc_code_list, max_dict, min_dict):
    processed_dict = {}
    imputed_dict = {'speed': 0.0, 'travel_time': 0.0}
    feat_key = ['speed', 'travel_time']
    for tmc_code in tmc_code_list:
        print(tmc_code)
        feat_df = feat_dict[tmc_code]
        df = construct_feat_df(feat_df)
        for col in df.columns:
            key = col[0:-2]
            if key in feat_key:
                min_max_normalization(df, col, min_dict[key], max_dict[key])
                impute_missing_value(df, col, imputed_dict[key])
        processed_dict[tmc_code] = df
    return processed_dict


# main
tmc_df = loadFromPickle('processed_data/inrix/tmc_df_filter_missing.pkl')
tmc_code_list = tmc_df['tmc_code'].tolist()
year = '2019'
feat_dict = loadFromPickle('processed_data/inrix/inrix_{}.pkl'.format(year))
processed_dict = construct_inrix_feat_dict(feat_dict, tmc_code_list, max_dict, min_dict)
saveAsPickle(processed_dict, 'processed_data/inrix/features/inrix_{}_normalized.pkl'.format(year))


# check
"""
feat_dict = loadFromPickle('processed_data/inrix/features/inrix_2017_normalized.pkl')
dict_keys = list(feat_dict.keys())
print(len(dict_keys))
df = feat_dict[dict_keys[35]]
df['date_time'] = pd.to_datetime(df['date_time'], errors='raise')
df = df[df['date_time'].dt.hour.isin(hours_selected)]
for idx, item in enumerate(df['travel_time_0']):
    print(idx, item)
"""