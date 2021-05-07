from app_object_type import DatespotAppType

from math import sqrt, radians, cos, sin, asin

class Match(metaclass=DatespotAppType):

    def __init__(self, user1, user2):
        """
        Args:
            user1 (UserObj): A user object.
            user2 (UserObj): A different user object.
        """
        self.user1 = user1
        self.user2 = user2
        self.midpoint = None # todo nuances wrt home vs. current location
        self.distance = None. # How far apart the two user are in meters.
        if user1.currentLocation and user2.currentLocation:
            self.midpoint = float('-inf') # todo calculate it as lat lon--geometry equation
            self._compute_distance()
    
        self.chat_logs = None # todo. Text of chats between the users, for running various restaurant-suggestor NLP algorithms on. 
                                # todo is this needed here or can it just be in users? Chats between
                                # those two specific users should be considered more heavily right?
                                #   E.g. they chatted about how they both love Terrezano's.

    
    def _compute_distance(self):
        """
        Return the Euclidean distance between the two users, in meters.
        """
        
        

    def _haversine(self, lat1, lon1, lat2, lon2) -> float:
        """Return the great circle distance between the two lat lon points, in meters."""
        # convert lat lon decimal degrees to radians:
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # https://en.wikipedia.org/wiki/Haversine_formula
        lonDistance = lon2 - lon1
        latDistance = lat2 - lat1
        a = sin(latDistance/2)**2 + cos(lat1) * cos(lat2) * sin(lonDistance/2)**2
        c = 2 * asin(sqrt(a)) # arcsine * 2 * radius solves for the distance
        earthRadius = 6368 # kilometers
        return c * r * 1000 # convert back to meters

    def get_joint_datespot_score(self, datespot):
        """
        Args:
            datespot (datespot.Datespot object): A datespot object.
        """
        score1 = self.user1.datespot_score(datespot)
        score2 = self.user2.datespot_score(datespot)
        return (score1 + score2) / 2 # simple mean score

    