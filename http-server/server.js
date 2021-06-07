var createError = require('http-errors');
var express = require('express');
const cors = require('cors');

var app = express();
app.use(cors()); // TODO too permissive for real deployment?
// app.options('*', cors()); 

var path = require('path');
var cookieParser = require('cookie-parser');
var logger = require('morgan');

var usersRouter = require('./routes/users');
var candidatesRouter = require('./routes/candidates');


module.exports = app; // TODO do we still care about exporting it?

const PORT = process.env.PORT || 8000;

app.use(logger('combined'));
app.use(express.json());
app.use(express.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(express.static(path.join(__dirname, 'public')));

const apiRouter = express.Router();

apiRouter.use('/candidates', candidatesRouter);
apiRouter.use('/users', usersRouter);


app.use('/api/v1', apiRouter);

apiRouter.get('/', (req, res) => {
  res.send('');
})

// catch 404 and forward to error handler
// app.use(function(req, res, next) {
//   next(createError(404));
// });


// error handler
app.use(function(err, req, res, next) {
  // set locals, only providing error in development
  res.locals.message = err.message;
  res.locals.error = req.app.get('env') === 'development' ? err : {};

  // serve the error JSON
  res.status(err.status || 500);
  console.log(err);
  console.log(err.message);
  res.send(err.message);
});

app.listen(PORT, () => {
  console.log(`Node-Express server listening on port ${PORT}`)
})