const fs = require('fs');
const imagePath = './assets/chorillo.png';

const createImage = () => {
    // Lee el archivo de imagen
    const image = fs.readFileSync(imagePath)

    // Convierte la imagen en base64
    const base64Image = Buffer.from(image).toString('base64')

    return base64Image;


}

module.exports = createImage;