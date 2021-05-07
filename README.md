# datespot
Conceptual prototype for a dating app API that suggests date locations to users.

# Roadmap

- [x] Design main domain-layer models
- [x] Decide initial database architecture (SQL vs. NoSQL).
- [x] Implement "repository" design pattern with simple JSON files as the database.
- [x] Parse Google Maps Places API "Nearby Search" responses into the app's internal date-location objects.
- [ ] Parse Google Maps Places API "Place Details" responses into attributes of app's internal date-location objects.
- [ ] Create client that makes Nearby Search and Place Details requests in response to other app code.
- [ ] Implement core restaurant-suggestion algorithm as a heap/priority queue.
- [ ] Implement unified API callable by a frontend / UI layer. An internal RESTful JSON server that can serve JSON to a Node/Express web API.
- [ ] Implement simple command line interface that simulates live interactions with the app's internal JSON-server API.
- [ ] Refactor, rationalize architecture, simplify code, expand tests coverage.
- [ ] Improve the restaurant-suggestion algorithm with sentiment analysis on restaurant reviews and simulated user chat histories.
