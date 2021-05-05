

# temporary simple mockup of locations DB
locationsDB = {}

##### DB schema #####

"""

    restaurant pk   | name  | location coordinates  | traits (cuisines, etc. to match with user likes/dislikes) | budget bucket $ to $$$$   | hours (table of weekly hours)
    -------------------------------------------------------------------------------------------------------------------------------------------------------------
                    |       |                       |                                                           |                           |

"""
#####  #####

class Datespot:

    def __init__(self, name: str, location: tuple, traits: list, price_range: int, hours: list): # todo almost all of these should be required. Instantiating code should pass them
                                                                                                                        # in from its Google/Yelp/etc. data.
        """
        Args:
            traits (List[str]): ... 
            hours (List[List[int]]): ...

        """
        # todo type hints not working for list to specify element types.

        self.name = name
        self.id = hash(self.name) # todo restaurants will share a name eventually. Want it to hash to same thing for now, so external caller can access the locationsDB via the hash.
        self.location = location
        self.traits = traits
        self.price_range = price_range
        self.hours = hours

        if not self.id in locationsDB:
            locationsDB[self.id] = {} # initialize in the fake DB
            locationEntry = locationsDB[self.id]
            locationEntry["name"] = self.name
            locationEntry["location"] = self.location
            locationEntry["traits"] = self.traits
            locationEntry["price_range"] = self.price_range
            locationEntry["hours"] = self.hours
        else:
            raise NotImplementedError("uuid collision (restaurant)")
    
    def is_open_now(self, day: int, hour: int) -> bool: # simple int in [0..6] for day, [0..23] for hour, for now
        hours = locationsDB[self.id][day]
        return hours[0] <= hour <= hours[1] # if between the opening time and the closing time


        

def main():

    pass

if __name__ == '__main__':
    main()