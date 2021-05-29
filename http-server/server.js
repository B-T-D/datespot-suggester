var createError = require('http-errors');
var express = require('express');
const cors = require('cors');

var app = express();
app.use('/', cors()); // TODO too permissive for real deployment?
// app.options('*', cors()); 

var path = require('path');
var cookieParser = require('cookie-parser');
var logger = require('morgan');

var usersRouter = require('./routes/users');
var candidatesRouter = require('./routes/candidates');


module.exports = app; // TODO do we still care about exporting it?

const PORT = process.env.PORT || 8000;

// TODO temp crude logging
app.use('/', (req, res, next) => {
  console.log(`${req.method} request received`);
  next();
})


app.use(logger('dev'));
app.use(express.json());
app.use(express.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(express.static(path.join(__dirname, 'public')));

const apiRouter = express.Router();

apiRouter.use('/candidates', candidatesRouter);

// apiRouter.use('/candidates', (req, res, next) => {
//   console.log(`${req.method} matched '/candidates`)
//   next()
// })

app.use('/api/v1', apiRouter);




// app.use('/', indexRouter);
app.use('/users', usersRouter);
app.use('/candidates', candidatesRouter);

app.use((req, res, next) => {
  console.log(`next thing in the middleware chain was called`)
  console.log(`req was ${req.body} to base url ${req.baseUrl}`)
  next()
})

// catch 404 and forward to error handler
app.use(function(req, res, next) {
  next(createError(404));
});

// error handler
app.use(function(err, req, res, next) {
  // set locals, only providing error in development
  res.locals.message = err.message;
  res.locals.error = req.app.get('env') === 'development' ? err : {};

  // render the error page
  res.status(err.status || 500);
  res.render('error');
});

app.listen(PORT, () => {
  console.log(`Node-Express server listening on port ${PORT}`)
})