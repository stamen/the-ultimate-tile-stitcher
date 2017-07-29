import math

# from OSM Slippy Tile definitions & https://github.com/Caged/tile-stitch
def latlon2tile(lat, lon, zoom):
    lat_radians = lat * math.pi / 180.0
    n = 1 << zoom
    return (
        n * ((lon + 180.0) / 360.0),
        n * (1 - (math.log(math.tan(lat_radians) + 1 / math.cos(lat_radians)) / math.pi)) / 2.0
    )

def tile2latlon(x, y, zoom):
    n = 1 << zoom
    lat_radians = math.atan(math.sinh(math.pi * (1.0 - 2.0 * y / n)))
    lat = lat_radians * 180 / math.pi
    lon = 360 * x / n - 180.0
    return (lat, lon)

