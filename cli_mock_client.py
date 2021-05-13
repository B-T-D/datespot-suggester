import json
import random
import sys

import geo_utils
from database_api import \
    DatabaseAPI  # Database API should be the only other internal app module this mock client needs


class MockClient:

    def __init__(self, user_id: int=1):
        self.user_id = user_id
        self.current_location = None
        self.exit_commands = {"exit()", "exit"} # todo handle ctrl-c
        self.commands = {
            "status()" : "Show status in your mock client session",
            "show_data()": "Print active user's JSON"
        }
        self.user_data = {}
        self.candidate_id = None
    
    def move(self):
        """
        Simulate the user traveling. Updates current location to a random distance between 
        0 and 3000m away from prior location in a random direction.
        """
        raise NotImplementedError # todo
    
    def parse_input(self, user_input: str):
        # check for exit command:
        if user_input in self.exit_commands:
            sys.exit()
        if user_input == "help":
            self.help()
        if user_input == "status":
            self.status()
        if user_input == "show_data":
            self.show_data()
        if user_input == "next":
            self.next_candidate()
    
    def help(self):
        print(self.commands)

    def get_input(self, prompt: str=None):
        if prompt:
            print(prompt)
        user_input = input(f">>> ")
        self.parse_input(user_input)
        return user_input
    
    def show_data(self):
        """Print the user's JSON."""
        print(self.user_data)
    
    def status(self):
        print(f"Current location: {self.user_data['current_location']}")
        print(f"Cached candidates: {len(self.user_data['cached_candidates'])}")
        print(f"You swiped 'yes' on and are awaiting response from {len(self.user_data['pending_likes'])} people")

    def login(self):
        db = DatabaseAPI()
        self.user_data = json.loads(db.get_json("user", self.user_id))
        print(f"Logged in as {self.user_data['name']}, current location {self.user_data['current_location']}")

    def next_candidate(self):
        db = DatabaseAPI()
        self.candidate_id = db.get_next_candidate(self.user_id)
        candidate_json = db.get_user_json(self.candidate_id)
        print(f"candidate json =\n{candidate_json}")
        self.decide_on_candidate(candidate_json)
    
    def decide_on_candidate(self, candidate_json):
        parse_to_true = {"y", "yes", "1", "t", "true"}
        parse_to_false = {"n", "no", "0", "f", "false"}
        candidate_data = json.loads(candidate_json)
        candidate_name, candidate_location =  candidate_data["name"], candidate_data["current_location"]
        prompt = f"Match with {candidate_name}?\n\t{candidate_name} is {geo_utils.haversine(tuple(self.user_data['current_location']), tuple(candidate_location))}m away from you at {candidate_location}"
        user_response = self.get_input(prompt)
        outcome = None
        if user_response.lower() in parse_to_true:
            outcome = True
        elif user_response.lower() in parse_to_false:
            outcome = False
        else:
            print(f"Bad input")
            self.decide_on_candidate(candidate_json)
        
        if outcome is not None:
            db = DatabaseAPI()
            outcome_json = json.dumps({"outcome": outcome})
            match_created = db.post_swipe(self.user_id, self.candidate_id, outcome_json) # returns True if candidate already liked user
            if match_created:
                print(f"Matched with {candidate_name}")


    
    def simulate_other_users(self):
        """
        Simulate other mock users' prior interactions with this user--simulate 50% of those users having swiped
        on this user's profile.
        """
        pass

    def simulate_other_swipe(self, probability_yes=0.8):
        pass

        
    
    def main(self):
        """Main loop to run the interactive CLI."""
        self.login()
        while True:
            self.get_input()


def main():
    if len(sys.argv) >= 3:
        if sys.argv[1] == "--id":
            user_id = int(sys.argv[2]) # i.e. $ mock_client.py --id 908098
            client = MockClient(user_id)
            
    else:
        client = MockClient()
    client.main()

if __name__ == "__main__":
    main()
