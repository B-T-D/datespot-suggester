var express = require('express');
const queryDb = require('../namedPipesUtil');
var usersRouter = express.Router();

usersRouter.use((req, res, next) => {
  console.log(`request came to users router`);
  next();
})

/* GET users listing. */
usersRouter.get('/', function(req, res, next) {
  console.log('respond with a resource');
  next()
});

/* TODO post request to login should include the location since that's required for User init;
that's why create new user needs to be POST not GET */

/* TODO isn't it better to wrap these somehow so not every single DB-accessing Express-middleware
function has to be an async? */

usersRouter.get('/login/:userId', async (req, res, next) => {
  try{
    // let responseJSON = null; // TODO this didn't solve the bug wrt returning the prior request's data
    const userId = req.params.userId;
    console.log(`received get request to users/login with user id ${userId}`);
    var dbRequestJSON = {
      "method": "get_login_user_info",
      "json_arg": {
        "user_id": userId
      }
    }
    responseJSON = await queryDb(dbRequestJSON);
    console.log(`in userRouter: responseJSON type = ${typeof(responseJSON)}`)
    console.log(`in usersrouter: responseJSON = ${JSON.stringify(responseJSON)} with type ${typeof(responseJSON)}`);
    console.log(`object keys = ${Object.keys(responseJSON)}`);
    res.json(responseJSON);
    next()
  } catch(err) {
      return next(err) // break the middleware chain in order to hand off to error handler
  }
});

usersRouter.post('/signup', async (req, res, next) => {
  try {

  
    console.log(`received signup post request with query = ${JSON.stringify(req.query)}`)
    let name = req.query.name;
    let location = [req.query.latitude, req.query.longitude];
    let dbRequestJSON = {
      "method": "post_object",
      "json_arg": {
        "object_model_name": "user",
        "json_data": {
          "name": name,
          "current_location": location
          }
        }
      }
    console.log(`dbRequest data is ${JSON.stringify(dbRequestJSON)}`);
    responseJSON = await queryDb(dbRequestJSON);
    res.json(responseJSON);
    next();
  } catch(err) {
    return next(err)
  }
})

module.exports = usersRouter;
