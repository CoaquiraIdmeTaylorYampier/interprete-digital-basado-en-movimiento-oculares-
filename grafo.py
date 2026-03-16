class Grafo:
    def __init__(self):
        self.adyacencia = {}

    def agregar_arista(self, origen, destino):
        if origen not in self.adyacencia:
            self.adyacencia[origen] = {}


        if destino not in self.adyacencia[origen]:
            self.adyacencia[origen][destino] = 1
        else:
            self.adyacencia[origen][destino] += 1

    def registrar_frase(self, frase):
       
        palabras = frase.strip().lower()
        palabras = ''.join(c for c in palabras if c.isalnum() or c.isspace()).split() ##split div

        if not palabras:
            return

        for i in range(len(palabras) - 1):
            origen = palabras[i]
            destino = palabras[i + 1]
            self.agregar_arista(origen, destino)

        ultima = palabras[-1]
        if ultima not in self.adyacencia:
            self.adyacencia[ultima] = {}

    def sugerir_por_peso(self, palabra_anterior):
      
        if palabra_anterior not in self.adyacencia:
            return []
  #hola ->  como(1) estas 
        siguientes = self.adyacencia[palabra_anterior]

        sugerencias_ordenadas = sorted(siguientes.items(), key=lambda item: item[1], reverse=True)#reve grande-peque
        
        return [palabra for palabra, peso in sugerencias_ordenadas]
        
    def imprimir(self):
        """Muestra el grafo completo (para depuración)."""
        for origen, destinos in self.adyacencia.items():
            print(f"[{origen}] -> ", end="")
            for destino, peso in destinos.items():
                print(f"{destino}({peso}) -> ", end="")
            print("NULL")