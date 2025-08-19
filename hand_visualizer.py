import threading
import cv2
import mediapipe as mp
import numpy as np
import time

# Beállítások
width, height = 1280, 720
debug_size = (640, 480)
fade_duration = 0.8  # másodperc

# MediaPipe setup
hands = mp.solutions.hands.Hands(max_num_hands=2, model_complexity=1)
cap = cv2.VideoCapture(0)

prev_openness = [0, 0]
prev_time = [time.time(), time.time()]
fade_intensity = [0.0, 0.0]
last_fade_time = [0.0, 0.0]
hand_heights = [0.0, 0.0]

light_canvas = np.zeros((height, width, 3), dtype=np.uint8)
lock = threading.Lock()
running = True

def create_light_mask(intensity_left, intensity_right, bg_brightness):
    mask = np.full((height, width), int(bg_brightness * 255), dtype=np.float32)

    for side, intensity in zip(['left', 'right'], [intensity_left, intensity_right]):
        center_x = int(width * 0.05) if side == 'left' else int(width * 0.95)
        center_y = int(height / 2)

        y, x = np.ogrid[:height, :width]
        distance = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
        fade = np.clip(1.0 - distance / (width * 0.7), 0, 1)
        mask += fade * intensity * 255

    mask = np.clip(mask, 0, 255)
    mask_blur = cv2.GaussianBlur(mask, (0, 0), sigmaX=90, sigmaY=90)
    mask_color = cv2.merge([mask_blur.astype(np.uint8)] * 3)
    return mask_color

def light_thread():
    global light_canvas
    while running:
        now = time.time()
        light_intensity = [0.0, 0.0]

        for i in range(2):
            time_since_fade = now - last_fade_time[i]
            if time_since_fade < fade_duration:
                alpha = 1 - (time_since_fade / fade_duration)
                light_intensity[i] = fade_intensity[i] * alpha

        avg_height = np.clip((hand_heights[0] + hand_heights[1]) / 2, 0, 1)
        bg_brightness = 0.25 * (1 - avg_height)  # alacsonyan fekete, magasan világosabb

        canvas = create_light_mask(light_intensity[0], light_intensity[1], bg_brightness)
        with lock:
            light_canvas = canvas
        time.sleep(1 / 60)

# Thread indítása
t = threading.Thread(target=light_thread)
t.start()

try:
    while True:
        now = time.time()
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)
        debug_view = frame.copy()

        if results.multi_hand_landmarks:
            for i, handLms in enumerate(results.multi_hand_landmarks):
                if i > 1: continue
                side_index = 0 if handLms.landmark[17].x < handLms.landmark[5].x else 1

                base = handLms.landmark[0]
                tip_ids = [4, 8, 12, 16, 20]
                distances = [np.sqrt((handLms.landmark[tid].x - base.x) ** 2 +
                                     (handLms.landmark[tid].y - base.y) ** 2)
                             for tid in tip_ids]
                openness = np.clip(np.mean(distances) / 0.35, 0, 1)
                hand_heights[side_index] = 1 - np.clip(base.y, 0, 1)

                cv2.putText(debug_view, f"{'Left' if side_index==0 else 'Right'}: {openness:.2f}",
                            (10, 30 + i * 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                dt = now - prev_time[side_index]
                delta = openness - prev_openness[side_index]

                if dt > 0.05 and delta > 0.1:
                    fade_intensity[side_index] = min(delta * 5, 1.0)
                    last_fade_time[side_index] = now

                prev_openness[side_index] = openness
                prev_time[side_index] = now

        with lock:
            current_canvas = light_canvas.copy()

        cv2.imshow("Debug", cv2.resize(debug_view, debug_size))
        cv2.imshow("Show", current_canvas)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    running = False
    t.join()
    cap.release()
    cv2.destroyAllWindows()
