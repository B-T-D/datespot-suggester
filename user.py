from app_object_type import DatespotAppType


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
        # todo homeLocation defaults to the currentLocation in the DB (not necessarily in a user object instance), then is honed over time based on 
        #   other info about the user (chat mentions of where they live, and absent that, a weighted centroid of their current locations).

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

    def update_current_location(self, location: tuple) -> int:
        """
        Update the user's current location and return a status-code int to caller.
        """
        # todo validate at the DB layer
        self.currentLocation = location
        return 0