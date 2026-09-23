import cv2
import mediapipe as mp
import math
import time
import numpy as np
import win32gui
import win32con
from pynput.keyboard import Controller, Key, Listener

WINDOW_NAME = "AI Virtual Keyboard"

CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720

DISPLAY_WIDTH = 1280
DISPLAY_HEIGHT = 620

KEY_W = 72
KEY_H = 60
KEY_GAP = 8
KEY_RADIUS = 14

PINCH_PRESS_DISTANCE = 38
PINCH_RELEASE_DISTANCE = 58

SMOOTHING = 0.35

keyboard_controller = Controller()

shift_active = False
caps_active = False

keyboard_visible = True
running = True

pinch_ready = True

last_clicked_button = None
last_clicked_time = 0

smooth_index_x = None
smooth_index_y = None

def on_global_key_press(key):
    global running
    global keyboard_visible

    if key == Key.f8:
        keyboard_visible = not keyboard_visible

        print(
            "Keyboard:",
            "SHOWN" if keyboard_visible else "HIDDEN"
        )

    elif key == Key.f10:
        print("Closing...")
        running = False

def rounded_rectangle(
    img,
    pt1,
    pt2,
    color,
    radius=15,
    thickness=-1,
):
    x1, y1 = pt1
    x2, y2 = pt2

    radius = min(
        radius,
        (x2 - x1) // 2,
        (y2 - y1) // 2,
    )

    if thickness == -1:
        cv2.rectangle(
            img,
            (x1 + radius, y1),
            (x2 - radius, y2),
            color,
            -1,
        )

        cv2.rectangle(
            img,
            (x1, y1 + radius),
            (x2, y2 - radius),
            color,
            -1,
        )

        cv2.circle(
            img,
            (x1 + radius, y1 + radius),
            radius,
            color,
            -1,
        )

        cv2.circle(
            img,
            (x2 - radius, y1 + radius),
            radius,
            color,
            -1,
        )

        cv2.circle(
            img,
            (x1 + radius, y2 - radius),
            radius,
            color,
            -1,
        )

        cv2.circle(
            img,
            (x2 - radius, y2 - radius),
            radius,
            color,
            -1,
        )

    else:
        cv2.line(
            img,
            (x1 + radius, y1),
            (x2 - radius, y1),
            color,
            thickness,
            cv2.LINE_AA,
        )

        cv2.line(
            img,
            (x1 + radius, y2),
            (x2 - radius, y2),
            color,
            thickness,
            cv2.LINE_AA,
        )

        cv2.line(
            img,
            (x1, y1 + radius),
            (x1, y2 - radius),
            color,
            thickness,
            cv2.LINE_AA,
        )

        cv2.line(
            img,
            (x2, y1 + radius),
            (x2, y2 - radius),
            color,
            thickness,
            cv2.LINE_AA,
        )

        cv2.ellipse(
            img,
            (x1 + radius, y1 + radius),
            (radius, radius),
            180,
            0,
            90,
            color,
            thickness,
            cv2.LINE_AA,
        )

        cv2.ellipse(
            img,
            (x2 - radius, y1 + radius),
            (radius, radius),
            270,
            0,
            90,
            color,
            thickness,
            cv2.LINE_AA,
        )

        cv2.ellipse(
            img,
            (x2 - radius, y2 - radius),
            (radius, radius),
            0,
            0,
            90,
            color,
            thickness,
            cv2.LINE_AA,
        )

        cv2.ellipse(
            img,
            (x1 + radius, y2 - radius),
            (radius, radius),
            90,
            0,
            90,
            color,
            thickness,
            cv2.LINE_AA,
        )

