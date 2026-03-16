import cv2
import mediapipe as mp
import numpy as np

cap = cv2.VideoCapture(0)
mp_face_mesh = mp.solutions.face_mesh

LEFT_IRIS = [468, 469, 470, 471, 472]
RIGHT_IRIS = [473, 474, 475, 476, 477]

LEFT_EYE = {
    "left": 133,
    "right": 33,
    "top": 159,
    "bottom": 145
}

RIGHT_EYE = {
    "left": 362,
    "right": 263,
    "top": 386,
    "bottom": 374
}

def eye_ratio(landmarks, eye, iris_points, w, h):
    # Centro del iris
    cx = np.mean([landmarks[i].x for i in iris_points]) * w
    cy = np.mean([landmarks[i].y for i in iris_points]) * h

    # Puntos del ojo
    left = landmarks[eye["left"]].x * w
    right = landmarks[eye["right"]].x * w
    top = landmarks[eye["top"]].y * h
    bottom = landmarks[eye["bottom"]].y * h

    # Ratios normalizados
    gaze_x = (cx - left) / (right - left)
    gaze_y = (cy - top) / (bottom - top)

    return gaze_x, gaze_y, int(cx), int(cy)

with mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True
) as face_mesh:

    while True:
        ret, frame = cap.read()
        if not ret: 
            continue
        
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        
        results = face_mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        if results.multi_face_landmarks:
            lm = results.multi_face_landmarks[0].landmark

            # Obtener ratios de ambos ojos
            gxL, gyL, cxL, cyL = eye_ratio(lm, LEFT_EYE, LEFT_IRIS, w, h)
            gxR, gyR, cxR, cyR = eye_ratio(lm, RIGHT_EYE, RIGHT_IRIS, w, h)

            # Promedio final de mirada
            gaze_x = (gxL + gxR) / 2
            gaze_y = (gyL + gyR) / 2

            # Dibujar centros
            cv2.circle(frame, (cxL, cyL), 2, (0,0,255), -1)
            cv2.circle(frame, (cxR, cyR), 2, (0,0,255), -1)

            # Mostrar valores
            cv2.putText(frame, f"GX: {gaze_x:.2f}  GY: {gaze_y:.2f}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

        cv2.imshow("Iris Tracking Real", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()
