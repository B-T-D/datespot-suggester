const { JSONCookie } = require('cookie-parser');
var express = require('express');

const queryDb = require('../namedPipesUtil');

var matchesRouter = express.Router();

/* GET matches for a user */
matchesRouter.get('/', async (req, res, next) => {
    try {
        const userId = req.query.userId
        console.log(`received GET request for user ${userId}'s matches`);
        var dbRequest = {
            "method": "get_matches_list",
            "query_data": {
                "user_id": userId
            }
        }
        const dbResponse = await queryDb(dbRequest);
        res.json(dbResponse);
        next()
    } catch(err) {
        return next(err)
    }
});

/* GET suggestions for a match */
matchesRouter.get('/:matchId/suggestions', async (req, res, next) => {
    try {
        const matchId = req.params.matchId;
        console.log(`received GET request for suggestions for match ${matchId}`);
        var dbRequest = {
            "method": "get_suggestions_list",
            "query_data": {
                "match_id": matchId
            }
        }
        const dbResponse = await queryDb(dbRequest);
        res.json(dbResponse);
        next()
    } catch(err) {
        return next(err)
    }
})

module.exports = matchesRouter