"""
Makes requests to the Google Maps Places API and parses responses into datespot objects stored as JSON.
"""

import json
from datespot_api import DatespotAPI

DEBUG = True # Don't e.g. allow it to make live API requests every time unit tests run.
EXAMPLE_NS_RESPONSE = "example_gpa_response.json"  # "NS" for "Nearby Search"
EXAMPLE_NS_NEXT_PAGE_RESPONSE = "example_next_page_response.json"
EXAMPLE_NS_LAST_PAGE_RESPONSE = "example_third_page_response.json"

class Client:

    def __init__(self):
        self._allow_live_requests = not DEBUG

    # todo NB the next_page_token. https://developers.google.com/maps/documentation/places/web-service/search#nearby-search-and-text-search-responses
        # You make further requests for the same results by attaching the token, until you've gotten up to 60 results total. Not clear if they count for pricing.
        # https://stackoverflow.com/questions/15692829/google-places-search-next-page-token-returns-same-results

    # todo baseline query should be
        # location = matchObj.midpoint
        # radius = matchObj.distance / 2
    # That is, imagine a circle c s/t each user's location is a point on the circle's perimeter. Query location is center of c, with query's radius equal to the c's radius.

class Parser:

    def __init__(self, response_from_file=None):
        if response_from_file is None and DEBUG: # default to reading non-live JSON from files in debug mode
            self.response_from_file = True
        if self.response_from_file:
            self.response_files = [EXAMPLE_NS_RESPONSE, EXAMPLE_NS_NEXT_PAGE_RESPONSE, EXAMPLE_NS_LAST_PAGE_RESPONSE]

        self.NS_response_data = [] # Google API "Nearby Search" response data. It ends up being a list, i.e. it's an array in JS syntax.
        self.data = {}
        self.known_fast_foods = {  # todo these sets should live in the main Datespots model.
            "Chipotle Mexican Grill",
            "Subway", # todo this might catch transportation related stuff, not all Datespots are restaurants
            "Arby's",
            "Chick-fil-A",
            "Popeyes Louisiana Kitchen",
        }
        self.known_unromantic_chains = {
            "Outback Steakhouse",
            "Olive Garden Italian Restaurant" 
        }
        self.known_anti_lgbt = {
            "Chick-fil-A",
        }
    
    def parse(self):

        if self.response_from_file: # put all three pages of results into a single dict
            for filename in self.response_files:
                with open(filename, 'r') as fobj:
                    file_response_data = json.load(fobj)
                file_response_data = file_response_data["results"] # strip non-relevant keys
                for entry in file_response_data:
                    self.NS_response_data.append(entry) # todo weird to keep it as a list.
        #self.NS_response_data = self.NS_response_data["results"] # strip non-relevant keys
        
    def add_datespot(self): # todo need to update existing ones, not overwrite. First check if the datespot is already in the DB.
                                # In theory GMAPI isn't the sole data source. Also user inputs, and maybe something like Yelp.
        datespot_api = DatespotAPI()
        for result in self.NS_response_data:
            print(result)
            location_result = result["geometry"]["location"]
            location = (location_result["lat"], location_result["lng"]) 
            traits = result["types"]
            name = result["name"]
            traits.extend(self._traits_from_name(name, traits))
            
            price_range = None
            if "price_level" in result:
                print(f"result {name} had a price level")
                price_range = result["price_level"]
            else:
                print(f"result {name} didn't have a price level")
            
            datespotKey = datespot_api.create_datespot(
                location=location,
                name=name,
                traits=traits,
                price_range=price_range,
            )
            datespotObj = datespot_api.load_datespot(datespotKey)
            print(f"datespotObj type = {type(datespotObj)}\n{datespotObj}")

    def _traits_from_name(self, name: str, traits: list) -> list:
        additional_traits = []

        # todo the parser shouldn't be editorializing like this. No reason this has to be done here, instead of somewhere else down the line.
            # Makes more sense for this to live in the main Datespot model. 

        # todo rationalize handling of casing. Don't want to be too tied to the exact names and casings Google happens to use (e.g. "Olive Garden Italian Restaurant")
        # todo see if can detect sufficient spanish words to confidently tag as Mexican genre
        if name in self.known_fast_foods: # some fast foods don't have that as their google maps "type"
            additional_traits.append("fast food")
        if name in self.known_unromantic_chains:
            additional_traits.append("unromantic chain")
        if "steakhouse" in name.lower():  # todo hardcoded ones like these aren't good enough for general case where the Datespot might not be a restaurant
            additional_traits.append("steak")
            additional_traits.append("steakhouse")
        if "thai" in name.lower():
            additional_traits.append("thai")
        return additional_traits


def main():
    myParser = Parser()
    myParser.parse()
    print(type(myParser.NS_response_data))
    #print(myParser.NS_response_data)
    print(len(myParser.NS_response_data))
    print("---------")
    myParser.add_datespot()

if __name__ == '__main__':
    main()