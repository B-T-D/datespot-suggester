"""Abstract base class for the helper APIs that interface between the database and the models."""

import abc

import json

JSON_DB_NAME = "jsonMap.json"

class ModelAPI:
    __metaclasss__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, datafile_name=JSON_DB_NAME):
        self._master_datafile = datafile_name
        self._datafile = None
        self._data = {}

    def _set_datafile(self):
        """Retrieve and set filename of this model's stored JSON."""
        print(f"---set datafile was called---")
        with open(self._master_datafile, 'r') as fobj:
            json_map = json.load(fobj)
            fobj.seek(0)
        self._datafile = json_map[f"{self._model}_data"]
    
    def _read_json(self):
        """Read stored JSON models into the API instance's native Python dictionary."""
        if not self._datafile:
            self._set_datafile()
        json_data = {}
        with open(self._datafile, 'r') as fobj: # todo there's a way to get the keys to parse to native ints in one pass--consult docs.
            json_data = json.load(fobj)
            fobj.seek(0)
        for key in json_data: # todo for now, forcing every key back to int here
            self._data[int(key)] = json_data[key]

    def _write_json(self):
        """Overwrite stored JSON for this model to exactly match current state of the API instance's native Python dictionary."""
        # Todo: Any safeguards that make sense to reduce risk of accidentally overwriting good data?
        if not self._datafile:
            self._set_datafile()
        with open(self._datafile, 'w') as fobj:
            json.dump(self._data, fobj)
            fobj.seek(0)
    
    def _validate_object_id(self, object_id: int) -> None:
        """
        Raise KeyError if object_id not in database.
        """
        self._read_json()
        if not object_id in self._data:
            raise KeyError(f"{self._model.sentence()} with id (key) {object_id} not found.")
    
    def get_all_data(self) -> dict:
        """Return the API instance's data as a native Python dictionary."""
        self._read_json()
        return self._data
    
    def delete(self, object_id: int) -> None:
        """Delete the data for key object_id."""
        self._read_json()
        self._validate_object_id(object_id)
        del self._data[object_id]
        self._write_json()
    
