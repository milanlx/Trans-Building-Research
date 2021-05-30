import numpy as np
import pandas as pd
import xlrd
import statistics
import pickle
import matplotlib.pyplot as plt


def saveAsPickle(obj, pickle_file):
    with open(pickle_file, 'wb') as handle:
        pickle.dump(obj, handle, protocol=pickle.HIGHEST_PROTOCOL)
    handle.close()


def loadFromPickle(pickle_file):
    with open(pickle_file, 'rb') as handle:
        unserialized_obj = pickle.load(handle)
    handle.close()
    return unserialized_obj


def read_data(file_path, type_str):
    """Read in data from excel
    :param: type_str: 'heating' or 'cooling'
    :return: dict, key -> year, val -> df
    """
    years = ['2018', '2019']
    org_dict = {}
    for year in years:
        df = pd.read_excel(file_path, sheet_name=year)
        if type_str == 'cooling':
            df = df.iloc[4:-1, [3,4]]
            df.columns = ['date_time', 'chilled_water']
        elif type_str == 'heating':
            df = df.iloc[4:-1, [3,6]]
            df.columns = ['date_time', 'steam']
        # processing
        df['date_time'] = df['date_time'].apply(lambda x: convert_to_datetime(x))
        if year == '2019':
            month_mask = [1,2,3,4,5]
            df = df.loc[df['date_time'].dt.month.isin(month_mask)]
        #df = orginal_data_processing(df)
        org_dict[year] = df
    return org_dict


def cumulative_to_absolute(df_dict):
    for key in df_dict.keys():
        df = df_dict[key]
        col_name = df.columns[1]
        data = df[col_name].to_numpy()
        n = data.shape[0]
        arr = np.zeros(n)
        for i in range(1, n):
            arr[i] = data[i] - data[i - 1]
        df[col_name] = arr
        # update
        df_dict[key] = df
    return df_dict


def convert_to_datetime(excel_time):
    """return datetime type directly"""
    return xlrd.xldate_as_datetime(excel_time, 0)


def check_missing_data_errors(df):
    """return: dict, key -> date_time, val -> type of error"""
    str_type = type('string')
    err_dict = {}
    for i, item in enumerate(df.iloc[:,1]):
        if type(item) == str_type:
            err_dict[str(df.iloc[i,0])] = item
    return err_dict


"""
# load in data
file_path = '../data/heating_cooling/cmu_heating_cooling_static.xlsx'
type_str = 'heating'
df_dict = read_data(file_path, type_str)
saveAsPickle(df_dict, '../data/heating_cooling/{}_org.pkl'.format(type_str))

# convert cumulative to absolute value
df_dict = loadFromPickle('../data/heating_cooling/heating_org.pkl')
df_dict = cumulative_to_absolute(df_dict)
saveAsPickle(df_dict, '../data/heating_cooling/heating_processed.pkl')
"""


