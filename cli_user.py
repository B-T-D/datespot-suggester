"""Command line interface for creating mock users."""

import database_api
import json
import sys

def cli_update_user(user_id: int):
     raise NotImplementedError

def cli_create_user():

    default_location = (40.7591880127792, -73.99438682889884)
    user_name = input("Enter user name\n>>>")
    print(f"Default location: {default_location}")
    location = default_location

    json_data = json.dumps({
        "name": user_name,
        "current_location": location
    })

    print(f"json is {json_data}")

    print(f"Creating user {user_name} at location {location}")

    db = database_api.DatabaseAPI()
    db.add("user", json_data)

def main():

    if len(sys.argv) > 1:
        if sys.argv[1] == "create":
            cli_create_user()
        elif sys.argv[1] == "update":
            if not sys.argv[2]:
                raise Exception("Need id of which user to update")
            user_id = int(sys.argv[2])
            cli_update_user(user_id)

if __name__ == '__main__':
    main()