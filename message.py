from app_object_type import DatespotAppType

import nltk
from vaderSentiment import vaderSentiment as vs

SENTIMENT_DECIMAL_PLACES = 4 # todo this should be an EV or a constant in an ABC shared by Review, Message, and any other
                                #   code that calls VSA methods that return floats.

class Message(metaclass=DatespotAppType):

    def __init__(self, time_sent: float, sender_id: str, recipient_ids: list, text: str):
        """

        Args:
            timestamp (float): UNIX timestamp of the time the message was sent
            sender_id (str): User ID of user who sent the message
            recipient_ids (list[str]): List of message recipients' user ID strings
            text (str): Text of the message
        """
        self.time_sent = time_sent
        self.sender_id  = sender_id
        self.recipient_ids = recipient_ids
        self.text = text

        self.id = self._id()
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
        Return this Message's id string to external callser.
        """
        hex_str = str(hex(hash(self)))
        return hex_str[2:] # strip "0x"

    def serialize(self) -> dict:
        """Return data about this object instance that should be stored, as a native Python dictionary."""
        return {
            "time_sent": self.timestamp,
            "sender": self.sender_id,
            "recipients": self.recipient_ids,
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
        self._sentiment_avg = round(sentiments_sum / len(self._sentences), SENTIMENT_DECIMAL_PLACES)
        return self._sentiment_avg

    # Todo consider an ABC for the text-based objects--reviews and messages. Lot of reusable operations. 