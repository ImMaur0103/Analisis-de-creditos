const express = require('express');
const session = require('express-session');
const exphbs = require('express-handlebars');
const path = require('path');
const Partials = require('./Config/partials');

const app = express();

// Middleware para procesar datos de formulario
app.use(express.urlencoded({ extended: true }));

// Middleware para procesar datos JSON
app.use(express.json());

// Variables
const port = 2500;
const StartMessage = 'Server started with port: ' + port + '\nReady to connect';

// Set up Handlebars
const hbs = exphbs.create({
    extname: '.handlebars',
    helpers: {
        eq: function (v1, v2) {
            return v1 === v2;
        },
        isObject: function(value) {
            return typeof value === 'object' && !Array.isArray(value) && value !== null;
        }
    }
});

app.engine('handlebars', hbs.engine);
app.set('view engine', 'handlebars');
app.set('views', './views');

// Registrar todos los parciales al inicio
Partials.registerAllPartials(hbs);

// Serve static files
app.use(express.static(path.join(__dirname, 'public')));

// Session management
app.use(session({
    secret: 'tu_secreto_aqui',
    resave: false,
    saveUninitialized: true,
    cookie: { secure: false } // Establece en true si usas https
}));
 
app.use(express.urlencoded({ extended: true }));

// Routes
app.use('/', require('./routes/index'));

app.listen(port, () => {
    console.log(StartMessage);
});

module.exports = app;