# Interprete digital basado en movimiento oculares#

## Descripcion

este proyecto implementa un teclado virtual el cual es controlado solo con el movimiento de las pupilas utilizando vision por computadora.ç
El sistema detecta la dirección de la mirada del usuario y permite seleccionar letras en un teclado virtual(parpadear) sin necesidad de usar las manos.

El objetivo es desarrollar una interfaz humano-computadora accesible, util especialmente para personas con discapacidad motora.

## Tecnologias utilizadas

- Python
- OpenCV
- MediaPipe
- TXT con palabras
- Estructura de datos arbol trie
- Estructura grafo
- estructura matriz dipersa

## Estructura del proyecto

main.py → archivo principal del sistema  
seguimiento.py → detección y seguimiento de ojos  
interfaz.py → interfaz del teclado virtual  
arboltrie.py → implementación del árbol Trie para predicción de palabras
grafo.py → estructura que permite retroalimentar , aprender con el usuario en tiempo real 
matrizdis.py → calculos de las posiciones de teclas 
palabras.txt → diccionario de palabras, las mas usadas o repetidas en español
## Instalación

1. Clonar el repositorio

git clone https://github.com/CoaquiraIdmeTaylorYampier/interprete-digital-basado-en-movimiento-oculares-.git

2. Crear entorno virtual

python -m venv venv

3. Instalar dependencias

pip install -r requirements.txt

## Autor

Taylor Yampier Coaquira Idme  
Estudiante de Ingeniería de Sistemas - UNA Puno
4to semestre 