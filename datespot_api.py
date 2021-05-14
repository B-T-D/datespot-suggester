"""
Interface between the database and the Datespot model.

All validation other than checking ids should be handled in the main DatabaseAPI. 
"""
# ^ Rationale: this module has plenty to do with its reads/writes of the json files. Handling those persistent
#   files are these helper APIs' "do one thing and do it well".

import json
import datespot
import geo_utils

import model_api_ABC



class DatespotAPI(model_api_ABC.ModelAPI):

    def __init__(self, datafile_name=None): # The abstract base class handles setting the filename to default if none provided
        if datafile_name: # Todo is there a one-liner for this? Ternary expression?
            super().__init__(datafile_name)
        else:
            super().__init__()

        self._model = "datespot"
        self._valid_model_fields = ["name", "location", "traits", "price_range", "hours"]
    
    def create_datespot(self, json_data: str) -> int:
        """
        Creates a new Datespot object, serializes it to the persistent JSON, and returns its id key.
        """
        self._read_json()
        json_dict = json.loads(json_data)
        # Validate fields
        for key in json_dict:
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
        new_object_id = datespot_obj.id

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

    def lookup_datespot_json(self, id: int) -> str:
        """
        Return the JSON string for a Datespot in the DB.
        """
        datespot_obj = self.lookup_datespot(id)
        return json.dumps(self._serialize_datespot(datespot_obj))

    def lookup_datespot(self, id: int) -> datespot.Datespot: # The main code that uses actual model object instances is other database API code, or the models' internal code
                                                                # ...(e.g. Datespot uses a User instance to score a restaurant; Match uses two Users and a heap of Datespots).
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
            if distance < radius: # todo do we need the full object in the results dict, or would only the lookup key suffice?
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