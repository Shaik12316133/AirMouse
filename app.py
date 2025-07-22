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
        self.thread = None

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.5, min_tracking_confidence=0.5)

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

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.cap.isOpened():
            self.cap.release()

    def _run(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self.hands.process(rgb_frame)

            if result.multi_hand_landmarks:
                hand_landmarks = result.multi_hand_landmarks[0]
                lm_list = [(int(lm.x * frame.shape[1]), int(lm.y * frame.shape[0])) for lm in hand_landmarks.landmark]

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


# --- Tray App Setup ---
controller = HandController()

def toggle_control(icon, item):
    if controller.running:
        controller.stop()
        icon.menu = pystray.Menu(
            pystray.MenuItem('Enable Hand Control', toggle_control),
            pystray.MenuItem('Exit', exit_app)
        )
    else:
        controller.start()
        icon.menu = pystray.Menu(
            pystray.MenuItem('Disable Hand Control', toggle_control),
            pystray.MenuItem('Exit', exit_app)
        )

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
    pystray.MenuItem('Enable Hand Control', toggle_control),
    pystray.MenuItem('Exit', exit_app)
)

icon.run()
