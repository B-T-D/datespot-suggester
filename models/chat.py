from app_object_type import DatespotAppType

from models.message import Message

# todo... this one may not need VSA and NLTK, if all it does it math on the sentiment
#   numbers of the Messages composing the Chat.

# Todo should probably store one of Chats and Messages, not both. Chats could be stored with just a 
#   list of the message ids. 

SENTIMENT_DECIMAL_PLACES = 4 # todo this should be an EV or a constant in an ABC shared by Review, Message, and any other
                                #   code that calls VSA methods that return floats.

class Chat(metaclass=DatespotAppType):

    def __init__(self, start_time: float, participant_ids: list, messages: list=[]):
        """
        Args:
            start_time (float): UNIX timestamp of the time the chat began.
            participant_ids (list[str]): List of user ID strings for the users participating in the chat.
            messages (list[Message]) : List of Message object literals. Will be empty unless instantiating an object from storage.
        """
        self.start_time = start_time
        self.participant_ids = participant_ids
        self.messages = messages
        self.id = self._id()

        self._sentiment_avg = None
     
        # self.sentiment_avg = self._average_sentiment() # Todo Defining the public variable to equal the internal method's return got too complicated in unit testing with the mock DB.
        self.sentiment_std_dev = None # Todo, implement...standard deviation of the sentiment (variance across messages)
    
    def __eq__(self, other):
        return hash(self) == hash(other)
    
    def __hash__(self):
        """Returns the result of calling Python builtin hash() on the start time.""" 
        # Start time will never change. Even if messages are deleted, participants join and leave, the start time can stay the same. 
        return hash(self.start_time)
    
    def _id(self) -> str:
        """
        Return this Chat's id string.
        """
        hex_str = str(hex(hash(self)))
        return hex_str[2:] # strip "0x"
    
    def _sort_messages_by_timestamp(self) -> None:
        """Sort the messages data in ascending order of timestamp (i.e. earliest first)."""
        # todo not sure how much sense this makes for performance. They should be going into the list in order anyway. 
        pass

    def serialize(self) -> dict:
        """Return relevant data for storage, as a native Python dictionary."""
        # sort the messages by timestamp.
        self.messages.sort(key = lambda message : message.time_sent)
        message_ids = [message.id for message in self.messages] # only store the IDs, don't redundantly store the full text etc. 
        return {
            "start_time": self.start_time,
            "participant_ids": self.participant_ids,
            "messages": message_ids
        }

    def _average_sentiment(self):
        """Compute the mean sentiment of the Chat's component Messages.""" # Read in the JSON and average the cached values.
        if not self.messages:
            return # todo not sure best thing to return 
        sentiments_sum = 0
        for message in self.messages:
            sentiments_sum += message.sentiment
        self._sentiment_avg = round(sentiments_sum / len(self.messages), SENTIMENT_DECIMAL_PLACES)
        return self._sentiment_avg
    
    def sentiment(self):
        self._average_sentiment()
        return self._sentiment_avg