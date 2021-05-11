"""
Interface between the database and the User model.
"""

# This one is cluttered so that the domain layer user.py can be relatively clean.
# Repository design pattern.

import uuid
import json
import user

import model_api_ABC

class UserAPI(model_api_ABC.ModelAPI):

    def __init__(self, datafile_name=None):
        if datafile_name: # Todo is there a one-liner for this? Ternary expression?
            super().__init__(datafile_name)
        else:
            super().__init__()

        self._model = "user"
        
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
        self._data[user_id] = self._serialize_user(newUser)
        self._write_json() # write all data back to the persistent json
        return user_id

    def load_user(self, user_id: int) -> user.User: # todo the keys in the dict are ending up as string, not ints. Not obvious why.
        """
        Instantiates a User object to represent an existing user, based on data retrieved from the database. Returns the User object,
        or raises error if not found.
        """
        self._read_json()
        userData = self._data[user_id]
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