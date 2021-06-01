from models.app_object_type import DatespotAppType

TASTE_STRENGTH_DECIMAL_PLACES = 6 # Todo confirm this is however many significant figures VSA includes

class User(metaclass=DatespotAppType):

    def __init__(
        self,
        user_id: str,
        name: str,
        current_location,
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
        self._current_location = current_location
        if predominant_location:
            self._predominant_location = predominant_location # Todo: If no other data, return the current location to an external caller. If multiple current location data points, and no
                                                            # confident fixed "this is where they live", compute predominant_location to be a time-weighted average location (weighted for how long the user spent at each point).
                                                        # Todo: Ideally, could watch for the user to state in chat where they live, and then lock the predominant_location to that.                                             #   e.g. translate "East Village" or "72nd and amsterdam" into an approximate lat lon.
        else:
            self._predominant_location = self._compute_predominant_location()
        self._fixed_predominant_location = False  # True if e.g. the User provided their home address

        self._tastes = tastes # Private attribute, because the structure of the dict's values is a confusing implementation detail.

        self.travel_propensity= travel_propensity #  todo placeholder. Integer indicating how willing the user is to travel, relative to other users. 
        self.chat_logs = None # todo you want NLP on the *user*'s chats, not just the chats for this
                                #   one match. If user said to someone else "Terrezano's is the worst
                                # restaurant on earth", that's relevant to all future matches containing
                                #   that user.

        self.matches = {} # Users this user matched with and therefore can chat with.
        self.pending_likes = {} # Users this user swiped "accept" on, but who haven't yet swiped back. Keys are user ids, values are time.time() timestamps
         
        self.match_blacklist = {} # Users with whom this user should never be matched. Keys are user ids, values timestamps indicating when the blacklisting happened. 

        # TODO How much data do we need to confidently assign a "hard" preference like vegan, kosher, halal?

        # TODO We don't want the chat-reader to e.g. massively over-weight Korean restaurants in suggestions for a user who says "I'm Korean" meaning ethnicity.
        #   Maybe there will be enough non-ethnic restaurant traits for it to wash out, TBD.

        # TODO Would it make sense to automatically put each User into their own blacklist, as a simple way to prevent them being in their own candidates feed?
    
    ### Public methods ###

    def __eq__(self, other): # must define if defining __hash__
        if type(self) != type(other):
            return False
        return hash(self) == hash(other) # TODO DRY into ABC? Identical code for all three of User, Datespot, and Match
    
    def __hash__(self):
        return hash(self.id)
    
    @property
    def current_location(self):
        return tuple(self._current_location) # Easier to allow external code to just pass it in as a list as decoded from JSON
    
    @property
    def predominant_location(self):
        for coord in self._predominant_location:  # Make sure coords go out as floats, even if they somehow got written into the model layer as strings
            if isinstance(coord, str):  
                self._predominant_location = (float(self._predominant_location[0]), float(self._predominant_location[1]))
        return self._predominant_location

    def taste_names(self):  # TODO would this be a good use case for a yield generator?
                            # i.e. lazily yield them one at a time for the caller to iterate over. The datespot scorer method iterates over them.
                            #   OTOH maybe useful to spend O(n) time then return them as a hash set?
                            # Todo: Or just store them as an alphabetized list and binary search, like the master tastes-lexicon of all recognized tastes.
        """Return only the names of the tastes"""
        return set([taste_name for taste_name in self._tastes.keys()])

    def taste_strength(self, taste) -> float: # Public method so external callers aren't affected by the confusing indexing in the tastes dict values
        """
        Return the current weighted average strength-score for this taste.
        """
        return round(self._tastes[taste][0], TASTE_STRENGTH_DECIMAL_PLACES)
    
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
            "tastes": self._tastes,
            "travel_propensity": self.travel_propensity,
            "matches": self.matches,
            "pending_likes": self.pending_likes,
            "match_blacklist": self.match_blacklist
        }
    
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
            prior_strength, prior_datapoints = self._tastes[taste][0], self._tastes[taste][1]
            weighted_prior_strength = prior_strength * prior_datapoints
            new_datapoints = prior_datapoints + 1
            new_strength = (weighted_prior_strength + strength) / new_datapoints
            self._tastes[taste] = [new_strength, new_datapoints]

    ### Private methods ###

    def _compute_predominant_location(self): # todo, placeholder for more sophisticated

        return self.current_location