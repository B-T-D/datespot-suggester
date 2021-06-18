[![Build Status](https://travis-ci.com/B-T-D/datespot.svg?branch=main)](https://travis-ci.com/B-T-D/datespot)

# Datespot suggester
Conceptual prototype for a dating app API that analyzes user chat messages, geolocation data, and publicly available information about potential date locations to intelligently generate date location suggestions.

- [Background and inspiration](#background-and-inspiration)
- [Implementation overview](#implementation-overview)
- [Problems, challenges, and issues](#problems-challenges-and-issues)
- [Roadmap for further work](#roadmap-for-further-work)

## Background and inspiration
When trying to pick a restaurant, I often feel overwhelmed by choices--especially in densely populated or unfamiliar areas. I typically select a place by reading about potential restaurants online, usually from Google Maps and Yelp. I've often imagined automating this process: What if I could programatically read thousands of reviews and profiles for dozens of nearby restaurants, and choose one based on my personal tastes and preferences?

Talking with friends about this choice-overload issue, I realized it could be especially problematic in a dating context. When picking a place for a first date, the people going on the date want to make a good first impression on each other, and want a certain type of environment in the establishment, but don't know each other's preferences well, and may want an establishment in an unfamiliar location. This led to the idea of a dating app that would use natural-language processing to learn about its users and the potential date locations in their area, and use that data to suggest date locations to the app's users.

## Implementation overview
The dating app I imagined would perform three basic tasks:

1. **Get text data about businesses and users.** To get business data, I looked to the sources I use solving this problem non-programatically: Google and Yelp. In exploring each of their available APIs, I quickly found both could programatically provide the same data I was accustomed to: Searching for businesses in a certain geographic vicinity, and gathering information about those businesses.

    For data about user preferences, I chose to rely solely on their chats. I wanted this project to focus on natural language processing, and modern dating apps   have an in-app chat feature. I also felt a user-preferences questionnaire would be undesirable from a hypothetical business standpoint: Network effects are critical to a dating app, and I assume asking users to complete a questionnaire about their dining preferences on signup would slow down user acquisition.

2. **Analyze text data.** To analyze this text data--business reviews, and user messages--I implemented the system's core logic in Python, because the Python ecosystem has so many good NLP resources. I initially assumed I'd need to train custom machine-learning models or develop custom non-ML NLP algorithms. But I quickly found the [VADER Sentiment Analysis](https://github.com/cjhutto/vaderSentiment) tool and the [Natural Language Toolkit](https://www.nltk.org/) were quite effective as-is, and so leveraged these to speed up my initial proof-of-concept.

3. **Transmit suggestions.** To process requests from outside callers, I used NodeJS and Express to create an HTTP server, and a custom Python listener process to manage communication between the HTTP server layer and the underlying model-layer algorithms. I wanted to use a lightweight HTTP framework rather than e.g. Django, and felt that Node would be more fully featured and extensible than Flask. To implement the chat functionality, I would use a separate WebSocket chat server that forwarded data to the HTTP server for analysis without delaying message delivery while waiting for expensive NLP algorithms to finish running.

Beyond these, it would also need the standard dating-app functionalities. I based those parts of the project primarily on Tinder, since Tinder's binary approach (users decide yes or no on each other, one at a time) seemed like logic that I could implement quickly. 

## Problems, challenges, and issues
  
### Efficient lookup of keyword strings: binary search vs. hash tables
  As part of analyzing user chats to learn restaurant preferences, I wanted to look up each word in a chat message in a list of known relevant keywords--e.g. "Thai", "vegetarian", "coffee"--and then use the net sentiment of the sentence containing the keyword as a proxy for the user's feelings toward that keyword ("I love Thai food" boosts Thai restaurants in that user's suggestions). In a real dating app, each of the thousands of users would send dozens or hundreds of messages daily, so the performance of the keyword lookup would be important. 
  
  My first instinct was to store the keywords in a hash set, for average-case O(1) time lookup. But the Python JSON encode/decode library doesn't decode to a Python set object by default; doing so would require creating a custom encoder (https://stackoverflow.com/questions/8230315/how-to-json-serialize-sets). So until I had time to write the custom encoder, I decided to store the keyword strings in a lexicographically sorted Python list (i.e. array) and look them up with binary search in worst-case O(log(n)) time. I expected this data to be quite static (i.e. not gaining new keywords very often), so I was not concerned about the time complexity of sorting the array or inserting new elements.

### Avoiding redundant iteration over message texts
  
  The vaderSentiment analyzer iterates over each character of the text it analyzes, but does not readily support certain tasks, such as matching strings against keywords relevant to a user's restaurant preferences. If the algorithms that analyze each message run the vaderSentiment analyzer once on the text to compute the sentiment, and then iterate over each word to check for keywords, that's a lot of duplicative work--two passes over the string when a single pass could perform both analyses.
  
  This is an open todo. I plan to solve it by forking the vaderSentiment repo and customizing the relevant methods to have them check for keywords in the same loop as they analyze the sentiment.

### Inter-process communication between Python and NodeJS
  I wanted to implement the REST web API using NodeJS rather than Python. I felt node was a better choice than Python web frameworks like Flask and Django because this project will eventually include a chat functionality, and Node performs better than Python in a context that requires lots of concurrency. 
  This raised the issue of how best to have the Node HTTP server send JSON to and receive JSON from the Python database/model layer. In my initial implementation, I chose to do this with Linux named pipes.

### Pre-computing suggestions
  The date location suggestor requires lots of computationally intensive text processing. I expect that even when decently optimized, the system will be far too slow if it only begins computing suggestions the moment the users request one. To solve this, I plan to compute best-guess suggestions at some appropriate intervals between the moment two users match with each other and the moment they actually request a date location suggestion, and then cache that suggestions heap.
  
### Making NLTK data portable
  NLTK [provides many collections of data](https://www.nltk.org/data.html) that aren't installed by default. VADER Sentiment relies on one of these for its tokenizers. When I configured this repostiory's TravisCI, making the NLTK data consistently available in the Travis virtual machine's environment turned out to be quite challenging. I realized this same issue would come up when the API is deployed--the cloud server instance's VM will also need the NLTK data. To make TravisCI work, I first tried scripting the VM to download the data programatically, using the [NLTK downloader's command line interface](https://www.nltk.org/data.html#command-line-installation). But the downloader had its own dependencies, and getting the downloader to run on the Travis VM seemed to require too many hacky workarounds. So I concluded that the best quick solution was to put the needed NLTK data (i.e., only the tokenizers) in the main repository, and use a single shell command to make the VM copy the data to a directory matching one of the paths where NLTK looks for the data.

## Roadmap for further work
This remains very much a work in progress. The ultimate end state would be a fully featured, production-grade, deployed mobile app using this API as its backend. I will see how far toward that I can get within the limits of a non-commercial portfolio project.

### Currently working on
- [ ] Stable server able to be deployed via Heroku or AWS EC2
- [ ] SQL. Replace ad hoc JSON-based system with Postgres database server
- [ ] Allow users to "swipe" on restaurant suggestions in the same way as they swipe on match candidates
- [ ] Dynamically pre-compute suggestions at intelligently chosen intervals, to reduce latency at the time users request suggestions
- [ ] Expand lexicons of dining-preference keywords
- [ ] Detect menu-item and cuisine-genre keywords in reviews

### Planned / proposed
- [ ] Secondary, ordered suggestions--if users went to a restaurant and want to continue the date, suggest them a nearby bar
- [ ] Implement mock chat WebSocket server
- [ ] Create chat bots to generate simulated chat data
- [ ] Resy integration. Support users booking via Resy; experiment with filtering suggestions by
reservation availability.
- [ ] Dynamically combine Yelp and Google API response data

### Implemented
- [X] Score all businesses on "baseline dateworthiness" to provide better suggestions even without personalized preferences data
- [X] Rank suggestions for a given user-pair by considering both users' known preferences
- [X] Filter for reviews that explicitly comment on a business's suitability as a date location, and update date location scoring based on whether the comment is negative or positive
- [X] Detect keywords in user chat messages that are relevant to dining preferences, and update the stored user preferences data accordingly
- [X] Begin search for date locations at a user pair's geographic midpoint
- [X] Consider information about businesses that would be obvious to a human reader based on the name
- [X] HTTP endpoints that return JSON for consumption by a front end client
