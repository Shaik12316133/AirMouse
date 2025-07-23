import cv2
import numpy as np
import mediapipe as mp
import pyautogui
import time
import threading
from PIL import Image, ImageDraw
import pystray

pyautogui.FAILSAFE = False

# --- Hand Gesture Controller Class ---
class HandController:
    def __init__(self):
        self.running = False
        self.show_feed = False  # Toggle to show/hide camera feed
        self.thread = None

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.mp_drawing = mp.solutions.drawing_utils

        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, 640)
        self.cap.set(4, 480)

        self.screen_w, self.screen_h = pyautogui.size()
        self.prev_x, self.prev_y = 0, 0
        self.smooth_factor = 2
        self.control_margin = 0.20

        self.pinch_active = False
        self.pinch_start_time = None
        self.PINCH_THRESHOLD = 20
        self.DRAG_HOLD_TIME = 1.0
        self.dragging = False

        self.click_delay = 0.6
        self.last_click_time = 0

        self.prev_time = time.time()  # For FPS

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()

    def toggle_feed(self):
        self.show_feed = not self.show_feed

    def _run(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self.hands.process(rgb_frame)

            if result.multi_hand_landmarks:
                for hand_landmarks, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
                    lm_list = [(int(lm.x * frame.shape[1]), int(lm.y * frame.shape[0])) for lm in hand_landmarks.landmark]

                    # --- Draw landmarks ---
                    if self.show_feed:
                        self.mp_drawing.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

                        # --- Bounding box ---
                        x_list = [pt[0] for pt in lm_list]
                        y_list = [pt[1] for pt in lm_list]
                        x_min, x_max = min(x_list), max(x_list)
                        y_min, y_max = min(y_list), max(y_list)
                        cv2.rectangle(frame, (x_min - 20, y_min - 20), (x_max + 20, y_max + 20), (0, 255, 0), 2)

                        # --- Label hand (Left/Right) ---
                        label = handedness.classification[0].label
                        cv2.putText(frame, label, (x_min - 30, y_min - 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

                    # --- Use only first hand for control ---
                    index_x, index_y = lm_list[8]
                    thumb_x, thumb_y = lm_list[4]
                    wrist_y = lm_list[0][1]

                    pinch_distance = np.hypot(index_x - thumb_x, index_y - thumb_y)
                    fingers_index_up = index_y < wrist_y - 30

                    if fingers_index_up:
                        margin_x = int(frame.shape[1] * self.control_margin)
                        margin_y = int(frame.shape[0] * self.control_margin)

                        target_x = np.interp(index_x, [margin_x, frame.shape[1] - margin_x], [0, self.screen_w])
                        target_y = np.interp(index_y, [margin_y, frame.shape[0] - margin_y], [0, self.screen_h])

                        distance_from_wrist = np.hypot(index_x - lm_list[0][0], index_y - wrist_y)
                        speed_multiplier = 1.0 + (40 / max(distance_from_wrist, 1))
                        speed_multiplier = min(speed_multiplier, 2.0)

                        curr_x = self.prev_x + (target_x - self.prev_x) / self.smooth_factor * speed_multiplier
                        curr_y = self.prev_y + (target_y - self.prev_y) / self.smooth_factor * speed_multiplier

                        pyautogui.moveTo(curr_x, curr_y)
                        self.prev_x, self.prev_y = curr_x, curr_y

                    # --- Pinch Gesture ---
                    if pinch_distance < self.PINCH_THRESHOLD:
                        if not self.pinch_active:
                            self.pinch_active = True
                            self.pinch_start_time = time.time()

                        pinch_duration = time.time() - self.pinch_start_time

                        if pinch_duration >= self.DRAG_HOLD_TIME and not self.dragging:
                            pyautogui.mouseDown()
                            self.dragging = True

                    else:
                        if self.pinch_active:
                            pinch_duration = time.time() - self.pinch_start_time

                            if pinch_duration < self.click_delay and not self.dragging:
                                if time.time() - self.last_click_time > self.click_delay:
                                    pyautogui.click()
                                    self.last_click_time = time.time()

                            if self.dragging:
                                pyautogui.mouseUp()
                                self.dragging = False

                        self.pinch_active = False
                        self.pinch_start_time = None

                    break  # Only process first hand

            # --- FPS Counter ---
            curr_time = time.time()
            fps = 1 / (curr_time - self.prev_time)
            self.prev_time = curr_time

            if self.show_feed:
                cv2.putText(frame, f'FPS: {int(fps)}', (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                cv2.imshow("Camera Feed", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.show_feed = False
                    cv2.destroyAllWindows()
            else:
                cv2.destroyAllWindows()


# --- Tray App Setup ---
controller = HandController()

def toggle_control(icon, item):
    if controller.running:
        controller.stop()
    else:
        controller.start()

def toggle_camera_feed(icon, item):
    controller.toggle_feed()

def exit_app(icon, item):
    controller.stop()
    icon.stop()

def create_image():
    image = Image.new('RGB', (64, 64), (0, 0, 0))
    dc = ImageDraw.Draw(image)
    dc.rectangle((8, 8, 56, 56), fill=(0, 255, 0))
    return image

icon = pystray.Icon("HandGestureControl")
icon.icon = create_image()
icon.menu = pystray.Menu(
    pystray.MenuItem('Enable/Disable Hand Control', toggle_control),
    pystray.MenuItem('Show/Hide Camera Feed', toggle_camera_feed),
    pystray.MenuItem('Exit', exit_app)
)

icon.run()
