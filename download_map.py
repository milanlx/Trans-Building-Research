# RA, 2019-01-16
# Download a rendered map from Mapbox based on a bounding box
# License: CC0 -- no rights reserved

import io
import urllib.request
from PIL import Image
from math import pi, log, tan, exp, atan, log2, floor

# Convert geographical coordinates to pixels
# https://en.wikipedia.org/wiki/Web_Mercator_projection
# Note on google API:
# The world map is obtained with lat=lon=0, w=h=256, zoom=0
# Note on mapbox API:
# The world map is obtained with lat=lon=0, w=h=512, zoom=0
#
# Therefore:
ZOOM0_SIZE = 512  # Not 256


# Geo-coordinate in degrees => Pixel coordinate
def g2p(lat, lon, zoom):
    return (
        # x
        ZOOM0_SIZE * (2 ** zoom) * (1 + lon / 180) / 2,
        # y
        ZOOM0_SIZE / (2 * pi) * (2 ** zoom) * (pi - log(tan(pi / 4 * (1 + lat / 90))))
    )


# Pixel coordinate => geo-coordinate in degrees
def p2g(x, y, zoom):
    return (
        # lat
        (atan(exp(pi - y / ZOOM0_SIZE * (2 * pi) / (2 ** zoom))) / pi * 4 - 1) * 90,
        # lon
        (x / ZOOM0_SIZE * 2 / (2 ** zoom) - 1) * 180,
    )


# axis to mapbox
def ax2mb(left, right, bottom, top):
    return (left, bottom, right, top)


# mapbox to axis
def mb2ax(left, bottom, right, top):
    return (left, right, bottom, top)


# bbox = (left, bottom, right, top) in degrees
def get_map_by_bbox(bbox):
    # Token from https://www.mapbox.com/api-documentation/maps/#static
    token = "pk.eyJ1IjoiYnVzeWJ1cyIsImEiOiJjanF4cXNoNmEwOG1yNDNycGw5bTByc3g5In0.flzpO633oGAY5aa-RQa4Ow"

    # The region of interest in geo-coordinates in degrees
    # For example, bbox = [120.2206, 22.4827, 120.4308, 22.7578]
    (left, bottom, right, top) = bbox

    # Sanity check
    assert (-90 <= bottom < top <= 90)
    assert (-180 <= left < right <= 180)

    # Rendered image map size in pixels as it should come from MapBox (no retina)
    (w, h) = (1024, 1024)

    # The center point of the region of interest
    (lat, lon) = ((top + bottom) / 2, (left + right) / 2)

    # Reduce precision of (lat, lon) to increase cache hits
    snap_to_dyadic = (lambda a, b: (lambda x, scale=(2 ** floor(log2(abs(b - a) / 4))): (round(x / scale) * scale)))

    lat = snap_to_dyadic(bottom, top)(lat)
    lon = snap_to_dyadic(left, right)(lon)

    assert ((bottom < lat < top) and (left < lon < right)), "Reference point not inside the region of interest"

    # Look for appropriate zoom level to cover the region of interest
    for zoom in range(16, 0, -1):
        # Center point in pixel coordinates at this zoom level
        (x0, y0) = g2p(lat, lon, zoom)

        # The "container" geo-region that the downloaded map would cover
        (TOP, LEFT) = p2g(x0 - w / 2, y0 - h / 2, zoom)
        (BOTTOM, RIGHT) = p2g(x0 + w / 2, y0 + h / 2, zoom)

        # Would the map cover the region of interest?
        if (LEFT <= left < right <= RIGHT):
            if (BOTTOM <= bottom < top <= TOP):
                break

    # Collect all parameters
    params = {
        'style': "streets-v10",
        'lat': lat,
        'lon': lon,
        'token': token,
        'zoom': zoom,
        'w': w,
        'h': h,
        'retina': "@2x",
    }

    url_template = "https://api.mapbox.com/styles/v1/mapbox/{style}/static/{lon},{lat},{zoom}/{w}x{h}{retina}?access_token={token}&attribution=false&logo=false"
    url = url_template.format(**params)

    # Download the rendered image
    with urllib.request.urlopen(url) as response:
        j = Image.open(io.BytesIO(response.read()))

    # If the "retina" @2x parameter is used, the image is twice the size of the requested dimensions
    (W, H) = j.size
    assert ((W, H) in [(w, h), (2 * w, 2 * h)])

    # Extract the region of interest from the larger covering map
    i = j.crop((
        round(W * (left - LEFT) / (RIGHT - LEFT)),
        round(H * (top - TOP) / (BOTTOM - TOP)),
        round(W * (right - LEFT) / (RIGHT - LEFT)),
        round(H * (bottom - TOP) / (BOTTOM - TOP)),
    ))

    return i


def test():
    bbox = [-79.97441, 40.415419, -79.910184, 40.474327]            # bus
    #bbox = [-79.97624, 40.411309, -79.897635, 40.45836]            # inrix
    map = get_map_by_bbox(bbox)

    import matplotlib as mpl
    mpl.use("TkAgg")

    import matplotlib.pyplot as plt
    plt.imshow(map, extent=mb2ax(*bbox))
    plt.show()

    map.save('map_data/inrix_org.png')



if __name__ == "__main__":
    test()