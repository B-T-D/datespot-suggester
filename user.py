from datespot import *

class User:

    def __init__(self, name:  str, currentLocation: tuple=None, homeLocation: tuple=None, likes: list=None, dislikes: list=None):
        """
        Args:
            currentLocation (tuple[int]): Tuple of two ints representing 2D coordinates.
            homeLocation (tuple[int]): Tuple of two ints representing 2D coordinates.
        """
        self.name = name
        self.currentLocation = currentLocation
        self.homeLocation = homeLocation
        self.likes = [] # features of a date location that would make the user like it
        self.dislikes = [] # features of a date location that would make the user dislike it
        self.travelPropensity= None #  todo placeholder. Integer indicating how willing the user is to travel, relative to other users. 
    
    def __str__(self):
        """
        Return the string representation of a dictionary containing all the user's info.
        """
        userDict = {
            "name": self.name,
            "current_location": self.currentLocation,
            "home_location": self.homeLocation,
            "likes": self.likes,
            "dislikes": self.dislikes
        }
        return "User" + str(userDict)
    
    def datespot_score(self, datespot) -> int:
        # Wrapper for external calls
        """
        Takes a datespot object and returns the score for how well this user matches with that datespot.

        Args:

            datespot (datespot.Datespot object): An instance of the Datespot class.
        """
        return self._get_datespot_score(datespot)

    def _get_datespot_score(self, datespot) -> int:
        
        score = 0
        for trait in datespot.traits: # todo this is O(n^2); should likes and/or traits be hash sets?
            if trait in self.likes:
                score += 1
            elif trait in self.dislikes:
                score -= 1
        return score    