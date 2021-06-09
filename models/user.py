from models.app_object_type import DatespotAppType

import collections
from typing import List
import time

from project_constants import TASTE_STRENGTH_DECIMAL_PLACES

class UserBase(metaclass=DatespotAppType):
    def __init__(
        self,
        user_id: str,
        name: str,
        current_location,
        predominant_location: tuple=None,
        tastes: dict={},
        travel_propensity: float=0.0,
        pending_likes: dict={},
    ):
        self.id = user_id  # User id depends on the original creation time, not on something the model class is able to compute
        self.name = name
        self._current_location = current_location
        self._predominant_location = predominant_location
        self._tastes = tastes  # Private attribute, because the structure of the dict's values is a confusing implementation detail.
        self.travel_propensity= travel_propensity #  todo placeholder. Integer indicating how willing the user is to travel, relative to other users.

        self.pending_likes = pending_likes  # References to Users this user swiped "accept" on, but who haven't yet swiped back. Keys are user ids, values are time.time() timestamps

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return hash(self) == hash(other)
    
    def __lt__(self, other): # TODO: Sorts on name to break ties; needed it for sorting nearby candidates results
        return self.name < other.name
    
    def __le__(self, other):
        return self.name <= other.name

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

class Candidate(UserBase):  # Stripped-down version of a User that omits Candidates and other attributes not relevant to an object that
                            #   is only being used as another User's candidate
    """
    Helper object to provide access to most User object interfaces without requiring recursive instantiation of a User's candidates
    queue.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class User(UserBase):

    # TODO this should store Candidates list, probably as a list of User objects rather than IDs. If that is storage/memory/time intensive,
    #   then can shrink the size of the candidates queue--user can only ever swipe on one at a time.

    # TODO use a Candidate object, because we don't care about the candidate's candidates. 

    def __init__(
        self,
        user_id: str,
        name: str,
        current_location,
        predominant_location: tuple=None,
        tastes: dict={},
        travel_propensity: float=0.0,
        candidates: list=[],
        pending_likes: dict={},
        matches: List[tuple]=[],
        match_blacklist: dict={},
        ):
        """
        Args:
            current_location (tuple[int]): Tuple of two ints representing 2D coordinates.
            home_location (tuple[int]): Tuple of two ints representing 2D coordinates.
            taste (dict): Dictionary of user's date-location relevant preferences. Format is 
                    { 
                        preference (str): [avg_sentiment (float), num_datapoints (int)],
                        "thai": [0.192, 3]  # User mentioned "thai" in 3 sentences, and average sentiment of those sentences was 0.192
                    }
            
            matches (list[tuple]): List of tuples containing data about Matches of which this user is a member. Format of matches[i]:
                    (match_id (str), timestamp (float), partner_id(str))
                
                - match_id is equal to that Match object's .id attribute
                - timestamp is the Unix timestamp equal to Match.timestamp
                - partner_id is the user ID string of the other member of the Match besides this User.
        """
        super().__init__(
            user_id=user_id,
            name=name,
            current_location=current_location,
            predominant_location=predominant_location,
            tastes=tastes,
            travel_propensity=travel_propensity
        )

        if predominant_location:
            self._predominant_location = predominant_location # Todo: If no other data, return the current location to an external caller. If multiple current location data points, and no
                                                            # confident fixed "this is where they live", compute predominant_location to be a time-weighted average location (weighted for how long the user spent at each point).
                                                        # Todo: Ideally, could watch for the user to state in chat where they live, and then lock the predominant_location to that.                                             #   e.g. translate "East Village" or "72nd and amsterdam" into an approximate lat lon.
        else:
            self._predominant_location = self._compute_predominant_location()
        self._fixed_predominant_location = False  # True if e.g. the User provided their home address

        self.candidates = collections.deque(candidates)  # Deque of User objects
        self._matches = matches # References to Matches of which this User is a constituent.
        self._sort_matches()  # Maintain list in sorted order on the default sort criteria

        self.match_blacklist = match_blacklist # References to Users with whom this user should never be matched. Keys are user ids, values timestamps indicating when the blacklisting happened. 
        if not self.id in self.match_blacklist: # Prevent this user being matched with themself
            self.match_blacklist[self.id] = time.time()

        # TODO How much data do we need to confidently assign a "hard" preference like vegan, kosher, halal?

        # TODO We don't want the chat-reader to e.g. massively over-weight Korean restaurants in suggestions for a user who says "I'm Korean" meaning ethnicity.
        #   Maybe there will be enough non-ethnic restaurant traits for it to wash out, TBD.

        # TODO Would it make sense to automatically put each User into their own blacklist, as a simple way to prevent them being in their own candidates feed?
    
    ### Public methods ###
    
    @property
    def matches(self):
        """
        Yields the match_ids of this User's Matches, sorted in descending timestamp order (most recently matched first).
        """
        for match in self._matches:
            yield match[0]  # External code shouldn't need to worry about the indexing of the tuples
    
    @property
    def match_partners(self):
        """
        Yields the user IDs of other Users this User has matched with.
        """
        for match in self._matches:
            yield match[2]
        
    def has_match(self, match_id: str)-> bool:
        """
        Returns True if match_id is already in this User's matches data, else False.
        """
        #  TODO: Hypothesize that it's faster to just use linear search here than to instantiate a 
        #       hash table of the matches every time a User is instantiated. User objects are instantiated
        #       much more often and in many more contexts than has_match() will need to be checked. Presumably
        #       a User won't have thousands of active Matches simultaneously.
        for match in self._matches:
            if match[0] == match_id:
                return  True
        return False

    def add_match(self, match_id: str, match_timestamp: float, match_partner_id: str) -> None:
        """
        Appends new Match data to this User's Matches data.
        """
        if not self.has_match(match_id):
            new_match = (match_id, match_timestamp, match_partner_id)
            self._matches.append(new_match)
        self._sort_matches()

    def _sort_matches(self, key="timestamp"):
        if key == "timestamp":
            self._matches.sort(key = lambda match : match[1], reverse=True)
        else:
            raise NotImplementedError

    def taste_names(self):  # TODO would this be a good use case for a yield generator?
                            # i.e. lazily yield them one at a time for the caller to iterate over. The datespot scorer method iterates over them.
                            #   OTOH maybe useful to spend O(n) time then return them as a hash set?
                            # Todo: Or just store them as an alphabetized list and binary search, like the master tastes-lexicon of all recognized tastes.
        """Return only the names of the tastes"""
        return set([taste_name for taste_name in self._tastes.keys()])

    def taste_strength(self, taste) -> float: # Public method so external callers aren't affected by the confusing indexing in the tastes dict values
        """
        Return the current weighted average strength-score for this taste.

        Args:
            taste (str): Name of one of the tastes in this user's tasts attribute.
        """
        print(TASTE_STRENGTH_DECIMAL_PLACES)
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
            "user_id": self.id,
            "name": self.name,
            "current_location": self.current_location,
            "predominant_location": self.predominant_location,
            "tastes": self._tastes,
            "travel_propensity": self.travel_propensity,
            "candidates": self._serialize_candidates(),  # List of only the ID hex-strings
            "pending_likes": self.pending_likes,
            "matches": self._matches,
            "match_blacklist": self.match_blacklist
        }
    
    def _serialize_candidates(self) -> List[str]:
        """
        Returns a list of the user IDs of each current candidate.
        """
        return [candidate.id for candidate in self.candidates]

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
    
    def next_candidate(self):
        """
        Returns the next candidate from this User's candidates queue.
        
        Returns:
            (Candidate): Candidate object for the next candidate.

        """
        if self.candidates[0].id == self.id: # TODO sloppy hack to prevent matching with self
            self.candidates.popleft()
        return self.candidates[0]
    
    def _pop_interacted_candidate(self, candidate):  # The interacted-with candidate (decided yes/no/defer on) should generally be at the head of the queue, but may not always be
        """
        Removes the interacted-with candidate from the candidates queue.

        Returns:
            None
        """
        # TODO will it literally always be a head of queue, such that this method isn't necessary?
        # Peek at head of queue, because most often the candidate should be there.
        if self.candidates[0] == candidate:
            self.candidates.popleft()
        else:
            self.candidates.remove(candidate)

    def accept_candidate(self, accepted_candidate) -> bool:
        """
        Moves an accepted candidate ("yes" decision) from this User's candidates queue to either their 
        matches (if other User already submitted a "yes" decision on this User) or their pending 
        matches (if not). Returns True if a match was created, else False.

        Args:
            accepted_candidate (User): User object for the accepted candidate.

        Returns:
            (bool): True if a match was created, else False
        """
        self._pop_interacted_candidate(accepted_candidate)
        if self.id in accepted_candidate.pending_likes:
            self.matches[accepted_candidate.id] = time.time()
            return True
        else:
            self.pending_likes[accepted_candidate.id] = time.time()
            return False
    
    def reject_candidate(self, rejected_candidate) -> None:
        """
        Moves a rejected candidate ("no" decision) from this User's candidates queue to their blacklist.
        If this User was in the rejected candidate's pending matches, removes it.
        Args:
            rejected_candidate (User): User object for the rejected candidate.
        
        Returns:
            None
        """
        self._pop_interacted_candidate(rejected_candidate)
        self._blacklist(rejected_candidate)
    
    def defer_candidate(self, deferred_candidate) -> None:
        """
        Removes a deferred candidate ("pass"/"maybe later" decision) from the head of this User's candidates queue
        but does not add them to blacklist.
        """
        self._pop_interacted_candidate(deferred_candidate)
    
    def _blacklist(self, rejected_candidate) -> None:
        """Adds a rejected candidate to this User's blacklist."""
        self.match_blacklist[rejected_candidate.id] = time.time()
    
    ### Private methods ###

    def _compute_predominant_location(self): # todo, placeholder for more sophisticated
        return self.current_location