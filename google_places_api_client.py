"""
Makes requests to the Google Maps Places API, parses the responses into Datespot objects, and stores them in the database.
"""

import json
import database_api

### Settings and config stuff ###
import sys, os
import dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
dotenv.load_dotenv(dotenv_path)

DEBUG = True # Don't e.g. allow it to make live API requests every time unit tests run.

GOOGLE_MAPS_API_KEY = 1 

EXAMPLE_NS_RESPONSE = "example_gpa_response.json"  # "NS" for "Nearby Search"
EXAMPLE_NS_NEXT_PAGE_RESPONSE = "example_next_page_response.json"
EXAMPLE_NS_LAST_PAGE_RESPONSE = "example_third_page_response.json"

print(os.getenv("GOOGLE_MAPS_API_KEY"))

###

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
        
    def _datespot_to_internal_json(self, result: dict): # todo: Messy. This is a dict as parsed elsewhere, then putting it back to string...
        """
        Convert entry in the GM response to a JSON string in the format expected by the database API.
        """
        # todo validate result
        result_dict = {
            "location": (result["geometry"]["location"]["lat"], result["geometry"]["location"]["lng"]),
            "name": result["name"],
            "traits": result["types"],
        }
        if "price_level" in result:
            result_dict["price_level"] = result["price_level"]
        return json.dumps(result_dict)

    def add_datespots(self): # todo need to update existing ones, not overwrite. First check if the datespot is already in the DB.
                                # In theory GMAPI isn't the sole data source. Also user inputs, and maybe something like Yelp.
        db = database_api.DatabaseAPI()
        for result in self.NS_response_data[:1]: # todo slice is debug
            result_json = self._datespot_to_internal_json(result)
            db.add("datespot", result_json)


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

    if len(sys.argv) > 1:
        if sys.argv[1] == "--live":
            print("***Called with live mode***")
    

    myParser = Parser()
    myParser.parse()
    print("---------")
    print(type(myParser.NS_response_data))
    #print(myParser.NS_response_data)
    print(len(myParser.NS_response_data))
    print("---------")
    myParser.add_datespots()

if __name__ == '__main__':
    main()