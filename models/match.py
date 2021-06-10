from models.app_object_type import DatespotAppType
import geo_utils

from typing import List, Tuple
import time, heapq

class Match(metaclass=DatespotAppType):

    def __init__(self, user1, user2, timestamp=time.time(), suggestions_queue=[]):


        # TODO we want to store the best-guess-so-far suggestions queue every time a Match object instantiates, to have it precomputed
        #   for when the constituent users ask for a suggestion.

        """
        Args:
            user1 (UserObj): A user object.
            user2 (UserObj): A different user object.
            timestamp (float): UNIX timestamp indicating the time the users first created this Match. Provide if instantiating a stored object,
                leave blank for new object.
            suggestions_queue (list): Previously stored list of suggestions. Provide if instantiating a stored object, leave blank for new object.
        """
        
        self.user1 = user1
        self.user2 = user2
        self._users = tuple(sorted([self.user1.id, self.user2.id]))  # Sort the users lexicographically on their ids, so that Match of "Bob-Alice" will hash to same thing as "Alice-Bob"
        self.timestamp = timestamp

        self._midpoint = self._compute_midpoint() # lat lon location equidistant between the two users. 
            # todo nuances wrt home vs. current location
        self._distance = self._compute_distance() # How far apart the two user are in meters.

        self.query_radius = None # Default value for datespot queries--how far out from the Match's 
                                            # geographical midpoint to look for datespots.
                                            # For now, defaults to self.distance / 2. That is, any point inside a circle
                                            #   centered on the midpoint and with the two users' locations on its perimeter.
                                        # Todo optimize / dynamically tailor to each Match (e.g. different travel propensities; or
                                        #   a restaurant just outside the normal query area would be an extraordinarily good fit). 

        # todo use home location for datespot finding if home location known, else use current location. 
            # todo infer some kind of approx home location over time from the user's usage pattern. 
    
        self.chat_logs = None # todo. Text of chats between the users, for running various restaurant-suggestor NLP algorithms on. 
                                # todo is this needed here or can it just be in users? Chats between
                                # those two specific users should be considered more heavily right?
                                #   E.g. they chatted about how they both love Terrezano's.

        self.same_sex = None # todo. Google Places can be tagged "LGBT friendly"; that trait should weight higher
                                # for a same sex match.

        self.suggestions_queue = suggestions_queue # List or queue of suggested restaurants
                                    # Todo: What's the max num it makes sense to store?
                                    # Todo: How often to update with fresh data? Whenever data on either user's preferences changed?
                                    # TODO does anyone need to access it from the outside? Seems like could be a private attribute
        self._max_suggestions_queue_length = 50

        self.chat_chemistry = 0 # todo. Score of how much the chat sentiment predicts a good vs. bad date.

    ### Public methods ###

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return hash(self) == hash(other)
    
    def __hash__(self): # Hash is the hash of the two users' ids
        return hash(self._users)
    
    @property
    def id(self) -> str:
        return self._id()

    @property
    def midpoint(self) -> Tuple[float]:
        return self._midpoint
    
    @property
    def distance(self) -> float:
        """Returns how far apart the Match's member Users are, in meters."""
        return self._distance

    def suggestions(self, candidate_datespots) -> list:
        """
        Args:
            candidate_datespots (list[tuple[distance, Datespot]]): List of distances and corresponding Datespot objects

        Returns:
            (list[Datespot]): List of Datespot objects (no distances) ordered from strongest suggestion to weakest.
        """
        # Todo: To the extent distance is factored into suggestion prioritization, that happens here in Match. S/t the
        #   distances are irrelevant by the time this method returns--if one restaurant was too far away, that's reflected
        #   in its position in the final list returned by this method.
        suggestions_heap = self._score_nearby_datespots(candidate_datespots)
        self.suggestions_queue = suggestions_heap # Todo: Correct that we want to store the scores (to easily maintain sorted order when updates)?
        results = [suggestion[1] for suggestion in suggestions_heap] # List of only the datespots, no scores. 
        # Todo compress to one-liner once it works
        return results  # TODO TBD if anyone outside needs this return value. May only need to use this method (with better name) to replenish suggestion-fodder

    def get_joint_datespot_score(self, datespot) -> float:
        # Todo: Intuition/hypothesis is that it won't make sense to try do better than a simple mean of the two users scores on that restaurant
        #   any time soon, if ever. 
        # To suggest a Datespot for a Match, you get the *initial queryset* based on the midpoint (and, at most, other stuff like price range (min, or based on confident
        #   prediction as to who is paying), hours based on Users' schedule). But once that initial set of restaurants is hand, all further qualitative filtering should be 
        #   based on scoring them for each User in isolation, then averaging--for now. Need to prune complexity anywhere possible, initially. 
        """
        Args:
            datespot (datespot.Datespot object): A datespot object.
        """
        score1 = datespot.score(self.user1)
        score2 = datespot.score(self.user2)
        return (score1 + score2) / 2 # simple mean

    def serialize(self) -> dict:
        """
        Return the data about this object that should be store.
        
        Returns:
            (dict): Native Python dictionary

        """
        return {
            "users": list(self._users),
            "timestamp": self.timestamp,
            "suggestions": self._serialize_suggestions()
        }
    
    def _serialize_suggestions(self) -> List[Tuple[float, str]]:
        result = []
        for suggestion in self.suggestions_queue:
            result.append((suggestion[0], suggestion[1].id))  # Substitute the Datespot's id for the Datespot object
        return result

    
    def has_suggestions(self) -> bool:  # For external code to check whether data is needed.  Match object can't be responsible for going out to Yelp, Google, etc. if it's out of suggestion-fodder.
        """
        Returns True if this Match has suggestions, else False.
        """
        return len(self.suggestions_queue) > 0

    ### Private methods ###

    def _id(self) -> str:
        """
        Return this Match's id key string.
        """
        hex_str = str(hex(hash(self)))
        return hex_str[2:] # strip "0x" from beginning

    def _compute_distance(self) -> None:
        """
        Compute the distance between the two users, in meters.
        """
        return geo_utils.haversine(self.user1.current_location, self.user2.current_location)

    def _compute_midpoint(self) -> None:
        """
        Compute the lat lon point equidistant from the two users, in meters.
        """
        # Todo we don't care about updating the midpoint, per se. Ideally we have the home/predominant location for each user, 
        #   in which case the midpoint doesn't change on the fly. We want the midpoint of the location from which they'd typically
        #   depart for the date. 
        # Todo: OTOH, maybe sometimes they leave from office, other times from home?
        return geo_utils.midpoint(self.user1.current_location, self.user2.current_location)

    def _score_nearby_datespots(self, candidate_datespots):
        """Compute the joint datespot score for each result, and push it to a max heap sorted on score.

        Args:
            candidate_datespots (list[tuple[distance, Datespot]]): Complex list of distance-Datespot tuples
        
        Returns:

            (max heap list): Heapq-list of datespots sorted on score. In form [negated_score, datespot_id]
        """
        heapq.heapify(candidate_datespots) # min heap sorted on distance
        suggestions_heap = []

        while candidate_datespots:
            candidate = heapq.heappop(candidate_datespots)[1] # todo it'd be simpler if this list had the id along with the other data.
            # elements in the heap are tuples, element[0] is the distance "key", element[1] is the actual object
            score = self.get_joint_datespot_score(candidate)
            # negate score then use it as first element "key" in tuple for max heap
            heapq.heappush(suggestions_heap, (-score, candidate)) # The object id pk is the heap key's value.
                                                                        # Intuition = this heap is only used inside this Match instance's lifetime, so no reason not to use the object literals,
                                                                            # having already gone through the motions of instantiating them from the db via their keys.
                # As of 5/19/21, Baseline dateworthiness is tiebreaker if they have the same score and heapq tries to use "<" between two 
                #   Datespot objects.
        return suggestions_heap # todo this doesn't write directly back to the main queue, it returns to the supervisor external method which constructs that quue