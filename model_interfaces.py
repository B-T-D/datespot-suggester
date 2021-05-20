"""Objects for interfacing between stored data and model-object instances."""
import abc, json, uuid, time

import models
#import models.user, models.datespot, models.match, models.review, models.message, models.chat
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
    
    def _validate_json_fields(self, json_dict: dict) -> None: # todo seems like too much code (needing to list the valid model fields for each child class). 
                                                                #   But under current architecture, can't just check against the keys from an arbitrary JSON object in the dict, 
                                                                #   because sometimes the DB is empty (esp in testing)
        """Raise ValueError if any key in json_dict isn't a valid field for this model.""" # todo do we need to check if data is none here, or would that be superfluous?
        for key in json_dict:
            if not key in self._valid_model_fields:
                raise ValueError(f"Invalid field in call to model interface create method: {key}")
    
    def _get_all_data(self) -> dict: # todo access this with the public attribute "self.data", not this method
        """Return the API instance's data as a native Python dictionary. I.e. all objects in a single dict, keys are the object ID strings."""
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
        self._valid_model_fields = {
            "id",
            "name",
            "current_location",
            "predominant_location",
            "tastes", 
            "travel_propensity", 
            "matches", 
            "pending_likes", 
            "match_blacklist",
            "force_key" # todo force_key isn't really a model field, conceptually
        }
        
    def create_user(self, json_data: str) -> int:
        """
        Takes json data in the app's internal format and returns the id key of the newly created user.
        Force key arg is for testing purposes to not always have huge unreadable uuids.
        """
        
        self._read_json()
        json_dict = json.loads(json_data)
        self._validate_json_fields(json_dict)
        if "force_key" in json_dict:
            force_key = json_dict["force_key"]
            if force_key in self._data: # Don't allow force-creating a key that's already taken
                raise ValueError(f"Can't force-create with key {force_key}, already in DB.")
            user_id = force_key
        else:
            user_id  = str(uuid.uuid1().int)
        new_user = models.User(
            user_id = user_id,
            name=json_dict["name"],
            current_location = tuple(json_dict["current_location"])
        )
        # todo adding tastes not supported here--does that make sense?
        #   Rationale is that any tastes data comes in later, not at the moment the user is created in the DB for the first time.

        self._data[user_id] = new_user.serialize()
        self._write_json()
        return user_id

    def lookup_json(self, user_id: int) -> str: # todo have a lookup JSON method in the ABC, then have individual MIs override if they need to. 
                                                #   For most models, simply reading the JSON and dumping back the data for object_id should suffice.
        """
        Return the JSON string for a user.
        """
        self._read_json() # todo User does it this way, Datespot does it by instantiating an object. If no reason for difference, determine which is better and standardize to that.
        return json.dumps(self._data[user_id]) # ...This way seems more intuitive. Part of the point of storing stuff is to look it up without repeating computations. 

    def lookup_obj(self, user_id: str) -> models.User:
        """
        Instantiates a User object to represent an existing user, based on data retrieved from the database. Returns the User object,
        or raises error if not found.
        """
        self._read_json()
        self._validate_object_id(user_id)
        user_data = self._data[user_id]
        user_obj = models.User(
            user_id = user_id,
            name=user_data["name"],
            current_location=user_data["current_location"],
            predominant_location = user_data["predominant_location"],
            tastes = user_data["tastes"],
            matches = user_data["matches"],
            pending_likes = user_data["pending_likes"],
            match_blacklist = user_data["match_blacklist"],
            travel_propensity = user_data["travel_propensity"]
        )

        return user_obj

    def update_user(self, user_id: int, new_json: str): # todo -- updating location might be single most important thing this does.
        # Todo support a "force datapoints count" option for updating tastes?
        """
        Takes JSON string, updates the native Python dict, and writes it to the stored master JSON.

        Specify the field to update as the key in the new_json string. E.g.  specifies to update location.

        Example calls:

            Update user's location:
                    {"location": [44.01, -72.12]}

                - Values should be a Python list / JS array. Currently, tuples encode to lists/arrays and decode as lists
                - Values should have two elements
                - value[0] is latitude float, value[1] is longitude float
            
            Update user's tastes:
                    {"tastes": 
                        {"taste_name": 0.17}
                    }
            
                - Tastes updates should be a dict/object, i.e. enclosed in braces
                - Keys within that dict/object should be strings
                - Value for each key should be a float between -1.0 and 1.0
                - Caller doesn't directly update the datapoints count
            
        """
        self._read_json()
        new_data = json.loads(new_json)
        user_data = self._data[user_id]
        self._validate_json_fields(new_data)
        for key in new_data: # todo best practice on type() vs isinstance?
            entry_type = type(user_data[key])
            entry = user_data[key]
            if key == "current_location": # todo location still parses as list, so make sure to overwrite, not append
                self._data[user_id]["current_location"] = new_data[key]
            elif key == "tastes":
                new_tastes_data = new_data[key]
                self._update_tastes(user_id, new_tastes_data)
            elif entry_type == list:
                self._data[user_id][key].extend(new_data[key])
            elif isinstance(entry, set):
                entry |= new_data[key] # todo this would require the new data to have been parsed to a set
            else:
                self._data[user_id][key] = new_data[key]
        self._write_json()
        return
    
    def _update_tastes(self, user_id: int, new_tastes_data:dict) -> None:
        """Helper method to handle calling the User model's tastes updater method."""
        # We assume the caller only ever sends one datapoint at a time--it doesn't need to access or modify the datapoints counter
        #   for the taste that it's updating.
        user_obj = self.lookup_obj(user_id)
        for taste_name, strength in new_tastes_data.items():
            user_obj.update_tastes(taste = taste_name, strength = strength)
        self._data[user_id]["tastes"] = user_obj.serialize()["tastes"] # Since we have an object literal in memory anyway, just have it give back the tastes dict.
        return # Caller is makes the _write_json call
    
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