class Button:
    def __init__(
        self,
        x,
        y,
        w,
        h,
        label,
        value=None,
        shift_value=None,
        special=False,
    ):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

        self.label = label
        self.value = value if value is not None else label

        self.shift_value = shift_value
        self.special = special

    def contains(self, px, py):
        return (
            self.x <= px <= self.x + self.w
            and
            self.y <= py <= self.y + self.h
        )

    def get_display_label(self):
        global shift_active
        global caps_active
        if (
            isinstance(self.value, str)
            and len(self.value) == 1
            and self.value.isalpha()
        ):
            uppercase = shift_active ^ caps_active

            if uppercase:
                return self.value.upper()

            return self.value.lower()
        if (
            shift_active
            and self.shift_value is not None
        ):
            return self.shift_value

        return self.label

    def draw(
        self,
        frame,
        hover=False,
        clicked=False,
        active=False,
    ):

        if clicked:
            fill = (55, 190, 110)
            border = (120, 255, 175)

        elif active:
            fill = (115, 75, 30)
            border = (255, 180, 75)

        elif hover:
            fill = (105, 80, 40)
            border = (255, 190, 80)

        elif self.special:
            fill = (48, 48, 58)
            border = (105, 105, 125)

        else:
            fill = (34, 34, 42)
            border = (85, 85, 105)

        rounded_rectangle(
            frame,
            (
                self.x + 4,
                self.y + 5,
            ),
            (
                self.x + self.w + 4,
                self.y + self.h + 5,
            ),
            (12, 12, 16),
            KEY_RADIUS,
            -1,
        )

        rounded_rectangle(
            frame,
            (self.x, self.y),
            (
                self.x + self.w,
                self.y + self.h,
            ),
            fill,
            KEY_RADIUS,
            -1,
        )

        rounded_rectangle(
            frame,
            (self.x, self.y),
            (
                self.x + self.w,
                self.y + self.h,
            ),
            border,
            KEY_RADIUS,
            2,
        )

        cv2.line(
            frame,
            (
                self.x + KEY_RADIUS,
                self.y + 4,
            ),
            (
                self.x + self.w - KEY_RADIUS,
                self.y + 4,
            ),
            (100, 100, 115),
            1,
            cv2.LINE_AA,
        )

        label = self.get_display_label()

        font_scale = 0.68

        if len(label) > 5:
            font_scale = 0.38

        elif len(label) > 2:
            font_scale = 0.50

        text_size = cv2.getTextSize(
            label,
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            2,
        )[0]

        tx = (
            self.x
            + (self.w - text_size[0]) // 2
        )

        ty = (
            self.y
            + (self.h + text_size[1]) // 2
            - 2
        )

        cv2.putText(
            frame,
            label,
            (tx, ty),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (245, 245, 250),
            2,
            cv2.LINE_AA,
        )

        if active:
            cv2.circle(
                frame,
                (
                    self.x + self.w - 10,
                    self.y + 10,
                ),
                4,
                (80, 220, 255),
                -1,
                cv2.LINE_AA,
            )

