"""
Makes requests to the Google Maps Places API and parses responses into datespot objects stored as JSON.
"""

import json
from datespot_api import DatespotAPI

DEBUG = True # Don't e.g. allow it to make live API requests every time unit tests run.
EXAMPLE_NS_RESPONSE = "example_gpa_response.json"

class Client:

    def __init__(self):
        pass

    # todo NB the next_page_token. https://developers.google.com/maps/documentation/places/web-service/search#nearby-search-and-text-search-responses
        # You make further requests for the same results by attaching the token, until you've gotten up to 60 results total. Not clear if they count for pricing.
        # https://stackoverflow.com/questions/15692829/google-places-search-next-page-token-returns-same-results

class Parser:

    def __init__(self):
        self.NS_response_data = {} # Google API "Nearby Search" response data.
        self.data = {}
    
    def parse(self):
        with open(EXAMPLE_NS_RESPONSE, 'r') as fobj:
            self.NS_response_data = json.load(fobj)
            fobj.seek(0)
        self.NS_response_data = self.NS_response_data["results"] # strip non-relevant keys
        
    def add_datespot(self): # todo need to update existing ones, not overwrite. First check if the datespot is already in the DB.
        datespot_api = DatespotAPI()
        for i in range(1):
            result = self.NS_response_data[i]
            print(result)
            location_result = result["geometry"]["location"]
            location = (location_result["lat"], location_result["lng"]) 
            name = result["name"]
            traits = result["types"]
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