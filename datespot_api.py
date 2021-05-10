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
            self.data[int(key)] = json_data[key]
    
    def _write_json(self):
        """Overwrite the stored JSON to exactly match current state of the API instance's native Python dictionary."""
        # Todo: Any kind of safety rails that make sense to reduce risk of undesired overwrites of good data?
        if not self._datafile:
            self._set_datafile()
        with open(self._datafile, 'w') as fobj:
            json.dump(self.data, fobj)
            fobj.seek(0)

    # todo delete once not needed for json syntax reference:
    """
    def _load_db(self): # todo DRY--write a JSON handler utility so this and 
                        #   UserAPI can share same code.
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
    """
    
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
        self.data[new_id] = {
            "location": location_tuple,
            "name": json_dict["name"],
            "traits": json_dict["traits"],
            "price_range": json_dict["price_range"],
            "hours": json_dict["hours"]
        }
        self._write_json()
        return new_id

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

    def _validate_datespot(self, id: int) -> None:
        """
        Raise KeyError if id isn't in the database.
        """
        if not id in self.data: # todo--mess with tuples vs string supported as keys
            raise KeyError(f"Restaurant with id-key {key} not found.")
    
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
        datespot_data = self.data[id]
        print("-------")
        print(type(datespot_data))
        print(datespot_data)
        print("-------")
        return datespot.Datespot(
            location = id,
            name = datespot_data["name"],
            traits = datespot_data["traits"],
            price_range = datespot_data["price_range"],
            hours = datespot_data["hours"]
        )
    
    def update_datespot(self, id: int, **kwargs): # Stored JSON is the single source of truth. We want a bunch of little, super fast read-writes. 
                                                    # This is where concurrency/sharding would become hypothetically relevant with lots of simultaneous users.

        self._read_json() # sync the API instance's native Python dictionary to match the latest known state of the stored JSON
        self._validate_datespot(id)
        datespot_data = self._data[id] # the data to modify is in the native Python dictionary. No need to instantiate a Datespot object with that data.

        # parse kwargs for which fields to update:

        for field in self._valid_model_fields:
            if field in kwargs:
                new_value = kwargs[field]
                if self._validate_parameter(new_value):
                    datespot_data[field] = new_value
                else:
                    raise ValueError(f"Invalid value for parameter '{field}': '{new_value}'")
        
        # Sync the stored JSON:
        self._write_json()
        
    def delete_datespot(self, id: int) -> None:
        self._read_json()
        self._validate_datespot(id)
        del self.data[location_key]
        self._write_json()