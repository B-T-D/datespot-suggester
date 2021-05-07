"""
Interface between the database and the User model.
"""

# This one is cluttered so that the domain layer user.py can be relatively clean.
# Repository design pattern.

import uuid
import json
import user

JSON_DB_NAME = "jsonMap.json"

class UserAPI:

    def __init__(self, datafile_name=JSON_DB_NAME):
        self._master_datafile = datafile_name
        self._datafile = None
        self.data = {}

    def _set_datafile(self):
        """Set the filename of the specific file containing the match data JSON."""
        with open(self._master_datafile, 'r') as fobj:
            jsonMap = json.load(fobj)
            fobj.seek(0)
        self._datafile = jsonMap["user_data"]
    
    def _read_json(self):
        """Write the API instance's Python dictionary literal with the corresponding JSON."""
        if not self._datafile:
            self._set_datafile()
        jsonData = {}
        with open(self._datafile, 'r') as fobj: # todo inefficient, get the strings to parse
                                                #   to ints correctly.
            jsonData = json.load(fobj)
            fobj.seek(0)
        print(f"--------------------jsonData:-------------------------------\n{jsonData}")
        for key in jsonData: # force every key back to int...
            self.data[int(key)] = jsonData[key]
    
        # todo see https://stackoverflow.com/questions/1450957/pythons-json-module-converts-int-dictionary-keys-to-strings
        #   Use the object_hook parameter of json.load().

    def _write_json(self):
        """Write the persistent JSON to match the current Python dictionary literal."""
        if not self._datafile:
            self._set_datafile()
        with open(self._datafile, 'w') as fobj:
            json.dump(self.data, fobj)
            fobj.seek(0)
        
    def create_user(self, name: str, currentLocation: tuple=None, homeLocation: tuple=None, force_key: int=None): 
        """
        Create a new user in the database, and return the user id of the new user. 

        To access the user.User object, call UserAPI.load_user() with the user id.
        """
        newUser = user.User(name, currentLocation, homeLocation)
        if force_key:
            user_id = force_key
        else:
            user_id = uuid.uuid1().int # generates uuid based on current time, see docs. ".int" attribute expresses the UUID object as int
        self.data[user_id] = self._serialize_user(newUser)
        self._write_json() # write all data back to the persistent json
        return user_id

    def is_valid_user(self, user_id) -> bool:
        """
        Public method for validating existence of a user in the user DB. Returns True if user_id corresponds to a valid user, 
        else False.
        """
        self._read_json()
        return user_id in self.data

    def load_user(self, user_id: int) -> user.User: # todo the keys in the dict are ending up as string, not ints. Not obvious why.
        """
        Instantiates a User object to represent an existing user, based on data retrieved from the database. Returns the User object,
        or raises error if not found.
        """
        print(f"\n user id in load user = {user_id} {type(user_id)}")
        print("load user before read call:")
        print(f"\n{self.data}")
        self._read_json()
        print("load user after read call:")
        print(f"\n{self.data}")
        userData = self.data[user_id]
        assert type(userData) == dict
        userObj = user.User(
            name=userData["name"],
            currentLocation=userData["current_location"],
            homeLocation=userData["home_location"],
            likes = userData["likes"],
            dislikes = userData["dislikes"]
        )
        return userObj

    def update_user(self, user_id): # todo -- updating location might be single most important thing this does. 
        pass
    
    def delete_user(self, user_id: int):
        """
        Delete the user corresponding to user_id.
        """
        if self.is_valid_user(user_id):
            del self.data[user_id]
            self._write_json()
            return 0
        else:
            return 1

    def _serialize_user(self, user: user.User) -> dict: # todo: superfluous?
        """
        Create a dictionary representation of the user.
        """
        userDict = {
            "name": user.name,
            "current_location": user.currentLocation,
            "home_location": user.homeLocation,
            "likes": user.likes,
            "dislikes": user.dislikes
        }
        return userDict


def main():
    pass


if __name__ == "__main__":
    main()