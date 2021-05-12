from app_object_type import DatespotAppType


class User(metaclass=DatespotAppType):

    # todo no camel case in the constructor arg names
    def __init__(self, name:  str, current_location: tuple=None, home_location: tuple=None, likes: list=None, dislikes: list=None):
        """
        Args:
            current_location (tuple[int]): Tuple of two ints representing 2D coordinates.
            homeLocation (tuple[int]): Tuple of two ints representing 2D coordinates.
        """
        self.name = name
        self.current_location = current_location
        self.home_location = home_location
        # todo homeLocation defaults to the current_location in the DB (not necessarily in a user object instance), then is honed over time based on 
        #   other info about the user (chat mentions of where they live, and absent that, a weighted centroid of their current locations).

        self.likes = [] # features of a date location that would make the user like it
        self.dislikes = [] # features of a date location that would make the user dislike it
        self.travel_tropensity= None #  todo placeholder. Integer indicating how willing the user is to travel, relative to other users. 
        self.chat_logs = None # todo you want NLP on the *user*'s chats, not just the chats for this
                                #   one match. If user said to someone else "Terrezano's is the worst
                                # restaurant on earth", that's relevant to all future matches containing
                                #   that user.

    # todo: Would be cool if NLP could extract a user's home location from chat text.
    #   E.g. they ask each other where they live, and NLP is able to process 
    #       "East Village" or "72nd and amsterdam" into an approximate lat lon.

        self.matches = {} # Users this user matched with and therefore can chat with. 
        self.match_blacklist = {} # Users with whom this user should never be matched. Keys are user ids, values timestamps indicating when the blacklisting happened. 
        self.match_queue = [] # Distance-ranked queue of users to suggest as matches. 
    
    def __str__(self):
        """
        Return the string representation of a dictionary containing all the user's info.
        """
        userDict = {
            "name": self.name,
            "current_location": self.current_location,
            "home_location": self.home_location,
            "likes": self.likes,
            "dislikes": self.dislikes
        }
        return "User" + str(userDict)

    def update_current_location(self, location: tuple) -> int:
        """
        Update the user's current location and return a status-code int to caller.
        """
        # todo validate at the DB layer
        self.current_location = location
        return 0
    
    def next_candidate(self) -> int:
        """
        Return the user id of this user's next potential match. I.e. get another person for this user to swipe on.
        """
        # todo big spaghettification risk here wrt what code pops from the queue vs just reads the current queue.
        if self.match_queue:
            return self.match_queue[-1] # peek, don't pop, for now.
        else:
            return None # todo best thing to return if the queue is empty? Refresh the queue and try again?