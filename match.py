from app_object_type import DatespotAppType

import geo_utils
import database_api

import heapq

class Match(metaclass=DatespotAppType):

    # todo conform code style wrt underscores for "private" methods and attributes. 
    def __init__(self, user1, user2):

        # Todo: Think about the (public) attributes in terms of what we want written to the persistent JSON representation of a Match
        #   object. 

        """
        Args:
            user1 (UserObj): A user object.
            user2 (UserObj): A different user object.
        """
        
        self.user1 = user1
        self.user2 = user2
        self.id = self._id() # can't be called before the self.user1 and self.user2 attributes are initialized
        
        self.midpoint = None # lat lon location equidistant between the two users.
            # todo nuances wrt home vs. current location
        self.distance = None # How far apart the two user are in meters.
        if self.user1.current_location and self.user2.current_location:
            self._compute_midpoint() # todo don't call them here
            self._compute_distance()

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

        self.suggestions_queue = [] # List or queue of suggested restaurants
                                    # Todo: What's the max num it makes sense to store?
                                    # Todo: How often to update with fresh data? Whenever data on either user's preferences changed?
        self._max_suggestions_queue_length = 50

        self.chat_chemistry = 0 # todo. Score of how much the chat sentiment predicts a good vs. bad date. 
    
    def __eq__(self, other): # Must define if defining __hash__
        return hash(self) == hash(other)
    
    def __hash__(self): # Hash is the hash of the two users' ids
        return hash((self.user1.id, self.user2.id))
    
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
        self.distance = geo_utils.haversine(self.user1.current_location, self.user2.current_location)

    def _compute_midpoint(self) -> None:
        """
        Compute the lat lon point equidistant from the two users, in meters.
        """
        self.midpoint = geo_utils.midpoint(self.user1.current_location, self.user2.current_location)

    def get_suggestions(self) -> list: # todo if it's external then it returns something
        """

        Returns:
            (list): List of Datespot objects
        """
        db = database_api.DatabaseAPI()
        suggestions_heap = self._score_nearby_datespots()
        # pop each from the heap and add to the main queue until queue is the desired length
        while suggestions_heap and len(self.suggestions_queue) < self._max_suggestions_queue_length:
            suggestion_key = heapq.heappop(suggestions_heap)[1] # [0] is the score that was used for the sort. 
            self.suggestions_queue.append(db.get_obj("datespot", suggestion_key)) # todo should the externally returned thing still have the object literals?
        return self.suggestions_queue


    def _get_datespots_by_geography(self) -> list:
        """Return a proximity sorted list of the the datespots within self.default_query_radius of this Match's geographical midpoint."""
        self.query_radius = self.distance / 2 # todo what if the users are next door neighbors? Don't want to query a 100m radius. Should be a more nuanced conditional min / max. 

        db = database_api.DatabaseAPI()

        query_results = db.get_datespots_near(location=self.midpoint, radius=self.query_radius)
        return query_results


    def _score_nearby_datespots(self):
        """Compute the joint datespot score for each result, and push it to a max heap sorted on score."""
        geo_results = self._get_datespots_by_geography()
        heapq.heapify(geo_results) # min heap sorted on distance
        suggestions_heap = []

        db = database_api.DatabaseAPI() # todo we don't want to do it this way if at all avoidable, because i.a. makes a mess in testing wrt which JSON map is used when.
        while geo_results:
            candidate = heapq.heappop(geo_results)[1] # todo it'd be simpler if this list had the id along with the other data.
            # elements in the heap are tuples, element[0] is the distance "key", element[1] is the actual object
            # print(f"\n*****type candidate = {type(candidate)}\n\ncandidate = {candidate}\n*********\n")
            # print(f"id type is {type(candidate['id'])}")
            candidate_obj = db.get_obj("datespot", candidate["id"])
            # print(type(candidate_obj))
            score = self.get_joint_datespot_score(candidate_obj)
            # negate score then use it as first element "key" in tuple for max heap
            heapq.heappush(suggestions_heap, (-score, candidate_obj.id)) # The object id pk is the heap key's value.
                                                                        # Intuition = this heap is only used inside this Match instance's lifetime, so no reason not to use the object literals,
                                                                            # having already gone through the motions of instantiating them from the db via their keys.
        
        return suggestions_heap # todo this doesn't write directly back to the main queue, it returns to the supervisor external method which constructs that quue

    def get_joint_datespot_score(self, datespot) -> float:
        # Intuition/hypothesis is that it won't make sense to try do better than a simple mean of the two users scores on that restaurant
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