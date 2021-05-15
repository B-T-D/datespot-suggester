"""Abstract base class to be instantiated by model-data interface concrete classes (one concrete class for each model)."""

import abc
import json

JSON_DB_NAME = "jsonMap.json"

class ModelAPI:
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
    
    def _validate_json_fields(self, json_dict: dict) -> None:
        """Raise ValueError if any key in json_dict isn't a valid field for this model."""
        for key in json_dict:
            if not key in self._valid_model_fields:
                raise ValueError(f"Invalid field in call to model interface create method: {key}")
    
    def _get_all_data(self) -> dict: # todo access this with the public attribute "self.data", not this method
        """Return the API instance's data as a native Python dictionary."""
        self._read_json()
        return self._data
    
    def delete(self, object_id: int) -> None:
        """Delete the data for key object_id."""
        self._read_json()
        self._validate_object_id(object_id)
        del self._data[object_id]
        self._write_json()