

class Match:

    def __init__(self, user1, user2):
        self.user1 = user1
        self.user2 = user2
    
    def get_joint_datespot_score(self, datespot):
        """
        Args:
            datespot (datespot.Datespot object): A datespot object.
        """
        score1 = self.user1.datespot_score(datespot)
        score2 = self.user2.datespot_score(datespot)
        return (score1 + score2) / 2 # simple mean score