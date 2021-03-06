"""Objects for interfacing between stored data and model-object instances."""
import abc, json, uuid, time, math
  # TODO Can't assume this will run on a system with sub-second timestamp precision. time.time() only guarantees non-decreasing values; it can't
                                #   return more precise timestamps than the underlying system clock supports. https://docs.python.org/3/library/time.html#time.time
from typing import List, Tuple

import models
import geo_utils

from project_constants import *

class ModelInterfaceABC: # Abstract base class
    __metaclasss__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, json_map_filename=MOCK_JSON_DB_MAP):
        self._master_datafile = json_map_filename
        self._datafile = None
        self._data = {}
        self.data = self._data #  todo what about assigning this to return of _read_json, and having that method return self._data?

    ### Public methods ###
    
    def is_valid_object_id(self, object_id: str) -> bool:
        """Returns True if the object_id corresponds to one in the database, else False."""
        self._read_json()
        return self._is_valid_object_id(object_id)

    ### Private methods ###
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
    
    # TODO convert all logic that uses the key-error-raiser one to use the boolean returning one?
    #   https://softwareengineering.stackexchange.com/questions/330824/function-returning-true-false-vs-void-when-succeeding-and-throwing-an-exception

    def _is_valid_object_id(self, object_id: int) -> bool:
        return object_id in self._data
    
    def _validate_json_fields(self, json_dict: dict) -> None:
        """Raise ValueError if any key in json_dict isn't a valid field for this model."""
        for key in json_dict:
            if not key in self._valid_model_fields:
                raise ValueError(f"Invalid field in call to model interface create method: {key}")
    
    def _validate_model_fields(self, data: dict) -> None: # TODO get rid of the "json_fields" one once nobody needs that name
        return self._validate_json_fields(data)
    
    def _get_all_data(self) -> dict: # TODO access this with the public attribute "self.data", not this method
        """Return the API instance's data as a native Python dictionary. I.e. all objects in a single dict, keys are the object ID strings."""
        self._read_json()
        return self._data
    
    def sync(self, object) -> None:
        """
        Overwrites database entry for the passed object with that object's current serialized data. Meant to be called
        by one model interface when it updates some other model, e.g. when the MatchMI creates a Match and needs to update each of 
        the two Users.
        
        Args:
            object: User, Datespot, Match, etc. instance.
        
        """
        self._read_json()
        self._data[object.id] = object.serialize()
        self._write_json()
    
    def delete(self, object_id: int) -> None:
        """Delete the data for key object_id."""
        self._read_json()
        self._validate_object_id(object_id)
        del self._data[object_id]
        self._write_json()

