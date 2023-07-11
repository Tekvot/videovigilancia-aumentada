const { Server } = require('socket.io')
const { log } = require('console');
const express = require('express');
const http = require('http');
const createImage = require('./bringImage');

//Import middlewares
const cors = require('cors');
const bodyParser = require('body-parser');



//Create a express server   
const app = express();
const server = http.createServer(app);
const port = 4000

//Middlewares
app.use(bodyParser.json());
app.use(cors());

//Socket.io
const io = new Server({
    //acept all cors origin
    cors: {
        origin: "*"
    }
});
//io port
io.listen(5000);



//Routes API
app.get('/', (req, res) => {
    res.send('Hello World!')
});


app.post('/', (req, res) => {
    if (req.body.dni && req.body.name && req.body.image64 && req.body.alert) {
        console.log("Hay una alerta y estos son los datos:", req.body);
        const newBody = {
            dni: req.body.dni,
            name: req.body.name,
            image64: req.body.image64,
            alert: req.body.alert
        }
        console.log('🚀 ~ file: index.js:49 ~ newBody:', newBody)
        io.emit('envioAlApp', newBody);
        res.send(newBody)
    } else if (req.body.alert === false) {
        console.log("No hay alerta");
        io.emit('envioAlApp', req.body);
        res.send(req.body)
    }
});



//Socket connection
io.on('connection', (socket) => {
    console.log('a user connected');
});


server.listen(port, () => {
    console.log(`CAMIA Backend en http://localhost:${port}`)
});


//Modelo
// {
//     "dni":dni,
//     "name":name,
//     "image64":cadena,
//     "alert":alert
// }