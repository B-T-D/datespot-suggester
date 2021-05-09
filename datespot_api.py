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
        print(f"_load_db was called")
        allJson = None
    
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
        try:
            with open(self._datafile, 'r') as fobj:
                datespotJson = json.load(fobj)
                fobj.seek(0)
        except (FileNotFoundError, json.decoder.JSONDecodeError): # create it and/or add "{}" string
            with open(self._datafile, 'w') as fobj: #todo this isn't actually working to write the blank dict
                json.dump(str(dict()), fobj)
            return # todo cleanup, this was quick hack
    
    def _update_json(self):
        print(f"self.data in _update_json = \n{self.data}")
        with open(self._datafile, 'w') as fobj:
            json.dump(self.data, fobj)
            fobj.seek(0)
    
    def create_datespot(self, json_data: str) -> int:
        """
        Returns the location's key.
        """
        datespot_dict = json.loads(json_data)
        # key is the hash of the two-coordinate location, for now. TBD if lat lon in the google response are stable enough to hash
        #   to same thing consistently and be useable for lookup.
        location_tuple = tuple(datespot_dict["location"])
        datespot_id = hash(location_tuple)

        self.data[datespot_id] = json_data
        print(self.data)
        self._update_json()
        return datespot_id


    def create_datespot_from_individual_strings(self, location: tuple, name: str, traits: list, price_range: int, hours: list=[]): # todo any reason for this to exist and not just accept only JSON?
        """
        Returns the location key. 
        """
        if len(location) < 3:
            # make new tuple with the third vertical dimension coordinate:
            three_coord_location = [element for element in location] 
            three_coord_location.append(0)
            location = tuple(three_coord_location)

            # todo: YAGNI? Is it really all that likely for two restaurants to have 
            #   identical lat lon, given that each coordinate is specified to 6+ decimal
            #   places? Consult google API docs--is collision possible at all in the
            #   response data? Google must've faced the X-Y collision issue too.
            #   If collision is possible, is it probable enough to justify the convolutedness
            #   of this DIY elevation coordinate?

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
            "traits": list(datespot.traits),
            "price_range": datespot.price_range,
            "hours": datespot.hours,
            "baseline_dateworthiness": datespot.baseline_dateworthiness
        }
        return datespotDict

    def _validate_datespot(self, key: tuple) -> None:
        """
        Raise KeyError if location_key isn't in the database.
        """
        if not key in self.data: # todo--mess with tuples vs string supported as keys
            raise KeyError(f"Restaurant with location-key {location_key} not found.")
    
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

    def lookup_datespot(self, id: int) -> datespot.Datespot:
        """Return the datespot object corresponding to key "id"."""
        self._validate_datespot(id)

    def load_datespot(self, location_key: tuple) -> datespot.Datespot: # todo deprecated, remove from tests etc.
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