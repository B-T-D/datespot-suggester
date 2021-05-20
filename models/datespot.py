from app_object_type import DatespotAppType
import models.user as user

import json

import hashlib, struct

BASELINE_SCORING_DATA = "datespot_baseline_scoring_data.json"
MAX_LATLON_COORD_DECIMAL_PLACES = 8
DATESPOT_SCORE_DECIMAL_PLACES = 4

##### DB schema #####

"""

    restaurant pk   | name  | location coordinates  | traits (cuisines, etc. to match with user likes/dislikes) | budget bucket $ to $$$$$   | hours (table of weekly hours)
    -------------------------------------------------------------------------------------------------------------------------------------------------------------
                    |       |                       |                                                           |                           |

"""
#####  #####

class Datespot(metaclass=DatespotAppType):

    # Todo: Plan as of 5/18 is that reviews per se aren't related to a datespot. Higher level info is extracted from the reviews--abstract traits about the 
    #   object--and those traits are related to the datespot object. We remember an aggregate knowledge of / opinion about the restaurant that we learned from 
    #   reading its reviews, we don't memorize the full text of every review we read.

    def __init__(self, location: tuple, name: str, traits: dict={}, price_range: int=None, hours: list=[]):
        """
        Args:
            traits (dict): ... 
            hours (List[List[int]]): ...

        
        Traits dict structure mirrors the User model's "tastes" dict:

            {
                str continuous_trait_name: [float score, int datapoints],
                str discrete_trait_name: [1.0, "discrete"]
            }

            "Continuous" traits are e.g. "loud", "dark", "fun"; "discrete" are e.g.
            "Thai", "Italian", "coffee" (a place either is a certain genre or it isn't, no spectrum).

        """
        # todo seems clunky / insufficiently intuitive way to handle the discrete vs. continuous traits. 
        assert isinstance(location, tuple)
        assert isinstance(traits, dict)
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

        self.baseline_dateworthiness = 0.0 # Todo: What's the best scoring scale? -1 to 1? 0 to 1? 0 to 99?

        self.traits = traits  
        
        for key in self.brand_reputations: # cast each non-associative array to a hash set for faster lookup
            self.brand_reputations[key] = set(self.brand_reputations[key])

    def __eq__(self, other): # Must define if defining __hash__
        """
        Return True if self should be treated as equal to other, else False.
        """
        return hash(self) == hash(other)

    def __lt__(self, other):# Todo: Weird to have eq be the hash and __lt__ be something else. This was quick hack because
            # heapq needed a way to break ties.
        """Return True if self has a lower baseline_dateworthiness than other."""
        return self.baseline_dateworthiness < other.baseline_dateworthiness

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
                self.traits[reputational_label] = 1.0 # todo treating these as binaries for now. E.g. a place is either 100% "fast food" or 0%.

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
        
        score = self.baseline_dateworthiness # Start it at the baseline, rather than 0.0, because it ends up getting averaged with the baseline.
                                                #   If there are no taste-trait matches, we don't want that to average in as a zero and erroneously lower the 
                                                #   restaurant's final suitability score.
            # todo does this logic hold up? Both mathematically and business-wise?
        datapoints = 0
        for trait in self.traits:
            if trait in user.taste_names():
                datapoints += 1
                score += self.traits[trait][0] * user.taste_strength(trait) # user.tastes[trait][0] is the actual score, [1] is the datapoints counter
        if datapoints: # Don't divide by zero
            score /= datapoints # Divide the score by the number of data points to scale it back to -1.0 to 1.0.
                                # Todo check the math and business logic on this...
        
        score = (2 * score + self.baseline_dateworthiness) / 3
                            # Current formula: final_score = (2*u + b) / 3, where "u" is unique user tastes match and "b" is baseline dateworthiness.
                            #   I.e., individualized user tastes count for twice as much as the baseline dateworthiness. 

                            # Todo: Goal is to weight user tastes data heavily if we have it, but otherwise defer to the baseline dateworthiness. Make
                            #   sure the formula here does that. 

                            # Todo: What about weighting the opposite way 2:1 baseline:score?
                            #   Or: Weight ethnic-cuisine keywords lower, to avoid weird biased suggestions for users' whose ethnicity matches a cuisine genre

        return round(score, DATESPOT_SCORE_DECIMAL_PLACES)
    
    def serialize(self) -> dict:
        """Return data about this object that should be stored."""
        return {
            "name": self.name,
            "location": self.location,
            "traits": self.traits,
            "price_range": self.price_range,
            "hours": self.hours
        }