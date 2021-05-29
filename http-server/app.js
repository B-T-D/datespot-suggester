var createError = require('http-errors');
var express = require('express');
var path = require('path');
var cookieParser = require('cookie-parser');
var logger = require('morgan');

var indexRouter = require('./routes/index');
var usersRouter = require('./routes/users');
var candidatesRouter = require('./routes/candidates');

var candidatesRouter = express.Router();

var app = express();
module.exports = app;

const PORT = process.env.PORT || 8000;

// view engine setup
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'jade');

app.use(logger('dev'));
app.use(express.json());
app.use(express.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(express.static(path.join(__dirname, 'public')));

// candidatesRouter.get('/', (req, res, next) => {
//   res.send('hello world from app.js override')
// });

app.use('/', (req, res, next) => {
  console.log(`${req.method} request received`);
  next();
})

app.use('/candidates', (req, res, next) => {
  console.log(`request matched path '/candidates'`);
  console.log(`candidatesRouter = ${candidatesRouter}`)
  res.send('that request matched /candidates');
  next();
})

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