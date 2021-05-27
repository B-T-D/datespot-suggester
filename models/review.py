from models.app_object_type import DatespotAppType

import nltk
from vaderSentiment import vaderSentiment as vs

SENTIMENT_DECIMAL_PLACES = 4 # TODO this should be an EV or a constant in an ABC shared by Review, Message, and any other
                                #   code that calls VSA methods that return floats.

class Review(metaclass=DatespotAppType):

    def __init__(self, datespot_id: str, text:str):
        self.datespot_id = datespot_id
        self.text = text

        self._date_related_words = {"date", "datespot", "datenight"}

        self._sentences = [] # TODO workable to just tokenize it at init?
        self._sentiment = self._analyze_sentiment()
        self._relevance = self._analyze_relevance()
        
    
    ### Public methods ###

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return hash(self) == hash(other)
    
    def __hash__(self):
        return hash(self.text) # If the text was updated, we don't want it to hash to the same integer.
        # TODO But we care that it's an update on a prior review, rather than an entirely new review. Slightly updated
        #   review shouldn't be treated as an additional review for stats purposes.
        #   Can hash the text to check for equality without having that be "the hash" of the whole Review object...
    
    @property
    def id(self) -> str:
        return self._id()

    @property
    def sentiment(self) -> float:
        return self._sentiment

    @property
    def relevance(self) -> float:
        return self._relevance
    
    def serialize(self) -> dict:
        """Returns a dict of storage-worthy object instance data."""
        object_dict = {
            "datespot_id": self.datespot_id,
            "text": self.text,
            "sentiment": self.sentiment,
            "relevance": self.relevance
        }
        return object_dict


    ### Private methods ###

    def _id(self) -> str:
        """
        Returns this Review's id string to external caller.
        """
        hex_str = str(hex(hash(self)))
        return hex_str[2:] # strip "0x"
    
    # TODO: Isn't this module responsible for weighting the sentiment by relevance?

    def _tokenize(self):
        """
        Tokenizes the review's text into sentences; and stores array of sentences in the private instance-variable.
        """
        self._sentences = nltk.tokenize.sent_tokenize(self.text)
    
    def _analyze_sentiment(self) -> float:
        self._tokenize()
        analyzer = vs.SentimentIntensityAnalyzer()
        sentiments_sum = 0 # sum of VSA "compound" scores
        for sentence in self._sentences:
            sentiments_sum += analyzer.polarity_scores(sentence)["compound"]
        sentiments_mean = round(sentiments_sum / len(self._sentences), SENTIMENT_DECIMAL_PLACES) # VSA demo rounds to 4 decimal places
        self._sentiment = sentiments_mean
        return self._sentiment
    
    def _analyze_relevance(self) -> float: # TODO quick hello world. Better to implement something super simple than nothing.
        # TODO Quick hack version: The proportion of all words in the text that are "date", expressed as float in [0..1]
        # Tokenize should already have happened in the init order
        date_words_count = 0
        for sentence in self._sentences:
            for word in sentence.split():
                word = word.rstrip('.,;:/').lower() # TODO very hacky, will miss lots of cases. Use isletter on the first and last character
                if word in self._date_related_words:
                    date_words_count += 1
        self._relevance = round(date_words_count / len(self.text), SENTIMENT_DECIMAL_PLACES) # TODO starting point is to at least normalize it better, this will never get close to 1.0
        return self._relevance