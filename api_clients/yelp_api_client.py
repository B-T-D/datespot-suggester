import json

import requests
import json
import sys
import urllib # todo: Actually used separately from the "from"s?


from urllib.error import HTTPError
from urllib.parse import quote
from urllib.parse import urlencode


import sys, os, dotenv

parent_path = os.path.abspath(os.path.join('.'))
dotenv_path = os.path.join(parent_path, ".env")
print(f"dotenv_path = {dotenv_path}")
dotenv.load_dotenv(dotenv_path)

### API docs resources ###

# Main docs:
#   https://www.yelp.com/developers/documentation/v3/business_search

# Python examples:
#   https://github.com/Yelp/yelp-fusion/blob/master/fusion/python/sample.py

 ### ###

# Todo: Can provide lots of filters, sorts, etc. to the business search endpoint--experiment
#   esp. if the default results are bad.

YELP_API_KEY = os.environ.get("YELP_API_KEY")
DEFAULT_RADIUS = 2000 # Todo put things like this as environment variables separate from the sensitive EVs such that they're ok
                        #   to be in public repo.


class YelpClient:

    def __init__(self):
        self._api_host_path = "https://api.yelp.com"
        self._business_search_path = "/v3/businesses/search"
        self._search_limit = 50 # Max allowed is 50. 50 only counts as a single API call as of 5/20.
        # See Yelp docs and https://github.com/Yelp/yelp-fusion/blob/master/fusion/python/sample.py 
        #   for further example path if need to search for business details.

        if not YELP_API_KEY:
            raise Exception("No API key")
    
    def search_businesses_near(self, location: tuple, radius: int=DEFAULT_RADIUS) -> list: 
        """
        Return app-formatted JSON for the businesses returned by the Yelp API for these geographic criteria.
        
        Returns:

            (list[dict]): List of dictionaries, each of which contains the data for one Datespot

        """
        # Returns a Python dict, not a JSON string. This client isn't the "JSON Server", its only job is to get data from Yelp and give it back to the JSON server.
        yelp_dict = self._request_business_search(location, radius)
        datespots_json = self._format_json(yelp_dict)
        return datespots_json

    def _request_business_search(self, location: tuple, radius: int, term: str=None) -> dict: # todo: term is placeholder for extending to more elaborate yelp querystrings later
        """Makes a request to the Yelp API for this location and radius, and returns the Yelp-formatted JSON dict.
        """
        # if not term:
        #     term = "restaurants" # todo what should term default to? You can only do one, can't do bars and restaurants
        url_params = {
            "latitude": location[0],
            "longitude": location[1],
            "radius": radius,
            "categories": "restaurants,bars",
            "limit": self._search_limit
        }

        return self._request(self._api_host_path, self._business_search_path, YELP_API_KEY, url_params=url_params)


    def _format_json(self, yelp_json_dict: dict) -> list:
        """Takes raw Yelp-formatted JSON and discards, relabels, and rearranges the data as needed to 
        create JSON string matching app's internal format."""
        # Todo: Be sure to strip everything from the questionmark onward from the URLs. They come back
        #   with weird and probably non-stable querystring stuff about "adjust creative" etc. 

        # Todo Yelp actually returns the distance (from the query lat lon) for free--do we want to make
        #   use of that? Prob doesn't make sense.

        # It starts as a dictionary with one key, "businesses", whose value is a list of nested dicts

        print(f"\n\nin yelp client _format_json: yelp_json_dict = {yelp_json_dict}\n\n")

        dicts = []

        for business in yelp_json_dict["businesses"]:
            assert isinstance(business, dict)

            # can one-liner this into the dict once syntax is confirmed:
            lat = business["coordinates"]["latitude"]
            lon = business["coordinates"]["longitude"]
            location = (lat, lon)

            price_range = len(business["price"]) - 1 # count number of '$' characters, then convert to zero-indexed
            assert 0 <= price_range <= 3 # todo error handling, price range is not worth halting the whole app over


            datespot_dict = {
                "name": business["name"],
                "location": location,
                "price_range": price_range,
                "yelp_rating": business["rating"],
                "yelp_review_count": business["review_count"],
                "yelp_url": business["url"],
                "yelp_id": business["id"]
            }

            dicts.append(datespot_dict)
        
        return dicts

    def _tidy_url(self, raw_yelp_url: str) -> str:
        # Todo: Use string.find() to slice off "?" and everything after it
        pass

    def _request(self, host, path, api_key, url_params=None): # We have this general-case code from the github examples, so might as well use it.
        """

        Returns:
            (dict): The response JSON as a Python dictionary. 
        """
        url_params = url_params or {}
        url = f"{host}{quote(path.encode('utf8'))}"
        headers = {
            "Authorization": f"Bearer {YELP_API_KEY}"
        }

        response = requests.request("GET", url, headers=headers, params=url_params)
        return response.json()

def main():
    test_location = (40.74655797234264, -74.00125328400289)
    myClient = YelpClient()
    myClient.search_businesses_near(test_location)

if __name__ == "__main__":
    main()
