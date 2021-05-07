"""
Interface between the database and the Datespot model.
"""

import json
import datespot

JSON_DB_NAME = "jsonMap.json"

class DatespotAPI:

    def __init__(self, datafile_name=JSON_DB_NAME): # takes datafile_name to simplify tests code
        self._master_datafile = datafile_name
        self._datafile = None
        self.data = {}
        self._load_db() # todo bad practice? https://softwareengineering.stackexchange.com/questions/48932/constructor-should-generally-not-call-methods

        # todo: refactor to a bunch of small read-writes, like in the user api.

    def _load_db(self): # todo DRY--write a JSON handler utility so this and 
                        #   UserAPI can share same code.
        """Load stored JSON into memory."""
        allJson = None
    
        #jsonData = None
        try:
            with open(self._master_datafile, 'r') as fobj:
                allJson = json.load(fobj)
                fobj.seek(0) # reset position to start of the file
        except FileNotFoundError:
            print(f"File {self._datafile} not found.")
        
        # the jsonMap file doesn't actually contain all the JSON, just the filenames
        #   for where to get it.
        self._datafile = allJson["datespot_data"]
        datespotJson = None
        with open(self._datafile, 'r') as fobj:
            datespotJson = json.load(fobj)
            fobj.seek(0)

        # convert each key to a tuple literal
        for stringKey in datespotJson:
            tupleKey = self._string_loc_key_to_tuple(stringKey)
            self.data[tupleKey] = datespotJson[stringKey]
    
    def _update_json(self):

        # convert each tuple key to a string
        jsonData = {}
        for tupleKey in self.data:
            stringKey = self._tuple_loc_key_to_string(tupleKey)
            jsonData[stringKey] = self.data[tupleKey]

        with open(self._datafile, 'r') as fobj: # todo artifact?
            fobj.seek(0)
        with open(self._datafile, 'w') as fobj:
            json.dump(jsonData, fobj)
            fobj.seek(0)
    
    def create_datespot(self, location: tuple, name: str, traits: list, price_range: int, hours: list):
        """
        Returns the location key. 
        """
        if len(location) < 3:
            # make new tuple with the third vertical dimension coordinate:
            three_coord_location = [element for element in location] 
            three_coord_location.append(0)
            location = tuple(three_coord_location)
        newDatespot = datespot.Datespot(
            location,
            name,
            traits,
            price_range,
            hours
        )
        self.data[location] = self._serialize_datespot(newDatespot) # todo json won't accept a tuple key. Figure out best way to handle.
        self._update_json()
        return location

    def _serialize_datespot(self, datespot) -> dict:
        datespotDict = {
            "location": datespot.location,
            "name": datespot.name,
            "traits": datespot.traits,
            "price_range": datespot.price_range,
            "hours": datespot.hours
        }
        return datespotDict

    def _validate_datespot(self, location_key: tuple) -> None:
        """
        Raise KeyError if location_key isn't in the database.
        """
        if not location_key in self.data: # todo--mess with tuples vs string supported as keys
            raise KeyError(f"Restaurant with location-key {location_key} not found.")
    

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

    def load_datespot(self, location_key: tuple) -> datespot.Datespot:
        self._validate_datespot(location_key)
        datespotData = self.data[location_key]
        datespotObj = datespot.Datespot(
            location = location_key,
            name = datespotData["name"],
            traits = datespotData["traits"],
            price_range = datespotData["price_range"],
            hours = datespotData["hours"]
        )
        return datespotObj
    
    def update_datespot(self, location_key: tuple, *args, **kwargs):
        pass

    def delete_datespot(self, location_key: tuple) -> None:
        self._validate_datespot(location_key)
        del self.data[location_key]
        self._update_json()