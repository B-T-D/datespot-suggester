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
                json.dump(self.data)
                fobj.seek(0)
        except FileNotFoundError:
            print(f"File '{self._datafile}' not found.")
    
    def create_datespot(self):
        pass

    def _validate_datespot(self, location_key: tuple) -> None:
        """
        Raise KeyError if location_key isn't in the database.
        """
        if not location_key in self.data:
            raise KeyError(f"Restaurant with location-key {location_key} not found.")
    
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
