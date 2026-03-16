import tkinter as tk
from interfaz import TecladoApp
from arboltrie import Trie

def cargar_trie_desde_archivo(nombre):
    trie = Trie()
    try:
        with open(nombre, "r", encoding="utf-8") as archivo:
            for linea in archivo:
                palabra = linea.strip()
                if palabra:
                    
                    trie.insertar(palabra)
        print(f"Diccionario cargado correctamente desde {nombre}")
    except FileNotFoundError:
        print(f"⚠️ No se encontró el archivo {nombre}. Se usarán palabras por defecto.")
        for palabra in ["hola","holanda","hombre","amigo","amor","animal",
                        "casa","casita","caso","cazar","perro","persona"]:
            trie.insertar(palabra)
    return trie


if __name__ == "__main__":
    ventana = tk.Tk()
    trie = cargar_trie_desde_archivo("palabras.txt")
    
    app = TecladoApp(ventana, trie)
    
    ventana.protocol("WM_DELETE_WINDOW", app.cerrar)

    ventana.mainloop()

    print("\nAplicación cerrada correctamente")