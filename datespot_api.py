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

    def __init__(self, json_map_filename=None): # The abstract base class handles setting the filename to default if none provided
        self._model = "datespot"
        if json_map_filename: # Todo is there a one-liner for this? Ternary expression?
            super().__init__(json_map_filename)
        else:
            super().__init__()
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