class DatespotModelInterface(ModelInterfaceABC):

    def __init__(self, json_map_filename=None): # The abstract base class handles setting the filename to default if none provided
        self._model = "datespot"
        if json_map_filename: # Todo is there a one-liner for this? Ternary expression?
            super().__init__(json_map_filename)
        else:
            super().__init__()
        self._valid_model_fields = ["name", "location", "traits", "price_range", "hours", "yelp_rating", "yelp_review_count", "yelp_url"]

    def create_datespot(self, json_str: str) -> str:
        """
        Creates a new Datespot object, serializes it to the persistent JSON, and returns its id key.
        """
        self._read_json()
        datespot_obj = self._instantiate_datespot_from_json(json_str)

        new_object_id = datespot_obj.id

        # Save the object's data to the DB using that hash as the key
        self._data[new_object_id] = datespot_obj.serialize()
        self._write_json()
        return new_object_id
    
    def _validate_new_datespot(self):
    # todo query the db by name and location to avoid duplicates. I.e. does a restaurant with that name 
    #   already exist at approximately that location in the db?
        pass

    def lookup_json(self, id: int) -> str:
        """
        Return the JSON string for a Datespot in the DB.
        """
        datespot_obj = self.lookup_obj(id)
        return json.dumps(self._serialize_datespot(datespot_obj))

    def lookup_obj(self, id: int) -> models.Datespot:
        """Return the datespot object corresponding to key "id"."""
        self._read_json()
        self._validate_object_id(id)
        datespot_data = self._data[id]
        return models.Datespot(
            location = tuple(datespot_data["location"]),
            name = datespot_data["name"],
            traits = datespot_data["traits"],
            price_range = datespot_data["price_range"],
            hours = datespot_data["hours"],
            yelp_rating = datespot_data["yelp_rating"],
            yelp_review_count = datespot_data["yelp_review_count"],
            yelp_url = datespot_data["yelp_url"]
        )
    
    def is_in_db(self, json_str) -> bool:
        """
        Return True if the Datespot corresponding to this JSON info is already known to the database, else false.
        """
        # This relies on the hashing logic in Datespot--datespot with given name at given location should hash uniquely.
        # Instantiate a datespot object with this JSON, then see if its ID string is in the DB.
        self._read_json()
        datespot_obj = self._instantiate_datespot_from_json(json_str)
        return datespot_obj.id in self._data

    def _instantiate_datespot_from_json(self, json_str: str) -> models.Datespot: # Helper for DRY-ness
        """
        Instantiate a Datespot object corresponding to this JSON, and return it without interacting with the database.
        """
        json_dict = json.loads(json_str)
        self._validate_json_fields(json_dict)
        location_tuple = tuple(json_dict["location"])
                
        # Instantiate an object with the data
        datespot_obj = models.Datespot(
            location = location_tuple,
            name = json_dict["name"]
        )

        optional_fields =  {
            "traits": datespot_obj.traits,
            "price_range": datespot_obj.price_range,
            "hours": datespot_obj.hours,
            "yelp_rating": datespot_obj.yelp_rating,
            "yelp_review_count": datespot_obj.yelp_review_count,
            "yelp_url": datespot_obj.yelp_url
            }
        
        for optional_field in optional_fields:
            if optional_field in json_dict:
                exec(f"datespot_obj.{optional_field} = json_dict[optional_field]") # Todo what's a better way than exec()? Or is this an ok use case for exec()?
        
        return datespot_obj



    def update_datespot(self, id: str, update_json: str): # Stored JSON is the single source of truth. Want a bunch of little, fast read-writes. 
                                                    # This is where concurrency/sharding would become hypothetically relevant with lots of simultaneous users.
        self._read_json()
        datespot_data = self._data[id] # Todo: kwargs isn't the "standard" way the other MIs have been doing it. Take JSON.
        json_data = json.loads(update_json)
        self._validate_json_fields(json_data)

        for field in self._valid_model_fields: # Todo: SRP--make separate helper to do the hard-to-follow dict updates?
            if field in json_data: # i.e. the keys in the dict
                new_value = json_data[field]
                if field == "traits": # todo what if you want to clear the dict?
                    assert isinstance(new_value, dict)
                    for update_key in new_value: # the "value" is a nested dict
                        # if not already in the restaurants traits, initialize it with 1 datapoint:
                        score, data_info = update_key[0], update_key[1] # todo for now, just pretend they're sending in a datapoints count
                        discrete = update_key[1] == "discrete" # todo the discrete vs. continuous thing seems needlessly complex, surely a better way
                        if not update_key in datespot_data["traits"]:
                            datespot_data["traits"][update_key] = [update_key]
                            if discrete:
                                datespot_data["traits"][update_key].append("discrete")
                            else:
                                datespot_data["traits"][update_key].append(1) # this was the first datapoint
                        elif not discrete:
                            trait_data = datespot_data["traits"][update_key]
                            stored_score = trait_data[0]
                            stored_num_datapoints = trait_data[1]
                            stored_score = (stored_score * stored_num_datapoints + score) / stored_num_datapoints + 1
                            stored_num_datapoints += 1

                        # if discrete and already in data, do nothing. E.g. we already knew it's an Italian restaurant, nothing to update.


                        # todo the caller only sends the label and the intensity (if applicable), not a datapoints count

                else: # Any field other than the traits dict can just be overwritten entirely
                    datespot_data[field] = new_value

        self._write_json()

    def query_num_datespots(self): # Todo hasty, more code-elegant ways to do this
        """Return the number of datespots in this API instance's data."""
        self._read_json()
        return len(self._data)

    def query_datespot_ids_near(self, location, radius=2000): # Todo hasty implementation. This is the most important query logic so better to get something working sooner.
        """Return list of the datespots in the DB within radius meters of location, sorted from nearest to farthest.
        
        Returns:
            (list): List of two-element tuples such that query_results[i][0] is distance from query location to the datespot
                and query_results[i][1] is the datespot's ID string.
        
        """ 
        if (not location) or (not geo_utils.is_valid_lat_lon(location)): # todo best architectural place for validating this?
            raise ValueError(f"Bad lat lon location: {location}")
        self._read_json()
        query_results = [] # list of two element tuples of (distance_from_query_location, serialized_datespot_dict). I.e. list[tuple[int, dict]]
        for id_key in self._data:
            datespot_data = self._data[id_key]
            place_loc = datespot_data["location"]
            distance = geo_utils.haversine(location, place_loc)
            if distance < radius: # todo do we need the full object in the results dict, or would only the lookup key suffice?
                query_results.append((distance, id_key)) # append as tuple with distance as the tuple's first element
        query_results.sort() # Todo no reason to heap-sort yet, this method's caller won't necessarily want it as a heap. 
        return query_results

    def query_datespot_objs_near(self, location, radius=2000):
        """
        Return a list of distances and corresponding Datespot object literals within radius meters of location,
        sorted from nearest to farthest. Same as query_datespot_ids_near() except that it returns the Datespot
        objects instead of the IDs.

        """
        # Todo do we want a one-pass algorithm to return a list of Datespot objects? Rather than some other code
        #   needing to make a second pass to lookup each datespot id?

        # Todo: Do we care about keeping the distances in the list at this point? Isn't it enough to return a distance-sorted
        #   list? OTOH, if the caller is Match algorithms, may end up wanting to factor distance into suggestions (all else equal,
        #   choose the closer restaurant).

        # Todo for now, just wrap the one that returns ids, and then convert each ID to a datespot object
        datespot_ids = self.query_datespot_ids_near(location, radius)
        query_results = []
        for composite_element in datespot_ids:
            distance, id_string = composite_element[0], composite_element[1]
            datespot_obj = self.lookup_obj(id_string)
            query_results.append((distance,datespot_obj))
        return query_results

