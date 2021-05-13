from utils.electricity_utils import *


# global parameters:
type_str = 'general'                     # 'general' or 'UC'
building = 'GHC'                         # 'GHC' or 'UC'


"""
# -------- Part I: convert to df format -------- ###
file_path = "electricity_data/cmu_2017-2019_UC_electricity.xlsx"
df = read_data(file_path, type_str)
#saveAsPickle(df, '../electricity_data/raw_{}.pkl'.format(type_str))


# -------- Part II: save and process features for each year -------- ###
# columns: [date_time, ele_increment]
org_dict = loadFromPickle('electricity_data/raw_{}.pkl'.format(type_str))
feat_dict = construct_electricity_data(org_dict, building)
#saveAsPickle(feat_dict, 'processed_data/electricity/ele_{}.pkl'.format(building))
"""