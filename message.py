from app_object_type import DatespotAppType

import json # to read in the keywords only
import nltk
from vaderSentiment import vaderSentiment as vs

TASTES_KEYWORDS = "tastes_keywords.txt"

SENTIMENT_DECIMAL_PLACES = 4 # todo this should be an EV or a constant in an ABC shared by Review, Message, and any other
                                #   code that calls VSA methods that return floats.

# Todo: Might want an external caller to be able to instantiate a Chat without creating messages.
#   If e.g. this morphs into an API that is "send in people and their chat, get back suggestions"

class Message(metaclass=DatespotAppType):

    def __init__(self, time_sent: float, sender_id: str, chat_id: str, text: str):
        """

        Args:
            time_sent (float): UNIX timestamp of the time the message was sent
            sender_id (str): User ID of user who sent the message
            chat_id (str): Chat ID of the Chat to which this message belongs
            text (str): Text of the message
        """
        self.time_sent = time_sent
        self.sender_id  = sender_id
        self.chat_id = chat_id
        self.text = text

        self.id = self._id()

        self._tastes_keywords =  None 

        with open(TASTES_KEYWORDS, 'r') as fobj:
            self._tastes_keywords = json.load(fobj)
        assert isinstance(self._tastes_keywords, list)
        self._tastes_keywords.sort() # for binary search
            # Todo store it sorted on disk. Have a unit test that reads it from disk and confirms it's sorted.

        self._sentences = []
        self._sentimient_avg = None
        self.sentiment_avg = self._analyze_sentiment() # Sentence-wise mean sentiment from VADER
        # Todo: Better for documentation not to just have a sentiment getter method with its own docstring?

    def __eq__(self, other):
        return hash(self) == hash(other)
    
    def __hash__(self):
        """Returns the result of calling Python builtin hash() on string concatenated from timestamp and sender id."""
        return hash(str(self.time_sent) + self.sender_id)
    
    def _id(self) -> str: # Todo Very easy to put this in an ABC
        """
        Return this Message's id string.
        """
        hex_str = str(hex(hash(self)))
        return hex_str[2:] # strip "0x"
    
    def __str__(self) -> str:
        return f"{self.time_sent}:\t{self.sender_id}:\t{self.text}"

    def serialize(self) -> dict:
        """Return data about this object instance that should be stored."""
        return {
            "time_sent": self.time_sent,
            "sender_id": self.sender_id,
            "chat_id": self.chat_id,
            "text": self.text,
            "sentiment": self.sentiment_avg
        }
    
    def _tokenize(self):
        """Tokenize the Message's text into individual sentences and store array of sentences in the private instance-variable."""
        self._sentences = nltk.tokenize.sent_tokenize(self.text)
    
    def _analyze_sentiment(self):
        """Compute the mean sentiment of the Message's sentences."""
        self._tokenize() # populate the sentences array
        sentiments_sum = 0 # sum of vaderSentiment SentimentIntensityAnalyzer "compound" scores
        analyzer = vs.SentimentIntensityAnalyzer()
        for sentence in self._sentences:
            sentiments_sum += analyzer.polarity_scores(sentence)["compound"]
            for word in sentence: # todo time complexity needlessly bad, VSA already made one pass 
                    # todo implement binary search
                if word in self._tastes_keywords:
                    pass # todo update the sender user object literal's tastes data. MessageModelInterface is responsible for writing the changes to both the 
                        #   message data and the user data.
        self._sentiment_avg = round(sentiments_sum / len(self._sentences), SENTIMENT_DECIMAL_PLACES)
        return self._sentiment_avg

    # Todo consider an ABC for the text-based objects--reviews and messages. Lot of reusable operations. 