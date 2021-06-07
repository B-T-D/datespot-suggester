import random, json


import database_api

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


def main():
    
    
    db = database_api.DatabaseAPI()


    # Clear the old file
    users_filename = None
    with open(db._json_map_filename) as fobj:
        users_filename = json.load(fobj)["user_data"]
    
    with open(users_filename, mode="w") as fobj:
        json.dump({}, fobj)


    random.seed(1)
    names = [
        "Akatosh",
        "Arkay",
        "Dibella",
        "Julianos",
        "Kynareth",
        "Mara",
        "Stendarr",
        "Talos",
        "Zenithar",
        "Azura",
        "Boethiah",
        "Clavicus Vile",
        "Hermaeus Mora",
        "Hircine",
        "Jyggalag",
        "Malacath",
        "Mehrunes Dagon",
        "Mephala",
        "Meridia",
        "Molag Bal",
        "Namira",
        "Nocturnal",
        "Peryite",
        "Sanguine",
        "Sheogorath",
        "Vaermina",
    ]

    for i in range(len(names)):
        json_data = {
            "name": names[i],
            "current_location": random_lat_lon(),
            "force_key": str(i)
        }
        json_arg = json.dumps({
            "object_model_name": "user",
            "json_data": json_data
        })
        db.post_object(json_arg)


if __name__ == "__main__":
    main()