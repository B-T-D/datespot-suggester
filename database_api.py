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

    def add(self, object_type: str, json_data: str) -> int:
        """

        Args:
            
            object_type (str): "user", "datespot", or "match"
            json_data (str): String in correct JSON format.

        """
        object_type = object_type.lower()
        if not self._validate_object_type(object_type): # todo how best to handle? Raise exception? String message back to caller rather than just int?
            return 1
        if object_type == "user":
            raise NotImplementedError
        elif object_type == "datespot":
            datespot_db = datespot_api.DatespotAPI()
            datespot_db.create_datespot(json_data)
        elif object_type == "match":
            raise NotImplementedError


    # Todo: All keys need to be ints in externally passable JSON.
    #   Also the restaurant tuples as keys might end up adding duplicates, if google maps has slightly different lat lon in the response sometimes. 
    def get(self, object_type, id) -> int:
    
        """

        Args:
            object_type (str): "user", "datespot", or "match"
            id (int): primary key of an object in the database.
        """
        pass

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



