class NodoTrie:
    def __init__(self):
        self.fin_palabra = False
        self.hijos = [None] * 26

class Trie:
    def __init__(self):
        self.raiz = NodoTrie()

    def insertar(self, palabra):
        actual = self.raiz                    
        for c in palabra.lower():
            if not c.isalpha():
                continue
            idx = ord(c) - ord('a')
            if 0 <= idx < 26:
                if actual.hijos[idx] is None:
                    actual.hijos[idx] = NodoTrie()
                actual = actual.hijos[idx]
        actual.fin_palabra = True

    def _buscar_recursivo(self, nodo, prefijo, resultados):
        if nodo.fin_palabra:
            resultados.append(prefijo)
        for i in range(26):
            if nodo.hijos[i] is not None:
                self._buscar_recursivo(nodo.hijos[i], prefijo + chr(i + ord('a')), resultados)                                                   

    def sugerir(self, prefijo):
        actual = self.raiz
        for c in prefijo.lower():
            if not c.isalpha():
                continue
            idx = ord(c) - ord('a')
            if not (0 <= idx < 26):
                return []
            if actual.hijos[idx] is None:
                return []
            actual = actual.hijos[idx]
        resultados = []
        self._buscar_recursivo(actual, prefijo.lower(), resultados)
        return resultados
