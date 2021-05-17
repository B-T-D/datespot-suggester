"""
Implementation-agnostic interface between the database and JSON-using external code. Goal is for external calling code to 
be unaffected by SQL vs. NoSQL and similar issues.
"""

import json

import model_interfaces

# todo: The models should serialize. That will expand reusability of the model interfaces. 

JSON_MAP_FILENAME = "jsonMap.json"

class DatabaseAPI:

    def __init__(self, json_map_filename: str=JSON_MAP_FILENAME, live_google_maps: bool=False):
        self._valid_model_names = {"user", "datespot", "match", "review", "message", "chat"}
        self._json_map_filename = json_map_filename
        self._live_google_maps = live_google_maps

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

    def post_object(self, object_type: str, json_data: str, **kwargs) -> str:
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
            if "force_key" in kwargs:
                new_object_id = user_db.create_user(json_data, kwargs["force_key"])
            else:
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
        user_db = user_api.UserAPI()
        if not outcome:
            user_db.blacklist(user_id, candidate_id)
        else: # todo cleaner to just send the update as JSON?
            # first check if the other user already like the active user:
            if user_db.lookup_is_user_in_pending_likes(candidate_id, user_id):
                return True
            else:
                user_db.add_to_pending_likes(user_id, candidate_id)
        return False

    def get_datespots_near(self, location: tuple, radius: int) -> list:
        """Wrapper for datespot api's query near. Return list of serialized datespots within radius meters
        of location."""

        # Todo: Dispatch differently for live vs. static google maps mode. One set of instructions for looking up from testmode cache,
        #   one for having the client make a real API call. 

        datespots_db = self._model_interface("datespot")
        # todo validate the location and radius here?
        results = datespots_db.query_datespots_near(location, radius)
        return results
    
    def get_next_datespot(self, match_id) -> str:
        """
        Return JSON for the next suggested date location for this match.
        """
        match_db = self._model_interface("match")
        return match_db.get_next_suggestion(match_id)
    
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