import json

import requests
import json
import sys
import urllib # todo: Actually used separately from the "from"s?


from urllib.error import HTTPError
from urllib.parse import quote
from urllib.parse import urlencode


import sys, os, dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
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
    
    def search_businesses_near(self, location: tuple, radius: int=DEFAULT_RADIUS) -> str:
        """Return app-formatted JSON for the businesses returned by the Yelp API for these geographic criteria.
        Returns a JSON string that can be directly passed as argument to DB API's post_object() method."""
        yelp_dict = self._request_business_search(location, radius)
        datespots_json = self._format_json(yelp_dict)
        pass

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


    def _format_json(self, yelp_json_dict: dict) -> str:
        """Takes raw Yelp-formatted JSON and discards, relabels, and rearranges the data as needed to 
        create JSON string matching app's internal format."""
        # Todo: Be sure to strip everything from the questionmark onward from the URLs. They come back
        #   with weird and probably non-stable querystring stuff about "adjust creative" etc. 

        # Todo Yelp actually returns the distance (from the query lat lon) for free--do we want to make
        #   use of that? Prob doesn't make sense.

        # It starts as a dictionary with one key, "businesses", whose value is a list of nested dicts

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
                "yelp_url": business["url"]
            }
        
        print(datespot_dict)

    def _tidy_url(self, raw_yelp_url: str) -> str:
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

        print(f"url = {url}")
        print(f"url_params = {url_params}")

        response = requests.request("GET", url, headers=headers, params=url_params)
        print(f"response = \n{response}")
        print(f"response text = \n{response.text}")
        return response.json()

def main():
    test_location = (40.74655797234264, -74.00125328400289)
    myClient = YelpClient()
    myClient.search_businesses_near(test_location)

if __name__ == "__main__":
    main()
