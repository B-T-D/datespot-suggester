"""Objects for interfacing between stored data and model-object instances."""

import abc
import json
import uuid
import time

import user, datespot, match, review, message # todo ...chat
import geo_utils

JSON_DB_NAME = "jsonMap.json"

class ModelInterfaceABC: # Abstract base class
    __metaclasss__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, json_map_filename=JSON_DB_NAME):
        self._master_datafile = json_map_filename
        self._datafile = None
        self._data = {}
        self.data = self._data #  todo what about assigning this to return of _read_json, and having that method return self._data?

    def _set_datafile(self): # todo this is broken, it's not actually creating the file when the file doesn't exist.
        """Retrieve and set filename of this model's stored JSON."""
        with open(self._master_datafile, 'r') as fobj:
            json_map = json.load(fobj)
            fobj.seek(0)
        self._datafile = json_map[f"{self._model}_data"]
    
    def _read_json(self): #  todo this gets messy when something is a set that needs to be manually converted back to a native python set
        """Read stored JSON models into the API instance's native Python dictionary."""
        if not self._datafile:
            self._set_datafile()
        json_data = {}
        with open(self._datafile, 'r') as fobj: # todo there's a way to get the keys to parse to native ints in one pass--consult docs.
            json_data = json.load(fobj)
            fobj.seek(0)
        for key in json_data:
            self._data[key] = json_data[key]

    def _write_json(self):
        """Overwrite stored JSON for this model to exactly match current state of the API instance's native Python dictionary."""
        # Todo: Any safeguards that make sense to reduce risk of accidentally overwriting good data?
        if not self._datafile:
            self._set_datafile()
        with open(self._datafile, 'w') as fobj:
            json.dump(self._data, fobj)
            fobj.seek(0)
    
    def _validate_object_id(self, object_id: str) -> None:
        """
        Raise KeyError if object_id not in database.
        """
        if not isinstance(object_id, str):
            raise TypeError(f"Id key type should be string. Type was {type(object_id)}")
        self._read_json() 
        if not object_id in self._data:
            raise KeyError(f"{self._model} with id (key) {object_id} not found.")
    
    # todo convert all logic that uses the key-error-raiser one to use the boolean returning one?

    def _is_valid_object_id(self, object_id: int) -> bool:
        return object_id in self._data
    
    def _validate_json_fields(self, json_dict: dict) -> None:
        """Raise ValueError if any key in json_dict isn't a valid field for this model."""
        for key in json_dict:
            if not key in self._valid_model_fields:
                raise ValueError(f"Invalid field in call to model interface create method: {key}")
    
    def _get_all_data(self) -> dict: # todo access this with the public attribute "self.data", not this method
        """Return the API instance's data as a native Python dictionary."""
        self._read_json()
        return self._data
    
    def delete(self, object_id: int) -> None:
        """Delete the data for key object_id."""
        self._read_json()
        self._validate_object_id(object_id)
        del self._data[object_id]
        self._write_json()

class UserModelInterface(ModelInterfaceABC):

    def __init__(self, json_map_filename=None):
        self._model = "user" # Initialization order matters e.g. if defining self.data to init to the read-in json.
        if json_map_filename: # Todo is there a one-liner for this? Ternary expression?
            super().__init__(json_map_filename)
        else:
            super().__init__()

        self._valid_model_fields = ["name", "current_location", "home_location", "likes", "dislikes", "match_blacklist", "force_key"] # todo is this necessary, or could you just check the keys?
        
    def create_user(self, json_data: str, force_key: int=None) -> int:
        """
        Takes json data in the app's internal format and returns the id key of the newly created user.
        Force key arg is for testing purposes to not always have huge unreadable uuids.
        """
        self._read_json()
        json_dict = json.loads(json_data)
        self._validate_json_fields(json_dict)
        if force_key: # Don't allow force-creating a key that's already taken
            if force_key in self._data:
                raise ValueError(f"Can't force-create with key {force_key}, already in DB.")
            user_id = force_key
        else:
            user_id  = str(uuid.uuid1().int)
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

    def lookup_obj(self, user_id: str) -> user.User:
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
        query_results.reverse() # Put nearest candidate at end, for performant pop() calls. 
        return query_results
           
    def query_users_near_user(self, user_id: int) -> list:
        """Return the list of users near this user and cache that list of candidates in this user's data."""
        self._read_json()
        query_location = self._data[user_id]["current_location"]
        query_results = self.query_users_currently_near_location(tuple(query_location))
        if query_results[-1] == user_id: # Don't include the user in that user's results
            query_results.pop()
        
        self._data[user_id]["cached_candidates"] = query_results # Fully overwrite to latest and greatest, even the cache already existed:
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
        if self._refresh_candidates(user_id): # todo check if user's location changed by enough to warrant new query rather than pulling from cache
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

    def _serialize_user(self, user: user.User) -> dict: # todo: serializer methods go in the model classes
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

