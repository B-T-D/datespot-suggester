var express = require('express');
const pipeHelloWorld = require('../namedPipesUtil');

const namedPipesInterface = require('../namedPipesUtil')

const databaseRequest = require('../namedPipesUtil');

var candidatesRouter = express.Router();


var mockDataIn = {
    "method": "get_next_candidate",
    "json_arg": {
        "user_id": "1"
    }
}

candidatesRouter.get('/', async function(req, res, next) {
    //pipeHelloWorld();
    var responseJSON = await databaseRequest(mockDataIn);
    console.log(`in candidates router: responseJSON = ${responseJSON}`)
    res.send(responseJSON);
    next()
    //console.log('candidates router called');
    //var pipesDataOut = namedPipesInterface(mockDataIn);
    //res.send(pipesDataOut)
    //res.send('hello world from candidates router');
})

module.exports = candidatesRouter;