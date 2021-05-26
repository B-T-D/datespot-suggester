"""Reusable functions for geographical calculations."""

from math import sqrt, radians, cos, sin, asin

def is_valid_lat_lon(location: tuple) -> bool:
    """Checks whether a latitude, longitude coordinate pair is within the range of valid possible values.
    
    Args:
        location (tuple[float]): Tuple of two floats such that tuple[0] represents latitude 
            and tuple[1] represents longitude.
    
    Returns:
        (bool): True if the latitude longitude are within the range of valid values, else False.
    """
    lat, lon = location[0], location[1]
    return (-90 <= lat <= 90) and (-180 <= lon <= 180)

# todo: Use numpy if distance computations are intensive enough to become a bottleneck.
def haversine(location1: tuple, location2: tuple) -> float:
    """
    Computes the great circle distance, in meters, between two points represented by latitude-longitude
    coordinate pairs.

    Args:
        location1 (tuple[float]): Tuple of two floats such that tuple[0] represents latitude 
            and tuple[1] represents longitude.
        location2 (tuple[float]): Second latitude-longitude tuple in same format as first.
    
    Returns:

        (float): Distance in meters between location 1 and location2.
    """
    # Unpack tuples and convert lat lon decimal degrees to radians:
    lat1, lon1, lat2, lon2 = map(radians, [location1[0], location1[1], location2[0], location2[1]])

    # See https://en.wikipedia.org/wiki/Haversine_formula
    lonDistance = lon2 - lon1
    latDistance = lat2 - lat1
    a = sin(latDistance/2)**2 + cos(lat1) * cos(lat2) * sin(lonDistance/2)**2
    c = 2 * asin(sqrt(a)) # arcsine * 2 * radius solves for the distance
    earthRadius = 6368 # kilometers
    return c * earthRadius * 1000 # convert back to meters

def midpoint(location1: tuple, location2: tuple) -> tuple:
    """
    Computes the midpoint between two points represented by latitude-longitude coordinate pairs,
    assuming those points are on a flat plane (i.e. ignoring curvature of the Earth).

    Args:
        location1 (tuple[float]): Tuple of two floats such that tuple[0] represents latitude 
            and tuple[1] represents longitude.
        location2 (tuple[float]): Second latitude-longitude tuple in same format as first.
    
    Returns:
        (tuple[float]): Tuple of two floats such that tuple[0] is the midpoint's latitude and 
            tuple[1] its longitude.
    """
    lat1, lon1 = location1[0], location1[1]
    lat2, lon2 = location2[0], location2[1]
    return ((lat1 + lat2) / 2, (lon1 + lon2) / 2)