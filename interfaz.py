import pyttsx3
from PIL import Image, ImageTk 
import queue
import tkinter as tk
import threading
from seguimiento import EyeTracker 
from matrizdis import MatrizTeclado 
from tkinter import font
from grafo import Grafo

class TecladoApp:
    def __init__(self, ventana, trie):
        self.ventana = ventana
        self.trie = trie
        self.ventana.title("Teclado con Control Ocular - Inserción por Parpadeo")
        self.ventana.resizable(False, False)

        self.botones_canvas = {}
        self.matriz_teclado = MatrizTeclado()
        self.grafo = Grafo()

        self.btn_font = font.Font(family="Arial", size=16, weight="bold")
        self.text_font = font.Font(family="Arial", size=26, weight="bold")
        self.suger_font = font.Font(family="Arial", size=20, weight="bold")

        self.canvas_fondo = tk.Canvas(ventana, width=1500, height=580, highlightthickness=0)
        self.canvas_fondo.pack(fill="both", expand=True)

        # Cargar fondo
        fondo_img = Image.open("fondo.jpg")
        fondo_img = fondo_img.resize((1500, 580), Image.LANCZOS)
        self.fondo_tk = ImageTk.PhotoImage(fondo_img)
        self.canvas_fondo.create_image(0, 0, image=self.fondo_tk, anchor="nw")
        print("✓ Fondo cargado correctamente")

        # Variables de estado
        self.texto_actual = ""
        self.sugerencias_actuales = []
        # Bandera para saber si la cámara ya se inicializó
        self.camara_inicializada = False 

        self.crear_cuadro_texto()
        self.crear_area_sugerencias()
        self.crear_teclado()
        self.crear_etiqueta_estado()

        self.eye_tracker = EyeTracker()
        self.boton_actual = None

        self.cola_voz = queue.Queue()
        self.voz_ocupada = False
        self.iniciar_sistema_voz()

        self.ventana.bind("<Key>", self.on_key_press)

        # Usar .after(100) es correcto para iniciar el tracking
        self.ventana.after(100, self.iniciar_sistema_ocular)

    def crear_cuadro_texto(self):
        """Crea el área de texto principal"""
        self.canvas_fondo.create_rectangle(
            100, 20, 1400, 80,
            fill='#34495e', outline='#3498db', width=3,
            tags="texto_fondo"
        )
        self.texto_id = self.canvas_fondo.create_text(
            750, 50, text="", font=self.text_font,
            fill='white', anchor=tk.CENTER
        )

    def crear_area_sugerencias(self):
        """Crea el área de sugerencias"""
        self.suger_elementos = []
        y_pos = 100
        x_inicial = 150
        ancho_suger = 280
        alto_suger = 60
        espacio = 15

        for i in range(4):
            x = x_inicial + i * (ancho_suger + espacio)
                
            rect = self.canvas_fondo.create_rectangle(
                x, y_pos, x + ancho_suger, y_pos + alto_suger,
                fill='#E0E0E0', outline='#3498db', width=2,
                tags=f"suger_{i}"
            )
            
            texto = self.canvas_fondo.create_text(
                x + ancho_suger/2, y_pos + alto_suger/2,
                text="", font=self.suger_font,
                fill='blue', anchor=tk.CENTER,
                tags=f"suger_{i}"
            )
            
            # Eventos de click
            self.canvas_fondo.tag_bind(f"suger_{i}", "<Button-1>", 
                                         lambda e, idx=i: self.autocompletar_desde_click(idx))
            self.canvas_fondo.tag_bind(f"suger_{i}", "<Enter>", 
                                         lambda e, idx=i: self.hover_sugerencia(idx, True))
            self.canvas_fondo.tag_bind(f"suger_{i}", "<Leave>",
                                         lambda e, idx=i: self.hover_sugerencia(idx, False))
            
            self.suger_elementos.append({'rect': rect, 'texto': texto})
            
            # Guardar en matriz dispersa
            self.matriz_teclado.insertar(f"suger_{i}", x, y_pos, x + ancho_suger, y_pos + alto_suger)

    def crear_teclado(self):
        """
        fila1 = ['1','2','3','4','5','6','7','8','9','0']
        fila2 = ['q','w','e','r','t','y','u','i','o','p']
        fila3 = ['a','s','d','f','g','h','j','k','l','ñ']
        fila4 = ['z','x','c','espacio','v','b','n','m','borrar','hablar']
        """
        fila1 = ['1','8','a','q','borrar','hablar','p','o','9','0']
        fila2 = ['2','w','e','r','l','y','u','i','ñ','5']
        fila3 = ['3','x','d','f','g','h','j','m','t','6']
        fila4 = ['4','z','s','espacio','c','v','b','n','k','7']
        
        filas = [fila1, fila2, fila3, fila4]

        ancho_tecla = 140
        alto_tecla = 90
        espacio_x = 7
        espacio_y = 7
        y_inicial = 190

        for fila_idx, fila in enumerate(filas):
            if fila_idx == 3:
                ancho_total = 0
                for valor in fila:
                    if valor == 'espacio':
                        ancho_actual = ancho_tecla * 1.5
                    
                    else:
                        ancho_actual = ancho_tecla
                    ancho_total += ancho_actual
                ancho_total += (len(fila) - 1) * espacio_x

            else:
                ancho_total = len(fila) * ancho_tecla + (len(fila) - 1) * espacio_x
            
            x_actual = (1500 - ancho_total) / 2
            
            for valor in fila:
                y = y_inicial + fila_idx * (alto_tecla + espacio_y)
                
                if valor == 'espacio':
                    ancho_actual = ancho_tecla * 1.5
                elif valor in ['borrar', 'hablar']:
                    ancho_actual = ancho_tecla 
                else:
                    ancho_actual = ancho_tecla
                
                rect = self.canvas_fondo.create_rectangle(
                    x_actual, y, x_actual + ancho_actual, y + alto_tecla,
                    fill='#B4CDCE', outline='#2980b9', width=2,
                    tags=f"tecla_{valor}"
                )
                
                if valor == 'borrar':
                    texto_tecla = '⌫'
                    fuente = ("Arial", 24, "bold")
                elif valor == 'hablar':
                    texto_tecla = '🔊'
                    fuente = ("Arial", 24, "bold")
                elif valor == 'espacio':
                    texto_tecla = '␣'
                    fuente = ("Arial", 20, "bold")
                else:
                    texto_tecla = valor.upper()
                    fuente = self.btn_font
                
                texto = self.canvas_fondo.create_text(
                    x_actual + ancho_actual/2, y + alto_tecla/2,
                    text=texto_tecla, font=fuente,
                    fill='black', anchor=tk.CENTER,
                    tags=f"tecla_{valor}"
                )
                
                self.canvas_fondo.tag_bind(f"tecla_{valor}", "<Button-1>", 
                                             lambda e, v=valor: self.accion_tecla(v))
                self.canvas_fondo.tag_bind(f"tecla_{valor}", "<Enter>", 
                                             lambda e, v=valor: self.hover_tecla(v, True))
                self.canvas_fondo.tag_bind(f"tecla_{valor}", "<Leave>", 
                                             lambda e, v=valor: self.hover_tecla(v, False))
                
                self.botones_canvas[valor] = {'rect': rect, 'texto': texto}
                
                self.matriz_teclado.insertar(valor, x_actual, y, x_actual + ancho_actual, y + alto_tecla)
                
                x_actual += ancho_actual + espacio_x

    def crear_etiqueta_estado(self):
        self.estado_texto = "Inicializando camara..."
        self.estado_id = self.canvas_fondo.create_text(
            750, 550, text=self.estado_texto,
            font=("Arial", 12, "bold"),
            fill='orange', anchor=tk.CENTER, tags="estado"
        )

    def actualizar_estado_camara(self, texto, color):
       
        self.canvas_fondo.itemconfig(self.estado_id, text=texto, fill=color)

    def hover_sugerencia(self, idx, entrar):
        
        if entrar:
            self.canvas_fondo.itemconfig(self.suger_elementos[idx]['rect'], fill="#98B40A")
        else:
            self.canvas_fondo.itemconfig(self.suger_elementos[idx]['rect'], fill='#E0E0E0')

    def hover_tecla(self, valor, entrar):
        """Efecto hover sobre teclas"""
        if entrar:
            self.canvas_fondo.itemconfig(self.botones_canvas[valor]['rect'], fill='#9DBABB')
        else:
            self.canvas_fondo.itemconfig(self.botones_canvas[valor]['rect'], fill='#B4CDCE')

    def accion_tecla(self, valor):
        """Ejecuta la acción de una tecla"""
        if valor == 'borrar':
            self.borrar_uno()
        elif valor == 'hablar':
            self.hablar_texto()
        elif valor == 'espacio':
            self.insertar(' ')
        else:
            self.insertar(valor)

    def actualizar_texto_display(self):
        self.canvas_fondo.itemconfig(self.texto_id, text=self.texto_actual)

    def actualizar_sugerencias_display(self):
        for i, elem in enumerate(self.suger_elementos):
            if i < len(self.sugerencias_actuales):
                self.canvas_fondo.itemconfig(elem['texto'], text=self.sugerencias_actuales[i])
            else:
                self.canvas_fondo.itemconfig(elem['texto'], text="")

    def iniciar_sistema_ocular(self):
        """Inicializa el sistema de tracking ocular"""
        self.ventana.update()
        
        window_width = self.ventana.winfo_width()
        window_height = self.ventana.winfo_height()
        
        self.cursor_window = tk.Toplevel(self.ventana) 
        self.cursor_window.overrideredirect(True)
        self.cursor_window.attributes('-topmost', True) 
        self.cursor_window.attributes('-transparentcolor', 'white')
        
        self.cursor_window.geometry(f"{window_width}x{window_height}+{self.ventana.winfo_x()}+{self.ventana.winfo_y()}")
        
        self.canvas = tk.Canvas(self.cursor_window, width=window_width, height=window_height,
                                      bg='white', highlightthickness=0)
        self.canvas.pack()
        
        center_x = window_width // 2
        center_y = window_height // 2
        radio = 15
        
        self.cursor_circle = self.canvas.create_oval(
            center_x-radio, center_y-radio, center_x+radio, center_y+radio,
            fill='red', outline='darkred', width=3
        )
        
        try:
            resultado = self.eye_tracker.start_tracking(
                gaze_callback=self.actualizar_cursor,
                blink_callback=self.on_blink_detected
            )
            if resultado:
                self.tracking_activo = True

            else:
                raise Exception("No se pudo iniciar la cámara")
        except Exception as e:
            print(f"❌ Error al iniciar tracking: {e}")
            self.actualizar_estado_camara("⚠️ Error: No se puede iniciar la cámara - Usa el teclado físico", "red")
            self.tracking_activo = False
            self.cursor_window.destroy()
        
        if hasattr(self, 'tracking_activo') and self.tracking_activo:
            self.verificar_posicion_cursor()

    def actualizar_cursor(self, gaze_x, gaze_y):
        
        try:
    
            window_width = self.ventana.winfo_width()
            window_height = self.ventana.winfo_height()
            
            x = int(gaze_x * window_width)
            y = int(gaze_y * window_height)
            
            radio = 15
            self.canvas.coords(self.cursor_circle, x-radio, y-radio, x+radio, y+radio)
            
            root_x = self.ventana.winfo_rootx()
            root_y = self.ventana.winfo_rooty()
            self.cursor_window.geometry(f"+{root_x}+{root_y}") 
          
            if not self.camara_inicializada:
                self.camara_inicializada = True
                self.actualizar_estado_camara("✓ Cámara activa - Parpadea para insertar", "green")
                
        except Exception as e:
           print(f"Error actualizando cursor: {e}")

  
    def verificar_posicion_cursor(self):
        if not hasattr(self, 'tracking_activo') or not self.tracking_activo:
            return

        try:
            coords = self.canvas.coords(self.cursor_circle)
            if len(coords) != 4:
                self.ventana.after(100, self.verificar_posicion_cursor)
                return

            cursor_x = (coords[0] + coords[2]) / 2
            cursor_y = (coords[1] + coords[3]) / 2

            boton_encontrado = None

            tecla_en_coord = self.matriz_teclado.obtener_por_coordenada(cursor_x, cursor_y)
            
            if tecla_en_coord:
                if tecla_en_coord.startswith('suger_'): 
                    idx = int(tecla_en_coord.split('_')[1]) 
                    boton_encontrado = ('sugerencia', idx)
                else:
                    boton_encontrado = (tecla_en_coord,)

            if boton_encontrado != self.boton_actual:
                
                if self.boton_actual:
                    if isinstance(self.boton_actual, tuple) and self.boton_actual[0] == 'sugerencia':
                        idx = self.boton_actual[1]
                        self.canvas_fondo.itemconfig(self.suger_elementos[idx]['rect'], fill='#E0E0E0')
                    else:
                        valor = self.boton_actual[0]
                        if valor in self.botones_canvas:
                            self.canvas_fondo.itemconfig(self.botones_canvas[valor]['rect'], fill='#B4CDCE')

                self.boton_actual = boton_encontrado
                if boton_encontrado:
                    if boton_encontrado[0] == 'sugerencia':
                        idx = boton_encontrado[1]
                        self.canvas_fondo.itemconfig(self.suger_elementos[idx]['rect'], fill='#FFD700')
                    else:
                        valor = boton_encontrado[0]
                        self.canvas_fondo.itemconfig(self.botones_canvas[valor]['rect'], fill='#7FB3B5')

        except Exception as e:
            print(f"Error en verificar_posicion_cursor: {e}")

        self.ventana.after(100, self.verificar_posicion_cursor)

    def on_blink_detected(self):
        if not self.boton_actual:
            print("⚠️ Parpadeo detectado pero no hay botón seleccionado")
            return
        
        if self.boton_actual[0] == 'sugerencia':
            idx = self.boton_actual[1]
            if idx < len(self.sugerencias_actuales):
                print(f"👁️ Parpadeo: Autocompletando '{self.sugerencias_actuales[idx]}'")
                self.autocompletar_desde_click(idx)

                self.canvas_fondo.itemconfig(self.suger_elementos[idx]['rect'], fill='lime')
                self.ventana.after(150, lambda i=idx: self.canvas_fondo.itemconfig(
                    self.suger_elementos[i]['rect'], fill='#E0E0E0'))
                self.boton_actual = None
        else:
            valor = self.boton_actual[0]
            print(f"👁️ Parpadeo: Presionando '{valor}'")
            if valor == 'borrar':
                self.borrar_uno()
            elif valor == 'hablar':
                self.hablar_texto()
            elif valor == 'espacio':
                self.insertar(' ')
            else:
                self.insertar(valor)
                
            if valor in self.botones_canvas:
                self.canvas_fondo.itemconfig(self.botones_canvas[valor]['rect'], fill='lime')
                self.ventana.after(150, lambda v=valor: self.canvas_fondo.itemconfig(
                    self.botones_canvas[v]['rect'], fill='#B4CDCE') if v in self.botones_canvas else None)
                self.boton_actual = None

    def iniciar_sistema_voz(self):
        def worker_voz():
            print("✓ Worker de voz iniciado")
            
            while True:
                try:
                    mensaje = self.cola_voz.get()
                    if mensaje == "STOP":
                        print("Worker de voz detenido")
                        break
                    
                    if mensaje:
                        print(f"🔊 Leyendo: {mensaje}")
                        self.voz_ocupada = True
                        
                        self.ventana.after(0, lambda: self.canvas_fondo.itemconfig(
                            self.canvas_fondo.find_withtag("texto_fondo")[0], fill='lightgreen'))

                        try:
                            # Reinicializar el motor en cada uso
                            engine = pyttsx3.init()
                            engine.setProperty('rate', 120)
                            engine.setProperty('volume', 1.0)
                            engine.say(mensaje)
                            engine.runAndWait()
                            engine.stop()
                            del engine  # Liberar recursos
                            print("✓ Reproducción completada")
                        except Exception as e:
                            print(f"❌ Error en reproducción: {e}")
                        finally:
                            # IMPORTANTE: Asegurar que siempre se resetee el estado
                            self.ventana.after(0, lambda: self.canvas_fondo.itemconfig(
                                self.canvas_fondo.find_withtag("texto_fondo")[0], fill='#34495e'))
                            self.voz_ocupada = False
                    
                    self.cola_voz.task_done()
                except Exception as e:
                    print(f"❌ Error en worker de voz: {e}")
                    self.voz_ocupada = False
    
        thread = threading.Thread(target=worker_voz, daemon=True)
        thread.start()

    def insertar(self, car):
        if car == 'espacio':
            car = ' '
        self.texto_actual += car
        self.actualizar_texto_display()
        self.actualizar_sugerencia()

    def borrar_uno(self):
        if self.texto_actual:
            self.texto_actual = self.texto_actual[:-1]
            self.actualizar_texto_display()
            self.actualizar_sugerencia()

    def hablar_texto(self):
        texto = self.texto_actual.strip() 
        if not texto:
            print("⚠️ No hay texto para leer")
            self.canvas_fondo.itemconfig(self.canvas_fondo.find_withtag("texto_fondo")[0], fill='red')
            self.ventana.after(200, lambda: self.canvas_fondo.itemconfig(
                self.canvas_fondo.find_withtag("texto_fondo")[0], fill='#34495e'))
            return
        
        self.grafo.registrar_frase(texto)
        print(f"✅ Frase registrada en el grafo: '{texto}'")
        
        if self.voz_ocupada:
            print("⚠️ Esperando a que termine la reproducción actual...")
            return
            
        print(f"📝 Agregando a cola: {texto}")
        self.cola_voz.put(texto)

    def actualizar_sugerencia(self):
        texto_completo = self.texto_actual.lower() 
        palabras = texto_completo.split()
        
        if not texto_completo or (not palabras and texto_completo == ' '):
            self.sugerencias_actuales = []
            self.actualizar_sugerencias_display()
            return
        
        if not texto_completo.endswith(' '):
            prefijo = palabras[-1]
            sugerencias = self.trie.sugerir(prefijo)
        else:
            palabra_anterior = palabras[-1]
            sugerencias = self.grafo.sugerir_por_peso(palabra_anterior)
        
        self.sugerencias_actuales = sugerencias[:4]
        self.actualizar_sugerencias_display()

    def autocompletar_desde_click(self, idx):
        if idx < len(self.sugerencias_actuales):
            palabra = self.sugerencias_actuales[idx]
            if palabra:
                palabras = self.texto_actual.split() 
                
                if palabras and not self.texto_actual.endswith(' '):
                    palabras[-1] = palabra
                    self.texto_actual = ' '.join(palabras) + ' '
                elif self.texto_actual.endswith(' '):
                    self.texto_actual += palabra + ' '
                else:
                    self.texto_actual = palabra + ' '
                
                self.actualizar_texto_display()
                self.actualizar_sugerencia()

    def on_key_press(self, event):
        if len(event.char) == 1 and (event.char.isalnum() or event.char.lower() == 'ñ'):
            self.insertar(event.char)
        elif event.keysym == "BackSpace":
            self.borrar_uno()
        elif event.keysym == "space":
            self.insertar(' ')

    def cerrar(self):
        """Cierra la aplicación y libera recursos"""
        self.cola_voz.put("STOP")
        self.eye_tracker.stop()
        if hasattr(self, 'cursor_window'):
            self.cursor_window.destroy()
        self.ventana.destroy()