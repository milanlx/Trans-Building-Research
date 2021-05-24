import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from utils.general_utils import *

"""
ref: 
   - plot dots: https://towardsdatascience.com/easy-steps-to-plot-geographic-data-on-a-map-python-11217859a2db 
   - get map: https://medium.com/@busybus/rendered-maps-with-python-ffba4b34101c
"""


def get_plot_df(filtered_bus_stops, bus_stops, dirt):
    """:return: df [stop_id, stop_lat, stop_lon], for one direction"""
    stop_list = []
    columns = ['stop_id', 'stop_lat', 'stop_lon']
    df = pd.DataFrame(columns=columns)
    for key in filtered_bus_stops.keys():
        if key[-1] == dirt:
            for stop_id in filtered_bus_stops[key]:
                if stop_id not in stop_list:
                    stop_list.append(stop_id)
    for stop_id in stop_list:
        lat = bus_stops.loc[bus_stops['stop_id'] == stop_id, 'stop_lat'].iloc[0]
        lon = bus_stops.loc[bus_stops['stop_id'] == stop_id, 'stop_lon'].iloc[0]
        df_row = {'stop_id': stop_id, 'stop_lat': lat, 'stop_lon': lon}
        df = df.append(df_row, ignore_index=True)
    return df


filtered_bus_stops = loadFromPickle('processed_data/bus/stops/filtered_stops.pkl')
bus_stops = loadFromPickle("processed_data/bus/stops/ground_truth/bus_stops.pkl")
dirt = '0'
df = get_plot_df(filtered_bus_stops, bus_stops, dirt)

group_center = loadFromPickle('processed_data/bus/stops/test.pkl')

# save
saveAsPickle(df, 'processed_data/bus/stops/bus_stops_total_seq_dir0.pkl')

bbox = (df.stop_lon.min(), df.stop_lon.max(), df.stop_lat.min(), df.stop_lat.max())
bbox = (-79.97441, -79.910184, 40.415419, 40.474327)
print(bbox)

ref_coord = [40.443431, -79.941643]

n = len(df.stop_lon)
labels = range(n)
print(n)

map_org = plt.imread('map_data/map_org.png')

fig, ax = plt.subplots(figsize=(15,18))
ax.scatter(df.stop_lon, df.stop_lat, zorder=1, alpha= 0.8, c='b', s=10)\
# group center point
ax.scatter(group_center.lon_mean, group_center.lat_mean, zorder=1, alpha= 0.8, c='g', s=30)
# direction arrow
for i in range(27):
    for adj in group_center.iat[i,2]:
        x_pos, y_pos = group_center.iat[i, 4], group_center.iat[i, 3]
        x_direct, y_direct = group_center.iat[adj, 4], group_center.iat[adj, 3]
        ax.annotate('', xy=(x_direct, y_direct), xytext=(x_pos, y_pos),
                     arrowprops=dict(arrowstyle='->', lw=1.5))
ax.scatter(ref_coord[1], ref_coord[0], zorder=1, alpha= 0.8, c='r', s=20)
# add number, start from 0
for i, txt in enumerate(labels):
    ax.annotate(txt, (df.stop_lon[i], df.stop_lat[i]))
ax.set_title('Spatial Bus Stops')
ax.set_xlim(bbox[0],bbox[1])
ax.set_ylim(bbox[2],bbox[3])
ax.imshow(map_org, zorder=0, extent=bbox, aspect='equal')
plt.savefig('bus_stop_map_dir0_center.png')


