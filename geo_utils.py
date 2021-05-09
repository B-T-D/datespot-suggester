"""Reusable utilities related to handling geographical data."""

from math import sqrt, radians, cos, sin, asin

def is_valid_lat_lon(location: tuple) -> bool:
    """Return false if the latitude or longitude is outside the valid range."""
    lat, lon = location[0], location[1]
    return (-90 <= lat <= 90) and (-180 <= lon <= 180)

# todo: Use numpy if distance computations are intensive enough to become a bottleneck.
def haversine(lat1, lon1, lat2, lon2) -> float: # more testable if outside the class
    """Return the great circle distance between the two lat lon points, in meters."""
    # convert lat lon decimal degrees to radians:
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # https://en.wikipedia.org/wiki/Haversine_formula
    lonDistance = lon2 - lon1
    latDistance = lat2 - lat1
    a = sin(latDistance/2)**2 + cos(lat1) * cos(lat2) * sin(lonDistance/2)**2
    c = 2 * asin(sqrt(a)) # arcsine * 2 * radius solves for the distance
    earthRadius = 6368 # kilometers
    return c * earthRadius * 1000 # convert back to meters

def midpoint(location1: tuple, location2: tuple) -> tuple:
    """Compute the flat plane midpoint between two lat-lon locations."""
    lat1, lon1 = location1[0], location1[1]
    lat2, lon2 = location2[0], location2[1]
    return ((lat1 + lat2) / 2, (lon1 + lon2) / 2)