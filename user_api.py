"""
Interface between the database and the User model.
"""

import uuid
import json
import user

JSON_DB_NAME = "mockDB.json"

class UserAPI:

    def __init__(self, datafile_name=JSON_DB_NAME):
        self._datafile = datafile_name
        self.data = None
        self._load_db() # todo bad practice?

    def _load_db(self):
        """Load all JSON into memory."""
        try:
            with open(self._datafile, 'r') as fobj:
                allData = json.load(fobj)
                fobj.seek(0) # reset position to start of the file
        except FileNotFoundError:
            print("Not found")
            #print(f"File {self._datafile} not found.")
        print(type(allData))
        if not "users" in allData: # initialize the "users" nested dict if not present
            allData["users"] = {}
        self.data = allData["users"]
    
    def create_user(self, name: str, currentLocation: tuple=None, homeLocation: tuple=None): 
        """
        Create a new user in the database, and return the user id of the new user. 

        To access the user.User object, call UserAPI.load_user() with the user id.
        """
        newUser = user.User(name, currentLocation, homeLocation)
        user_id = uuid.uuid1().int # generates uuid based on current time, see docs. ".int" attribute expresses the UUID object as int
        self.data[int(user_id)] = self._serialize_user(newUser)
        self._update_json() # write all data back to the persistent json
        return user_id

    def _validate_user(self, user_id):
        """
        Rause a KeyError if the user_id doesn't exist.
        """
        if not user_id in self.data:
            raise KeyError(f"User with id {user_id} not found.")
        return


    def load_user(self, user_id: int) -> user.User: # todo the keys in the dict are ending up as string, not ints. Not obvious why.
        """
        Instantiates a User object to represent an existing user, based on data retrieved from the database. Returns the User object,
        or raises error if not found.
        """
        self._validate_user(user_id)
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

    def update_user(self, user_id): # todo -- tbd if it takes id key vs user object.
        pass
    
    def delete_user(self, user_id: int):
        """
        Delete the user corresponding to user_id.
        """
        self._validate_user(user_id)
        del self.data[user_id]
        self._update_json()

    def _serialize_user(self, user: user.User) -> dict:
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
    
    def _update_json(self):
        try:
            with open(self._datafile, 'r') as fobj: # load all json, the file is not just the users "table", it's other models too
                allData = json.load(fobj)
                fobj.seek(0)
            allData["users"] = self.data
            print(f"allData = {allData}")
            with open(self._datafile, 'w') as fobj:
                json.dump(allData, fobj)
                fobj.seek(0)
        except FileNotFoundError:
            print(f"File '{self._datafile}' not found.")
        return 0


def main():

    api = UserAPI()
    print(api.data)

    # Init user "Grort"

    # Init user "Drobb"

    # Init second user "Grort" for name collision

    api = UserAPI()
    
    newUser = api.create_user("Grort")
    #print(newUser.name)
    #print(newUser)
    #print(api.data)

    # load existing user with id 1
    existingUser = api.load_user("1")
    print(existingUser)

    #assert "1" in api.data
    #api.delete_user("1")
    print(api.data)
    #assert not "1" in api.data

if __name__ == "__main__":
    main()