class MatchModelInterface(ModelInterfaceABC):

    def __init__(self, json_map_filename=None):
        self._model = "match"
        if json_map_filename:
            super().__init__(json_map_filename)
        else:
            super().__init__()
        self._valid_model_fields = [] # todo 

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
        match_obj = models.Match(user1_obj, user2_obj)
        new_object_id = match_obj.id
        self._data[new_object_id] = match_obj.serialize()
        self._write_json()
        return new_object_id
    
    def lookup_obj(self, match_id: int) -> models.Match:
        self._read_json()
        self._validate_object_id(match_id)
        match_data = self._data[match_id] # todo the three lines through the end of this one could easily go to a helper method in the ABC. E.g. _get_data_for_id
        user_id_1, user_id_2 = match_data["users"][0], match_data["users"][1]
        user1 = self.user_api_instance.lookup_obj(user_id_1)
        user2 = self.user_api_instance.lookup_obj(user_id_2)
        match_obj = models.Match(
            user1 = user1,
            user2 = user2,
            timestamp = match_data["timestamp"],
            suggestions_queue = match_data["suggestions_queue"])
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

        new_obj = models.Review( # Instantiate a model object
            datespot_id = json_dict["datespot_id"],
            text = json_dict["text"]
        )
        new_obj_id = new_obj.id # Get object's id hash string
        self._data[new_obj_id] = new_obj.serialize() # Save with that id as the key
        self._write_json()
        return new_obj_id