class DatespotModelInterface(ModelInterfaceABC):

    def __init__(self, json_map_filename=None): # The abstract base class handles setting the filename to default if none provided
        self._model = "datespot"
        if json_map_filename: # Todo is there a one-liner for this? Ternary expression?
            super().__init__(json_map_filename)
        else:
            super().__init__()
        self._valid_model_fields = ["name", "location", "traits", "price_range", "hours"]
    
    def create_datespot(self, json_data: str) -> str:
        """
        Creates a new Datespot object, serializes it to the persistent JSON, and returns its id key.
        """
        self._read_json()
        json_dict = json.loads(json_data)
        # Validate fields
        for key in json_dict: # todo refactor to use the inherited _validate_fields method
            if not key in self._valid_model_fields: # todo validate the values
                raise ValueError(f"Bad JSON in call to create_datespot(): {key}")
        location_tuple = tuple(json_dict["location"])
        # Instantiate an object with the data
        datespot_obj = datespot.Datespot(
            location = location_tuple,
            name = json_dict["name"]
        )
        if "traits" in json_dict:
            datespot_obj.traits = json_dict["traits"]
        if "price_range" in json_dict and json_dict["price_range"] is not None:
            datespot_obj.price_range = int(json_dict["price_range"])
        if "hours" in json_dict: # todo better handling when hours format is made realistic
            datespot_obj.hours = json_dict["hours"]

        # Hash that object
        new_object_id = datespot_obj.id # todo refactor to the uniform approach: create the object, then call its id method.

        # Save the object's data to the DB using that hash as the key
        self._data[new_object_id] = self._serialize_datespot(datespot_obj)
        self._write_json()
        return new_object_id

    def _serialize_datespot(self, datespot) -> dict: # Todo don't need the id here, right? Or is that unneccessarily confusing and should just slap the id everywhere?
        datespotDict = {
            "id": datespot.id,
            "location": datespot.location,
            "name": datespot.name,
            "traits": list(datespot.traits),
            "price_range": datespot.price_range,
            "hours": datespot.hours,
            "baseline_dateworthiness": datespot.baseline_dateworthiness
        }
        return datespotDict
    
    def _validate_new_datespot(self):
    # todo query the db by name and location to avoid duplicates. I.e. does a restaurant with that name 
    #   already exist at approximately that location in the db?
        pass

    # todo try using the object_hook arg to json.load to handle the tuple vs string 
    #   thing in a more code-concise way. 
    def _tuple_loc_key_to_string(self, location_key: tuple) -> str:
        """
        Convert a tuple literal to a string representation that Python json library
        defaults accept as a key.
        """
        return str(location_key)
    
    def _string_loc_key_to_tuple(self, location_key_string: str) -> tuple:
        """
        Convert a string representation of the three-element tuple to a literal
        three-element tuple object.
        """
        stripped = location_key_string.strip('()') # todo one-liner means fewer copies right?
        values = [float(substring) for substring in stripped.split(sep=',')]
        return tuple(values)

    def lookup_json(self, id: int) -> str:
        """
        Return the JSON string for a Datespot in the DB.
        """
        datespot_obj = self.lookup_obj(id)
        return json.dumps(self._serialize_datespot(datespot_obj))

    def lookup_obj(self, id: int) -> datespot.Datespot:
        """Return the datespot object corresponding to key "id"."""
        self._read_json()
        self._validate_object_id(id)
        datespot_data = self._data[id]
        return datespot.Datespot(
            location = tuple(datespot_data["location"]),
            name = datespot_data["name"],
            traits = datespot_data["traits"],
            price_range = datespot_data["price_range"],
            hours = datespot_data["hours"]
        )

    def update_datespot(self, id: int, **kwargs): # Stored JSON is the single source of truth. Want a bunch of little, fast read-writes. 
                                                    # This is where concurrency/sharding would become hypothetically relevant with lots of simultaneous users.
        self._read_json()
        datespot_data = self._data[id]

        for field in self._valid_model_fields:
            if field in kwargs:
                new_value = kwargs[field]
                if field == "traits": # todo what if you want to clear the list? YAGNI for now
                    if isinstance(new_value, list):
                        datespot_data[field].extend(new_value)
                    else:
                        datespot_data[field].append(new_value)
                else: # Any field other than the traits list can just be overwritten entirely
                    datespot_data[field] = new_value

        self._write_json()

    def query_num_datespots(self): # Todo hasty, more code-elegant ways to do this
        """Return the number of datespots in this API instance's data."""
        self._read_json()
        return len(self._data)

    def query_datespots_near(self, location, radius=2000): # Todo hasty implementation. This is the most important query logic so better to get something working sooner.
        """Return list of the datespots in the DB within radius meters of location, sorted from nearest to farthest.""" 
        if (not location) or (not geo_utils.is_valid_lat_lon(location)): # todo best architectural place for validating this?
            raise ValueError(f"Bad lat lon location: {location}")
        self._read_json()
        query_results = [] # list of two element tuples of (distance_from_query_location, serialized_datespot_dict). I.e. list[tuple[int, dict]]
        for id_key in self._data:
            place = self._data[id_key]
            place_loc = place["location"]
            distance = geo_utils.haversine(location, place_loc)
            if distance < radius: # todo do we need the full object in the results dict, or would only the lookup key suffice?
                query_results.append((distance, place)) # append as tuple with distance as the tuple's first element
        query_results.sort() # Todo no reason to heap-sort yet, this method's caller won't necessarily want it as a heap. 
        return query_results