class UserModelInterface(ModelInterfaceABC):

    def __init__(self, json_map_filename=None):
        self._model = "user"  # Initialization order matters e.g. if defining self.data to init to the read-in json.
        if json_map_filename:
            super().__init__(json_map_filename)
        else:
            super().__init__()
        self._valid_model_fields = {
            "user_id",
            "name",
            "current_location",
            "predominant_location",
            "tastes", 
            "travel_propensity",
            "candidates",
            "matches", 
            "pending_likes", 
            "match_blacklist",
            "force_key"
        }

        self._required_instantiation_fields = {
            "user_id",
            "name",
            "current_location",
        }
        self._optional_instantiation_fields = {field for field in self._valid_model_fields if not field in self._required_instantiation_fields}


        self.user_safe_model_fields = {  # model fields appropriate for viewing by the user whose data it is
            "user_id",
            "name",
            "predominant_location",
            "matches",
            "pending_likes"
        }

        self.candidate_safe_model_fields = {  # model fields appropriate for sharing with other users
            "user_id",
            "name"
        }
    
    ### Public methods ###

    def create(self, new_data: dict) -> str:
        """
        Takes json data in the app's internal format and returns the id key of the newly created user.
        Force key arg is for testing purposes to not always have huge unreadable uuids.

        new_data examples:

            {
                "name": "foo",
                "current_location": [40.00, -71.00]
            }
        
            - Name and location are required

        """
        
        self._read_json()
        self._validate_model_fields(new_data)
        if "force_key" in new_data:
            if new_data["force_key"] in self._data: # Don't allow force-creating a key that's already taken
                raise ValueError(f"Can't force-create with key {new_data['force_key']}, already in DB.")
            new_data["user_id"] = new_data["force_key"]
            del new_data["force_key"]
        else:
            new_data["user_id"]  = uuid.uuid1().hex  
        new_user = self._instantiate_obj_from_dict(new_data)
        # todo adding tastes not supported here--does that make sense?
        #   Rationale is that any tastes data comes in later, not at the moment the user is created in the DB for the first time.

        self._data[new_user.id] = new_user.serialize()
        self._write_json()
        return new_user.id

    def _instantiate_obj_from_dict(self, obj_data: dict) -> models.User:
        """
        Returns a User model object corresponding to the data in object_data.
        """
        self._validate_model_fields(obj_data)
        if isinstance(obj_data["current_location"], list):
            obj_data["current_location"] = tuple(obj_data["current_location"])
        
        model_obj = models.User(
            user_id = obj_data["user_id"],
            name = obj_data["name"],
            current_location = obj_data["current_location"]
        )

        for optional_field in self._optional_instantiation_fields:
            if optional_field in obj_data:
                exec(f"model_obj.{optional_field} = obj_data[optional_field")
        
        return model_obj
        

    def lookup_obj(self, user_id: str) -> models.User:
        """
        Instantiates a User object to represent an existing user, based on data retrieved from the database. Returns the User object,
        or raises error if not found.
        """
        # TODO refactor to use _instantiate_obj_from_dict
        self._read_json()
        self._validate_object_id(user_id)
        user_data = self._data[user_id]
        #  Use Candidate objects to avoid recursively initializing User objects for candidates of candidates
        candidates = []
        if "candidates" in user_data and len(user_data["candidates"]) > 0:
            for candidate_id in user_data["candidates"]:
                candidates.append(self._lookup_candidate_obj(candidate_id))

        user_obj = models.User(
            user_id = user_id,
            name=user_data["name"],
            current_location=user_data["current_location"],
            predominant_location = user_data["predominant_location"],
            tastes = user_data["tastes"],
            travel_propensity = user_data["travel_propensity"],
            candidates = candidates,
            matches = user_data["matches"],
            pending_likes = user_data["pending_likes"],
            match_blacklist = user_data["match_blacklist"],
        )
        if not len(user_obj.candidates) > 0: # TODO SRP. This shouldn't be responsible for refreshing candidates, its only job should be converting the stored data into an object instance
            nearby_candidate_query_results = self.query_users_currently_near_location(user_obj.predominant_location)
            for result in nearby_candidate_query_results[::-1]:  # Iterate backward, because query results are sorted by descending distance from user
                assert isinstance(result[1], models.Candidate)
                user_obj.candidates.append(result[1])  # Second element of the result tuple is the user id

        return user_obj
    
    def _lookup_candidate_obj(self, candidate_id: str) -> models.Candidate:
        """
        Instantiates a Candidate helper-object and returns it.
        """
        self._read_json() #  The relevant data is the wider User data
        self._validate_object_id(candidate_id)
        candidate_data = self._data[candidate_id]
        return models.Candidate(
            user_id=candidate_id,
            name=candidate_data["name"],
            current_location=candidate_data["current_location"],
            predominant_location=candidate_data["predominant_location"],
            tastes = candidate_data["tastes"],
            travel_propensity = candidate_data["travel_propensity"]
        )

    def update(self, user_id: int, new_data: dict): # todo -- updating location might be single most important thing this does.
        # Todo support a "force datapoints count" option for updating tastes?
        """
        Takes Python dict, updates the native Python dict, and writes it to the stored master JSON.

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
            else:
                self._data[user_id][key] = new_data[key]
        self._write_json()
        return

    
    # todo all the "query objects near" methods could probably be abstracted to the ABC.
    def query_users_currently_near_location(self, location: tuple, radius=50000) -> List[models.Candidate]: # todo is the radius parameter totally unnecessary? 
        """
        Return list of Candidate objects whose current location is within radius meters of location.
        """
        # Defaults to a very high radius, expectation is that radius won't be specified in most queries.

        if (not location) or (not geo_utils.is_valid_lat_lon(location)): # todo best architectural place for validating this?
            raise ValueError(f"Bad lat lon location: {location}\n\ttype = {type(location)}")
        self._read_json()
        query_results = []
        for user_id in self._data:
            candidate = self._lookup_candidate_obj(user_id)
            user_location = candidate.predominant_location
            assert isinstance(user_location[0], float), f"user_location = {user_location}"
            distance = geo_utils.haversine(location, user_location)
            if distance < radius:
                query_results.append((distance, candidate)) # todo no need to put the whole dict into the results, right?
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
    
    def query_next_candidate(self, user_id: str) -> str:
        """
        Returns the user id of the next candidate for this user to decide on.

        Args:
            user_id (str): User ID string
        
        Returns:
            (str): User ID string of the next candidate
        """
        self._read_json()
        user_obj = self.lookup_obj(user_id)
        self._data[user_id] = user_obj.serialize()
        self._write_json()
        return user_obj.next_candidate().id  # Model layer handles the queue, blacklisting, etc.
    
    def render_user(self, user_id: str) -> dict:
        """
        Returns data about a user relevant for display to that user.

        Returns:
            (dict): Dictionary of User object fields pruned to those relevant for display.
        """
        self._read_json()
        user_data = self._data[user_id]
        renderable_data = {}
        for key in self.user_safe_model_fields:
            renderable_data[key] = user_data[key]
        return renderable_data
    
    def render_candidate(self, candidate_id: str) -> dict:
        """
        Returns data about a candidate-user for appropriate for display to an unknown other user (i.e., User A deciding whether they want to match with User B
        shouldn't see all data about User B, only some subset relevant to User A's decisionmaking process).

        Returns:
            (dict): Dictionary of User object fields pruned to those appropriate and relevant for display.
        """
        self._read_json()
        candidate_data = self._data[candidate_id]
        renderable_data = {}
        for key in self.candidate_safe_model_fields:
            renderable_data[key] = candidate_data[key]
        return renderable_data

    def render_matches_list(self, user_id: str) -> List[dict]:
        """
        Returns a list of relevant information about this User's matches relevant and appropriate for display to that user.

        Args:
            user_id (str): User ID string
        
        Returns:
            (list[dict]): List of dictionaries, each of which contains the rendering-relevant info for one match.
        """
        self._read_json()
        renderable_data = []
        user_obj = self.lookup_obj(user_id)
        for match_data in user_obj.match_data:  # Need to convert each user id to a name
            renderable_match_data = {
                "match_id": match_data["match_id"],
                "match_timestamp": match_data["match_timestamp"],
                "match_partner_info": self.render_candidate(match_data["match_partner_id"])
            }
            renderable_data.append(renderable_match_data)

        return renderable_data

    def add_to_pending_likes(self, user_id_1: int, user_id_2: int):
        """Add a second user that this user swiped "yes" on to this user's hash map of pending likes."""
        self._read_json()
        user_data = self._data[user_id_1]
        user_data["pending_likes"][user_id_2] = time.time()
        self._write_json()
    
    def delete_from_pending_likes(self, current_user_id: int, other_user_id: int):
        """Remove user2 from user1's pending likes."""
        pass

    def lookup_is_user_in_pending_likes(self, current_user_id: int, other_user_id:int) -> bool: # TODO re-implement in the object-composition based way. Use a User objects, call their method(s), then write each back to the DB
        """Return true if current user previously swiped "yes" on other user, else False."""
        self._read_json()
        return str(other_user_id) in self._data[current_user_id]["pending_likes"] # todo the keys in the pending likes dict are strings at this point in execution, very confusing

    def blacklist(self, current_user_id: int, other_user_id: int):  # TODO can prob create a custom decorator that says "whenever this method is called, call read json right before and update json right after"
        """
        Add other_user_id to current_user_id user's no-match blacklist.
        """
        self._read_json()
        user_data = self._data[current_user_id]
        if not "match_blacklist" in user_data:  # TODO legacy, should be able to just initialize them with a blank dict
            user_data["match_blacklist"] = {other_user_id: time.time()}
        else:
            user_data["match_blacklist"][other_user_id] = time.time()
        self._write_json()

    ### Private methods ###
    
    def _update_tastes(self, user_id: int, new_tastes_data:dict) -> None:
        """Helper method to handle calling the User model's tastes updater method."""
        # We assume the caller only ever sends one datapoint at a time--it doesn't need to access or modify the datapoints counter
        #   for the taste that it's updating.
        user_obj = self.lookup_obj(user_id)
        for taste_name, strength in new_tastes_data.items():
            user_obj.update_tastes(taste = taste_name, strength = strength)
        self._data[user_id]["tastes"] = user_obj.serialize()["tastes"] # Since we have an object literal in memory anyway, just have it give back the tastes dict.
        return # Caller is makes the _write_json call
    
    def _refresh_candidates(self, user_id) -> bool:
        """Return True if this user's candidates cache is null, empty, or otherwise should be updated."""
        user_data = self._data[user_id]
        if not "cached_candidates" in user_data or len(user_data["cached_candidates"]) < 1:
            return True
        return False