def create_keyboard():
    buttons = []

    y = 55
    x = 45

    number_keys = [
        ("1", "!"),
        ("2", "@"),
        ("3", "#"),
        ("4", "$"),
        ("5", "%"),
        ("6", "^"),
        ("7", "&"),
        ("8", "*"),
        ("9", "("),
        ("0", ")"),
        ("-", "_"),
        ("=", "+"),
    ]

    for normal, shifted in number_keys:
        buttons.append(
            Button(
                x,
                y,
                KEY_W,
                KEY_H,
                normal,
                normal,
                shifted,
            )
        )

        x += KEY_W + KEY_GAP

    buttons.append(
        Button(
            x,
            y,
            180,
            KEY_H,
            "BACKSPACE",
            "BACKSPACE",
            special=True,
        )
    )

    y += KEY_H + KEY_GAP
    x = 70

    buttons.append(
        Button(
            x,
            y,
            100,
            KEY_H,
            "TAB",
            "TAB",
            special=True,
        )
    )

    x += 100 + KEY_GAP

    for letter in "QWERTYUIOP":
        buttons.append(
            Button(
                x,
                y,
                KEY_W,
                KEY_H,
                letter,
                letter.lower(),
            )
        )

        x += KEY_W + KEY_GAP

    buttons.append(
        Button(
            x,
            y,
            KEY_W,
            KEY_H,
            "[",
            "[",
            "{",
        )
    )

    x += KEY_W + KEY_GAP

    buttons.append(
        Button(
            x,
            y,
            KEY_W,
            KEY_H,
            "]",
            "]",
            "}",
        )
    )

    y += KEY_H + KEY_GAP
    x = 95

    buttons.append(
        Button(
            x,
            y,
            125,
            KEY_H,
            "CAPS",
            "CAPS",
            special=True,
        )
    )

    x += 125 + KEY_GAP

    for letter in "ASDFGHJKL":
        buttons.append(
            Button(
                x,
                y,
                KEY_W,
                KEY_H,
                letter,
                letter.lower(),
            )
        )

        x += KEY_W + KEY_GAP

    buttons.append(
        Button(
            x,
            y,
            KEY_W,
            KEY_H,
            ";",
            ";",
            ":",
        )
    )

    x += KEY_W + KEY_GAP

    buttons.append(
        Button(
            x,
            y,
            KEY_W,
            KEY_H,
            "'",
            "'",
            '"',
        )
    )

    x += KEY_W + KEY_GAP

    buttons.append(
        Button(
            x,
            y,
            140,
            KEY_H,
            "ENTER",
            "ENTER",
            special=True,
        )
    )

    y += KEY_H + KEY_GAP
    x = 145

    buttons.append(
        Button(
            x,
            y,
            135,
            KEY_H,
            "SHIFT",
            "SHIFT",
            special=True,
        )
    )

    x += 135 + KEY_GAP

    for letter in "ZXCVBNM":
        buttons.append(
            Button(
                x,
                y,
                KEY_W,
                KEY_H,
                letter,
                letter.lower(),
            )
        )

        x += KEY_W + KEY_GAP

    buttons.append(
        Button(
            x,
            y,
            KEY_W,
            KEY_H,
            ",",
            ",",
            "<",
        )
    )

    x += KEY_W + KEY_GAP

    buttons.append(
        Button(
            x,
            y,
            KEY_W,
            KEY_H,
            ".",
            ".",
            ">",
        )
    )

    x += KEY_W + KEY_GAP

    buttons.append(
        Button(
            x,
            y,
            KEY_W,
            KEY_H,
            "/",
            "/",
            "?",
        )
    )

    y += KEY_H + KEY_GAP

    buttons.append(
        Button(
            390,
            y,
            500,
            KEY_H,
            "SPACE",
            "SPACE",
            special=True,
        )
    )

    return buttons

def tap_key(key):
    keyboard_controller.press(key)
    keyboard_controller.release(key)


def send_to_windows(button):
    global shift_active
    global caps_active

    value = button.value

    if value == "BACKSPACE":
        tap_key(Key.backspace)
        return

    if value == "ENTER":
        tap_key(Key.enter)
        return

    if value == "TAB":
        tap_key(Key.tab)
        return

    if value == "SPACE":
        tap_key(Key.space)
        return

    if value == "SHIFT":
        shift_active = not shift_active
        return

    if value == "CAPS":
        caps_active = not caps_active
        return
    if (
        isinstance(value, str)
        and len(value) == 1
        and value.isalpha()
    ):
        uppercase = shift_active ^ caps_active

        char = (
            value.upper()
            if uppercase
            else value.lower()
        )

        keyboard_controller.type(char)

        if shift_active:
            shift_active = False

        return
    if (
        shift_active
        and button.shift_value is not None
    ):
        keyboard_controller.type(
            button.shift_value
        )

        shift_active = False

    else:
        keyboard_controller.type(
            str(value)
        )

