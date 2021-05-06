

class Match:

    def __init__(self, user1, user2):
        self.user1 = user1
        self.user2 = user2
        self.midpoint = None # todo. Midpoint of a straight line between the two users' locations. 
                                # Later, nuances wrt home vs. current location, asymmetrical propensities to travel
        self.chat_logs = None # todo. Text of chats between the users, for running various restaurant-suggestor NLP algorithms on. 
    
    def get_joint_datespot_score(self, datespot):
        """
        Args:
            datespot (datespot.Datespot object): A datespot object.
        """
        score1 = self.user1.datespot_score(datespot)
        score2 = self.user2.datespot_score(datespot)
        return (score1 + score2) / 2 # simple mean score