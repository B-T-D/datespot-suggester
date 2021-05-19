from app_object_type import DatespotAppType

import nltk
from vaderSentiment import vaderSentiment as vs

SENTIMENT_DECIMAL_PLACES = 4 # todo this should be an EV or a constant in an ABC shared by Review, Message, and any other
                                #   code that calls VSA methods that return floats.

class Review(metaclass=DatespotAppType):

    def __init__(self, datespot_id: str, text:str):
        self.datespot_id = datespot_id
        self.text = text

        self.id = self._id()

        self._date_related_words = {"date", "datespot", "datenight"}

        self._sentences = [] # todo workable to just tokenize it at init?
        self._relevance = None
        self._sentiment = None
        self.sentiment = self._analyze_sentiment() # todo callers may not care about these; might only need the single-number relevance-weighted sentiment
        self.relevance = self._analyze_relevance()
    
    def __eq__(self, other):
        return hash(self) == hash(other)
    
    def __hash__(self): # Hash is the default Python hash of the full text string. An updated review shouldn't hash to same.
        return hash(self.text)
    
    def _id(self) -> str:
        """
        Return this Review's id string to external caller.
        """
        hex_str = str(hex(hash(self)))
        return hex_str[2:] # strip "0x"
    
    def _tokenize(self):
        """
        Tokenize the review's text into sentences; and store array of sentences in the private instance-variable.
        """
        self._sentences = nltk.tokenize.sent_tokenize(self.text)
    
    def _analyze_sentiment(self):
        self._tokenize()
        analyzer = vs.SentimentIntensityAnalyzer()
        sentiments_sum = 0 # sum of VSA "compound" scores
        for sentence in self._sentences:
            sentiments_sum += analyzer.polarity_scores(sentence)["compound"]
        sentiments_mean = round(sentiments_sum / len(self._sentences), 4) # VSA demo rounds to 4 decimal places
        self._sentiment = sentiments_mean
        return self._sentiment
    
    def _analyze_relevance(self): # todo quick hello world. Better to implement something super simple than nothing.
        # Todo: Quick hack version: The proportion of all words in the text that are "date", expressed as float in [0..1]
        # Tokenize should already have happened in the init order
        date_words_count = 0
        for sentence in self._sentences:
            for word in sentence.split():
                word = word.rstrip('.,;:/').lower() # todo very hacky, will miss lots of cases. Use isletter on the first and last character
                if word in self._date_related_words:
                    date_words_count += 1
        self._relevance = round(date_words_count / len(self.text), SENTIMENT_DECIMAL_PLACES) # todo starting point is to at least normalize it better, this will never get close to 1.0
        return self._relevance
    
    def serialize(self) -> dict:
        """Return a dict of storage-worthy object instance data."""
        object_dict = {
            "datespot_id": self.datespot_id,
            "text": self.text,
            "sentiment": self.sentiment,
            "relevance": self.relevance
        }
        return object_dict