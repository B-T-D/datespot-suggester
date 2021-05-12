"""
Interface between the database and the User model.
"""

# This one is cluttered so that the domain layer user.py can be relatively clean.
# Repository design pattern.

import uuid
import json
import user
import time

import model_api_ABC
import geo_utils

class UserAPI(model_api_ABC.ModelAPI):

    def __init__(self, datafile_name=None):
        if datafile_name: # Todo is there a one-liner for this? Ternary expression?
            super().__init__(datafile_name)
        else:
            super().__init__()

        self._model = "user"
        self._valid_model_fields = ["name", "current_location", "home_location", "likes", "dislikes", "match_blacklist"]
        
    def create_user(self, json_data: str, force_key: int=None) -> int:
        """
        Takes json data in the app's internal format and returns the id key of the newly created user.
        Force key arg is for testing purposes to not always have huge unreadable uuids.
        """
        self._read_json()
        json_dict = json.loads(json_data)
        for key in json_dict:
            if not key in self._valid_model_fields:
                raise ValueError(f"Bad JSON in call to create_user: \n{key}")
        location = tuple(json_dict["current_location"])
        if force_key: # Don't allow force-creating a key that's already taken
            if force_key in self._data:
                raise ValueError(f"Can't force-create with key {force_key}, already in DB.")
            user_id = force_key
        else:
            user_id  = uuid.uuid1().int
        # todo rationale for instantiating here is that the model may have algorithms it runs that add data.
        #   E.g. for restaurants, instantiating a datespot and running the apply-brand-reps method will add 
        #   traits that can then be included in the initial db write. Not sure if this is actually good architecture.

        # todo won't that ^ cause circular imports if the models' are using this DBAPI to instantiate other model objects?
        new_user = user.User(
            name=json_dict["name"],
            current_location = location
        )
        self._data[user_id] = self._serialize_user(new_user)
        self._write_json()
        return user_id

    def lookup_user(self, user_id: int) -> user.User: # todo the keys in the dict are ending up as string, not ints. Not obvious why.
        """
        Instantiates a User object to represent an existing user, based on data retrieved from the database. Returns the User object,
        or raises error if not found.
        """
        self._read_json()
        user_data = self._data[user_id]
        assert type(user_data) == dict
        user_obj = user.User(
            name=user_data["name"],
            current_location=user_data["current_location"],
            home_location=user_data["home_location"],
            likes = user_data["likes"],
            dislikes = user_data["dislikes"]
        )
        if "match_blacklist" in user_data: # todo legacy for mock entries that didn't have the field
            user_obj.match_blacklist = user_data["match_blacklist"]

        return user_obj

    def blacklist(self, current_user_id: int, other_user_id: int):  # todo can prob create a custom decorator that says "whenever this method is called, call read json right before and update json right after"
        """
        Add other_user_id to current_user_id user's no-match blacklist.
        """
        self._read_json()
        user_data = self._data[current_user_id]
        if not "match_blacklist" in user_data: # todo legacy, should be able to just initialize them with a blank dict
            user_data["match_blacklist"] = {other_user_id: time.time()}
        else:
            user_data["match_blacklist"][other_user_id] = time.time()
        self._write_json()


    def update_user(self, user_id): # todo -- updating location might be single most important thing this does. 
        pass
    
    # todo all the "query objects near" methods could probably be abstracted to the ABC.
    def query_users_currently_near(self, location: tuple, radius=50000): # todo is the radius parameter totally unnecessary? 
        """
        Return list of serialized users whose current location is within radius meters of location.
        """
        # Defaults to a very high radius, expectation is that radius won't be specified in most queries.

        if (not location) or (not geo_utils.is_valid_lat_lon(location)): # todo best architectural place for validating this?
            raise ValueError(f"Bad lat lon location: {location}")
        self._read_json()
        query_results = []
        for user_id in self._data:
            user = self._data[user_id]
            user_location = user["current_location"]
            distance = geo_utils.haversine(location, user_location)
            if distance < radius:
                query_results.append((distance, user_id)) # todo no need to put the whole dict into the results, right?
        query_results.sort()
        return query_results

    def _serialize_user(self, user: user.User) -> dict: # todo: superfluous?
        """
        Create a dictionary representation of the user.
        """
        userDict = {
            "name": user.name,
            "current_location": user.current_location,
            "home_location": user.home_location,
            "likes": user.likes,
            "dislikes": user.dislikes
        }
        return userDict


def main():
    pass


if __name__ == "__main__":
    main()