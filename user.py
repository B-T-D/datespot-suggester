from app_object_type import DatespotAppType

from datespot import *

class User(metaclass=DatespotAppType):

    # todo no camel case in the constructor arg names
    def __init__(self, name:  str, currentLocation: tuple=None, homeLocation: tuple=None, likes: list=None, dislikes: list=None):
        """
        Args:
            currentLocation (tuple[int]): Tuple of two ints representing 2D coordinates.
            homeLocation (tuple[int]): Tuple of two ints representing 2D coordinates.
        """
        self.name = name
        self.currentLocation = currentLocation
        self.homeLocation = homeLocation
        self.likes = [] # features of a date location that would make the user like it
        self.dislikes = [] # features of a date location that would make the user dislike it
        self.travelPropensity= None #  todo placeholder. Integer indicating how willing the user is to travel, relative to other users. 
        self.chat_logs = None # todo you want NLP on the *user*'s chats, not just the chats for this
                                #   one match. If user said to someone else "Terrezano's is the worst
                                # restaurant on earth", that's relevant to all future matches containing
                                #   that user.

    # todo: Would be cool if NLP could extract a user's home location from chat text.
    #   E.g. they ask each other where they live, and NLP is able to process 
    #       "East Village" or "72nd and amsterdam" into an approximate lat lon.
    
    def __str__(self):
        """
        Return the string representation of a dictionary containing all the user's info.
        """
        userDict = {
            "name": self.name,
            "current_location": self.currentLocation,
            "home_location": self.homeLocation,
            "likes": self.likes,
            "dislikes": self.dislikes
        }
        return "User" + str(userDict)
    
    def datespot_score(self, datespot) -> int:
        # Wrapper for external calls
        """
        Takes a datespot object and returns the score for how well this user matches with that datespot.

        Args:

            datespot (datespot.Datespot object): An instance of the Datespot class.
        """
        return self._get_datespot_score(datespot)

    def _get_datespot_score(self, datespot) -> int:
        
        score = 0
        for trait in datespot.traits: # todo this is O(n^2); should likes and/or traits be hash sets?
            if trait in self.likes:
                score += 1
            elif trait in self.dislikes:
                score -= 1
        return score

    def _validate_location(self, location: tuple) -> bool:
        """
        Return True if location is valid lat-lon coordinate pair, else False.
        """
        # todo is it cluttering for the validator to live here instead of some 
        #   shallower layer?
        if len(location) != 2:
            return False
        lat, lon = location[0], location[1]
        if not (isinstance(lat, float) and isinstance(lon, float)):
            return False
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return False
        return True

    def update_current_location(self, location: tuple) -> int:
        """
        Update the user's current location and return a status-code int to caller.
        """
        if not self._validate_location(location):
            return 1
        self.currentLocation = location
        return 0