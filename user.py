from app_object_type import DatespotAppType


class User(metaclass=DatespotAppType):

    def __init__(
        self,
        user_id: str,
        name: str,
        current_location: tuple=None,
        predominant_location: tuple=None,
        tastes: dict={},
        matches: dict={},
        pending_likes: dict={},
        match_blacklist: dict={},
        travel_propensity: float=0.0
        ):
        """
        Args:
            current_location (tuple[int]): Tuple of two ints representing 2D coordinates.
            home_location (tuple[int]): Tuple of two ints representing 2D coordinates.
            taste (dict): Dictionary of user's date-location relevant preferences. Format is 
                    { 
                        str preference: [float avg_sentiment, int num_datapoints],
                        "thai": [0.192, 3]  # User mentioned "thai" in 3 sentences, and average sentiment of those sentences was 0.192
                    }
        """
        self.id = user_id # Unlike Datespot and Match, the id isn't a function of hashing some attribute of the object; it comes from the chronological creation order in the DB
        self.name = name
        self.current_location = current_location
        self.predominant_location = None
        if predominant_location:
            self.predominant_location = predominant_location # Todo: If no other data, return the current location to an external caller. If multiple current location data points, and no
                                                            # confident fixed "this is where they live", compute predominant_location to be a time-weighted average location (weighted for how long the user spent at each point).
                                                        # Todo: Ideally, could watch for the user to state in chat where they live, and then lock the predominant_location to that.                                             #   e.g. translate "East Village" or "72nd and amsterdam" into an approximate lat lon.
        else:
            self.predominant_location = self._compute_predominant_location()

        self._tastes = tastes # Private attribute, because the structure of the dict's values is a confusing implementation detail.

        self.travel_propensity= travel_propensity #  todo placeholder. Integer indicating how willing the user is to travel, relative to other users. 
        self.chat_logs = None # todo you want NLP on the *user*'s chats, not just the chats for this
                                #   one match. If user said to someone else "Terrezano's is the worst
                                # restaurant on earth", that's relevant to all future matches containing
                                #   that user.

        self.matches = {} # Users this user matched with and therefore can chat with.
        self.pending_likes = {} # Users this user swiped "accept" on, but who haven't yet swiped back. Keys are user ids, values are time.time() timestamps
         
        self.match_blacklist = {} # Users with whom this user should never be matched. Keys are user ids, values timestamps indicating when the blacklisting happened. 
    
    def __eq__(self, other): # must define if defining __hash__
        return hash(self) == hash(other) # todo DRY into ABC? Identical code for all three of User, Datespot, and Match
    
    def __hash__(self):
        return hash(self.id)

    def __str__(self):
        """
        Return the string representation of a dictionary containing all the user's info.
        """
        userDict = {
            "name": self.name,
            "current_location": self.current_location,
            "home_location": self.home_location,
        }
        return "User" + str(userDict)

    def _compute_predominant_location(self): # todo, placeholder for more sophisticated
        return self.current_location


    def update_current_location(self, location: tuple) -> int:
        """
        Update the user's current location and return a status-code int to caller.
        """
        # todo validate at the DB layer
        self.current_location = location
        return 0

    def update_tastes(self, taste: str, strength: float) -> None:
        """
        Update this User's tastes data. If taste is not yet in the tastes hashmap, add it as a new 
        key with its strength-score and a one total datapoint. Otherwise, update that taste's weighted average
        strength-score and increment its total datapoints count in the hashmap.

        Args:
            taste (str): String label of the taste. E.g. "thai", "italian", "loud", "quiet", "dark"
            score (float): Strength of the preference from that datapoint. Normalized to between 
                -1.0 and 1.0.
        """
        taste = taste.lower().strip() # todo is this cluttering, or worthwhile as a redundant, relatively easy/cheap check?

        if not taste in self._tastes:
            self._tastes[taste] = [strength, 1] # [strength_score, num_datapoints]
        else:
            prior_strength, datapoints = self._tastes[taste][0], self._tastes[taste][1]
            weighted_prior_strength = prior_strength * datapoints
            datapoints += 1 # increment datapoints count to new total after multiplying by the prior value
            new_strength = (weighted_prior_strength + strength) / datapoints
            self._tastes[taste] = [new_strength, datapoints]
    
    def taste_strength(self, taste) -> float: # Public method so external callers aren't affected by the confusing indexing in the tastes dict values
        """
        Return the current weighted average strength-score for this taste.
        """
        return self._tastes[taste][0]
    
    def taste_datapoints(self, taste) -> int: # toto YAGNI?
        """
        Return the current number of datapoints for this taste. That is, how many sentiment floats were used in 
        computing the current weighted average strength score.
        """
        return self._tastes[taste][1]

    def serialize(self) -> dict:
        """Return the data about this object that should be stored."""
        return {
            "id": self.id,
            "name": self.name,
            "current_location": self.current_location,
            "predominant_location": self.predominant_location,
            "tastes": self.tastes,
            "travel_propensity": self.travel_propensity,
            "matches": self.matches,
            "pending_likes": self.pending_likes,
            "match_blacklist": self.match_blacklist
        }