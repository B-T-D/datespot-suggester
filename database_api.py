"""
Implementation-agnostic interface between the database and JSON-using external code. Goal is for external calling code to 
be unaffected by SQL vs. NoSQL and similar issues.
"""

import user_api
import datespot_api
import match_api

class DatabaseAPI:

    def __init__(self):
        self._valid_object_types = {"user", "datespot", "match"}

    def _validate_object_type(self, object_type: str):
        return object_type.lower() in self._valid_object_types

    def add(self, object_type: str, json_data: str, **kwargs) -> int:
        """

        Args:
            
            object_type (str): "user", "datespot", or "match"
            json_data (str): String in correct JSON format.

        """
        new_object_id = None
        object_type = object_type.lower()
        if not self._validate_object_type(object_type): # todo how best to handle? Raise exception? String message back to caller rather than just int?
            return 1
        if object_type == "user":
            user_db = user_api.UserAPI()
            if "force_key" in kwargs:
                new_object_id = user_db.create_user(json_data, kwargs["force_key"])
            else:
                new_object_id = user_db.create_user(json_data)
        elif object_type == "datespot":
            datespot_db = datespot_api.DatespotAPI()
            datespot_db.create_datespot(json_data)
        elif object_type == "match":
            raise NotImplementedError

        if new_object_id:
            return new_object_id

    # Todo: All keys need to be ints in externally passable JSON.
    #   Also the restaurant tuples as keys might end up adding duplicates, if google maps has slightly different lat lon in the response sometimes. 
    def get_obj(self, object_type, id) -> int:
    
        """
        Return an internal-model object literal for the data corresponding to the key "id".

        Args:
            object_type (str): "user", "datespot", or "match"
            id (int): primary key of an object in the database.
        """
        if object_type == "datespot":
            datespot_db = datespot_api.DatespotAPI()
            return datespot_db.lookup_datespot(id)
        else:
            raise NotImplementedError

    def get_json(self, object_type, object_id) -> str:
        """
        Return the JSON for the object corresponding to object_id.
        """
        if object_type == "user":
            user_db = user_api.UserAPI()
            return user_db.lookup_user_json(object_id)
    
    def put_json(self, object_type:str, object_id:int, new_json: str) -> None:
        """
        Update the stored JSON for the corresponding field of the corresponding object."""

        if object_type ==  "user":
            user_db = user_api.UserAPI()
            user_db.update_user(object_id, new_json)
    

    def get_datespots_near(self, location: tuple, radius: int) -> list:
        """Wrapper for datespot api's query near. Return list of serialized datespots within radius meters
        of location."""

        datespots_db = datespot_api.DatespotAPI()
        # todo validate the location and radius here?
        results = datespots_db.query_datespots_near(location, radius)
        return results
    
    def get_next_candidate(self, user_id: int) -> str:
        """
        Returns the stored JSON info on the next candidate.
        """
        user_db = user_api.UserAPI()
        candidate_id = user_db.query_next_candidate(user_id) # This only returns the user's id key
        candidate_json = user_db.lookup_user_json(candidate_id)
        return candidate_json
    
    def post_swipe(self, user_id: int, candidate_id: int, swipe: bool) -> bool:
        """
        Args:
            user_id (int): pass
            candidate_id (int): pass
            swipe (bool): True if user wants to match with candidate, else False.
        
        Returns:
            (bool): True if candidate already wants to match with user, else False.
        """
        # todo case "candidate already swiped 'no'" should be handled by that candidate never
        #   having been shown to user in the first place, confirm that's happening. 
        

    def find(self, object_type: str, field: str, *args) -> str:
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