class DatespotModelInterface(ModelInterfaceABC):

    def __init__(self, json_map_filename=None): # The abstract base class handles setting the filename to default if none provided
        self._model = "datespot"
        if json_map_filename:
            super().__init__(json_map_filename)
        else:
            super().__init__()
        self._valid_model_fields = ["datespot_id", "name", "location", "traits", "price_range", "hours", "yelp_rating", "yelp_review_count", "yelp_url", "yelp_id", "google_id"]
        self._renderable_fields = {"name", "location", "yelp_url"}

    ### Public methods ###

    def create(self, new_data: dict) -> str:
        """
        Creates a new Datespot object, serializes it to the persistent JSON, and returns its id key.
        """
        self._read_json()

        if not "datespot_id" in new_data or new_data["datepot_id"] in self._data:  # If no test-mode forced-key provided, or if provided force key already in use
            new_data["datespot_id"] = uuid.uuid1().hex

        datespot_obj = self._instantiate_obj_from_dict(new_data)

        new_object_id = datespot_obj.id

        # Save the object's data to the DB using that hash as the key
        self._data[new_object_id] = datespot_obj.serialize()
        self._write_json()
        return new_object_id

    def lookup_obj(self, id: int) -> models.Datespot:
        """Return the datespot object corresponding to key "id"."""
        self._read_json()
        self._validate_object_id(id)
        datespot_data = self._data[id]
        return self._instantiate_obj_from_dict(datespot_data)
    
    def render_obj(self, object_id: str) -> dict:
        """
        Return a dictionary of info about the specified Datespot appropriate and relevant for display
        to users in a suggestion.
        """
        self._read_json()
        renderable_data = {}
        object_data = self._data[object_id]
        for key in object_data:
            if key in self._renderable_fields:
                renderable_data[key] = object_data[key]
        return renderable_data

    def update(self, id: str, update_data: dict):
        self._read_json()
        datespot_data = self._data[id] # Todo: kwargs isn't the "standard" way the other MIs have been doing it. Take JSON.
        self._validate_json_fields(update_data)

        for field in self._valid_model_fields: # Todo: SRP--make separate helper to do the hard-to-follow dict updates?
            if field in update_data: # i.e. the keys in the dict
                new_value = update_data[field]
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


                        # TODO The caller only sends the label and the intensity (if applicable), not a datapoints count

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

    def is_known_name_location(self, datespot_name: str, datespot_location: tuple) -> bool:
        """
        Return True if a Datespot with this name at this location is already known to the database, else False.
        """
        datespot_name = datespot_name.lower()
        datespot_location = (round(datespot_location[0], LAT_LON_DECIMAL_PLACES), round(datespot_location[1], LAT_LON_DECIMAL_PLACES))
        self._read_json()
        for datespot_id in self._data:  
            datespot_data = self._data[datespot_id]
            if datespot_data["name"].lower() == datespot_name:  # TODO make this a geo_util?
                if geo_utils.haversine(datespot_location, datespot_data["location"]) < 50:  # If less than 50m apart and have same name, should be safe to assume it's same establishment
                    return True
        return False

    def is_in_db(self, datespot_data) -> bool:  # TODO obviated?
        # TODO this may be needed uniquely for Datespot model, because there's unique risk of entering the same venue's data twice.
        """
        Return True if the Datespot corresponding to this JSON info is already known to the database, else false.
        """
        # This relies on the hashing logic in Datespot--datespot with given name at given location should hash uniquely.
        # Instantiate a datespot object with this JSON, then see if its ID string is in the DB.
        self._read_json()
        if not "datespot_id" in datespot_data:
            model_obj = self._instantiate_obj_from_dict(datespot_data)
        if "yelp_id" in datespot_data and datespot_data["yelp_id"] == model_obj.yelp_id:  # TODO unittests that can be run ad hoc on live APIs
            return True
        if "google_id" in datespot_data and datespot_data["google_id"] == model_obj.google_id:
            return True
        return False
    
    ### Private methods ###

    def _validate_new_datespot(self):
    # todo query the db by name and location to avoid duplicates. I.e. does a restaurant with that name 
    #   already exist at approximately that location in the db?
        pass

    def _instantiate_obj_from_dict(self, obj_data: dict) -> models.Datespot: # Helper for DRY-ness
        """
        Instantiate a Datespot object corresponding to this JSON, and return it without interacting with the database.
        """

        # TODO this can be implemented in the base class. Every MI subclass can have self.required_fields and self.optional_fields
        #   attributes. 

        self._validate_json_fields(obj_data)
        location_tuple = tuple(obj_data["location"])  # TODO customize JSON encode/decode


        

                
        # Instantiate an object with the data
        model_obj = models.Datespot(
            datespot_id = obj_data["datespot_id"],
            location = location_tuple,
            name = obj_data["name"]
        )

        optional_fields =  {
            "traits": model_obj.traits,
            "price_range": model_obj.price_range,
            "hours": model_obj.hours,
            "yelp_rating": model_obj.yelp_rating,
            "yelp_review_count": model_obj.yelp_review_count,
            "yelp_url": model_obj.yelp_url,
            "yelp_id": model_obj.yelp_id,
            "google_id": model_obj.google_id
            }
        
        for optional_field in optional_fields:
            if optional_field in obj_data:
                exec(f"model_obj.{optional_field} = obj_data[optional_field]") # Todo what's a better way than exec()? Or is this an ok use case for exec()?
        
        return model_obj