def draw_hand(
    frame,
    hand_landmarks,
    mp_hands,
):
    h, w, _ = frame.shape
    for connection in mp_hands.HAND_CONNECTIONS:
        a = hand_landmarks.landmark[
            connection[0]
        ]

        b = hand_landmarks.landmark[
            connection[1]
        ]

        p1 = (
            int(a.x * w),
            int(a.y * h),
        )

        p2 = (
            int(b.x * w),
            int(b.y * h),
        )
        cv2.line(
            frame,
            p1,
            p2,
            (18, 18, 24),
            6,
            cv2.LINE_AA,
        )
        cv2.line(
            frame,
            p1,
            p2,
            (90, 220, 255),
            3,
            cv2.LINE_AA,
        )
    for i, lm in enumerate(
        hand_landmarks.landmark
    ):
        x = int(lm.x * w)
        y = int(lm.y * h)

        if i == 8:
            color = (255, 100, 220)
            radius = 6

        elif i == 4:
            color = (100, 240, 255)
            radius = 6

        else:
            color = (90, 220, 255)
            radius = 4

        cv2.circle(
            frame,
            (x, y),
            radius + 2,
            (18, 18, 24),
            -1,
            cv2.LINE_AA,
        )

        cv2.circle(
            frame,
            (x, y),
            radius,
            color,
            -1,
            cv2.LINE_AA,
        )

def setup_overlay():
    hwnd = win32gui.FindWindow(
        None,
        WINDOW_NAME,
    )

    if not hwnd:
        return

    style = win32gui.GetWindowLong(
        hwnd,
        win32con.GWL_EXSTYLE,
    )

    style |= win32con.WS_EX_LAYERED
    style |= win32con.WS_EX_TRANSPARENT
    style |= win32con.WS_EX_NOACTIVATE

    win32gui.SetWindowLong(
        hwnd,
        win32con.GWL_EXSTYLE,
        style,
    )
    win32gui.SetLayeredWindowAttributes(
        hwnd,
        0,
        255,
        win32con.LWA_COLORKEY,
    )

    win32gui.SetWindowPos(
        hwnd,
        win32con.HWND_TOPMOST,
        0,
        0,
        0,
        0,
        win32con.SWP_NOMOVE
        | win32con.SWP_NOSIZE
        | win32con.SWP_NOACTIVATE,
    )

def on_press(key):
    global running
    global keyboard_visible

    if key == Key.f8:
        keyboard_visible = not keyboard_visible

    elif key == Key.f10:
        running = False

