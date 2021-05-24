import pandas as pd
import numpy as np
from utils.general_utils import *
import networkx as nx
import matplotlib.pyplot as plt


# global parameters
# reference point (campus)
r_lat = 40.443431
r_lon = -79.941643
# FIXED, bounding box box of base map
bbox = (-79.97624, -79.897635, 40.411309, 40.45836)


# -------------------------- raw map -------------------------- #
def get_tmc_coord(tmc_path):
    tmc_df = loadFromPickle(tmc_path)
    # find mean of start/end lat/lon for each tmc_code
    start_lat, start_lon, end_lat, end_lon = [], [], [], []
    n = len(tmc_df.index)
    for i in range(n):
        start_lat.append(np.mean(tmc_df['start_lat'][i]))
        start_lon.append(np.mean(tmc_df['start_lon'][i]))
        end_lat.append(np.mean(tmc_df['end_lat'][i]))
        end_lon.append(np.mean(tmc_df['end_lon'][i]))
    return start_lat, start_lon, end_lat, end_lon


def plot_tmc_map(map_path, output_path, start_lat, start_lon, end_lat, end_lon):
    """plot each of the tmc road with direction"""
    base_map = plt.imread(map_path)
    n = len(start_lat)
    # plot
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.scatter(start_lon, start_lat, zorder=1, alpha=0.8, c='b', s=10)
    ax.scatter(end_lon, end_lat, zorder=1, alpha=0.8, c='b', s=10)
    ax.scatter(r_lon, r_lat, zorder=1, alpha=0.2, c='r', s=200)
    # arrow
    for i in range(n):
        x_direct, y_direct = start_lon[i], start_lat[i]
        x_pos, y_pos = end_lon[i], end_lat[i]
        ax.annotate('', xy=(x_direct, y_direct), xytext=(x_pos, y_pos),
                    arrowprops=dict(arrowstyle='->', lw=1.2))
    # decoration
    ax.set_title('Inrix Spatial Data')
    ax.set_xlim(bbox[0], bbox[1])
    ax.set_ylim(bbox[2], bbox[3])
    ax.imshow(base_map, zorder=0, extent=bbox, aspect='equal')
    plt.savefig(output_path)
    return 0


# -------------------------- networkx plot (edge -> vertex) -------------------------- #
def get_edges(tmc_path):
    tmc_df = loadFromPickle(tmc_path)
    edges = []
    n = len(tmc_df.index)
    for i in range(n):
        neighbors = tmc_df['neighbors'][i]
        for neighbor in neighbors:
            edges.append((i, neighbor))
    return edges


def get_center_coord(start_lat, start_lon, end_lat, end_lon):
    n = len(start_lat)
    coords = {}
    for i in range(n):
        center_lat = (start_lat[i] + end_lat[i]) / 2
        center_lon = (start_lon[i] + end_lon[i]) / 2
        coords[i] = (center_lon, center_lat)
    return coords


def plot_networkx(edges, coords, output_path):
    G = nx.DiGraph()
    G.add_edges_from(edges)
    plt.figure(figsize=(9,9))
    nx.draw_networkx(G, pos=coords, with_labels=True, node_color='blue', font_color='white', arrowsize=10)
    plt.savefig(output_path)
    #plt.show()
    return 0



# raw plot
#tmc_path = 'processed_data/inrix/tmc_df.pkl'
tmc_path = 'processed_data/inrix/tmc_df_filter_missing.pkl'
map_path = './map_data/inrix_org.png'
output_path = 'figure/inrix/original_road_map_2.png'
start_lat, start_lon, end_lat, end_lon = get_tmc_coord(tmc_path)
plot_tmc_map(map_path, output_path, start_lat, start_lon, end_lat, end_lon)

# networkx plot
output_path = 'figure/inrix/equivalent_vertex_map_2.png'
edges = get_edges(tmc_path)
coords = get_center_coord(start_lat, start_lon, end_lat, end_lon)
plot_networkx(edges, coords, output_path)

