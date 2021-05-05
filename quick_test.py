from user import *
from  datespot import * 
from match import *

def main():

    # init users
    newUser0 = User("Grort")
    newUser0.likes.extend(["italian", "wine"])
    newUser0.dislikes.extend(["warehouse"])

    newUser1 = User("Grort")

    newUser2 = User("Drobb")
    newUser0.likes.extend(["pasta"])
    newUser0.dislikes.extend(["NOT FROM PIZZA HUT", "warehouse", "wine"])

    print(usersDB)

    

    # init locations
    terrezanosHours = [[14, 22], [14, 21], [14, 21], [14, 21], [14, 23], [14, 23], [14, 20]] # ints in [0..23] representing hours, for now
    terrezanosLocation = (2,2) # Terrezano's is at (x=2,y=2) in the imaginary world
    terrezanosTraits = ["italian", "wine", "pasta", "NOT FROM PIZZA HUT", "authentic", "warehouse"]
    terrezanosPriceRange = 2
    terrezanos = Datespot("Terrezano's", location=terrezanosLocation, traits=terrezanosTraits, price_range=terrezanosPriceRange, hours=terrezanosHours)

    domenicosLocation = (-3, -7)
    domenicosHours = [[8, 19], [8, 19], [8, 19], [8, 19], [8, 19], [8, 19], [10, 17]]
    domenicosTraits = ["coffee", "coffee shop", "gourmet", "americano", "knows coffee", "bricks", "burger juice"]
    domenicosPriceRange = 1
    domenicos = Datespot("Domenico's", location=domenicosLocation, traits=domenicosTraits, price_range=domenicosPriceRange, hours=domenicosHours)

    print(locationsDB)

    ###
    score_user0_terrezanos = newUser0.get_restaurant_score("Terrezano's")
    print(score_user0_terrezanos)


    # init a match between Grort0 and Drobb
    GrortDrobb = Match(newUser0, newUser2)
    print(GrortDrobb.get_joint_restaurant_score("Terrezano's"))

if __name__ == '__main__':
    main()