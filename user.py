import uuid
from datespot import *

# temporary simple mockup of users DB
usersDB = {}

class User:

    def __init__(self, name:  str, currentLocation: tuple=None, homeLocation: tuple=None):
        """
        Args:
            currentLocation (tuple[int]): Tuple of two ints representing 2D coordinates.
            homeLocation (tuple[int]): Tuple of two ints representing 2D coordinates.
        """
        self.id = uuid.uuid1() # generates uuid based on current time
        self.name = name
        self.currentLocation = currentLocation
        self.homeLocation = homeLocation
        self.likes = [] # features of a date location that would make the user like it
        self.dislikes = [] # features of a date location that would make the user dislike it

        if not self.id in usersDB: #  initialize the user in the mock db
            usersDB[self.id] = {} # initialize the pk
            userEntry = usersDB[self.id]
            userEntry["name"] = self.name
            userEntry["current_location"] = self.currentLocation
            userEntry["home_location"] = self.homeLocation
            userEntry["likes"] = self.likes # todo probably should at least have these be sets for O(1)* lookup 
            userEntry["dislikes"] = self.dislikes
        else:
            raise NotImplementedError("uuid collision (user)")

    def get_restaurant_score(self, restaurant_name: str) -> int:
        """
            Takes the unique name of a restaurant and returns the score for how well this user matches with that restaurant.
        """
        print(f"restaurant name = {restaurant_name}")
        print(f"hash = {hash(restaurant_name)}")
        restaurantsDBEntry = locationsDB[hash(restaurant_name)]
        print(restaurantsDBEntry)
        restaurantTraits = locationsDB[hash(restaurant_name)]["traits"]
        print(restaurantTraits)

        score = 0

        # todo heinous time complexity
        for trait in restaurantTraits:
            if trait in self.likes:
                score += 1
            elif trait in self.dislikes:
                score -= 1
        
        return score



def main(): # temp debugging
    
    pass


if __name__ == '__main__':
    main()
    