"""
Implementation-agnostic interface between internal app database and JSON-using external code. Provides public methods that parallel HTTP request
methods and return JSON.

Goal is for external calling code to be unaffected by SQL vs. NoSQL and similar issues.
"""

import json
import sys

import model_interfaces

import api_clients.yelp_api_client


# Todo: In a live app, the messages wouldn't go through this JSON backend for analysis before continuing on to the recipient(s). Something would copy them
#   in the middle, send them immediately on to recipient, and then dispatch the data to the backend for analysis on a less urgent timeframe.

JSON_MAP_FILENAME = "jsonMap.json"
DEFAULT_RADIUS = 2000

class DatabaseAPI:

    def __init__(self, json_map_filename: str=JSON_MAP_FILENAME, live_google_maps: bool=False, live_yelp: bool=False):
        self._valid_model_names = {"user", "datespot", "match", "review", "message", "chat"}
        self._json_map_filename = json_map_filename
        self._live_google_maps = live_google_maps # TODO implement different dispatching for the datespot queries based on this setting
        self._live_yelp = live_yelp # TODO one combined boolean toggle "live mode"

        self._yelp_client = api_clients.yelp_api_client.YelpClient()

    ### Public methods ### 

    # TODO: Decorator that calls string.lower() on object_model_name for any method that takes that as a string arg.
    
    def post_object(self, json_arg: str) -> str:
        """
        Add data for a new object to the database and return its id string.

        Args:
            
            object_type (str): "user", "datespot", or "match"
            json_data (str): String in correct JSON format.
        
        json_data examples:

            Creating a user with forced key:

                {
                    "object_model_name": "user",
                    "json_data": {
                        "name": myUserName,
                        "current_location": [40.00, -71.00],
                        "force_key": "1"
                    }
                }
            
            - Location and name are required to create a new user

        """ # If force_key for creating a user, put that as JSON key/field.
        json_arg = json.loads(json_arg)
        object_model_name = json_arg["object_model_name"]
        json_data = json_arg["json_data"]
        self._validate_model_name(object_model_name)
        new_object_id = self._model_interface(object_model_name).create(json_data)
        if new_object_id:
            return self.get_login_user_info(json.dumps({"user_id": new_object_id}))
        else:
            raise Exception("Failed to post object")

    def get_object(self, object_type, object_id):
    
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

    def get_json(self, json_arg: str) -> str:
        """
        Return the JSON for the object corresponding to object_id.

        json_arg examples:

            Get a user by id:

                {
                    "object_model_name": "user",
                    "object_id": "abc123"
                }
        """
        json_arg = json.loads(json_arg)
        object_model_name = json_arg["object_model_name"]
        object_id = json_arg["object_id"]
        self._validate_model_name(object_model_name)
        model_db = self._model_interface(object_model_name)
        return model_db.lookup_json(object_id)
    
    def _get_json(self, object_type, object_id) -> str: # internal version that doesn't require tedious JSON arg
        """
        Return the JSON for the object corresponding to object_id.
        """
        self._validate_model_name(object_type)
        model_db = self._model_interface(object_type)
        return model_db.lookup_json(object_id)

    def get_all_json(self, object_type) -> str:
        """
        Return JSON of all objects of the specified type.
        """
        model_db = self._model_interface(object_type)
        return json.dumps(model_db._get_all_data()) # todo meant to be an internal method. Goal is to implement s/t can use model_db.data public attribute.
    
    def put_json(self, object_model_name:str, object_id:int, new_json: str) -> None: # TODO return success/error message as JSON
        """
        Update the stored JSON for the corresponding field of the corresponding object.
        """
        supported_models = {"user", "datespot", "match", "chat"}  # Review and Message aren't updateable.

        if not object_model_name in supported_models:
            raise ValueError(f"Updating {object_model_name} model data not supported.")

        model_interface = self._model_interface(object_model_name)
        # TODO This should be codeable s/t a single line call to model_interface.update(object_id, new_json)
        #   works for all models. All the MIs should name their updater to work with that.
        model_interface = self._model_interface(object_model_name)
        model_interface.update(object_id, new_json)
    
    def post_swipe(self, json_data: str) -> str:
        """
        Sends swipe data to the DB and returns True if the swipe completed a pending match (i.e. 
        other user had already swiped yes).
        
        
        json_data examples:

            {
                "user_id": "abc123",
                "candidate_id: "987zyx",
                "outcome": false
            }

            - false indicates user doesn't want to match with candidate
        """
        swipe_data = json.loads(json_data)
        user_id, candidate_id, outcome = swipe_data["user_id"], swipe_data["candidate_id"], swipe_data["outcome"]
        if not isinstance(outcome, bool): # TODO need comprehensive approach to validation
            raise ValueError
        response = {"match_created": False}
        user_db = self._model_interface("user")
        if not outcome:
            user_db.blacklist(user_id, candidate_id)
        else:
            # first check if the other user already liked the active user:
            if user_db.lookup_is_user_in_pending_likes(candidate_id, user_id):
                response["match_created"] = True
            else:
                user_db.add_to_pending_likes(user_id, candidate_id)
        return json.dumps(response)

    def _prune_data_user(self, user_id: str) -> dict:
        """
        Returns JSON data about the user appropriate for display to that same user (what
        a user should be able to see about themself while logged in). Prunes undesired fields
        but does not alter data from server-side format (e.g. doesn't convert the user's matches
        to a usefully renderable list, instead leaves it as a list of user id strings.)
        """
        user_data = json.loads(self._get_json("user", user_id))
        user_safe_fields = self._model_interface("user").user_safe_model_fields
        pruned_data = {}
        for field in user_data:
            if field in user_safe_fields:
                pruned_data[field] = user_data[field]
        return pruned_data

    def _prune_data_candidate(self, candidate_id: str) -> dict:
        """
        Returns JSON of those user fields suitable for display as a candidate to some other user.
        JSON arg is the user id of the user to render data for.

        Example JSON:

            {
                "user_id": "abc123"
            }

        """
        candidate_data = json.loads(self._get_json("user", candidate_id))
        candidate_safe_fields = self._model_interface("user").candidate_safe_model_fields
        pruned_data = {}
        for field in candidate_data:
            if field in candidate_safe_fields:
                pruned_data[field] = candidate_data[field]
        return pruned_data
    
    # TODO have the methods that return HTTP-facing JSON be named with HTTP verbs, and ones that return server-side JSON
    #   be named differently?

    def get_login_user_info(self, json_arg: str) -> str:
        """
        Returns JSON data in response to a login request. Either data about the user suitable for frontend rendering if valid login, else
        JSON containing an error message.

        Example JSON:

            {
                "user_id": "abc123"
            }
        """
        response = {}
        user_id = json.loads(json_arg)["user_id"]
        user_db = self._model_interface("user")
        if not user_db.validate_object_id(user_id):
            response["error"] = f"Invalid user id: '{user_id}'"
        else:
            response = self._prune_data_user(user_id)
        return json.dumps(response)

    def get_next_candidate(self, json_arg: str) -> str:  # TODO: Return censored JSON appropriate for a Tinder-type front-end.  A React front end calling this doesn't have
                                                            #   much use for the user ID, but also don't want a swiping user to see all info about a candidate, so can't send back
                                                            #   the entire serialized User. Need a separate "send censored user data JSON to client" method
        """
        Returns JSON data about next candidate appropriate for display to an unknown other user.

        Example JSON:

            {
                "user_id": "abc123"
            }
        """
        user_id = json.loads(json_arg)["user_id"]  # TODO validate
        user_db = self._model_interface("user")
        candidate_id = user_db.query_next_candidate(user_id)
        return json.dumps(self._prune_data_candidate(candidate_id))

    def get_datespots_near(self, json_data) -> list: # TODO if this returns Datespot objects it should prob be internal
        """

        Example json_data:

            Location and non-default radius:
                {
                    "location": [40.737291166191476, -74.00704685527774],
                    "radius": 4000
                }

            Location only, use default radius:
                {
                    "location": [40.737291166191476, -74.00704685527774]
                }
        """
        # Todo: Ultimately, we want to check the cache first, there might've just been a query at that location
        #   such that another API call is wasteful recomputation on the same reviews data.
        geo_data = json.loads(json_data)
        location = tuple(geo_data["location"]) # TODO validate json
        radius = DEFAULT_RADIUS
        if "radius" in geo_data:
            radius = geo_data["radius"]
        if not self._live_yelp: # todo add "and if not live google"?
            return self._get_cached_datespots_near(location, radius)
        elif self._live_yelp: # TODO create a middleman script to permit 100% tests-coverage of this module?
            # Todo: First, analyze whether we have cached data sufficient to respond to the query. If so, return self._get_cached_datespots_near(),
            #   even if we're in live-yelp mode. Maybe an LRU cache of lat lon radius circles--if there was a search inside that circle recently enough
            #   to still be in the LRU cache, then return cached results?
            return self._get_yelp_datespots_near(location, radius)
    
    def get_datespot_suggestions(self, json_data: str) -> list:
        """
        Return list of Datespot objects and their distances from the Match's midpoint, ordered by distance.

        Example json:

            {
                "match_id": "abc123"
            }
        """

        # Instantiate the Match object
        match_id = json.loads(json_data)["match_id"]
        match_obj = self.get_object("match", match_id)

        # Ask it the midpoint to use
        midpoint = match_obj.midpoint

        # Perform a geographic query using that midpoint
        candidate_datespots = self.get_datespots_near(json.dumps({"location": midpoint})) # todo can one-liner this into passing match_obj.midpoint as the arg

        # Pass that list[Datespot] to Match's next_suggestion public method.
        return match_obj.suggestions(candidate_datespots) # todo TBD how much we care about returning just one vs. returning a prioritized queue
                                                    #   and letting the client handle swiping on restaurants without needing a new query every time
                                                    #   the users reject a suggestion. Would guess that latter approach is better practice.

    ### Private methods ###

    def _model_interface(self, model_name: str): # TODO integrate this approach below (change the separate constructor calls into calls to this)
        """
        Returns an instance of a model interface object for the specified model name.

        Args:
            model_name (str): String matching the name of a supported data model.
        
        Returns:
            A model-interface object for the specified model.
        """
        self._validate_model_name(model_name)
        # TODO Could shorten this a lot by using exec() on an fstring. Seems safe if this validates the model
        #   name and is >=2 layers below any requests from the actual web, right? The Node web API and the 
        #   backend JSON server entrypoint controller thing would be between this method and any attempt to pass
        #   arbitrary code to exec(). 
        #   Pro of using exec() would be lower maintenance in supporting further model names, or changes to model names.
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

    def _validate_model_name(self, model_name: str):
        if not model_name in self._valid_model_names:
            raise ValueError(f"Invalid model name: {model_name}")

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

    def _get_cached_datespots_near(self, location: tuple, radius: int=2000) -> list:
        """Wrapper for datespot api's query near. Return list of serialized datespots within radius meters
        of location."""

        # Todo: Dispatch differently for live vs. static google maps mode. One set of instructions for looking up from testmode cache,
        #   one for having the client make a real API call. 

        datespots_db = self._model_interface("datespot")
        # todo validate the location and radius here?
        results = datespots_db.query_datespot_objs_near(location, radius)
        return results

def test_live_yelp(location, radius=DEFAULT_RADIUS):
    """Test function for use ad hoc use outside main tests suite."""
    live_db = DatabaseAPI(live_yelp=True) # Defaults to the main mock DB json map
    live_db.get_datespots_near(location)

def main():

    if len(sys.argv) > 2:
        
        if sys.argv[1] == "--test":
            if sys.argv[2] == "--live":
                test_location = (40.74977666604178, -73.99597469657479)
                test_live_yelp(test_location)

if __name__ == "__main__":
    main()