class MessageModelInterface(ModelInterfaceABC):

    # Todo: The message analysis might be better suited to its own special architecture. Message is uniquely 
    #   interwoven with User and Chat, so trying to do the MI on the same pattern as the more static models
    #   (Datespot, User) results in the MI needing to worry a lot about the objects' implementation details.

    def __init__(self, json_map_filename=None):
        self._model = "message"
        if json_map_filename:
            super().__init__(json_map_filename)
        else:
            super().__init__()
        self._valid_model_fields = ["time_sent", "sender_id", "chat_id", "text"]
    
    def create_message(self, json_data: str) -> str:
        """
        Returns the new object's id key string.

        JSON format:
            {
                "time_sent": <<UNIX timestamp>>,
                "sender_id": <<ID string of a stored User object>>,
                "chat_id": <<ID string of the stored Chat object in which this message was sent>>,
                "text": <<String text of the message>>
            }
        """
        # Todo SRP. This method is doing too much. 
        self._read_json()
        json_dict = json.loads(json_data)
        self._validate_json_fields(json_dict)
        
        
        time_sent = None
        if "time_sent" in json_dict: # If caller sent JSON containing a time stamp, use it...
            time_sent = json_dict["time_sent"]
        else:
            time_sent = time.time() # ...otherwise, create timestamp now.

        # Constructor needs a User object literal in order to update its tastes.
        user_db = UserModelInterface(self._master_datafile) # The MIs can't go out to the main database API because it causes circular imports
        sender_user_obj = user_db.lookup_obj(json_dict["sender_id"])
        prior_user_tastes = str(sender_user_obj.serialize()["tastes"]) # for comparison later, to see if any updates happened

        new_obj = models.Message(
            time_sent = time_sent,
            sender = sender_user_obj,
            chat_id = json_dict["chat_id"],
            text = json_dict["text"]
        )

        # Write any changes to the User object back to the user DB--if we discovered anything about the user's tastes,
        #   save that info to improve suggestions later:
        updated_user_tastes = sender_user_obj.serialize()["tastes"]
        if str(prior_user_tastes) != str(sender_user_obj.serialize()["tastes"]):  # Todo what's simplest, most performant here? Goal is to update only those tastes that
                                                    # changed, and do so via the User MI. User MI currently doesn't support wholesale overwrite of 
                                                    # the tastes, only incremental update. So to use that interface, would need to sort out here
                                                    # which ones changed. 
            user_data = user_db._get_all_data()[sender_user_obj.id] # Todo: Expedient for now. Use the private method to just overwrite the entire dict.
            user_data["tastes"] = updated_user_tastes
            user_db._write_json() # Todo: For now need to manually tell it to write since didn't use one of its public methods.

        # Todo would it make sense to have some kind of flag that indicates whether any tastes updates need to happen?
        #   So can skip that in the large majority of cases where the message won't match any tastes keywords?
        
        new_obj_id = new_obj.id

         # Add the message to its Chat's data:
        fobj = open(self._master_datafile, "r")
        chat_db = ChatModelInterface(json_map_filename=self._master_datafile) # Same JSON map as this instance is working from
        chat_json = json.dumps({"messages": [new_obj_id]})
        chat_id = new_obj.chat_id
        chat_db.update_chat(new_obj.chat_id, chat_json)

        self._data[new_obj_id] = new_obj.serialize()
        self._write_json()
        return new_obj_id
    
    def lookup_obj(self, object_id: int) -> models.Message:
        """Return the Message object corresponding to id."""
        self._read_json()
        self._validate_object_id(object_id)
        message_data = self._data[object_id]
        user_db = UserModelInterface(self._master_datafile) # need a User MI to get a User obj to call the Message constructor with
        return models.Message(
            time_sent = message_data["time_sent"],
            sender = user_db.lookup_obj(message_data["sender_id"]),
            chat_id = message_data["chat_id"],
            text = message_data["text"]
        ) # Todo: Not copying the sentiment because that can be recomputed on the object. Is that the right approach?
        #       Or maybe better to pull the cached sentiment? It'd still update as soon as anything called the Message's SA method.
    
    def lookup_json(self, object_id: str) -> str:
        """Return the stored JSON string for the Message matching this id."""
        self._read_json()
        self._validate_object_id(object_id)
        return json.dumps(self._data[object_id])

