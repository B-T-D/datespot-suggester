"""
Interface between the database and the Datespot model.

All validation other than checking ids should be handled in the main DatabaseAPI. 
"""
# ^ Rationale: this module has plenty to do with its reads/writes of the json files. Handling those persistent
#   files are these helper APIs' "do one thing and do it well".

import json
import datespot
import geo_utils

JSON_DB_NAME = "jsonMap.json"

class DatespotAPI:

    def __init__(self, datafile_name=JSON_DB_NAME): # takes datafile_name to simplify tests code
        self._master_datafile = datafile_name
        self._datafile = None
        self._data = {} # Can't be directly accessed by external callers, because it often won't be populated at the moment of the attempted access. Access with DatespotAPI.get_all_data()
        self._valid_model_fields = ["name", "location", "traits", "price_range", "hours"]

    def _set_datafile(self): # Todo: Worthwhile to refactor to an abstract base class that all three model-apis can inherit methods like this from?
        """Set the filename of the specific file containing the match data JSON.""" 
        with open(self._master_datafile, 'r') as fobj:
            json_map = json.load(fobj)
            fobj.seek(0)
        self._datafile = json_map["datespot_data"]
    
    def _read_json(self): # Todo: Another method that could go to an ABC
        """Read the stored JSON models into the API instance's native Python dictionary."""
        # We want object literals, rather than strings, as the native Python dict values for query purposes. Convert everything to the "real" type
        #   once, here, so that e.g. arithmetic queries can operate on the "location" key's value's literals.
        if not self._datafile:
            self._set_datafile()
        json_data = {}
        with open(self._datafile, 'r') as fobj: # todo there's a way to get keys to parse to native ints in one pass, consult docs.
            json_data = json.load(fobj)
            fobj.seek(0)
        for key in json_data: # todo: For now, forcing every key back to int here
            self._data[int(key)] = json_data[key]
    
    def _write_json(self):
        """Overwrite the stored JSON to exactly match current state of the API instance's native Python dictionary."""
        # Todo: Any kind of safety rails that make sense to reduce risk of undesired overwrites of good data?
        if not self._datafile:
            self._set_datafile()
        with open(self._datafile, 'w') as fobj:
            json.dump(self._data, fobj)
            fobj.seek(0)

    def get_all_data(self) -> dict: # todo can go in the ABC
        """Return the API instance's data as a native Python dictionary."""
        self._read_json()
        return self._data

    
    def create_datespot(self, json_data: str) -> int:
        """
        Returns the location's key.
        """
        self._read_json()
        json_dict = json.loads(json_data)
        for key in json_dict:
            if not key in self._valid_model_fields:
                raise ValueError(f"Bad JSON in call to create_datespot(): \n{key}")
        location_tuple = tuple(json_dict["location"])
        new_id = hash(location_tuple) # primary key is the hash of the two coordinate location tuple. TBD if the tuples from GM API are stable enough to hash to same thing every time.
                                        #   Todo might make more sense to just use the GM place id. Or its hash.
        
        
        # Todo need to validate the values for each
        self._data[new_id] = {
            "id": new_id,
            "location": location_tuple,
            "name": json_dict["name"],
            "traits": json_dict["traits"],
            "price_range": json_dict["price_range"],
            "hours": json_dict["hours"]
        }

        # todo create it as a Datespot object, in order to call Datespot's higher-order NLP algorithms.
        #   I.e. right now, to apply the brand reputations and store them in the DB. 

        self._write_json()
        return new_id

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

    def _validate_datespot(self, object_id: int) -> None: # todo to ABC
        """
        Raise KeyError if id isn't in the database.
        """
        self._read_json()
        if not object_id in self._data: # todo--mess with tuples vs string supported as keys
            raise KeyError(f"Restaurant with id-key {object_id} not found.")
    
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

    def lookup_datespot(self, id: int) -> datespot.Datespot: # The main code that uses actual model object instances is other database API code, or the models' internal code
                                                                # ...(e.g. Datespot uses a User instance to score a restaurant; Match uses two Users and a heap of Datespots).
        """Return the datespot object corresponding to key "id"."""
        self._validate_datespot(id)
        datespot_data = self._data[id]
        return datespot.Datespot(
            datespot_id = id,
            location = datespot_data["location"],
            name = datespot_data["name"],
            traits = datespot_data["traits"],
            price_range = datespot_data["price_range"],
            hours = datespot_data["hours"]
        )

    
    def update_datespot(self, id: int, **kwargs): # Stored JSON is the single source of truth. We want a bunch of little, super fast read-writes. 
                                                    # This is where concurrency/sharding would become hypothetically relevant with lots of simultaneous users.

        self._read_json() # sync the API instance's native Python dictionary to match the latest known state of the stored JSON
        datespot_data = self._data[id] # the data to modify is in the native Python dictionary. No need to instantiate a Datespot object with that data.


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

        
        # Sync the stored JSON:
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
        #matches_dict = {} #{ int id : {datespot JSON}}
        query_results = [] # list of two element tuples of (distance_from_query_location, serialized_datespot_dict). I.e. list[tuple[int, dict]]
        for id_key in self._data:
            place = self._data[id_key]
            place_loc = place["location"]
            distance = geo_utils.haversine(location, place_loc)
            if distance < radius:
                query_results.append((distance, place)) # append as tuple with distance as the tuple's first element
        query_results.sort() # Todo no reason to heap-sort yet, not sure if this method's caller will actually want it as a heap.
                                # More likely, the caller heapifies these results internally. 
        return query_results

        

    def query(self, field:str, operator:str, operand:str): # todo for now, complex/joined queries (and, or) only supported through using python and/or between multiple calls to this query method

        # See https://stackoverflow.com/questions/18591778/how-to-pass-an-operator-to-a-python-function

        """
        Args:
            field (str): Any of the valid model fields; "distance".
            operator(str): for traits: "all", "in", "not in", "or"; for locations: +, -, *, //, <, <=, ==, =>, >
        """
        # parse field and operators, and call appropriate subroutine:
        pass

    def _query_traits(self):
        pass
        # Complicated to implement properly, and may not be needed all that often by the app's core logic.
        #   The typical use case is more likely "Look at *all* traits of restaurant R, and process each of those
        #   traits relative to the matched users' preferences." Rather than "find all restaurants with trait X
        #   but not trait Y."

        # Todo: If the restaurant queries get complex ("all restaurants with X, Y, but not Z traits, open at T time
        #   on each of Wed/Thurs/Fri"), then that could indicate SQL is a better fit. Restaurant data seemed like the 
        #   closest to being better off with SQL at the first round of designing. 

        
    def delete_datespot(self, id: int) -> None:
        self._read_json()
        self._validate_datespot(id)
        del self._data[location_key]
        self._write_json()