class MatchModelInterface(ModelInterfaceABC):

    def __init__(self, json_map_filename=None):
        self._model = "match"
        if json_map_filename:
            super().__init__(json_map_filename)
        else:
            super().__init__()
        self._valid_model_fields = [] # todo 

        self.user_api_instance = UserModelInterface(json_map_filename=self._master_datafile)
    
    ### Public methods ###

    def create(self, new_data: dict) -> str:
        """
        Creates a Match object from the two users and return its id key.  Handles adding the Match reference to stored data
        for each constituent User.

        json example:
            {
                "user1_id": "abc123",
                "user2_id": "zyx987"
            }

        """
        self._read_json()
        user1_id, user2_id = new_data["user1_id"], new_data["user2_id"]
        user1_obj, user2_obj = self.user_api_instance.lookup_obj(user1_id), self.user_api_instance.lookup_obj(user2_id)
        match_obj = models.Match(user1_obj, user2_obj)
        new_object_id = match_obj.id
        self._data[new_object_id] = match_obj.serialize()
        self._write_json()

        # Make sure each User object has this Match in its data:
        user1_obj.add_match(match_id=new_object_id, match_timestamp=match_obj.timestamp, match_partner_id=user2_obj.id)
        user2_obj.add_match(match_id=new_object_id, match_timestamp=match_obj.timestamp, match_partner_id=user1_obj.id)

        # Update each of the two User objects' stored data:
        self.user_api_instance.sync(user1_obj)
        self.user_api_instance.sync(user2_obj)

        return new_object_id
    
    def lookup_obj(self, match_id: int) -> models.Match:
        self._read_json()
        self._validate_object_id(match_id)
        match_data = self._data[match_id] # todo the three lines through the end of this one could easily go to a helper method in the ABC. E.g. _get_data_for_id
        user_id_1, user_id_2 = match_data["users"][0], match_data["users"][1]
        user1 = self.user_api_instance.lookup_obj(user_id_1)
        user2 = self.user_api_instance.lookup_obj(user_id_2)

        cached_suggestions = []
        datespot_db = DatespotModelInterface(json_map_filename=self._master_datafile)
        for suggestion in match_data["suggestions"]:  # Convert the datespot IDs to datespot objects
            suggestion_tuple = (
                suggestion[0],
                datespot_db.lookup_obj(suggestion[1])
                )
            cached_suggestions.append(suggestion_tuple)  # TODO confirm this preserves sorted order (descending on score, highest score first)

        match_obj = models.Match(
            user1 = user1,
            user2 = user2,
            timestamp = match_data["timestamp"],
            suggestions_queue = cached_suggestions)

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
    
    def render_suggestions_list(self, match_id: str) -> List[dict]:
        """
        Return list of dictionaries containg information about suggested Datespots relevant and appropriate
        for display to Users in suggestions.
        """
        self._read_json()
        renderable_data = []
        match_obj = self.lookup_obj(match_id)
        datespot_db = DatespotModelInterface(json_map_filename=self._master_datafile)
        for suggestion in match_obj.suggestions_queue:  # TODO it should be an @property that yields, like User.matches
            # TODO whatever Match model code is called here should be solely responsible for updating the suggestions queue if necessary
            datespot_obj = suggestion[1]  # TODO External callers shouldn't have to deal with the indexing like this; Match generators should handle it
            renderable_data.append(datespot_db.render_obj(datespot_obj.id))
        return renderable_data
        
    def update(self, object_id, json_data=None): # Todo
        # e.g. if the current location changed, meaning the Match.midpoint changed
        """

        Example calls:

            my_match.update() 
                 - Calling with no args applies any updates inferable from the constituent User objects. E.g. 
                    if the Users' predominant locations, then the Match's midpoint changes, which could alter the
                    suggestions queue.
        """
        self._read_json()
        self._validate_object_id(object_id)
        object_data = self._data[object_id]

        # For a Match object as of this writing, we want to instantiate a Match object for any supported update. As imagined so far,
        #   there's no such thing as "just update this one little think in the stored JSON, no need to instantiate an object". The most
        #   common expected use of this method is to call it with no arguments, to cause an update of the suggestions queue.

        object_instance = self.lookup_obj(object_id) # Instantiate it to trigger computations called by the constructor, then re-serialize it.
        if not json_data:
            self._data[object_id] = object_instance.serialize()
        else: # TODO Do we care about enabling external code to update the suggestions queue? Intuition is that Match owns the suggestions queue, full stop--any
                #   new information should be factored into suggestions by calling the methods in the Match model. 
            raise NotImplementedError("Updating that field of a Match not supported")

    def suggestion_candidates_needed(self, object_id: str) -> bool:
        """
        Returns True if the match corresponding to object_id needs more Datespots to consider for suggestions, 
        else False.
        """
        self._read_json()
        self._validate_object_id(object_id)
        match_data = self._data[object_id]
        return not match_data["suggestions"]
    
    def refresh_suggestion_candidates(self, object_id: str, candidates: List[Tuple[float, models.Datespot]]) -> None:
        """
        Feeds new external data about Datespots to a Match object, for consideration in suggestions.
        """
        self._read_json()
        self._validate_object_id(object_id)
        match_obj = self.lookup_obj(object_id)
        match_obj.suggestions(candidates)
        self.sync(match_obj)  # Update the new suggestions in the DB

    ### Private methods ###

    def _set_datafile(self):
        """Set the filename of the specific file containing the match data JSON."""
        with open(self._master_datafile, 'r') as fobj: # TODO was there some reason for overriding the inherited ABC one, or is this artifact?
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

