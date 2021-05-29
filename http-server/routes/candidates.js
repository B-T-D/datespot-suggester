var express = require('express');

const namedPipesInterface = require('../namedPipesUtil')

var candidatesRouter = express.Router();


var mockDataIn = {
    "method": "get_next_candidate"
}

candidatesRouter.get('/', function(req, res, next) {
    console.log('candidates router called');
    var pipesDataOut = namedPipesInterface(mockDataIn);
    res.send(pipesDataOut)
    //res.send('hello world from candidates router');
})

module.exports = candidatesRouter;