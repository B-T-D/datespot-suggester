var express = require('express');

const queryDb = require('../namedPipesUtil');

var candidatesRouter = express.Router();


var mockDataIn = {
    "method": "get_next_candidate",
    "json_arg": {
        "user_id": "1"
    }
}

candidatesRouter.use('/', (req, res, next) => {
    console.log(`request arrived to candidates router`);
    next();
})

candidatesRouter.get('/next', async (req, res, next) => {
    try {
        let userId = req.query.userId
        let dbRequestJSON = {
            "method": "get_next_candidate",
            "json_arg": {
                "user_id": userId
            }
        }
        responseJSON = await queryDb(dbRequestJSON);
        res.json(responseJSON);
        next();
    } catch(err) {
        return next(err)
    }
})


module.exports = candidatesRouter;