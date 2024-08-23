const express = require('express');
const multer = require('multer');
const router = express.Router();
const axios = require('axios');
const paths = require('./path').paths;
const Components = require('./path').Components;
const fs = require('fs');
const { isAuthenticated } = require('../middlewares/auth');

const upload = multer();

router.get('/', isAuthenticated, (req, res) => {
    res.render(paths.home, { 
        title: 'G2L',
        Navbar: true, 
        Footer: true, 
        user: req.session.user,
        additionalCSS: [
            '/css/home.css'
        ]
    });
});

router.get('/error', isAuthenticated, (req, res) => {
    res.render(paths.error, { 
        title: 'Error',
        Navbar: true,
        Footer: true,
        additionalCSS: ['/css/error.css'],
        additionalJS: ['/js/error.js']
    });

});

router.get('/login', (req, res) => {
    res.render(paths.login, { 
        title: 'Login page',
        Navbar: false,
        customCSS: [
            'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css',
            'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css',
            '/css/login.css'
        ],
        customJS: ['/js/login.js'],
        additionalJS: [
            'https://assets.codepen.io/16327/MorphSVGPlugin3.min.js',
            'https://assets.codepen.io/16327/ScrambleTextPlugin3.min.js',
            'https://unpkg.com/gsap@3.11.0/dist/gsap.min.js'
        ]
    });

});

router.get('/PDF_analyzer', isAuthenticated, (req, res) => {
    res.render(paths.PDF, { 
        title: 'PDF Analysis',
        Navbar: true, 
        Footer: true, 
        user: req.session.user,
        additionalCSS: [ '/css/PDF_sec.css' ],
        customJS: ['/js/PDF.js'],
    });
});

router.get('/Criteria', isAuthenticated, async (req, res) => {
    var criteria_list;
    try {        
        // Crear un nuevo FormData para enviar a la otra API
        const json_requet = {
            "info_request": "criteria"
          };
        const head= {
            "accept": "application/json",
            "content-Type": "application/json"
          }
        const Headers = new axios.AxiosHeaders(head)
        // Enviar los archivos a la otra API
        const response = await axios.get(url='http://127.0.0.1:8000/api/Important_info',{ data: json_requet, headers: Headers});
        criteria_list = Object.entries(response.data).reduce((acc, [key, value]) => {
            acc[key] = value;
            return acc;
          }, {});
      } catch (error) {
        console.error('Error:', error);
        res.redirect('/error')
      } 
    res.render(paths.criteria, { 
        title: 'Criteria List',
        Navbar: true, 
        Footer: true, 
        user: req.session.user,
        additionalCSS: [
            '/css/criteria.css'
        ],
        customJS: ['/js/criteria.js'],
        Criteria_list: criteria_list
    });
});
 

router.get('/logout', (req, res) => {
    req.session.destroy((err) => {
        res.redirect('/login');
    });
});

router.get('/about', (req, res) => {
    res.render('about', { title: 'About' });
});

router.get('/contact', (req, res) => {
    res.render('contact', { title: 'Contact' });
});

router.post('/upload', upload.fields([
    { name: 'application', maxCount: 1 },
    { name: 'history', maxCount: 10 }
  ]),async (req, res) => {
    try {
        console.log(req.files);
        
        // Crear un nuevo FormData para enviar a la otra API
        const formData = new FormData();
        
        // Agregar el archivo de aplicación
        if (req.files.application && req.files.application[0]) {
          formData.append('application', fs.createReadStream(req.files.application[0].path), req.files.application[0].originalname);
        }
        
        // Agregar los archivos de historial
        if (req.files.history) {
          req.files.history.forEach((file) => {
            formData.append('history', fs.createReadStream(file.path), file.originalname);
          });
        }
        
        // Enviar los archivos a la otra API
        const response = await axios.post('https://otra-api.com/ruta-de-subida', formData, {
          headers: {
            ...formData.getHeaders()
          }
        });
        
        console.log('Respuesta de la otra API:', response.data);
        
        // Eliminar los archivos temporales después de enviarlos
        if (req.files.application) {
          fs.unlinkSync(req.files.application[0].path);
        }
        if (req.files.history) {
          req.files.history.forEach(file => fs.unlinkSync(file.path));
        }
        
        res.status(200).json({ message: 'Archivos recibidos y enviados correctamente' });
      } catch (error) {
        console.error('Error:', error);
        res.status(500).json({ message: 'Error al procesar los archivos' });
      }
});

router.post('/login', upload.none(),(req, res) => {
    // Aquí iría tu lógica de autenticación
    // Por ejemplo:
    if (req.body.username === 'admin' && req.body.password === 'admin') {
        req.session.user = { username: req.body.username };
        res.json({ success: true, redirect: '/' });
    } else {
        res.render(paths.login, { 
            title: 'Login', 
            error: 'Credenciales inválidas' 
        });
    }
});

module.exports = router;