class ReviewModelInterface(ModelInterfaceABC):

    def __init__(self, json_map_filename=None):
        self._model = "review"
        if json_map_filename:
            super().__init__(json_map_filename)
        else:
            super().__init__()
        self._valid_model_fields = ["datespot_id", "text"]
    
    ### Public methods ###

    def create(self, new_data: dict) -> str:

        # Todo: Could store only the review's hash in the DB. We likely don't care
        #   about anything other than checking whether a given review is already in the DB.
        #   Or maybe (id, sentiment, relevance) -- point being we don't want to store the text
        #   of thousands of reviews.

        # TODO How to handle updates to the text of reviews? That will be a very common case if 
        #   scraping/crawling the same restaurants repeatedly. Need a setup that allows tying a 
        #   given review to a post on Yelp/Google/whatever without requiring identical text, to 
        #   avoid counting a trivial edit as an entirely new review. 

        # TODO Only store relevant Reviews, not all Reviews. 

        self._read_json()

        self._validate_json_fields(new_data) # Validate fields

        # TODO Model this on message MI create(): If the Review contains stuff that should be updated in the stored
        #   info about the Datespot, then this create() method makes the necessary updates to the Datespot object's 
        #   traits. 

        new_obj = models.Review( # Instantiate a model object
            datespot_id = new_data["datespot_id"],
            text = new_data["text"]
        )
        new_obj_id = new_obj.id # Get object's id hash string
        self._data[new_obj_id] = new_obj.serialize() # Save with that id as the key
        self._write_json()
        return new_obj_id
    
    def lookup_obj(self, object_id: str) -> models.Review:
        self._read_json()
        self._validate_object_id(object_id)
        object_data = self._data[object_id]
        object_constructor = eval(f"models.{self._model.title()}") 
        obj = object_constructor( # TODO Was experimenting with generalizing it as much as possible. Should be able to generalize the constructor call with aggressive use of eval/exec.
            datespot_id = object_data["datespot_id"],
            text = object_data["text"]
        )
        return obj

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
    
    ### Public methods ###

    def create(self, new_data: dict) -> str:
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
        self._validate_json_fields(new_data)
        
        time_sent = None
        if "time_sent" in new_data: # If caller sent JSON containing a time stamp, use it...
            time_sent = new_data["time_sent"]
        else:
            time_sent = time.time() # ...otherwise, create timestamp now.

        # Constructor needs a User object literal in order to update its tastes.
        user_db = UserModelInterface(self._master_datafile) # The MIs can't go out to the main database API because it causes circular imports
        sender_user_obj = user_db.lookup_obj(new_data["sender_id"])
        prior_user_tastes = str(sender_user_obj.serialize()["tastes"]) # for comparison later, to see if any updates happened

        new_obj = models.Message(
            time_sent = time_sent,
            sender = sender_user_obj,
            chat_id = new_data["chat_id"],
            text = new_data["text"]
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
        chat_update_data = {"messages": [new_obj_id]}
        chat_id = new_obj.chat_id
        chat_db.update_chat(new_obj.chat_id, chat_update_data)

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

class ChatModelInterface(ModelInterfaceABC):

    def __init__(self, json_map_filename=None):
        self._model = "chat"
        if json_map_filename:
            super().__init__(json_map_filename)
        else:
            super().__init__()
        self._valid_model_fields = ["start_time", "participant_ids", "messages"]
    
    ### Public methods ###

    def create(self, new_data: dict):
        self._read_json()
        self._validate_json_fields(new_data)

        start_time = None # Same as Message. If it didn't come in with a timestamp, use the current time
        if "start_time" in new_data:
            start_time = new_data["start_time"]
        else:
            start_time = time.time()

        new_obj = models.Chat(
            start_time = start_time,
            participant_ids = new_data["participant_ids"]
        ) # no messages yet

        new_obj_id = new_obj.id

        self._data[new_obj_id] = new_obj.serialize()
        self._write_json()
        return new_obj_id

    def update_chat(self, object_id: str, update_data: dict): # Todo will need more sophisticated interface for adding/removing from lists. Same in other models that have running-list data.
        self._read_json()
        self._validate_object_id(object_id)
        self._validate_json_fields(update_data)
        chat_data = self._data[object_id] # load the old data
        if "start_time" in update_data:
            del update_data["start_time"] # Start time treated as immutable
        for key in update_data:
            if type(chat_data[key]) == list:
                chat_data[key].extend(update_data[key])
        self._write_json()
    
    def lookup_obj(self, object_id: str):
        self._read_json()
        self._validate_object_id(object_id)
        chat_data = self._data[object_id]

        # Instantiate a Message object literal from each stored Message ID
            # TODO how could this possibly perform well IRL? Chats would run to hundreds of messages...
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