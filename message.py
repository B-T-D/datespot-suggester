"""
Data and algorithms relevant to ascertaining user tastes and preferences based on natural-language user chat messages.
"""

from app_object_type import DatespotAppType

import nltk
from vaderSentiment import vaderSentiment as vs
import bisect

import user

TASTES_KEYWORDS = "tastes_keywords.txt"
# Todo: Needs more menu item keywords. Ideally, find a list of menu items at NYC restaurants sorted by how common they are.
    # Fast food so not super helpful: https://www.foodnetwork.com/restaurants/photos/most-popular-dish-at-americas-top-chain-restaurants 
    # Decent starting point for specific dishes and food words: https://ny.eater.com/maps/new-york-iconic-dishes

# Todo: Specific restaurant names ("I hate Terrezano's")
    # Todo: Where to get a list of them? Dynamically based on user-chat mentions or known locations of actual completed dates?
    # Todo: How differently than a normal keyword should they be handled?

SENTIMENT_DECIMAL_PLACES = 4 # todo this should be an EV or a constant in an ABC shared by Review, Message, and any other
                                #   code that calls VSA methods that return floats.

# Todo: Might want an external caller to be able to instantiate a Chat without creating messages.
#   If e.g. this morphs into an API that is "send in people and their chat, get back suggestions"

class Message(metaclass=DatespotAppType):

    def __init__(self, time_sent: float, sender: user.User, chat_id: str, text: str):
        """

        Args:
            time_sent (float): UNIX timestamp of the time the message was sent
            sender (user.User): User model-object instance
            chat_id (str): Chat ID of the Chat to which this message belongs
            text (str): Text of the message
        """
        self.time_sent = time_sent
        self.sender  = sender
        self.chat_id = chat_id
        self.text = text

        self.id = self._id()

        self._tastes_keywords = [] 

        with open(TASTES_KEYWORDS, 'r') as fobj:
            for line in fobj.readlines():
                self._tastes_keywords.append(line.rstrip()) # strip newline character from right
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
        return hash(str(self.time_sent) + self.sender.id)
    
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
            "sender_id": self.sender.id, # access the public id attribute of the User object
            "chat_id": self.chat_id,
            "text": self.text,
            "sentiment": self.sentiment_avg
        }
    
    def _tokenize(self):
        """Tokenize the Message's text into individual sentences and store array of sentences in the private instance-variable."""
        self._sentences = nltk.tokenize.sent_tokenize(self.text)

    def _bsearch_taste_keywords(self, word: str):
        # Todo: Every element in this list is guaranteed to be unique. Can we improve performance meaningfully by exploiting that constraint?
        # todo placeholder, not implemented. Just returning the linear search for now

        # Python standard lib bisect implements the core work in C, under the hood. https://github.com/python/cpython/blob/3.9/Lib/bisect.py
        #   No DIY pure-Python implementation will come close to performing faster. If we're running the Python interpreter anyway, best performance
        #   presumably comes from using bisect.

        i = bisect.bisect_left(self._tastes_keywords, word) # returns the index that would be immediately to the left of the first occurrence of word,
        return (i < len(self._tastes_keywords) - 1) and (self._tastes_keywords[i] == word) # First condition is to check against running past the end 

        # Todo: Add some kind of dev-mode functools decorators that logs to file how long each query takes?

    # Todo this can get much more sophisticated.
        # Todo e.g. "Sichuan" should also map to "Chinese"

    def _analyze_sentiment(self):
        """Compute the mean sentiment of the Message's sentences."""
        self._tokenize() # populate the sentences array
        sentiments_sum = 0 # sum of vaderSentiment SentimentIntensityAnalyzer "compound" scores
        analyzer = vs.SentimentIntensityAnalyzer()
        for sentence in self._sentences:
            sentence_sentiment = analyzer.polarity_scores(sentence)["compound"]
            sentiments_sum += sentence_sentiment
            for word in sentence.split(): # todo time complexity needlessly bad, VSA already made one pass. Subclass VSA into a custom MessageAnalyzer and change just the one method
                                    #     by making it also check for the keywords. 
                    # todo implement binary search
                word = word.lower().strip() # todo refactor this preprocessing to a helper
                while not word[-1].isalpha(): # strip ending punctuation
                    word = word[:-1]
                # Todo should we search character-wise to deal with plurals? Or always strip "s" from plurals?
                if self._bsearch_taste_keywords(word):
                    self.sender.update_tastes(taste = word, strength = sentence_sentiment) # Todo improve the business logic. Right now, this merely treats the sentiment of the 
                                                                            # sentence in which the word appeared as the user's sentiment toward that taste.

                     # todo update the sender user object literal's tastes data. MessageModelInterface is responsible for writing the changes to both the 
                        #   message data and the user data.
        self._sentiment_avg = round(sentiments_sum / len(self._sentences), SENTIMENT_DECIMAL_PLACES)
        return self._sentiment_avg

    # Todo consider an ABC for the text-based objects--reviews and messages. Lot of reusable operations. 