class ChatModelInterface(ModelInterfaceABC):

    def __init__(self, json_map_filename=None):
        self._model = "chat"
        if json_map_filename:
            super().__init__(json_map_filename)
        else:
            super().__init__()
        self._valid_model_fields = ["start_time", "participant_ids", "messages"]
    
    def create_chat(self, new_obj_json: str):
        self._read_json()
        json_dict = json.loads(new_obj_json)
        self._validate_json_fields(json_dict)

        start_time = None # Same as Message. If it didn't come in with a timestamp, use the current time
        if "start_time" in json_dict:
            start_time = json_dict["start_time"]
        else:
            start_time = time.time()

        new_obj = models.Chat(
            start_time = start_time,
            participant_ids = json_dict["participant_ids"]
        ) # no messages yet

        new_obj_id = new_obj.id

        self._data[new_obj_id] = new_obj.serialize()
        self._write_json()
        return new_obj_id

    def update_chat(self, object_id: str, update_json: str): # Todo will need more sophisticated interface for adding/removing from lists. Same in other models that have running-list data.
        self._read_json()
        self._validate_object_id
        
        update_json_dict = json.loads(update_json)
        self._validate_json_fields(update_json_dict)
        chat_data = self._data[object_id] # load the old data
        if "start_time" in update_json_dict:
            del update_json_dict["start_time"] # Start time treated as immutable
        for key in update_json_dict:
            if type(chat_data[key]) == list:
                chat_data[key].extend(update_json_dict[key])
        self._write_json()
    
    def lookup_obj(self, object_id: str):
        self._read_json()
        self._validate_object_id(object_id)
        chat_data = self._data[object_id]

        # Instantiate a Message object literal from each stored Message ID
            # Todo how could this possibly perform well IRL? Chats would run to hundreds of messages...
            #   ...Think about when a Chat object actually gets instantiated. If it happens very often, 
            #           should probably do this some other way.
        
        message_objects = []
        message_db = MessageModelInterface(json_map_filename=self._master_datafile)
        for message_id in chat_data["messages"]:
            message_objects.append(message_db.lookup_obj(message_id))

        return models.Chat(
            start_time = chat_data["start_time"],
            participant_ids = chat_data["participant_ids"],
            messages = message_objects
        ) 