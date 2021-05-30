var express = require('express');
const databaseRequest = require('../namedPipesUtil');
var usersRouter = express.Router();

/* GET users listing. */
usersRouter.get('/', function(req, res, next) {
  res.send('respond with a resource');
  res.next()
});

/* TODO post request to login should include the location since that's required for User init;
that's why create new user needs to be POST not GET */

usersRouter.get('/login', (req, res, next) => {
  console.log(`received get request to users/login`);
  res.next();
})

/* TODO isn't it better to wrap these somehow so not every single DB-accessing Express-middleware
function has to be an async? */

usersRouter.get('/login/:userId', async (req, res, next) => {
  const userId = req.params.userId;
  console.log(`received get request to users/login with user id ${userId}`);
  var dbRequestJSON = {
    "method": "get_login_user_info",
    "json_arg": {
      "user_id": userId
    }
  }
  var responseJSON = await databaseRequest(dbRequestJSON);
  res.send(responseJSON)
  res.next();
})

module.exports = usersRouter;
