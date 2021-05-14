from app_object_type import DatespotAppType
import user

import json

import hashlib, struct

BASELINE_SCORING_DATA = "datespot_baseline_scoring_data.json"
MAX_LATLON_COORD_DECIMAL_PLACES = 8

##### DB schema #####

"""

    restaurant pk   | name  | location coordinates  | traits (cuisines, etc. to match with user likes/dislikes) | budget bucket $ to $$$$$   | hours (table of weekly hours)
    -------------------------------------------------------------------------------------------------------------------------------------------------------------
                    |       |                       |                                                           |                           |

"""
#####  #####

class Datespot(metaclass=DatespotAppType):

    def __init__(self, location: tuple, name: str, traits: list=[], price_range: int=None, hours: list=[]):
        """
        Args:
            traits (List[str]): ... 
            hours (List[List[int]]): ...

        """
        assert isinstance(location, tuple)
        self._location = ( # External code shouldn't mess with this, e.g. e.g. inadvertently casting to string or changing number of decimal places
            round(location[0], MAX_LATLON_COORD_DECIMAL_PLACES),
            round(location[1], MAX_LATLON_COORD_DECIMAL_PLACES)
            )
        self.location = self._location
        self.id = self._id() # todo confirm this is correct and good practice
        self.name = name
        
        self.price_range = price_range
        self.hours = hours

        with open(BASELINE_SCORING_DATA) as fobj: # todo each json.load(fobj) call is another pass through the entire json file, right?
                                                    # Is there a smarter way to ensure a single pass than reading all the json into a 
                                                    #   dict and then unpacking that dict?
            all_json = json.load(fobj)
            self.baseline_trait_weights = all_json["trait_weights"]
            self.brand_reputations = all_json["brand_reputations"]

        self.baseline_dateworthiness = 50 # Todo: What's the best scoring scale? -1 to 1? 0 to 1? 0 to 99?

        self.traits = traits # Todo: Need these to parse in as a hash set in a single O(n) pass...
        if self.traits:     #    ...Rather than one pass by json.load(), then another pass by set()
            self.traits = set(self.traits) # Probably almost no IRL performance gain from putting them into a set, because lookup only happens once.
                                            #   Hash set likely only improves speed if json can decode it into a native hash set in a single pass. 
        
        for key in self.brand_reputations: # cast each non-associative array to a hash set for faster lookup
            self.brand_reputations[key] = set(self.brand_reputations[key])

    def __eq__(self, other): # Must define __eq__ if you define __hash__
        """
        Return True if self should be treated as equal to other, else False.
        """
        return hash(self) == hash(other)

    def __hash__(self):
        return hash(self._location)

    def _id(self) -> str:
        """
        Return this Datespot's id key to an external caller.
        """
        hex_str = str(hex(self.__hash__())) # todo can/should you just just "hash(self)"?
        return hex_str[2:] # strip the "0x"


    # todo is_open queries might be better handled by direct DB queries, i.e. outside this module.
    #   One of the DB APIs will be able to do stuff like "check if we already know the hours for this restaurant recently enough,
    #       if so fetch them from DB, else request from the GM client". 
    def is_open_now(self, day: int, hour: int) -> bool: # simple int in [0..6] for day, [0..23] for hour, for now
        hours = locationsDB[self.id][day]
        return hours[0] <= hour <= hours[1] # if between the opening time and the closing time
    
    def _apply_brand_reputations(self):
        """
        Add traits associated with known brand reputation (traits confidently addable based on restaurant's name).
        """
        for reputational_label, tagged_restaurants in self.brand_reputations.items():
            if self.name in tagged_restaurants:
                self.traits.add(reputational_label)

    def _update_dateworthiness(self):
        """
        Update the location's baseline dateworthiness score based on the current traits.
        """
        # todo some of the trait bonuses/maluses shouldn't stack. E.g. "chain" and "unromantic chain"

        # todo make sure trait_weights are correcely integrated into whatever ends up being the overall scoring scale

        for trait in self.baseline_trait_weights:
            if trait in self.traits:
                self.baseline_dateworthiness = max(0, self.baseline_dateworthiness + self.baseline_trait_weights[trait])

    def score(self, user: user.User) -> float:
        # Externally callable wrapper
        return self._score(user)

    def _score(self, user:user.User) -> float:
        # Make sure all brand-related traits have been applied before updating the baseline dateworthiness.
        self._apply_brand_reputations() # These probably never get called more than once in the lifetime of a single Datespot instance.
        self._update_dateworthiness() #  ...In practice, Datespot objects will be instantiated solely so that this method can be called. Then they're garbage-collected.
        score = 0.0
        for trait in self.traits:
            if trait in user.likes: # todo user.likes is an array, not a hash set as of this writing
                score += 1
            elif trait in user.dislikes:
                score -= 1
        return score


def main():

    pass

if __name__ == '__main__':
    main()