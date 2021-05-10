from app_object_type import DatespotAppType

from math import sqrt, radians, cos, sin, asin

import geo_utils

class Match(metaclass=DatespotAppType):

    def __init__(self, user1, user2):
        """
        Args:
            user1 (UserObj): A user object.
            user2 (UserObj): A different user object.
        """
        self.user1 = user1
        self.user2 = user2
        self.midpoint = None # lat lon location equidistant between the two users.
            # todo nuances wrt home vs. current location
        self.distance = None # How far apart the two user are in meters.
        if self.user1.currentLocation and self.user2.currentLocation:
            self._compute_midpoint()
            self._compute_distance()

        # todo use home location for datespot finding if home location known, else use current location. 
            # todo infer some kind of approx home location over time from the user's usage pattern. 
    
        self.chat_logs = None # todo. Text of chats between the users, for running various restaurant-suggestor NLP algorithms on. 
                                # todo is this needed here or can it just be in users? Chats between
                                # those two specific users should be considered more heavily right?
                                #   E.g. they chatted about how they both love Terrezano's.

        self.same_sex = None # todo. Google Places can be tagged "LGBT friendly"; that trait should weight higher
                                # for a same sex match.

    
    def _compute_distance(self) -> None:
        """
        Compute the distance between the two users, in meters.
        """
        lat1, lon1 = self.user1.currentLocation
        lat2, lon2 = self.user2.currentLocation
        self.distance = geo_utils.haversine(lat1, lon1, lat2, lon2)

    def _compute_midpoint(self) -> None:
        """
        Compute the lat lon point equidistant from the two users, in meters.
        """
        self.midpoint = geo_utils.midpoint(self.user1.currentLocation, self.user2.currentLocation)

    def get_joint_datespot_score(self, datespot):
        # Intuition/hypothesis is that it won't make sense to try do better than a simple mean of the two users scores on that restaurant
        #   any time soon, if ever. 
        # To suggest a Datespot for a Match, you get the *initial queryset* based on the midpoint (and, at most, other stuff like price range (min, or based on confident
        #   prediction as to who is paying), hours based on Users' schedule). But once that initial set of restaurants is hand, all further qualitative filtering should be 
        #   based on scoring them for each User in isolation, then averaging--for now. Need to prune complexity anywhere possible, initially. 
        """
        Args:
            datespot (datespot.Datespot object): A datespot object.
        """
        score1 = self.user1.datespot_score(datespot)
        score2 = self.user2.datespot_score(datespot)
        return (score1 + score2) / 2 # simple mean score   