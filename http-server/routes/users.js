var express = require('express');
const databaseRequest = require('../namedPipesUtil');
var usersRouter = express.Router();

/* GET users listing. */
usersRouter.get('/', function(req, res, next) {
  res.send('respond with a resource');
  next()
});

/* TODO post request to login should include the location since that's required for User init;
that's why create new user needs to be POST not GET */

usersRouter.get('/login', (req, res, next) => {
  console.log(`received get request to users/login`);
  console.log(`path was ${req.path}`)
  next();
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
  let responseJSON = await databaseRequest(dbRequestJSON);
  if (responseJSON instanceof Error) {
    console.log("YES");
    return next(responseJSON);
  } else {
    console.log("NO");
  }
  // responseJSON = JSON.parse(responseJSON);
  console.log(`in usersrouter: responseJSON = ${JSON.stringify(responseJSON)} with type ${typeof(responseJSON)}`);
  console.log(`object keys = ${Object.keys(responseJSON)}`);
  res.send(responseJSON);
  next();
});

module.exports = usersRouter;
