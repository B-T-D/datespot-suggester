

class Match:

    def __init__(self, user1, user2):
        self.user1 = user1
        self.user2 = user2
    
    def get_joint_restaurant_score(self, restaurant_name: str):
        score1 = self.user1.get_restaurant_score(restaurant_name)
        score2 = self.user2.get_restaurant_score(restaurant_name)
        return (score1 + score2) / 2 # simple mean score