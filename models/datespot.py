from models.app_object_type import DatespotAppType
import models.user as user

import json

from project_constants import *

class Datespot(metaclass=DatespotAppType):

    # TODO Plan as of 5/18 is that reviews per se aren't related to a datespot. Higher level info is extracted from the reviews--abstract traits about the 
    #   object--and those traits are related to the datespot object. We remember an aggregate knowledge of / opinion about the restaurant that we learned from 
    #   reading its reviews, we don't memorize the full text of every review we read.

    def __init__(
        self,
        datespot_id: str,
        location: tuple,
        name: str,
        traits: dict={},
        price_range: int=None, # [0..3], i.e. 4 distinct levels. 
        hours: list=[],
        yelp_url=None,
        yelp_rating: float=None,
        yelp_review_count: int=0,
        yelp_id: str=None,
        google_id: str=None):
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
        # TODO seems clunky / insufficiently intuitive way to handle the discrete vs. continuous traits. 
        self.id = datespot_id
        assert isinstance(location, tuple)
        assert isinstance(traits, dict)
        self._location = ( # External code shouldn't mess with this, e.g. e.g. inadvertently casting to string or changing number of decimal places
            round(location[0], LAT_LON_DECIMAL_PLACES),
            round(location[1], LAT_LON_DECIMAL_PLACES)
            )
        self.location = self._location
        self.name = name
        
        self.price_range = price_range # Todo reconcile google-yelp if still using google--google is [0..4], yelp is [0..3] apparently
        self.hours = hours
        
        self.yelp_url = yelp_url # TODO TBD if this is best way to cache a mapping of yelp urls to restaurants
                                    # Rationale: We can get 50 urls for the price of 1 yelp API call by caching at the time 
                                    #   of the nearby businesses search; versus needing 1 call for each restaurant if querying the 
                                    #   Yelp API for the url of a specific restaurant.
        self.yelp_rating = yelp_rating # todo: This is very relevant to baseline dateworthiness--incorporate into formulae
        self.yelp_review_count = yelp_review_count # number of yelp reviews

        self.yelp_id = yelp_id
        self.google_id = google_id


        with open(BASELINE_SCORING_DATA) as fobj: # TODO each json.load(fobj) call is another pass through the entire json file, right?
                                                    # Is there a smarter way to ensure a single pass than reading all the json into a 
                                                    #   dict and then unpacking that dict?
            all_json = json.load(fobj)
            self.baseline_trait_weights = all_json["trait_weights"]
            self.brand_reputations = all_json["brand_reputations"]

        self.baseline_dateworthiness = 0.0
        self.traits = traits  
        
        for key in self.brand_reputations: # cast each non-associative array to a hash set for faster lookup
            self.brand_reputations[key] = set(self.brand_reputations[key])

    ### Public methods ###

    def __eq__(self, other):
        """
        Return True if self should be treated as equal to other, else False.
        """
        if type(self) != type(other):
            return False
        return hash(self) == hash(other)

    def __lt__(self, other):# TODO Weird to have eq be the hash and __lt__ be something else. This was quick hack because
            # heapq needed a way to break ties.
        """Return True if self has a lower baseline_dateworthiness than other."""
        return self.baseline_dateworthiness < other.baseline_dateworthiness

    def __hash__(self): # TODO Not sure how sound the logic is here. Should test lots of cases to support that same restaurant hashes to same thing.
        rounded_lat_lon = (round(self.location[0], 4), round(self.location[1])) # Rationale for rounding is to reduce chances of e.g. the 7th decimal value
                                                                                #   changing and causing same restaurant to hash differently.
        string_to_hash = f"{self.name} {rounded_lat_lon}"
        return hash(string_to_hash)

    def score(self, user: user.User) -> float:
        # Externally callable wrapper
        return self._score(user)
    
    def serialize(self) -> dict:
        """Return data about this object that should be stored."""
        return {
            "datespot_id": self.id,
            "name": self.name,
            "location": self.location,
            "traits": self.traits,
            "price_range": self.price_range,
            "hours": self.hours,
            "yelp_rating": self.yelp_rating,
            "yelp_review_count": self.yelp_review_count,
            "yelp_url": self.yelp_url,
            "yelp_id": self.yelp_id,
            "google_id": self.google_id
        }

    ### Private Methods ### 

    def _id(self) -> str:
        """
        Return this Datespot's id key to an external caller.
        """
        hex_str = str(hex(hash(self))) 
        return hex_str[2:] # strip the "0x"
    
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
        # TODO some of the trait bonuses/maluses shouldn't stack. E.g. "chain" and "unromantic chain"

        # TODO make sure trait_weights are correcely integrated into whatever ends up being the overall scoring scale

        for trait in self.baseline_trait_weights:
            if trait in self.traits:
                self.baseline_dateworthiness = max(0, self.baseline_dateworthiness + self.baseline_trait_weights[trait])

    def _score(self, user:user.User) -> float:
        # Make sure all brand-related traits have been applied before updating the baseline dateworthiness.
        self._apply_brand_reputations() # These probably never get called more than once in the lifetime of a single Datespot instance.
        self._update_dateworthiness() #  ...In practice, Datespot objects will be instantiated solely so that this method can be called. Then they're garbage-collected.
        
        score = self.baseline_dateworthiness # Start it at the baseline, rather than 0.0, because it ends up getting averaged with the baseline.
                                                #   If there are no taste-trait matches, we don't want that to average in as a zero and erroneously lower the 
                                                #   restaurant's final suitability score.
            # TODO does this logic hold up? Both mathematically and business-wise?
        datapoints = 0
        for trait in self.traits:
            if trait in user.taste_names():
                datapoints += 1
                score += self.traits[trait][0] * user.taste_strength(trait) # user.tastes[trait][0] is the actual score, [1] is the datapoints counter
        if datapoints: # Don't divide by zero
            score /= datapoints # Divide the score by the number of data points to scale it back to -1.0 to 1.0.
                                # TODO check the math and business logic on this...
        
        score = (2 * score + self.baseline_dateworthiness) / 3
                            # Current formula: final_score = (2*u + b) / 3, where "u" is unique user tastes match and "b" is baseline dateworthiness.
                            #   I.e., individualized user tastes count for twice as much as the baseline dateworthiness. 

                            # TODO Goal is to weight user tastes data heavily if we have it, but otherwise defer to the baseline dateworthiness. Make
                            #   sure the formula here does that. 

                            # TODO What about weighting the opposite way 2:1 baseline:score?
                            #   Or: Weight ethnic-cuisine keywords lower, to avoid weird biased suggestions for users' whose ethnicity matches a cuisine genre

        return round(score, DATESPOT_SCORE_DECIMAL_PLACES)