const fs = require('fs');
const path = require('path');
const Components = require('../routes/path').Components;

function registerPartials(dir, hbs) {
    const filenames = fs.readdirSync(dir);

    filenames.forEach((filename) => {
        const matches = /^([^.]+).handlebars$/.exec(filename);
        if (!matches) {
            return;
        }
        const name = matches[1];
        const template = fs.readFileSync(path.join(dir, filename), 'utf8');
        hbs.handlebars.registerPartial(name, template);
    });
}
 
function registerAllPartials(hbs) {
    const partialsDir = path.join(process.cwd(), 'views', 'partials');
    const ViewsDir = path.join(process.cwd(), 'views');
    registerPartials(partialsDir, hbs);

    Object.keys(Components).forEach(key => {
        const subdir = Components[key]
        const subdirPath = path.join(ViewsDir, subdir);
        if (fs.existsSync(subdirPath)) {
            registerPartials(subdirPath, hbs);
        }
    });   
    
}

module.exports = {
    registerAllPartials
};