class MatchModelInterface(ModelInterfaceABC):

    def __init__(self, json_map_filename=None):
        self._model = "match"
        if json_map_filename:
            super().__init__(json_map_filename)
        else:
            super().__init__()

        self.user_api_instance = UserModelInterface(json_map_filename=self._master_datafile)
    
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

class ReviewModelInterface(ModelInterfaceABC):

    def __init__(self, json_map_filename=None):
        self._model = "review"
        if json_map_filename:
            super().__init__(json_map_filename)
        else:
            super().__init__()
        self._valid_model_fields = ["datespot_id", "text"]
    
    def create_review(self, json_str: str) -> str:
        self._read_json()
        json_dict = json.loads(json_str)

        self._validate_json_fields(json_dict) # Validate fields

        new_obj = review.Review( # Instantiate a model object
            datespot_id = json_dict["datespot_id"],
            text = json_dict["text"]
        )
        new_obj_id = new_obj.id # Get object's id hash string
        self._data[new_obj_id] = new_obj.serialize() # Save with that id as the key
        self._write_json()
        return new_obj_id

class MessageModelInterface(ModelInterfaceABC):

    def __init__(self, json_map_filename=None):
        self._model = "message"
        if json_map_filename:
            super().__init__(json_map_filename)
        else:
            super().__init__()
        self._valid_model_fields = ["time_sent", "sender_id", "recipient_ids", "text"]
    
    def create_message(self, json_data: str) -> str:
        """
        Returns the new object's id key string.
        """

        self._read_json()
        json_dict = json.loads(json_data)
        self._validate_json_fields(json_dict)
        
        
        time_sent = None
        if "time_sent" in json_dict: # If caller sent JSON containing a time stamp, use it...
            time_sent = json_dict["time_sent"]
        else:
            time_sent = time.time() # ...otherwise, create timestamp now.

        new_obj = message.Message(
            time_sent = time_sent,
            sender_id = json_dict["sender_id"],
            recipient_ids = json_dict["recipient_ids"],
            text = json_dict["text"]
        )
        # Todo update the messages array in the sender User object's attributes?
            # That's not the full conversation though anyway. 
        new_obj_id = new_obj.id
        self._data[new_obj_id] = new_obj.serialize()
        self._write_json()
        return new_obj_id
    
