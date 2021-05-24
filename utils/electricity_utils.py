import numpy as np
import pandas as pd
import xlrd
import statistics
from utils.general_utils import *


building_dict = {'GHC': [1], 'Scaife': [2], 'Roberts': [3], 'Baker': [6], 'Porter': [7],
                 'Purnell': [10], 'Hamburg': [18], 'MMCH': [27], 'NSH': [28], 'UC': [1]}


def read_data(file_path, type_str):
    """
    Read in data from excel
    :return: dict, key -> year, val -> df
    """
    years = ['2017', '2018', '2019']
    org_dict = {}
    for year in years:
        df = pd.read_excel(file_path, sheet_name=year)
        if year == '2019':
            if type_str == 'UC':
                df = df.iloc[0:20250, 3:5]
            else:
                df = df.iloc[0:20250, 2:31]
        else:
            if type_str == 'UC':
                df = df.iloc[0:-1, 3:5]
            else:
                df = df.iloc[0:-1, 2:31]
        # processing
        df = orginal_data_processing(df)
        org_dict[year] = df
    return org_dict


def orginal_data_processing(df):
    df.fillna('', inplace=True)             # replace NA with ''
    df.iat[3, 0] = 'date_time'
    df.columns = df.iloc[3]
    df = df.drop([0, 1, 2, 3])
    df = df.reset_index(drop=True)
    df = df.rename_axis(None, axis=1)
    df['date_time'] = df['date_time'].apply(lambda x: convert_to_datetime(x))
    return df


def convert_to_datetime(excel_time):
    """return datetime type directly"""
    return xlrd.xldate_as_datetime(excel_time, 0)


# ------------------------ pre-processing ------------------------ #
def cumulative_to_absolute(org_list):
    n = len(org_list)
    abs_list = [0 for i in range(n)]
    for i in range(1, n):
        abs_list[i] = org_list[i] - org_list[i-1]
    return abs_list


def check_missing_data_errors(df):
    """return: dict, key -> date_time, val -> type of error"""
    str_type = type('string')
    err_dict = {}
    for i, item in enumerate(df.iloc[:,1]):
        if type(item) == str_type:
            err_dict[str(df.iloc[i,0])] = item
    return err_dict


def check_reading_error(df):
    """return: dict, key -> date_time, val -> absolution increment"""
    str_type = type('string')
    err_dict = {}
    for i in range(1, len(df.index)):
        prev, curr = df.iloc[i-1, 1], df.iloc[i, 1]
        if type(prev) != str_type and type(curr) != str_type:
            abs_val = curr - prev
            if abs_val < 0:
                err_dict[str(df.iloc[i,0])] = abs_val
    return err_dict


def fill_with_median(df, med):
    """Fill errors (missing data & error readings) with median, add as a new column"""
    n = len(df.index)
    str_type = type('string')
    df['ele_increment'] = np.zeros(n)
    for i in range(1,n):
        prev, curr = df.iloc[i-1, 1], df.iloc[i, 1]
        if type(prev) != str_type and type(curr) != str_type:
            df.iat[i,2] = curr - prev
        else:
            df.iat[i, 2] = np.nan
    # assign with median
    df.loc[df['ele_increment'] <= 0, 'ele_increment'] = med
    df.fillna({'ele_increment': med}, inplace=True)
    return df


def get_median_increment(df):
    """get the median of absolute increment"""
    str_type = type('string')
    n = len(df.index)
    abs_list = []
    for i in range(1, n):
        prev, curr = df.iloc[i-1,1], df.iloc[i,1]
        if type(prev) != str_type and type(curr) != str_type:
            abs_list.append(curr-prev)
    return statistics.median(abs_list)


def construct_electricity_data(org_dict, building):
    years = ['2017', '2018', '2019']
    feat_dict = {}
    for year in years:
        df = org_dict[year].iloc[:, [0, building_dict[building][0]]]
        med = get_median_increment(df)
        #missing_dict = check_missing_data_errors(df)
        #reading_dict = check_reading_error(df)
        df = fill_with_median(df, med)
        df = df.drop(df.columns[1], 1)
        feat_dict[year] = df
    return feat_dict


"""
# read in raw
file_path = "../electricity_data/cmu_2017-2019_UC_electricity.xlsx"
type_str = 'UC'
df = read_data(file_path, type_str)
saveAsPickle(df, '../electricity_data/raw_{}.pkl'.format(type_str))

# post-processing and save
org_dict = loadFromPickle('../electricity_data/raw_{}.pkl'.format(type_str))
building = 'UC'
df = construct_electricity_data(org_dict, building)
saveAsPickle(df, '../processed_data/electricity/ele_{}.pkl'.format(building))
"""
