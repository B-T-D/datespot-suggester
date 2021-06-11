import random, json
import database_api

random.seed(1)

db = database_api.DatabaseAPI()

user_names = [
    "Akatosh",
    "Arkay",
    "Azura",
    "Boethiah",
    "Clavicus Vile",
    "Dibella",
    "Hermaeus Mora",
    "Hircine",
    "Julianos",
    "Jyggalag",
    "Kynareth",
    "Malacath",
    "Mara",
    "Mehrunes Dagon",
    "Mephala",
    "Meridia",
    "Molag Bal",
    "Namira",
    "Nocturnal",
    "Peryite",
    "Sanguine",
    "Sheogorath",
    "Stendarr",
    "Talos",
    "Vaermina",
    "Zenithar"
]

user_ids_map = {}

def random_lat_lon() -> tuple:
    """Generate a realistic random location inside the test zone."""
    test_zone_west_border = -74.0190416952495
    test_zone_east_border = -73.97929135884165
    test_zone_north_border = 40.770353116208085
    test_zone_south_border = 40.71114205989834

    return (
        random.uniform(test_zone_north_border, test_zone_south_border),
        random.uniform(test_zone_west_border, test_zone_east_border)
    )

def clear_existing_mock_data():
    users_filename = None
    with open(db._json_map_filename) as fobj:
        users_filename = json.load(fobj)["user_data"]
    
    with open(db._json_map_filename) as fobj:
        filenames_map = json.load(fobj)
    
    del filenames_map["datespot_data"]  # Skip datespots, re-fetching the helloworld live Yelp data would mean making a live API call every time the test suite runs
                        # TODO cache small stable amount of yelp data and read in from that (or have the Yelp client parse a cached Yelp API response)

    for filename in filenames_map.values():
        with open(filename, 'w') as fobj:
            json.dump({}, fobj)
            fobj.seek(0)

def populate_mock_users():
    
    for i in range(len(user_names)):
        name = user_names[i]
        user_data = {
            "name": name,
            "current_location": random_lat_lon(),
            "force_key": str(i)
        }
        args_data = {
            "object_model_name": "user",
            "object_data": user_data
        }
        user_id =  db.post_object(args_data)
        assert user_id == str(i)  # DB is supposed to return the user ID
    
def populate_matches():
    
    # Match Akatosh with each of the three next names

    akatosh = "Akatosh"
    assert akatosh == user_names[0]

    for i in range(1, 4):  # User ids are simply the string representations of the user_names indices
        match_id = db.post_object(
            {"object_model_name": "match",
            "object_data": {
                "user1_id": "0", # ID of Akatosh
                "user2_id": str(i)
            }
        })

def main():
    print(f"Populating mock data")
    clear_existing_mock_data()
    populate_mock_users()
    populate_matches()

if __name__ == "__main__":
    main()