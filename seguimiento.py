import cv2
import threading
import time
import mediapipe as mp
import numpy as np

class EyeTracker:
    def __init__(self, *args, **kwargs):
        # ----------------- INICIALIZACIÓN (SIN CAMBIOS) -----------------
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5
        )
        self.cap = None
        self.running = True
        self.camera_ready = False
        
        
        self.SENS_X = 2000
        self.SENS_Y = 15000
        self.alpha = 0.05
        self.cursor_x_filtered = 750
        self.cursor_y_filtered = 290
        
        self.LEFT_IRIS = 468
        self.RIGHT_IRIS = 473
        self.LEFT_EYE_CONTOUR = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        self.RIGHT_EYE_CONTOUR = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
        self.LEFT_IRIS_LANDMARKS = [468, 469, 470, 471, 472]
        self.RIGHT_IRIS_LANDMARKS = [473, 474, 475, 476, 477]
        
        self.LEFT_EYE_TOP = 159
        self.LEFT_EYE_BOTTOM = 145
        self.RIGHT_EYE_TOP = 386
        self.RIGHT_EYE_BOTTOM = 374
        
        self.blink_threshold = 0.010
        self.last_blink_time = 0
        self.blink_cooldown = 0.3
        self.blink_callback = None
    
    
    def inicializar_camara(self):
        try:
            print("Intentando abrir la cámara...")
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                print("❌ Error: No se puede abrir la cámara")
                return False
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 280)
            ret, _ = self.cap.read()
            if not ret: return False
            self.camera_ready = True
            print("✓ Cámara inicializada correctamente")
            return True
        except Exception as e:
            print(f"❌ Excepción al inicializar cámara: {e}")
            return False

    def lm_px(self, lm, w, h):
        return int(lm.x * w), int(lm.y * h)

    def eye_center_x(self, face, indices):
        return np.mean([face.landmark[i].x for i in indices])

    def eye_width(self, face, indices):
        xs = [face.landmark[i].x for i in indices]
        return max(xs) - min(xs)

    def detect_blink(self, face):
        left_eye_top = face.landmark[self.LEFT_EYE_TOP].y
        left_eye_bottom = face.landmark[self.LEFT_EYE_BOTTOM].y
        right_eye_top = face.landmark[self.RIGHT_EYE_TOP].y
        right_eye_bottom = face.landmark[self.RIGHT_EYE_BOTTOM].y
        left_eye_height = abs(left_eye_bottom - left_eye_top)
        right_eye_height = abs(right_eye_bottom - right_eye_top)
        is_blinking = (left_eye_height < self.blink_threshold) or (right_eye_height < self.blink_threshold)
        current_time = time.time()
        if is_blinking and (current_time - self.last_blink_time) > self.blink_cooldown:
            self.last_blink_time = current_time
            return True
        return False

    def calculate_gaze(self, face, frame_height, frame_width):
        try:
            iris_left = face.landmark[self.LEFT_IRIS]
            iris_right = face.landmark[self.RIGHT_IRIS]
            
            iris_y = (iris_left.y + iris_right.y) / 2
            iris_y_px = int(iris_y * frame_height)
            y_norm = ((iris_y_px / frame_height) - 0.5) * 2
            y_norm = np.clip(y_norm, -1, 1)

            left_eye_center_x = self.eye_center_x(face, self.LEFT_EYE_CONTOUR)
            right_eye_center_x = self.eye_center_x(face, self.RIGHT_EYE_CONTOUR)
            left_eye_w = self.eye_width(face, self.LEFT_EYE_CONTOUR)
            right_eye_w = self.eye_width(face, self.RIGHT_EYE_CONTOUR)
            
            iris_x_norm_left = (iris_left.x - left_eye_center_x) / (left_eye_w / 2)
            iris_x_norm_right = (iris_right.x - right_eye_center_x) / (right_eye_w / 2)
            x_norm = (iris_x_norm_left + iris_x_norm_right) / 2.0
            x_norm = np.clip(x_norm, -1, 1)

            target_x = 750 + x_norm * self.SENS_X
            target_y = 290 + y_norm * self.SENS_Y
            
            self.cursor_x_filtered = self.alpha * target_x + (1 - self.alpha) * self.cursor_x_filtered
            self.cursor_y_filtered = self.alpha * target_y + (1 - self.alpha) * self.cursor_y_filtered
            
            self.cursor_x_filtered = np.clip(self.cursor_x_filtered, 0, 1500)
            self.cursor_y_filtered = np.clip(self.cursor_y_filtered, 0, 580)
            
            gaze_x_normalized = self.cursor_x_filtered / 1500
            gaze_y_normalized = self.cursor_y_filtered / 580
            
            return gaze_x_normalized, gaze_y_normalized
            
        except Exception as e:
            return None, None

    # ----------------- MÉTODO PRINCIPAL MODIFICADO -----------------

    def start_tracking(self, gaze_callback, blink_callback=None):
        
        if not self.inicializar_camara():
            return False
        
        self.blink_callback = blink_callback
            
        def track():
            DIAGNOSTIC_WINDOW = "Eye Zoom Tracker (Ampliacion)"
            cv2.namedWindow(DIAGNOSTIC_WINDOW)
            
            # 🟢 La bandera cv_window_open se usa para salir del bucle si se cierra la ventana
            cv_window_open = True
            
            while self.running and self.camera_ready and cv_window_open:
                ret, frame = self.cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue
                
                frame = cv2.flip(frame, 1)
                h, w, _ = frame.shape
                
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.face_mesh.process(rgb)
                
                if results.multi_face_landmarks:
                    face = results.multi_face_landmarks[0]

                    # 1. Cálculo del Bounding Box (para recorte)
                    xs, ys = [], []
                    for i in self.LEFT_EYE_CONTOUR + self.RIGHT_EYE_CONTOUR:
                        x, y = self.lm_px(face.landmark[i], w, h)
                        xs.append(x)
                        ys.append(y)

                    pad = 30
                    x1 = max(min(xs) - pad, 0)
                    y1 = max(min(ys) - pad, 0)
                    x2 = min(max(xs) + pad, w)
                    y2 = min(max(ys) + pad, h)
                    
                    # 🟢 Recortar y redimensionar
                    eye_crop = frame[y1:y2, x1:x2].copy()
                    if eye_crop.size == 0:
                        continue

                    eye_crop = cv2.resize(eye_crop, (700, 300))
                    ch, cw, _ = eye_crop.shape

                    def map_point(px, py):
                        zx = int((px - x1) * cw / (x2 - x1))
                        zy = int((py - y1) * ch / (y2 - y1))
                        return zx, zy

                    # 🟢 Lógica de Dibujo (Contornos, Iris y Puntos)
                    def draw_contour(indices, color=(0, 255, 0), thickness=2):
                        pts = []
                        for i in indices:
                            px, py = self.lm_px(face.landmark[i], w, h)
                            pts.append(map_point(px, py))
                        pts = np.array(pts, np.int32)
                        cv2.polylines(eye_crop, [pts], True, color, thickness)
                    
                    draw_contour(self.LEFT_EYE_CONTOUR)
                    draw_contour(self.RIGHT_EYE_CONTOUR)

                    def draw_iris(indices):
                        pts = []
                        for i in indices:
                            px, py = self.lm_px(face.landmark[i], w, h)
                            pts.append(map_point(px, py))
                        pts = np.array(pts)
                        center = pts.mean(axis=0).astype(int)
                        radius = int(np.mean([np.linalg.norm(p - center) for p in pts]))
                        cv2.circle(eye_crop, tuple(center), radius, (255, 255, 255), 2)
                        cv2.circle(eye_crop, tuple(center), 3, (0, 0, 255), -1) 

                    draw_iris(self.LEFT_IRIS_LANDMARKS)
                    draw_iris(self.RIGHT_IRIS_LANDMARKS)

                    for i in self.LEFT_EYE_CONTOUR + self.RIGHT_EYE_CONTOUR:
                        px, py = self.lm_px(face.landmark[i], w, h)
                        zx, zy = map_point(px, py)
                        cv2.circle(eye_crop, (zx, zy), 3, (0, 0, 255), -1)

                    
                    cv2.imshow(DIAGNOSTIC_WINDOW, eye_crop)

                    
                    gaze_x, gaze_y = self.calculate_gaze(face, h, w)
                    if gaze_x is not None and gaze_y is not None:
                        self.gaze_x = gaze_x
                        self.gaze_y = gaze_y
                        if gaze_callback:
                            gaze_callback(gaze_x, gaze_y)
                     
                    if self.blink_callback and self.detect_blink(face):
                        self.blink_callback()
                
              
                key = cv2.waitKey(1)
                if key & 0xFF == 27:
                    self.running = False
                
                if cv2.getWindowProperty(DIAGNOSTIC_WINDOW, cv2.WND_PROP_VISIBLE) < 1:
                    print("Ventana de Zoom cerrada. Deteniendo tracking.")
                    self.running = False
                    cv_window_open = False

                time.sleep(0.03)
            
            if self.cap:
                self.cap.release()
            cv2.destroyAllWindows() 
        
        thread = threading.Thread(target=track, daemon=True)
        thread.start()
        print("✓ Thread de tracking iniciado con visualización de zoom (Ventana única).")
        return True
    
    def stop(self):
        """Detiene el seguimiento y libera recursos (Llamado desde Tkinter)."""
        self.running = False
        
        if self.cap is not None:
            self.cap.release()
            self.cap = None 
        cv2.destroyAllWindows()
        
        print("✓ Tracking detenido (Cierre limpio).")