def main():
    global running
    global keyboard_visible

    global shift_active
    global caps_active

    global pinch_ready

    global last_clicked_button
    global last_clicked_time

    global smooth_index_x
    global smooth_index_y
    listener = Listener(
        on_press=on_press
    )

    listener.start()
    cap = cv2.VideoCapture(0)

    cap.set(
        cv2.CAP_PROP_FRAME_WIDTH,
        CAMERA_WIDTH,
    )

    cap.set(
        cv2.CAP_PROP_FRAME_HEIGHT,
        CAMERA_HEIGHT,
    )

    if not cap.isOpened():
        print("Camera error.")
        listener.stop()
        return
    mp_hands = mp.solutions.hands

    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.70,
        min_tracking_confidence=0.70,
    )

    buttons = create_keyboard()
    cv2.namedWindow(
        WINDOW_NAME,
        cv2.WINDOW_NORMAL,
    )

    cv2.resizeWindow(
        WINDOW_NAME,
        DISPLAY_WIDTH,
        DISPLAY_HEIGHT,
    )

    blank = np.zeros(
        (
            DISPLAY_HEIGHT,
            DISPLAY_WIDTH,
            3,
        ),
        dtype=np.uint8,
    )

    cv2.imshow(
        WINDOW_NAME,
        blank,
    )

    cv2.waitKey(100)

    setup_overlay()

    print("")
    print("==============================")
    print("     AI VIRTUAL KEYBOARD")
    print("==============================")
    print("")
    print("Pinch : press")
    print("F8    : hide/show")
    print("F10   : exit")
    print("")

    while running:
        success, camera = cap.read()

        if not success:
            break

        camera = cv2.flip(
            camera,
            1,
        )

        camera = cv2.resize(
            camera,
            (
                CAMERA_WIDTH,
                CAMERA_HEIGHT,
            ),
        )

        rgb = cv2.cvtColor(
            camera,
            cv2.COLOR_BGR2RGB,
        )

        results = hands.process(rgb)
        display = np.zeros(
            (
                DISPLAY_HEIGHT,
                DISPLAY_WIDTH,
                3,
            ),
            dtype=np.uint8,
        )

        hovered = None
        hand = None

        index_x = None
        index_y = None

        thumb_x = None
        thumb_y = None

        pinch_distance = None

        if results.multi_hand_landmarks:
            hand = results.multi_hand_landmarks[0]

            index_tip = hand.landmark[8]
            thumb_tip = hand.landmark[4]

            raw_x = int(
                index_tip.x
                * DISPLAY_WIDTH
            )

            raw_y = int(
                index_tip.y
                * DISPLAY_HEIGHT
            )

            thumb_x = int(
                thumb_tip.x
                * DISPLAY_WIDTH
            )

            thumb_y = int(
                thumb_tip.y
                * DISPLAY_HEIGHT
            )
            if smooth_index_x is None:
                smooth_index_x = raw_x
                smooth_index_y = raw_y

            else:
                smooth_index_x = int(
                    smooth_index_x
                    +
                    (
                        raw_x
                        - smooth_index_x
                    )
                    * SMOOTHING
                )

                smooth_index_y = int(
                    smooth_index_y
                    +
                    (
                        raw_y
                        - smooth_index_y
                    )
                    * SMOOTHING
                )

            index_x = smooth_index_x
            index_y = smooth_index_y

            pinch_distance = math.hypot(
                raw_x - thumb_x,
                raw_y - thumb_y,
            )

            if keyboard_visible:
                for button in buttons:
                    if button.contains(
                        index_x,
                        index_y,
                    ):
                        hovered = button
                        break
                if (
                    pinch_ready
                    and hovered is not None
                    and pinch_distance
                    < PINCH_PRESS_DISTANCE
                ):
                    send_to_windows(
                        hovered
                    )

                    last_clicked_button = hovered
                    last_clicked_time = time.time()

                    pinch_ready = False
                if (
                    not pinch_ready
                    and pinch_distance
                    > PINCH_RELEASE_DISTANCE
                ):
                    pinch_ready = True

        else:
            smooth_index_x = None
            smooth_index_y = None

            pinch_ready = True

        if keyboard_visible:
            for button in buttons:
                hover = button == hovered

                clicked = (
                    button
                    == last_clicked_button
                    and
                    time.time()
                    - last_clicked_time
                    < 0.18
                )

                active = (
                    (
                        button.value == "SHIFT"
                        and shift_active
                    )
                    or
                    (
                        button.value == "CAPS"
                        and caps_active
                    )
                )

                button.draw(
                    display,
                    hover,
                    clicked,
                    active,
                )

        if hand is not None:
            draw_hand(
                display,
                hand,
                mp_hands,
            )
            cv2.circle(
                display,
                (
                    index_x,
                    index_y,
                ),
                18,
                (100, 80, 130),
                2,
                cv2.LINE_AA,
            )

            cv2.circle(
                display,
                (
                    index_x,
                    index_y,
                ),
                9,
                (255, 100, 220),
                2,
                cv2.LINE_AA,
            )
            if (
                pinch_distance
                < PINCH_PRESS_DISTANCE
            ):
                pinch_color = (
                    80,
                    255,
                    150,
                )

            else:
                pinch_color = (
                    150,
                    150,
                    170,
                )

            cv2.line(
                display,
                (
                    index_x,
                    index_y,
                ),
                (
                    thumb_x,
                    thumb_y,
                ),
                pinch_color,
                2,
                cv2.LINE_AA,
            )

        cv2.imshow(
            WINDOW_NAME,
            display,
        )

        cv2.waitKey(1)

    listener.stop()

    hands.close()

    cap.release()

    cv2.destroyAllWindows()

    print("Virtual Keyboard closed.")


if __name__ == "__main__":
    main()