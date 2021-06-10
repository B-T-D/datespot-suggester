"""
Implementation-agnostic interface between internal app database and JSON-using external code. Provides public methods that parallel HTTP request
methods and return JSON.

Goal is for external calling code to be unaffected by SQL vs. NoSQL and similar issues.
"""

import sys, os, dotenv
from typing import List

import model_interfaces, models

import api_clients.yelp_api_client
from project_constants import *

JSON_MAP_FILENAME = "jsonMap.json"  

class DatabaseAPI:

    def __init__(self, json_map_filename: str=JSON_MAP_FILENAME, live_google_maps: bool=False, live_yelp: bool=False):
        self._valid_model_names = {"user", "datespot", "match", "review", "message", "chat"}
        self._json_map_filename = json_map_filename
        self._live_google_maps = live_google_maps # TODO implement different dispatching for the datespot queries based on this setting
        self._live_yelp = live_yelp # TODO one combined boolean toggle "live mode"

        self._yelp_client = api_clients.yelp_api_client.YelpClient()

    ### Public methods ### 

    # TODO: Decorator that calls string.lower() on object_model_name for any method that takes that as a string arg.
    
    def post_object(self, args_data: dict) -> str:
        """
        Add data for a new object to the database and return its id string.

        Args:
            
            json_arg (str): JSON string specifying the object-model name to create, and providing
                the initialization data for the new object.
        
        json_arg examples:

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
        object_model_name = args_data["object_model_name"]
        new_data = args_data["object_data"]
        self._validate_model_name(object_model_name)
        new_object_id = self._model_interface(object_model_name).create(new_data)
        if new_object_id:
            return new_object_id
        else:
            raise Exception("Failed to post object")

    def put_data(self, args_data: dict) -> None:
        supported_models = {"user", "datespot", "match", "chat"}  # Review and Message aren't updateable.
        object_model_name = args_data["object_model_name"]
        if not object_model_name in supported_models:
            raise ValueError(f"Updating {object_model_name} model data not supported.")
        object_id = args_data["object_id"]
        update_data = args_data["update_data"]
        
        model_interface = self._model_interface(object_model_name)
        model_interface.update(object_id, update_data)

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
    
    def post_decision(self, query_data: dict) -> str:
        """
        Sends swipe data to the DB and returns True if the swipe completed a pending match (i.e. 
        other user had already swiped yes).
        
        
        json_arg examples:

            {
                "user_id": "abc123",
                "candidate_id: "987zyx",
                "outcome": false
            }

            - false indicates user doesn't want to match with candidate
        """
        user_id, candidate_id, outcome = query_data["user_id"], query_data["candidate_id"], query_data["outcome"]
        # if not self._is_valid_decision:  # TODO implement--requires updating User model to have a candidates data structure
        #     raise ValueError("Invalid decision, e.g. that user wasn't supposed to have been deciding on that candidate")
        if not isinstance(outcome, bool): # TODO need comprehensive approach to validation
            raise TypeError(f"Expected outcome to be of type bool, actual type was {type(outcome)}")
        response_data = {"match_created": False}
        user_db = self._model_interface("user")
        if not outcome:
            user_db.blacklist(user_id, candidate_id)
        else:
            # first check if the other user already liked the active user:
            if user_db.lookup_is_user_in_pending_likes(candidate_id, user_id):
                response_data["match_created"] = True
                match_db = self._model_interface("match")  # Handle Match creation here
                match_id = match_db.create({
                    "user1_id": user_id,
                    "user2_id": candidate_id
                })
                
            else:
                user_db.add_to_pending_likes(user_id, candidate_id)
        return response_data
    
    def _is_valid_decision(self, user_id, candidate_id) -> bool:
        # TODO return False if candidate_id not in User.candidates
        raise NotImplementedError

    def get_login_user_info(self, query_data: dict) -> dict:
        """
        Returns JSON data in response to a login request. Either data about the user suitable for frontend rendering if valid login, else
        JSON containing an error message.

        Example query_data:

            {
                "user_id": "abc123"
            }

            - user_id is the only required field
        """
        response = {}
        user_id = query_data["user_id"]
        user_db = self._model_interface("user")
        if not user_db.is_valid_object_id(user_id):
            response["error"] = f"Invalid user id: '{user_id}'"
        else:
            response = user_db.render_user(user_id)
        return response

    def get_next_candidate(self, query_data: dict) -> dict:  # TODO: Return censored JSON appropriate for a Tinder-type front-end.  A React front end calling this doesn't have
                                                            #   much use for the user ID, but also don't want a swiping user to see all info about a candidate, so can't send back
                                                            #   the entire serialized User. Need a separate "send censored user data JSON to client" method
        """
        Returns JSON data about next candidate appropriate for display to an unknown other user.

        Example JSON:

            {
                "user_id": "abc123"
            }
        """
        user_id = query_data["user_id"]  # TODO validate
        user_db = self._model_interface("user")
        candidate_id = user_db.query_next_candidate(user_id)
        return user_db.render_candidate(candidate_id)

    def get_datespots_near(self, query_data: dict) -> list: # TODO if this returns Datespot objects it should prob be internal
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
        print(f"get_datespots_near was called")
        location = tuple(query_data["location"]) # TODO validate json
        radius = DEFAULT_RADIUS
        if "radius" in query_data:
            radius = query_data["radius"]
        if not self._live_yelp: # todo add "and if not live google"?
            return self._get_cached_datespots_near(location, radius)
        elif self._live_yelp: # TODO create a middleman script to permit 100% tests-coverage of this module?
            # Todo: First, analyze whether we have cached data sufficient to respond to the query. If so, return self._get_cached_datespots_near(),
            #   even if we're in live-yelp mode. Maybe an LRU cache of lat lon radius circles--if there was a search inside that circle recently enough
            #   to still be in the LRU cache, then return cached results?
            return self._get_yelp_datespots_near(location, radius)
    
    # TODO rename to "suggestion candidates". There are "suggestion candidates" and "match candidates".
    def get_candidate_datespots(self, query_data: dict) -> list:  # TODO probably obviated
        """  
        Return list of Datespot objects and their distances from the Match's midpoint, ordered by distance.

        Example json:

            {
                "match_id": "abc123"
            }
        """

        # Instantiate the Match object
        match_id = query_data["match_id"]
        match_obj = self._model_interface("match").lookup_obj(match_id)

        # Ask it the midpoint to use
        midpoint = match_obj.midpoint
        distance = match_obj.distance

        print(f"from DBAPI get_candidate_datespots(): users are {match_obj.distance}m apart with midpoint at {midpoint}")

        radius = max(DEFAULT_RADIUS, distance)  # Query a radius of at least DEFAULT_RADIUS, but if users are farther apart than that, query 
                                                #   from the center of a circle that has each user location on its perimeter.
        results = self.get_datespots_near({"location": midpoint, "radius": radius})
        max_possible_radius = (EARTH_CIRCUMFERENCE_KM // 2) * 1000  # Maximum logical query radius, in meters. Querying radius equal to 1/2 Earth's circumference
                                                                    #   would query all points on Earth. 
        
        # TODO Set the min suggestion candidates higher, to at least 10, once the system is more robust
        while len(results) < MIN_SUGGESTION_CANDIDATES and radius < max_possible_radius:  # If no results, double the query radius and try again until querying entire Earth
            radius *= 2  # TODO In many cases might make more sense to intelligently move the location instead of expanding the radius
            results = self.get_datespots_near({"location": midpoint, "radius": radius})  

        return results

        # Perform a geographic query using that midpoint
        #candidate_datespots = self.get_datespots_near({"location": midpoint}) # todo can one-liner this into passing match_obj.midpoint as the arg

        # Pass that list[Datespot] to Match's next_suggestion public method.
        return match_obj.suggestions(candidate_datespots) # todo TBD how much we care about returning just one vs. returning a prioritized queue
                                                    #   and letting the client handle swiping on restaurants without needing a new query every time
                                                    #   the users reject a suggestion. Would guess that latter approach is better practice.
    
    def get_matches_list(self, query_data: dict) -> List[dict]:
        """
        Args:
            query_data (dict): Dictionary containing the user_id. E.g.
                    {"user_id": "abc123"}
        
        Returns:
            (list[dict]): List containing one dictionary of rendering appropriate/relevant data for each specified
                Match of which the specified User is a member.
        """
        user_id = query_data["user_id"]
        return self._model_interface("user").render_matches_list(user_id)
    
    def get_suggestions_list(self, query_data: dict) -> List[dict]:
        """
        Returns a list of dicts containing display relevant/appropriate info about each of a Match's suggested Datespots.

        Args:
            query_data (dict): Dictionary containing the match_id. E.g.
                    {"match_id": "abc123"}
        
        Returns:
            (list[dict]): List of dictionaries of data about each Datespot.
        """
        print(f"get suggestions list was called")
        match_id = query_data["match_id"]

        match_db = self._model_interface("match")
        if match_db.suggestion_candidates_needed(match_id):
            print(f"more suggestion fodder candidates needed")
            candidates = self.get_candidate_datespots(query_data)
            print(f"got {len(candidates)} suggestions candidates; passing them to matchMI refresh candidates")
            match_db.refresh_suggestion_candidates(match_id, candidates)

        return self._model_interface("match").render_suggestions_list(match_id)


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
            if not datespot_db.is_known_name_location(datespot_name=datespot_dict["name"], datespot_location=datespot_dict["location"]):
                datespot_db.create(datespot_dict)  # TODO unittest confirming this won't duplicatively enter the same restaurant
                
    def _get_yelp_datespots_near(self, location, radius):
        datespot_json_list = self._yelp_client.search_businesses_near(location, radius)
        self._cache_datespots(datespot_json_list)
        return datespot_json_list # todo we want this and get_cached_datespots_near to return identically structured lists
                                    #  Rn, this returns list of strings, other one returns list of dicts. 

    def _get_cached_datespots_near(self, location: tuple, radius: int=2000) -> List[models.Datespot]:
        """Wrapper for datespot api's query near. Return list of serialized datespots within radius meters
        of location."""

        # Todo: Dispatch differently for live vs. static google maps mode. One set of instructions for looking up from testmode cache,
        #   one for having the client make a real API call.

        print(f"_get_cached_datespots_near() was called with location {type(location)} = {location}, radius{type(radius)} = {radius}")

        datespots_db = self._model_interface("datespot")
        # todo validate the location and radius here?
        results = datespots_db.query_datespot_objs_near(location, radius)
        return results

def test_live_yelp(location, radius=DEFAULT_RADIUS):
    """Test function for use ad hoc use outside main tests suite."""
    live_db = DatabaseAPI(live_yelp=True) # Defaults to the main mock DB json map
    live_db.get_datespots_near(query_data = {"location": location, "radius": radius})

def main():

    if len(sys.argv) > 2:
        
        if sys.argv[1] == "--test":
            if sys.argv[2] == "--live":
                test_location = (40.74977666604178, -73.99597469657479)
                test_live_yelp(test_location)

if __name__ == "__main__":
    main()