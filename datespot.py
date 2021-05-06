
##### DB schema #####

"""

    restaurant pk   | name  | location coordinates  | traits (cuisines, etc. to match with user likes/dislikes) | budget bucket $ to $$$$   | hours (table of weekly hours)
    -------------------------------------------------------------------------------------------------------------------------------------------------------------
                    |       |                       |                                                           |                           |

"""
#####  #####

class Datespot:

    def __init__(self, location: tuple, name: str, traits: list, price_range: int, hours: list): # todo almost all of these should be required. Instantiating code should pass them
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
        
        self.traits = traits
        self.price_range = price_range
        self.hours = hours
    
    def is_open_now(self, day: int, hour: int) -> bool: # simple int in [0..6] for day, [0..23] for hour, for now
        hours = locationsDB[self.id][day]
        return hours[0] <= hour <= hours[1] # if between the opening time and the closing time


def main():

    pass

if __name__ == '__main__':
    main()