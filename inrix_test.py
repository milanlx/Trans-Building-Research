import numpy as np
import pandas as pd
from utils.inrix_utils import *
from utils.general_utils import *
import matplotlib.pyplot as plt


file_path = 'processed_data/inrix/tmc_df.pkl'
tmc_df = loadFromPickle(file_path)
less_missing_list = [0,1,2,3,4,5,6,7,8,19,20,21,22,23,28,29,30,31,32,37,38,39,40,41,42,43,44,45,48,49,50,51,52,53,54,
                     55,56,57,58,59,62,63,64,65,66]
df = tmc_df.loc[less_missing_list]
df.reset_index(drop=True, inplace=True)
df = df.drop(columns=['neighbors'])
df = append_neighbors(df)
print(df.columns)
print(df)
saveAsPickle(df, 'processed_data/inrix/tmc_df_filter_missing.pkl')