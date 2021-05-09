# datespot
Conceptual prototype for a dating app API that suggests date locations to users.

## Roadmap

- [x] Design main domain-layer models
- [x] Decide initial database architecture (SQL vs. NoSQL).
- [x] Implement "repository" design pattern with simple JSON files as the database.
- [x] Parse Google Maps Places API "Nearby Search" responses into the app's internal date-location objects.
- [ ] Parse Google Maps Places API "Place Details" responses into attributes of app's internal date-location objects.
- [ ] Implement HTTP client to make Nearby Search and Place Details requests in response to other internal app code.
- [ ] Implement core restaurant-suggestion algorithm as a heap/priority queue.
- [ ] Implement unified API callable by a frontend / UI layer. An internal RESTful JSON server that can serve JSON to a Node/Express web API.
- [ ] Implement simple command line interface that simulates live interactions with the app's internal JSON-server API.
- [ ] Refactor, rationalize architecture, simplify code, improve code quality and documentation, expand tests coverage.
- [ ] Improve the restaurant-suggestion algorithm with sentiment analysis on restaurant reviews and simulated user chat histories.
- [ ] Integrate data from additional third-party APIs (Yelp?) to improve recommendation algorithm.
- [ ] Add support for hypothetical concurrent DB interactions. In a real dating app, multiple users would sometims interact with a single DB object concurrently.

## Priorities

* Good suggestions for tiny geographic area > mediocre suggestions worldwide
* Good restaurant suggestions > mediocre suggestions for fuller range of locations and activities

## Problems encountered

### SQL vs. NoSQL
  I wasn't sure whether SQL or a non-SQL data architecture would be best. For some parts of the app, I felt SQL might be helpful (the restaurants data, which I expect would remain fairly relational and rigid in its schema), but for others I felt the flexibility and hypothetical concurrency and horizontal scalability of a non-SQL system would be valuable. I ended up implementing a JSON-based system, primarily to avoid prematurely spending time worrying about database architecture, while still having a system that could interface easily with the third-party, JSON-serving web APIs that much of the app's core data will come from. This quickly paid off when it came time to code the parsing of Google Maps API requests. 
  
### Computing the distance between two latitude-longitude coordinate pairs.
  This required a bit more math than I anticipated this app needing (the simple Euclidean distance isn't useful when the "coordinates" are lat lon decimals), but it was straightforward with the correct formulae.
