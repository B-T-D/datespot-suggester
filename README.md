# datespot
Conceptual prototype for a dating app API that suggests date locations to users.

## Roadmap

- [x] Design main domain-layer models
- [x] Decide initial database architecture (SQL vs. NoSQL).
- [x] Implement "repository" design pattern with simple JSON files as the database.
- [x] Parse Google Maps Places API "Nearby Search" responses into the app's internal date-location objects.
- [ ] Parse Google Maps Places API "Place Details" responses into attributes of app's internal date-location objects.
- [ ] Implement HTTP client to make Nearby Search and Place Details requests in response to other internal app code.
- [X] Implement core restaurant-suggestion algorithm as a heap/priority queue.
- [ ] Implement unified API callable by a frontend / UI layer. An internal RESTful JSON server that can serve JSON to a Node/Express web API.
- [X] Implement simple command line interface that simulates live interactions with the app's internal JSON-server API.
- [ ] Refactor, rationalize architecture, simplify code, improve code quality and documentation, expand tests coverage.
- [ ] Minimalist simulation of user chats so that chat text can be available for NLP. 
- [ ] Improve the restaurant-suggestion algorithm with sentiment analysis on restaurant reviews and simulated user chat histories.
- [ ] Integrate data from additional third-party APIs (Yelp?) to improve recommendation algorithm.
- [ ] Add support for hypothetical concurrent DB interactions. In a real dating app, multiple users would sometims interact with a single DB object concurrently.
- [ ] Resy integration. Support users booking via Resy; experiment with filtering suggestions by
reservation availability.
- [ ] Configure TravisCI and Coveralls on main branch of repo.
- [ ] Achieve 100% unit test code coverage.
- [ ] Improve unit tests to include large, edge, and boundary test cases for the most important algorithms.

### Milestone features
- [ ] Analyze user chats to find keywords relevant to date-location preferences, and tailor that user's suggestions accordingly.
- [ ] Dynamically adjust suggested dates' price level and expected duration based on sentiment analysis of a user chats. Nudge users toward investing less money and time in a date that is less likely to be successful, and more in a date that is likelier to have good chemistry.

## Priorities

* Good suggestions for tiny geographic area > mediocre suggestions worldwide
* Good restaurant suggestions > mediocre suggestions for fuller range of locations and activities

## Problems encountered

### SQL vs. NoSQL
  I wasn't sure whether SQL or a non-SQL data architecture would be best. For some parts of the app, I felt SQL might be helpful (the restaurants data, which I expect would remain fairly relational and rigid in its schema), but for others I felt the flexibility and hypothetical concurrency and horizontal scalability of a non-SQL system would be valuable. I ended up implementing a JSON-based system, primarily to avoid prematurely spending time worrying about database architecture, while still having a system that could interface easily with the third-party, JSON-serving web APIs that much of the app's core data will come from. This quickly paid off when it came time to code the parsing of Google Maps API requests. 
  
### Computing the distance between two latitude-longitude coordinate pairs.
  This required a bit more math than I anticipated this app needing (the simple Euclidean distance isn't useful when the "coordinates" are lat lon decimals), but it was straightforward with the correct formulae.
  
### Efficient lookup of keyword strings: binary search vs. hash tables
  As part of analyzing user chats to learn restaurant preferences, I wanted to look up each word in a chat message in a list of known relevant keywords--e.g. "Thai", "vegetarian", "coffee"--and then use the net sentiment of the sentence containing the keyword as a proxy for the user's feelings toward that keyword ("I love Thai food" boosts Thai restaurants in that user's suggestions). In a real dating app, each of the thousands of users would send dozens or hundreds of messages daily, so the performance of the keyword lookup would be important. 
  
  My first instinct was to store the keywords in a hash set, for average-case O(1) time lookup. But the Python JSON encode/decode library doesn't decode to a Python set object by default; doing so would require creating a custom encoder (https://stackoverflow.com/questions/8230315/how-to-json-serialize-sets). So until I had time to write the custom encoder, I decided to store the keyword strings in a lexicographically sorted Python list (i.e. array) and look them up with binary search in worst-case O(log(n)) time. I expected this data to be quite static (i.e. not gaining new keywords very often), so I was not concerned about the time complexity of sorting the array or inserting new elements.

### Avoiding redundant iteration over message texts
  The vaderSentiment analyzer iterates over each character of the text it analyzes, but does not readily support certain tasks, such as matching strings against keywords relevant to a user's restaurant preferences. If the algorithms that analyze each message run the vaderSentiment analyzer once on the text to compute the sentiment, and then iterate over each word to check for keywords, that's a lot of duplicative work--two passes over the string when a single pass could perform both analyses.
  
  This is an open todo. I plan to solve it by forking the vaderSentiment repo and customizing the relevant methods to have them check for keywords in the same loop as they analyze the sentiment.
