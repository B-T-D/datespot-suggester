from app_object_type import DatespotAppType

class Match(metaclass=DatespotAppType):

    def __init__(self, user1, user2):
        """
        Args:
            user1 (UserObj): A user object.
            user2 (UserObj): A different user object.
        """
        self.user1 = user1
        self.user2 = user2
        self.midpoint = None # todo. Midpoint of a straight line between the two users' locations. 
                                # Later, nuances wrt home vs. current location, asymmetrical propensities to travel
        self.chat_logs = None # todo. Text of chats between the users, for running various restaurant-suggestor NLP algorithms on. 
                                # todo is this needed here or can it just be in users? Chats between
                                # those two specific users should be considered more heavily right?
                                #   E.g. they chatted about how they both love Terrezano's.
    
    def get_joint_datespot_score(self, datespot):
        """
        Args:
            datespot (datespot.Datespot object): A datespot object.
        """
        score1 = self.user1.datespot_score(datespot)
        score2 = self.user2.datespot_score(datespot)
        return (score1 + score2) / 2 # simple mean score