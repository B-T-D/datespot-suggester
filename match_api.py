"""
Interface between database and the Match model.
"""

import json
import match
import time

import user_api

JSON_DB_NAME = "jsonMap.json"

class MatchAPI:

    def __init__(self, datafile_name=JSON_DB_NAME):
        self._master_datafile = datafile_name
        self._datafile = None
        self.data = {}
        self._load_db() # todo handle better
        self.user_api_instance = user_api.UserAPI(datafile_name=self._master_datafile)
    
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
            self.data[tupleKey] = jsonData[stringKey]
    
    def _update_json(self):
        if not self._datafile:
            self._set_datafile()

        # convert each tuple key to a string:
        jsonData = {}
        for tupleKey in self.data:
            stringKey = self._tuple_key_to_string(tupleKey)
            jsonData[stringKey] = self.data[tupleKey]
        
        with open(self._datafile, 'w') as fobj:
            json.dump(jsonData, fobj)
            fobj.seek(0)

    def _tuple_key_to_string(self, tuple_key: tuple) -> str:
        return str(tuple_key)

    def _string_key_to_tuple(self, string_key: str) -> tuple:
        stripped = string_key.strip('()')
        values = [float(substring) for substring in stripped.split(sep=',')]
        return tuple(values)
    
    def create_match(self, userid_1: int, userid_2: int):
        matchKey = (userid_1, userid_2) # hashable tuple of (int, int)
        self.data[matchKey] = {"users": [userid_1, userid_2]}
        self._update_json()
        return matchKey
    
    def load_match(self, matchKey: tuple):
        """
        Return a match object corresponding to those user ids.
        """
        matchData = self.data[(matchKey)]
        userid_1, userid_2 = matchKey[0], matchKey[1]
        print(f"\n--------------------user id 1 = {userid_1} {type(userid_1)}")
        user1 = self.user_api_instance.load_user(userid_1)
        user2 = self.user_api_instance.load_user(userid_2)
        matchObj = match.Match(user1, user2)
        return matchObj
    
    def update_match(self, data): # Todo
        # e.g. if the current location changed, meaning the Match.midpoint changed
        pass

    def delete_match(self, matchKey: tuple):
        del self.data[matchKey]