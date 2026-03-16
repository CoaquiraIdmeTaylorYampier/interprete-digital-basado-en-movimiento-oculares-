class Tecla:
    def __init__(self, letra, x1, y1, x2, y2):
        self.letra = letra
        self.x1 = x1  
        self.y1 = y1 
        self.x2 = x2 
        self.y2 = y2  

    def contiene(self, x, y):
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2


class MatrizTeclado:
    def __init__(self):
        self.teclas = []  

    def insertar(self, letra, x1, y1, x2, y2):
        self.teclas.append(Tecla(letra, x1, y1, x2, y2))

    def obtener_por_coordenada(self, x, y):
        for t in self.teclas:
            if t.contiene(x, y):
                return t.letra
        return None  # si no está mirando ninguna tecla
