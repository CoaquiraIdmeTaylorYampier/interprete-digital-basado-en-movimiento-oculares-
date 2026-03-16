import cv2
import mediapipe as mp
import numpy as np

# ================== MEDIAPIPE ==================
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True
)

# ================== LANDMARKS ==================
LEFT_EYE_CONTOUR = [
    33, 7, 163, 144, 145, 153, 154, 155,
    133, 173, 157, 158, 159, 160, 161, 246
]

RIGHT_EYE_CONTOUR = [
    362, 382, 381, 380, 374, 373, 390, 249,
    263, 466, 388, 387, 386, 385, 384, 398
]

LEFT_IRIS  = [468, 469, 470, 471, 472]
RIGHT_IRIS = [473, 474, 475, 476, 477]

# ================== UTILS ==================
def lm_px(lm, w, h):
    """Convierte las coordenadas de landmark normalizadas a píxeles."""
    return int(lm.x * w), int(lm.y * h)

# ================== CAMERA ==================
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = face_mesh.process(rgb)

    # Inicializamos una bandera para saber si encontramos la cara
    face_found = False
    
    if result.multi_face_landmarks:
        face = result.multi_face_landmarks[0]
        face_found = True

        # --------- 1. CÁLCULO DEL BOUNDING BOX SOLO OJOS (Dinámico) ---------
        xs, ys = [], []
        # Obtenemos los puntos clave de los contornos de ambos ojos
        for i in LEFT_EYE_CONTOUR + RIGHT_EYE_CONTOUR:
            x, y = lm_px(face.landmark[i], w, h)
            xs.append(x)
            ys.append(y)

        # Establecemos un margen (padding) para el zoom
        pad = 30
        x1 = max(min(xs) - pad, 0)
        y1 = max(min(ys) - pad, 0)
        x2 = min(max(xs) + pad, w)
        y2 = min(max(ys) + pad, h)

        # --------- AÑADIDO: Dibujar el recuadro dinámico en el frame original ---------
        # Dibuja un rectángulo rojo alrededor del área que se está ampliando
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
        # -----------------------------------------------------------------------------

        # --------- 2. RECORTAR, REDIMENSIONAR y PROCESAR el ZOOM ---------
        eye_crop = frame[y1:y2, x1:x2].copy() # Usamos .copy() para evitar problemas de referencia
        if eye_crop.size == 0:
            # Si el recorte es inválido (ej. fuera de la imagen), saltamos la iteración
            continue

        # Redimensionamos la imagen para el efecto de zoom
        eye_crop = cv2.resize(eye_crop, (700, 300))
        ch, cw, _ = eye_crop.shape

        # Función para mapear las coordenadas del frame original al frame de zoom
        def map_point(px, py):
            # Escala las coordenadas y las desplaza según el punto de inicio del recorte
            zx = int((px - x1) * cw / (x2 - x1))
            zy = int((py - y1) * ch / (y2 - y1))
            return zx, zy

        # --------- CONTORNOS (VERDE) ---------
        def draw_contour(indices):
            pts = []
            for i in indices:
                px, py = lm_px(face.landmark[i], w, h)
                pts.append(map_point(px, py))
            pts = np.array(pts, np.int32)
            cv2.polylines(eye_crop, [pts], True, (0, 255, 0), 2) # Verde

        draw_contour(LEFT_EYE_CONTOUR)
        draw_contour(RIGHT_EYE_CONTOUR)

        # --------- IRIS (BLANCO) ---------
        def draw_iris(indices):
            pts = []
            for i in indices:
                px, py = lm_px(face.landmark[i], w, h)
                pts.append(map_point(px, py))
            pts = np.array(pts)
            # Cálculo del centro y radio del círculo del iris
            center = pts.mean(axis=0).astype(int)
            radius = int(np.mean([np.linalg.norm(p - center) for p in pts]))
            
            # Dibujar el círculo del iris (Blanco) y el punto central (Rojo)
            cv2.circle(eye_crop, tuple(center), radius, (255, 255, 255), 2) # Círculo blanco
            cv2.circle(eye_crop, tuple(center), 3, (0, 0, 255), -1) # Punto central rojo

        draw_iris(LEFT_IRIS)
        draw_iris(RIGHT_IRIS)

        # --------- PUNTOS ROJOS (AL FRENTE en el zoom) ---------
        for i in LEFT_EYE_CONTOUR + RIGHT_EYE_CONTOUR:
            px, py = lm_px(face.landmark[i], w, h)
            zx, zy = map_point(px, py)
            cv2.circle(eye_crop, (zx, zy), 3, (0, 0, 255), -1) # Puntos rojos pequeños
            
        # --------- MOSTRAR SOLO OJOS (El zoom) ---------
        cv2.imshow("Eye Zoom Tracker (Ampliacion)", eye_crop)

    # --------- MOSTRAR EL FRAME ORIGINAL ---------
    # Muestra el frame principal, que ahora tiene el recuadro dinámico
    cv2.imshow("Webcam Original", frame)

    if cv2.waitKey(1) & 0xFF == 27: # Presiona ESC para salir
        break

cap.release()
cv2.destroyAllWindows()