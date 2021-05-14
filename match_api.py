"""
Interface between database and the Match model.
"""

import json
import match
import time

import user_api
import datespot_api

import model_api_ABC

# todo: For all three "api": At a given point in time, a model instance's data is either a json-legal dict,
#   or an app-internal dict literal. Those are the only options. Should be one method that toggles between them,
#   and should be simple and obvious to tell which way it's toggled at any given place in the code / execution.

class MatchAPI(model_api_ABC.ModelAPI):

    def __init__(self, json_map_filename=None):
        self._model = "match"
        if json_map_filename:
            super().__init__(json_map_filename)
        else:
            super().__init__()

        

        self.user_api_instance = user_api.UserAPI(json_map_filename=self._master_datafile)
    
    def _set_datafile(self):
        """Set the filename of the specific file containing the match data JSON."""
        with open(self._master_datafile, 'r') as fobj:
            jsonMap = json.load(fobj)
            fobj.seek(0)
        self._datafile = jsonMap["match_data"]

    def _load_db(self):
        """Load stored JSON into memory."""
        jsonMap = None

        with open(self._master_datafile, 'r') as fobj: # todo this can be DRY-ed. Identical for match, user, and datespot DB APIs.
            jsonMap = json.load(fobj)
            fobj.seek(0)
        
        self._datafile = jsonMap["match_data"]
        matchJson = None
        with open(self._datafile, 'r') as fobj:
            matchJson = json.load(fobj)
            fobj.seek(0)
        
        # convert each key to tuple literal:
        jsonData = {}
        for stringKey in jsonData:
            tupleKey = self._string_key_to_tuple(stringKey)
            self._data[tupleKey] = jsonData[stringKey]
    

    def _tuple_key_to_string(self, tuple_key: tuple) -> str:
        return str(tuple_key)

    def _string_key_to_tuple(self, string_key: str) -> tuple:
        stripped = string_key.strip('()')
        values = [float(substring) for substring in stripped.split(sep=',')]
        return tuple(values)
    
    def create_match(self, user1_id: str, user2_id: str) -> str:
        """
        Create a Match object from the two users and return its id key.
        """
        self._read_json()
        user1_obj, user2_obj = self.user_api_instance.lookup_obj(user1_id), self.user_api_instance.lookup_obj(user2_id)
        match_obj = match.Match(user1_obj, user2_obj)
        new_object_id = match_obj.id
        self._data[new_object_id] = {
            "users": [user1_id, user2_id],
            "timestamp": time.time()
        }
        self._write_json()
        return new_object_id

    # def create_match(self, userid_1: str, userid_2: str) -> str: # todo the create methods can probably be abstracted to the ABC too
    #     self._read_json()
    #     match_key = hash((userid_1, userid_2)) # hashable tuple of (int, int)
    #     # todo create a Match instance and uses hash(matchInstance) as the id
    #     if self._is_valid_object_id(match_key):
    #         raise KeyError("match_key collision") # todo unit test confirming trying to re-match the same users causes collision
    #     self._data[match_key] = {"users": [userid_1, userid_2], "timestamp": time.time()}
    #     self._write_json()
    #     return match_key
    
    def lookup_obj(self, match_id: int) -> match.Match:
        self._read_json()
        self._validate_object_id(match_id)
        match_data = self._data[match_id] # todo the three lines through the end of this one could easily go to a helper method in the ABC. E.g. _get_data_for_id
        user_id_1, user_id_2 = match_data["users"][0], match_data["users"][1]
        user1 = self.user_api_instance.lookup_obj(user_id_1)
        user2 = self.user_api_instance.lookup_obj(user_id_2)
        match_obj = match.Match(user1, user2)
        return match_obj
    
    def get_all_suggestions(self, match_id: int) -> list:
        """Get the full list of suggested restaurants for a match."""
        self._read_json()
        match_obj = self.lookup_obj(match_id)
        datespots = match_obj.get_suggestions()
        if not "suggestions_queue" in self._data[match_id]:
            self._data[match_id]["suggestions_queue"] = [datespot.id for datespot in datespots]
        self._write_json()
        return datespots # todo if external code wants the full list, need to return as strings or dicts not the internal objects
    
    def get_next_suggestion(self, match_id: int) -> dict:
        """
        Return a Python native dict of the top suggestion, and update the suggestions queue in the DB.
        """
        self._read_json()
        self.get_all_suggestions(match_id)
        datespot_id = self._data[match_id]["suggestions_queue"].pop()
        datespot_db = datespot_api.DatespotAPI()
        return datespot_db.lookup_json(datespot_id)

    def update_match(self, data): # Todo
        # e.g. if the current location changed, meaning the Match.midpoint changed
        pass