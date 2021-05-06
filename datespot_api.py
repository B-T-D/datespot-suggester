"""
Interface between the database and the Datespot model.
"""
# Non-DRY now, but want to support divergence between User and Datespot down the
#   road.

import json
import datespot

JSON_DB_NAME = "mockDatespotsDB.json"

class DatespotAPI:

    def __init__(self, datafile_name=JSON_DB_NAME): # takes datafile_name to simplify tests code
        self._datafile = datafile_name
        self.data = None
        self._load_db() # todo bad practice?

    def _load_db(self): # todo DRY--write a JSON handler utility so this and 
                        #   UserAPI can share same code.
        """Load all JSON into memory."""
        allData = None
        try:
            with open(self._datafile, 'r') as fobj:
                allData = json.load(fobj)
                fobj.seek(0) # reset position to start of the file
        except FileNotFoundError:
            print(f"File {self._datafile} not found.")
        if not allData:
            self.data = {}
        else:
            self.data = allData
    
    def _update_json(self):
        try:
            with open(self._datafile, 'r') as fobj:
                fobj.seek(0)
            with open(self._datafile, 'w') as fobj:
                json.dump(self.data, fobj)
                fobj.seek(0)
        except FileNotFoundError:
            print(f"File '{self._datafile}' not found.")
    
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
        self.data[str(location)] = self._serialize_datespot(newDatespot) # todo json won't accept a tuple key. Figure out best way to handle.
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

    def _validate_datespot(self, location_key: tuple) -> None:
        """
        Raise KeyError if location_key isn't in the database.
        """
        if not str(location_key) in self.data: # todo--mess with tuples vs string supported as keys
            raise KeyError(f"Restaurant with location-key {location_key} not found.")
    
    def load_datespot(self, location_key: tuple) -> datespot.Datespot:
        self._validate_datespot(location_key)
        datespotData = self.data[str(location_key)] # todo tuple vs string key
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
