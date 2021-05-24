import numpy as np
import pandas as pd
from utils.general_utils import loadFromPickle, saveAsPickle


# global parameters
max_dict = {'on': 204.0, 'off': 199.0, 'load': 225.0, 'total_on': 470.0, 'total_off': 546.0}
min_dict = {'on': 1.0,   'off': 1.0,   'load': 1.0,   'total_on': 1.0,   'total_off': 1.0}
group_selected = [0, 1, 2, 3, 4, 7, 8, 12, 13, 14, 15, 16, 17, 24]
hours_selected = [i for i in range(7, 20)]


def get_range_stats(feat_dict, group_selected, hours_selected, stats_type='total'):
    max_dict, min_dict = {'on': [], 'off': []}, {'on': [], 'off': []}
    feat_keys = ['on', 'off']
    for group_id in group_selected:
        df = feat_dict[group_id]
        df = df[df['date_time'].dt.hour.isin(hours_selected)]
        for key in feat_keys:
            df = df.dropna(subset=[key])
            df[key] = df[key].apply(lambda x: np.sum(x))
            max_dict[key].append(np.max(df[key]))
            min_dict[key].append(np.min(df[key]))
    # update
    for key in feat_keys:
        max_dict[key] = np.nanmax(max_dict[key])
        min_dict[key] = np.nanmin(min_dict[key])
    return max_dict, min_dict


def min_max_normalization(df, col_name, min_val, max_val):
    """column-wise normalization, modified in place"""
    df[col_name] = df[col_name].apply(lambda x: (x-min_val)/(max_val-min_val))
    return 0


def impute_missing_value(df, col_name, val):
    """impute missing value in place"""
    df[col_name] = df[col_name].fillna(val)
    return 0


def extract_feat(feat_list, type_str):
    """list input"""
    if type_str != 'load':
        return [np.min(feat_list), np.max(feat_list), np.mean(feat_list), np.sum(feat_list)]
    else:
        return [np.min(feat_list), np.max(feat_list), np.mean(feat_list)]


def construct_bus_feat_df(feat_df):
    list_type = type([])
    columns = ['date_time', 'min_on', 'max_on', 'mean_on', 'total_on', 'min_off', 'max_off', 'mean_off', 'total_off',
               'min_load', 'max_load', 'mean_load']
    num_rows = len(feat_df.index)
    df = pd.DataFrame(index=np.arange(num_rows), columns=columns)
    for i in range(num_rows):
        date_time, on, off, load = feat_df.loc[i]
        on_feat = extract_feat(on, 'on') if type(on) == list_type else [np.nan]*4
        off_feat = extract_feat(off, 'off') if type(off) == list_type else [np.nan]*4
        load_feat = extract_feat(load, 'load') if type(load) == list_type else [np.nan]*3
        df.iloc[i] = [date_time] + on_feat + off_feat + load_feat
    return df


def construct_bus_feat_dict(feat_dict, group_selected, max_dict, min_dict):
    """
    :param feat_dict: key->group_id, val->df, with date_time, on, off, load as features
    :param selected_group: filtered group_id that has few missing value
    :return: normalized and transferred feature dict, with key->group_id, val->df
    """
    processed_dict = {}
    imputed_val = 0.0
    feat_keys = ['on', 'off', 'load', 'total_on', 'total_off']
    for group_id in group_selected:
        print(group_id)
        feat_df = feat_dict[group_id]
        df = construct_bus_feat_df(feat_df)
        for col in df.columns:
            key = col.split('_')[1]
            if key in feat_keys and col not in feat_keys:
                min_max_normalization(df, col, min_dict[key], max_dict[key])
                impute_missing_value(df, col, imputed_val)
            elif key in feat_keys and col in feat_keys:
                min_max_normalization(df, col, min_dict[col], max_dict[col])
                impute_missing_value(df, col, imputed_val)
        processed_dict[group_id] = df
    return processed_dict


name_str = 'dir1_2019'
feat_dict = loadFromPickle('processed_data/bus/features/feat_dict_{}.pkl'.format(name_str))
processed_dict = construct_bus_feat_dict(feat_dict, group_selected, max_dict, min_dict)
# save
saveAsPickle(processed_dict, 'processed_data/bus/features/feat_dict_{}_normalized.pkl'.format(name_str))


# check
"""
feat_dict = loadFromPickle('processed_data/bus/features/feat_dict_dir1_2018_normalized.pkl')
df = feat_dict[15]
df['date_time'] = pd.to_datetime(df['date_time'], errors='raise')
print(df.columns)
df = df[df['date_time'].dt.hour.isin(hours_selected)]
for idx, item in enumerate(df['mean_off']):
    print(idx, item)
"""


