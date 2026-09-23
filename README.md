# AI Virtual Keyboard

AI Virtual Keyboard is a touch-free virtual keyboard controlled using hand gestures and a webcam.

The application uses real-time hand tracking to detect the user's index finger and thumb. Moving the index finger allows the user to select a virtual key, while a pinch gesture between the index finger and thumb presses the selected key.

The keyboard appears as a transparent overlay on Windows, allowing users to type directly into applications such as Notepad, browsers, text editors, and other programs.

## Features

- Real-time hand tracking
- Touch-free keyboard control
- Index finger cursor tracking
- Pinch gesture for key presses
- Transparent Windows overlay
- Click-through interface
- QWERTY keyboard layout
- Number and symbol keys
- Shift support
- Caps Lock support
- Backspace
- Enter
- Tab
- Space
- Smooth cursor movement
- Pinch-release detection to prevent repeated key presses
- Visual hover and press feedback
- Active Shift and Caps Lock indicators
- Global keyboard shortcuts

## Controls

| Action | Control |
| --- | --- |
| Move cursor | Index finger |
| Press a key | Pinch index finger and thumb |
| Hide / Show keyboard | F8 |
| Exit application | F10 |

## Technologies

- Python
- OpenCV
- MediaPipe
- NumPy
- pynput
- PyWin32

## Requirements

- Windows
- Python 3.12
- Webcam

## Installation

Clone the repository:

```bash
git clone YOUR_REPOSITORY_URL
cd virtual-keyboard
```

Create a virtual environment:

```bash
py -3.12 -m venv venv
```

Activate the virtual environment:

```bash
.\venv\Scripts\Activate.ps1
```

Install the required packages:

```bash
pip install -r requirements.txt
```

## Run

Start the application with:

```bash
python main.py
```

Allow access to the webcam if Windows requests camera permission.

## How It Works

The webcam captures the user's hand in real time. MediaPipe detects hand landmarks, including the index fingertip and thumb tip.

The index fingertip is mapped to the virtual keyboard and acts as the cursor. When the distance between the index finger and thumb falls below the configured pinch threshold, the currently selected key is pressed.

The application uses `pynput` to send the selected key to Windows, allowing the virtual keyboard to type into other applications.

The interface is rendered using OpenCV and displayed as a transparent, always-on-top Windows overlay using PyWin32.

## Project Structure

```text
virtual-keyboard/
├── main.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Notes

The application currently supports Windows because the transparent overlay uses Windows-specific APIs through PyWin32.

Hand tracking accuracy can vary depending on lighting, camera quality, hand position, and distance from the webcam.

## License

This project is intended for educational and experimental purposes.