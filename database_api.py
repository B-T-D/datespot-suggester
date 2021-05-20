"""
Implementation-agnostic interface between internal app database and JSON-using external code. Provides public methods that parallel HTTP request
methods and return JSON.

Goal is for external calling code to be unaffected by SQL vs. NoSQL and similar issues.
"""

import json
import sys

import model_interfaces

import yelp_api_client

# todo: What's the best name for this module? "JSON_server"? "REST_server"? "REST_API"? "REST_backend"? "JSON_backend"?
    # It's not a full REST API. It's not meant to handle actual HTTP requests; it doesn't use appropriate URIs. It's meant to get the JSON 
    #   that the actual web-facing REST API will return in HTTP responses.\

# Todo: In a live app, the messages wouldn't go through this JSON backend for analysis before continuing on to the recipient(s). Something would copy them
#   in the middle, send them immediately on to recipient, and then dispatch the data to the backend for analysis on a less urgent timeframe.

JSON_MAP_FILENAME = "jsonMap.json"
DEFAULT_RADIUS = 2000

class DatabaseAPI:

    def __init__(self, json_map_filename: str=JSON_MAP_FILENAME, live_google_maps: bool=False, live_yelp: bool=False):
        self._valid_model_names = {"user", "datespot", "match", "review", "message", "chat"}
        self._json_map_filename = json_map_filename
        self._live_google_maps = live_google_maps # todo implement different dispatching for the datespot queries based on this setting
        self._live_yelp = live_yelp # todo one combined boolean toggle "live mode"

        self._yelp_client = yelp_api_client.YelpClient()

    def _model_interface(self, model_name: str): # todo integrate this approach below (change the separate constructor calls into calls to this)
        """Return an instance of a model interface object for the specified model name.""" # goal is to avoid repetitive calls passing the relevant json filename.
        self._validate_model_name(model_name)
        if model_name == "user":
            return model_interfaces.UserModelInterface(json_map_filename=self._json_map_filename)
        elif model_name == "datespot":
            return model_interfaces.DatespotModelInterface(json_map_filename=self._json_map_filename)
        elif model_name == "match":
            return model_interfaces.MatchModelInterface(json_map_filename=self._json_map_filename)
        elif model_name == "review":
            return model_interfaces.ReviewModelInterface(json_map_filename=self._json_map_filename)
        elif model_name == "message":
            return model_interfaces.MessageModelInterface(json_map_filename=self._json_map_filename)
        elif model_name == "chat":
            return model_interfaces.ChatModelInterface(json_map_filename=self._json_map_filename)

    def _validate_model_name(self, model_name):
        if not model_name in self._valid_model_names:
            raise ValueError(f"Invalid model name: {model_name}")

    def post_object(self, object_type: str, json_data: str, **kwargs) -> str: # todo kwargs should be deleteable now
        """
        Add data for a new object to the database and return its id string.

        Args:
            
            object_type (str): "user", "datespot", or "match"
            json_data (str): String in correct JSON format.
        
        json_data examples:

            Creating a user with forced key:
                {"name": myUserName,
                "current_location": [40.00, -71.00],
                "force_key": "1"}

        """ # If force_key for creating a user, put that as JSON key/field.
        self._validate_model_name(object_type)
        new_object_id = None
        object_type = object_type.lower()
        if object_type == "user":
            user_db = self._model_interface("user")
            new_object_id = user_db.create_user(json_data)
        elif object_type == "datespot":
            datespot_db = self._model_interface("datespot")
            datespot_db.create_datespot(json_data)
        elif object_type == "match":
            match_db = self._model_interface("match")
            json_data = json.loads(json_data)
            user_id_1, user_id_2 = json_data["users"]
            new_object_id = match_db.create_match(user_id_1, user_id_2)
        elif object_type == "message":
            message_db = self._model_interface("message")
            new_object_id = message_db.create_message(json_data)
        elif object_type == "chat":
            chat_db = self._model_interface("chat")
            new_object_id = chat_db.create_chat(json_data)

        if new_object_id:
            return new_object_id

    def get_obj(self, object_type, object_id): # todo need consistent naming. "Post" uses full word "object" not "obj"
    
        """
        Return an internal-model object literal for the data corresponding to the key "id".

        Args:
            object_type (str): "user", "datespot", or "match"
            id (int): primary key of an object in the database.
        
        Returns:
            (model object): Instance of one of the app's custom model classes.
        """
        self._validate_model_name(object_type) # todo rename "object_type" arg to "model_name"
        model_db = self._model_interface(object_type)
        return model_db.lookup_obj(object_id)
    
    def get_all_obj(self, object_type, object_id) -> str:
        self._validate_model_name(object_type)
        model_db = self._model_interface(object_type)
        return model_db._get_all_data() # todo don't use an internal method

    def get_json(self, object_type, object_id) -> str:
        """
        Return the JSON for the object corresponding to object_id.
        """
        self._validate_model_name(object_type)
        model_db = self._model_interface(object_type)
        return model_db.lookup_json(object_id) # todo not implemented for match model interface

    def get_all_json(self, object_type) -> str:
        """
        Return JSON of all objects of the specified type.
        """
        self._validate_model_name(object_type)
        model_db = self._model_interface(object_type)
        return json.dumps(model_db._get_all_data()) # todo meant to be an internal method. Goal is to implement s/t can use model_db.data public attribute.
    
    def put_json(self, object_model_name:str, object_id:int, new_json: str) -> None:
        """
        Update the stored JSON for the corresponding field of the corresponding object."""

        if object_model_name ==  "user":
            user_db = self._model_interface("user")
            user_db.update_user(object_id, new_json)
        if object_model_name == "chat":
            chat_db = self._model_interface("chat")
            chat_db.update_cjat(object_id, new_json)
    
    def post_swipe(self, user_id, candidate_id, outcome_json: str) -> bool:
        """
        Sends swipe data to the DB and returns True if the swipe completed a pending match (i.e. 
        other user had already swiped yes).
        
        Args:
            outcome_json (str): JSON in format "{'outcome': 1}" for yes or "{'outcome': 0} for no.
        """
        outcome = json.loads(outcome_json)["outcome"]
        if not (outcome == 0 or outcome == 1):
            raise ValueError
        outcome = bool(outcome)
        user_db = self._model_interface("user")
        if not outcome:
            user_db.blacklist(user_id, candidate_id)
        else: # todo cleaner to just send the update as JSON?
            # first check if the other user already like the active user:
            if user_db.lookup_is_user_in_pending_likes(candidate_id, user_id):
                return True
            else:
                user_db.add_to_pending_likes(user_id, candidate_id)
        return False

    def get_datespots_near(self, location: tuple, radius: int=2000) -> list:
        # Todo: Ultimately, we want to check the cache first, there might've just been a query at that location
        #   such that another API call is wasteful recomputation on the same reviews data.
        if not self._live_yelp: # todo add "and if not live google"?
            return self._get_cached_datespots_near(location, radius)
        elif self._live_yelp:
            # Todo: First, analyze whether we have cached data sufficient to respond to the query. If so, return self._get_cached_datespots_near(),
            #   even if we're in live-yelp mode. Maybe an LRU cache of lat lon radius circles--if there was a search inside that circle recently enough
            #   to still be in the LRU cache, then return cached results?
            return self._get_yelp_datespots_near(location, radius)
            
    
    def _cache_datespots(self, datespot_dict_list: list):
        datespot_db = self._model_interface("datespot")
        for datespot_dict in datespot_dict_list:
            datespot_json = json.dumps(datespot_dict)
            if not datespot_db.is_in_db(datespot_json):
                datespot_db.create_datespot(datespot_json)

    def _get_yelp_datespots_near(self, location, radius):
        datespot_json_list = self._yelp_client.search_businesses_near(location, radius)
        self._cache_datespots(datespot_json_list)
        return datespot_json_list # todo we want this and get_cached_datespots_near to return identically structured lists
                                    #  Rn, this returns list of strings, other one returns list of dicts. 

    def _get_cached_datespots_near(self, location: tuple, radius: int=2000) -> list: # todo make private method?
        """Wrapper for datespot api's query near. Return list of serialized datespots within radius meters
        of location."""

        # Todo: Dispatch differently for live vs. static google maps mode. One set of instructions for looking up from testmode cache,
        #   one for having the client make a real API call. 

        datespots_db = self._model_interface("datespot")
        # todo validate the location and radius here?
        results = datespots_db.query_datespot_objs_near(location, radius)
        return results
    
    def get_datespot_suggestions(self, match_id) -> list:
        """
        Return list of Datespot objects and their distances from the Match's midpoint, ordered by distance.
        """

        # Instantiate the Match object
        match_obj = self.get_obj("match", match_id)

        # Ask it the midpoint to use
        midpoint = match_obj.midpoint

        # Perform a geographic query using that midpoint
        candidate_datespots = self.query_datespot_objs_near(midpoint) # todo can one-liner this into passing match_obj.midpoint as the arg

        # Pass that list[Datespot] to Match's next_suggestion public method.
        return match_obj.suggestions(candidate_datespots) # todo TBD how much we care about returning just one vs. returning a prioritized queue
                                                    #   and letting the client handle swiping on restaurants without needing a new query every time
                                                    #   the users reject a suggestion. Would guess that latter approach is better practice.

        
    def get_next_candidate(self, user_id: int) -> int:
        """
        Returns user id of next candidate.
        """
        user_db = self._model_interface("user")
        return user_db.query_next_candidate(user_id)

    def get_message_sentiment(self, message_id: str) -> float:
        """Return the average sentiment for message matching this id."""
        message_db = self._model_interface("message")    
        json_data = json.loads(message_db.lookup_json(message_id))
        return json_data["sentiment"]

    def find(self, object_type: str, field: str, *args) -> str:
        # See https://stackoverflow.com/questions/18591778/how-to-pass-an-operator-to-a-python-function
        """
        Returns JSON string of the corresponding object(s).

        Args:
            object_type (str): "user", "datespot", or "match"
            field (str): key in the JSON object.
            *args (str): Further query parameters, e.g. MongoDB-like query parameters. 

        Returns:
            str : JSON for the objects matching the query

        Examples:
            db.find("user", "name", "=", "Grort")  # Return users with name == "Grort"

        """
        pass

def test_live_yelp(location, radius=DEFAULT_RADIUS):
    """Test function for use ad hoc use outside main tests suite."""
    live_db = DatabaseAPI(live_yelp=True) # Defaults to the main mock DB json map
    live_db.get_datespots_near(location)

def main():

    for i in range(len(sys.argv)):
            print(f"sys.argv[{i}] = {sys.argv[i]}")

    if len(sys.argv) > 2:
        
        if sys.argv[1] == "--test":
            if sys.argv[2] == "--live":
                test_location = (40.74977666604178, -73.99597469657479)
                test_live_yelp(test_location)

if __name__ == "__main__":
    main()
