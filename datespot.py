from app_object_type import DatespotAppType


##### DB schema #####

"""

    restaurant pk   | name  | location coordinates  | traits (cuisines, etc. to match with user likes/dislikes) | budget bucket $ to $$$$   | hours (table of weekly hours)
    -------------------------------------------------------------------------------------------------------------------------------------------------------------
                    |       |                       |                                                           |                           |

"""
#####  #####

class Datespot(metaclass=DatespotAppType):

    def __init__(self, location: tuple, name: str, traits: list, price_range: int, hours: list=[]): # todo almost all of these should be required. Instantiating code should pass them
                                                                                                                        # in from its Google/Yelp/etc. data.
        """
        Args:
            traits (List[str]): ... 
            hours (List[List[int]]): ...

        """
        assert type(location) == tuple
        # todo type hints not working for list to specify element types.
        self.location = location
        self.name = name
        # todo key is the location tuple, with a third element for a Z coordinate in case two restaurants were in same building on different floors.
        
        
        self.price_range = price_range
        self.hours = hours

        self.baseline_dateworthiness = 50 # Integer from 0 to 99
                    # todo should probably be normalized to float in [0..1] or [-1..1]
            # concept: There are some features that make a place obviously unsuitable for dates in general. You don't
            #   need sophisticated user input or AI to tell you that a McDonalds should have a lower 
            #   baseline dateworthiness.   

        self.traits = traits
        if self.traits:
            self.traits = set(self.traits)
            self._update_dateworthiness() # check if any traits affect the baseline_dateworthiness score
                # todo what's a better time/place to call this?

    def is_open_now(self, day: int, hour: int) -> bool: # simple int in [0..6] for day, [0..23] for hour, for now
        hours = locationsDB[self.id][day]
        return hours[0] <= hour <= hours[1] # if between the opening time and the closing time
    
    def _update_dateworthiness(self):
        """
        Update the location's baseline dateworthiness score based on the current traits.
        """
        trait_weights = {
            "fast food": - 25, # e.g. largish penalty for being fast food
            "lodging": -5, # e.g. slight penalty for being hotel (some nice hotel bars could have "lodging" type)
            "pizza": -10,
            "chain": -5, # todo this shouldn't stack with "unromantic chain..."
            "unromantic chain": -15, # e.g. Olive Garden, Outback Steakhouse
            "bar": 5,
            "cafe": 5
            } 
        for trait in trait_weights:
            if trait in self.traits:
                self.baseline_dateworthiness = max(0, self.baseline_dateworthiness + trait_weights[trait])


def main():

    pass

if __name__ == '__main__':
    main()