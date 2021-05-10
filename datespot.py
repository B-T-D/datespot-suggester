from app_object_type import DatespotAppType

import json

BASELINE_SCORING_DATA = "datespot_baseline_scoring_data.json"

##### DB schema #####

"""

    restaurant pk   | name  | location coordinates  | traits (cuisines, etc. to match with user likes/dislikes) | budget bucket $ to $$$$$   | hours (table of weekly hours)
    -------------------------------------------------------------------------------------------------------------------------------------------------------------
                    |       |                       |                                                           |                           |

"""
#####  #####

class Datespot(metaclass=DatespotAppType):

    def __init__(self, location: tuple, name: str, traits: list, price_range: int, hours: list=[]):
        """
        Args:
            traits (List[str]): ... 
            hours (List[List[int]]): ...

        """
        assert type(location) == tuple
        self.location = location
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

        self.traits = traits
        if self.traits:
            self.traits = set(self.traits)
            self._update_dateworthiness() # check if any traits affect the baseline_dateworthiness score
                # todo call this when external caller requests a restaurant recc.
        
        # todo need these to parse in as a hash set with only one O(n) pass. Rather than one O(n) pass by 
        #   json.load(), then another by casting the list to a set.
        
        # cast each non-associative array to a hash set for faster lookup:
        for key in self.brand_reputations:
            self.brand_reputations[key] = set(self.brand_reputations[key])

    # todo: Should the "how much would X user like Y restaurant?" method be in user, or in datespot? Or in match? Or in some other model?
        # If this "baseline_dateworthiness" is a key part of an overall score, then makes some sense for datespot model to own the core 
        #   restaurant suggestor, right?

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
        for reputational_label, tagged_restaurants in self.brand_reputations:
            if self.name in tagged_restaurants:
                self.traits.add(reputational_label)

    def _update_dateworthiness(self): # 
        """
        Update the location's baseline dateworthiness score based on the current traits.
        """
        # todo some of the trait bonuses/maluses shouldn't stack. E.g. "chain" and "unromantic chain"

        # todo make sure trait_weights are correcely integrated into whatever ends up being the overall scoring scale

        for trait in self.baseline_trait_weights:
            if trait in self.traits:
                self.baseline_dateworthiness = max(0, self.baseline_dateworthiness + trait_weights[trait])

def main():

    pass

if __name__ == '__main__':
    main()