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

    def __init__(self, json_map_filename=None):
        if json_map_filename: # Todo is there a one-liner for this? Ternary expression?
            super().__init__(json_map_filename)
        else:
            super().__init__()

        self._model = "user"
        self._valid_model_fields = ["name", "current_location", "home_location", "likes", "dislikes", "match_blacklist"] # todo is this necessary, or could you just check the keys?
        
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
        if force_key: # Don't allow force-creating a key that's already taken
            if force_key in self._data:
                raise ValueError(f"Can't force-create with key {force_key}, already in DB.")
            user_id = force_key
        else:
            user_id  = str(uuid.uuid1().int)
        # todo rationale for instantiating here is that the model may have algorithms it runs that add data.
        #   E.g. for restaurants, instantiating a datespot and running the apply-brand-reps method will add 
        #   traits that can then be included in the initial db write. Not sure if this is actually good architecture.

        # todo won't that ^ cause circular imports if the models' are using this DBAPI to instantiate other model objects?
        new_user = user.User(
            user_id = user_id,
            name=json_dict["name"],
            current_location = tuple(json_dict["current_location"])
        )

        self._data[user_id] = self._serialize_user(new_user)
        self._write_json()
        return user_id

    def lookup_json(self, user_id: int) -> str:
        """
        Return the JSON string for a user.
        """
        self._read_json()
        return json.dumps(self._data[user_id])

    def lookup_obj(self, user_id: str) -> user.User: # todo the keys in the dict are ending up as string, not ints. Not obvious why.
        """
        Instantiates a User object to represent an existing user, based on data retrieved from the database. Returns the User object,
        or raises error if not found.
        """
        self._read_json()
        self._validate_object_id(user_id)
        user_data = self._data[user_id]
        assert type(user_data) == dict
        user_obj = user.User(
            user_id = user_id,
            name=user_data["name"],
            current_location=user_data["current_location"],
            home_location=user_data["home_location"],
            likes = user_data["likes"],
            dislikes = user_data["dislikes"]
        )
        if "match_blacklist" in user_data: # todo legacy for mock entries that didn't have the field
            user_obj.match_blacklist = user_data["match_blacklist"]

        return user_obj


    def update_user(self, user_id: int, new_json: str): # todo -- updating location might be single most important thing this does. 
        """
        Takes JSON string, updates the native Python dict, and writes it to the stored master JSON.

        Specify the field to update as the key in the new_json string. E.g. {"location": (44.01, -72.12)} specifies to update location.
        """
        self._read_json()
        new_data = json.loads(new_json)
        user_data = self._data[user_id]
        for key in new_data:
            if not key in self._valid_model_fields: # todo this validation isn't complete or in the smartest/clearest place. Need to check shape, make sure 100% right about append vs. overwrite
                raise ValueError(f"Invalid user field: {key}")
            if type(new_data[key]) != type(user_data[key]):
                raise TypeError(f"Incorrect user data type for field {key}.\nExpected type {type(user_data[key])}")
        for key in new_data: # todo best practice on type() vs isinstance?
            entry_type = type(user_data[key])
            entry = user_data[key]
            if key == "current_location": # todo location still parses as list, so make sure to overwrite, not append
                self._data[user_id]["current_location"] = new_data[key]
            elif entry_type == list:
                self._data[user_id][key].extend(new_data[key])
            elif isinstance(entry, set):
                entry |= new_data[key] # todo this would require the new data to have been parsed to a set
            else:
                self._data[user_id][key] = new_data[key]
        self._write_json()
        return
    
    # todo all the "query objects near" methods could probably be abstracted to the ABC.
    def query_users_currently_near_location(self, location: tuple, radius=50000) -> list: # todo is the radius parameter totally unnecessary? 
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
        query_results.reverse() # Want to pop nearest candidate from end. 
        return query_results
           
    def query_users_near_user(self, user_id: int) -> list:
        """Return the list of users near this user and cache that list of candidates in this user's data."""
        self._read_json()
        query_location = self._data[user_id]["current_location"]
        query_results = self.query_users_currently_near_location(tuple(query_location))
        if query_results[-1] == user_id: # Don't include the user in that user's results
            query_results.pop()
        # Want to fully overwrite it to the latest and greatest, even if the cache already existed:
        self._data[user_id]["cached_candidates"] = query_results
        self._write_json()

        return query_results
    

    def _refresh_candidates(self, user_id) -> bool:
        """Return True if this user's candidates cache is null, empty, or otherwise should be updated."""
        user_data = self._data[user_id]
        if not "cached_candidates" in user_data or len(user_data["cached_candidates"]) < 1:
            return True
        return False

    def query_next_candidate(self, user_id) -> int:
        """Return the user id of the next candidate for user user_id to swipe on."""
        self._read_json()
        if self._refresh_candidates(user_id): # todo check if the user's location changed by enough to warrant a new query rather than pulling from cache
            self.query_users_near_user(user_id)
        user_data = self._data[user_id]
        candidate_id = user_data["cached_candidates"].pop()[1] # todo confusing code with the slice. Does the cache really need the distance?
        
        blacklist = user_data["match_blacklist"]
        while candidate_id in blacklist: # keep popping until a non blacklisted one is found
            candidate_id = self._data[user_id]["cached_candidates"].pop()[1] # todo again, need the slice to access the id itself rather than the list containing [distance, id]
        self._write_json()
        return candidate_id
        # We can pop the candidate, because that id is coming back either as a match or as a blacklist, assuming the tinder model.

    def add_to_pending_likes(self, user_id_1: int, user_id_2: int): # todo think about most intuitive and maintainable architecture for this
        """Add a second user that this user swiped "yes" on to this user's hash map of pending likes."""
        self._read_json()
        user_data = self._data[user_id_1]
        user_data["pending_likes"][user_id_2] = time.time()
        self._write_json()
    
    def delete_from_pending_likes(self, current_user_id: int, other_user_id: int):
        """Remove user2 from user1's pending likes."""
        pass

    def lookup_is_user_in_pending_likes(self, current_user_id: int, other_user_id:int) -> bool:
        """Return true if current user previously swiped "yes" on other user, else False."""
        self._read_json()
        return str(other_user_id) in self._data[current_user_id]["pending_likes"] # todo the keys in the pending likes dict are strings at this point in execution, very confusing

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

    def _serialize_user(self, user: user.User) -> dict: # todo: superfluous?
        """
        Create a dictionary representation of the user.
        """
        userDict = {
            "name": user.name,
            "current_location": user.current_location,
            "home_location": user.home_location,
            "likes": user.likes,
            "dislikes": user.dislikes,
            "match_blacklist": user.match_blacklist,
            "pending_likes": user.pending_likes,
            "matches": user.matches
        }
        return userDict


def main():
    pass


if __name__ == "__main__":
    main()