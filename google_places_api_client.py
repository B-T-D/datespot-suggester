"""
Makes requests to the Google Maps Places API, parses the responses into Datespot objects, and stores them in the database.
"""

import json
import requests

import database_api
import geo_utils

### Settings and config stuff ###
import sys, os
import dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
dotenv.load_dotenv(dotenv_path)

GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")

DEBUG = True # Don't e.g. allow it to make live API requests every time unit tests run.

EXAMPLE_NS_RESPONSE = "example_gpa_response.json"  # "NS" for "Nearby Search"
EXAMPLE_NS_NEXT_PAGE_RESPONSE = "example_next_page_response.json"
EXAMPLE_NS_LAST_PAGE_RESPONSE = "example_third_page_response.json"


###

DEFAULT_NS_RADIUS = 2000  # Default number of meters to use for radius parameter in Nearby Search requests

class Client:

    # todo method that makes details requests. Need details requests to get hours.

    def __init__(self, allow_live_requests=(not DEBUG)): # default value is False if debug mode, and vice versa
        self._allow_live_requests = allow_live_requests
        self._gmp_nearby_search_base_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?key={GOOGLE_MAPS_API_KEY}" # "gmp" for "google maps places"
        self._gmp_next_page_token = None

    # todo NB the next_page_token. https://developers.google.com/maps/documentation/places/web-service/search#nearby-search-and-text-search-responses
        # You make further requests for the same results by attaching the token, until you've gotten up to 60 results total. Not clear if they count for pricing.
        # https://stackoverflow.com/questions/15692829/google-places-search-next-page-token-returns-same-results

    # todo baseline query should be
        # location = matchObj.midpoint
        # radius = matchObj.distance / 2
    # That is, imagine a circle c s/t each user's location is a point on the circle's perimeter. Query location is center of c, with query's radius equal to the c's radius.

    def _validate_location_parameter(self, location: tuple):
        valid = True

        if not isinstance(location, tuple): # Caller should send it as a tuple
            valid = False

        if not geo_utils.is_valid_lat_lon(location):
            valid = False

        if not valid:
            raise Exception(f"Bad location parameter: '{location}' with type = {type(location)}")

    def _location_tuple_to_query_param_string(self, location: tuple) -> str:
        """Converts the location tuple to a querystring in the format expected by GMP API."""
        return ''.join([str(location[0]), ',', str(location[1])])

    def _concatenate_gmp_nearby_search_querystring(self, location: tuple, **kwargs) -> str:
        """Returns the correctly formed querystring url."""

        if ("rankby" in kwargs and "radius" in kwargs):
            raise Exception(f"Query params cannot have both 'radius' and 'rankby'.")

        ## Construct url character array
        url = list(self._gmp_nearby_search_base_url)

        location_str = self._location_tuple_to_query_param_string(location)
        url.extend("&location=" + ''.join(location_str))

        if not "rankby" in kwargs: # can't have rankby and radius in same request
            radius = DEFAULT_NS_RADIUS # Default radius
            if "radius" in kwargs:
                radius = str(kwargs["radius"])
            url.extend(f"&radius={radius}")
        else:
            rankby = None
            if kwargs["rankby"].lower() in {"prominence", "distance"}: # only two valid values
                rankby = kwargs["rankby"].lower()
            else:
                raise Exception(f"Invalid Nearby Search 'rankby' parameter: '{kwargs['rankby']}'")
            url.extend(f"&rankby={rankby}")

        place_type = None # todo validate it against the list of supported types to reduce malformed requests. https://developers.google.com/maps/documentation/places/web-service/supported_types
        if "type" in kwargs:
            place_type = kwargs["type"]
        else:
            place_type = "restaurant" # default to restaurant for now
        if place_type:
            url.extend(f"&type={place_type}")

        return ''.join(url)


    def request_gmp_nearby_search(self, location: tuple, **kwargs) -> str:
        # Todo for unit testing, just have it request to a non-billable url? Or at that point is it basically unit testing the requests library?
        """
        Returns the requests.models.Response object's "text" attribute.

        Args:
            location (tuple): Pair of latitude, longitude coordinate floats.
        
        Supported **kwargs:
            radius (int): Search radius, in meters.
        """
        # todo most extensible to just support all of the query parameters listed at https://developers.google.com/maps/documentation/places/web-service/search

        # todo make sure everything is ok with the encoding Requests "guesses" is correct. https://docs.python-requests.org/en/master/user/quickstart/#make-a-request
        

        ## Validate required query params
        
        response = None

        self._validate_location_parameter(location)

        url = self._concatenate_gmp_nearby_search_querystring(location, **kwargs)
            
        if self._allow_live_requests:
            response = requests.get(url)
        else:
            print("Live requests disabled.")
        return response

class Parser:

    # todo parse Place Details responses. See Buddakan example for formatting.

    def __init__(self, response_from_file=None): # todo just have it take the response object as an arg to the constructor
        if response_from_file is None and DEBUG: # default to reading non-live JSON from files in debug mode
            self.response_from_file = True
        if self.response_from_file:
            self.response_files = [EXAMPLE_NS_RESPONSE, EXAMPLE_NS_NEXT_PAGE_RESPONSE, EXAMPLE_NS_LAST_PAGE_RESPONSE]

        self.NS_response_data = [] # Google API "Nearby Search" response data. It ends up being a list, i.e. it's an array in JS syntax.
        self.data = {}
    
    def response_to_memory(self, response: requests.Response) -> None:
        print(response.text)
        self.NS_response_data = json.loads(response.text)["results"]

    def parse(self, response_text: str=None):

        if self.response_from_file: # put all three pages of results into a single dict
            for filename in self.response_files:
                with open(filename, 'r') as fobj:
                    file_response_data = json.load(fobj)
                file_response_data = file_response_data["results"] # strip non-relevant keys
                for entry in file_response_data:
                    self.NS_response_data.append(entry) # todo weird to keep it as a list.
            return
        
        
    def _datespot_to_internal_json(self, result: dict) -> str:# todo: Messy. This is a dict as parsed elsewhere, then putting it back to string...
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
        for result in self.NS_response_data: # todo slice is debug
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

    test_location = (40.74977666604178, -73.99597469657479)

    if len(sys.argv) > 1:
        if sys.argv[1] == "--live":
            print("***Called with live mode***")
            myClient = Client(allow_live_requests=True)
        
    else:
        myClient = Client()

    myParser = Parser()
    #myParser.response_to_memory(myClient.request_gmp_nearby_search(test_location))
    myParser.parse()
    myParser.add_datespots()
    
    #print("---------")
    #print(type(myParser.NS_response_data))
    #print(myParser.NS_response_data)
    #print(len(myParser.NS_response_data))
    #print("---------")


if __name__ == '__main__':
    main()