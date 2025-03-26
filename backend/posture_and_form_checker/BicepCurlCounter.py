import cv2
import numpy as np
import time
import pyttsx3
import threading
import queue
import PoseModule as pm_modified

# Initialize TTS engine and message queue
engine = pyttsx3.init()
tts_queue = queue.Queue()
tts_lock = threading.Lock()


def tts_worker():
    """Background worker for text-to-speech"""
    while True:
        message = tts_queue.get()
        if message is None:
            break
        with tts_lock:
            try:
                engine.say(message)
                engine.runAndWait()
            except Exception as e:
                print(f"TTS Error: {str(e)}")
        tts_queue.task_done()


# Start TTS thread
tts_thread = threading.Thread(target=tts_worker, daemon=True)
tts_thread.start()

# Video input setup
video_capture = cv2.VideoCapture("./videos/biceps.mp4")
frame_delay = int(1000 / video_capture.get(cv2.CAP_PROP_FPS))
pose_detector = pm_modified.PoseDetectorModified()

# UI Constants
PRIMARY_COLOR = (0, 255, 255)  # Cyan
SECONDARY_COLOR = (255, 0, 150)  # Pink
ERROR_COLOR = (0, 0, 255)  # Red
SUCCESS_COLOR = (0, 255, 0)  # Green
BG_TRANSPARENCY = 0.7

# Exercise parameters
counter = 0
movement_dir = 0
form_errors = []
shoulder_history = []
hip_shoulder_distance_history = []

# Error logging variables
previous_form_errors = set()
message_queue = []
last_message_time = 0
MESSAGE_DELAY = 5  # seconds between messages

# Constants
MIN_ELBOW_ANGLE = 60
MAX_ELBOW_ANGLE = 160
SHOULDER_ANGLE_THRESHOLD = 20
HIP_SWAY_THRESHOLD = 0.1


def draw_gradient_rect(frame, start_point, end_point, color1, color2):
    """Draw vertical gradient rectangle"""
    for y in range(start_point[1], end_point[1]):
        alpha = (y - start_point[1]) / (end_point[1] - start_point[1])
        blend = tuple(
            [int(c1 * (1 - alpha) + c2 * alpha) for c1, c2 in zip(color1, color2)]
        )
        cv2.line(frame, (start_point[0], y), (end_point[0], y), blend, 1)


def rounded_rect(frame, pos, size, color, corner_radius=10, alpha=1.0):
    """Draw rounded rectangle with transparency"""
    x, y = pos
    w, h = size
    overlay = frame.copy()

    # Rounded rectangle
    cv2.rectangle(
        overlay, (x + corner_radius, y), (x + w - corner_radius, y + h), color, -1
    )
    cv2.rectangle(
        overlay, (x, y + corner_radius), (x + w, y + h - corner_radius), color, -1
    )
    cv2.circle(
        overlay, (x + corner_radius, y + corner_radius), corner_radius, color, -1
    )
    cv2.circle(
        overlay, (x + w - corner_radius, y + corner_radius), corner_radius, color, -1
    )
    cv2.circle(
        overlay, (x + corner_radius, y + h - corner_radius), corner_radius, color, -1
    )
    cv2.circle(
        overlay,
        (x + w - corner_radius, y + h - corner_radius),
        corner_radius,
        color,
        -1,
    )

    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)


# Main processing loop
frame_count = 0
while video_capture.isOpened():
    current_time = time.time()
    success, frame = video_capture.read()
    if not success:
        break

    frame_count += 1
    frame = cv2.resize(frame, (1280, 720))
    frame = pose_detector.findPose(frame, draw=True)
    landmarks_list = pose_detector.findPosition(frame, draw=False)
    form_errors = []
    current_stage = "Start"

    if landmarks_list:
        # Get key angles and positions
        elbow_angle = pose_detector.findAngle(frame, 11, 13, 15, landmarks_list)
        shoulder_angle = pose_detector.findAngle(frame, 23, 11, 13, landmarks_list)
        wrist_angle = pose_detector.findAngle(frame, 13, 15, 17, landmarks_list)

        # Get positions for hip-shoulder alignment check
        hip = landmarks_list[23][1:3]
        shoulder = landmarks_list[11][1:3]
        horizontal_distance = abs(hip[0] - shoulder[0]) / frame.shape[1]

        # Progress calculation
        progress_percentage = np.interp(
            elbow_angle, [MIN_ELBOW_ANGLE, MAX_ELBOW_ANGLE], [100, 0]
        )
        progress_bar_y = int(np.interp(progress_percentage, [0, 100], [600, 100]))

        # Enhanced Form Checks
        if elbow_angle > MAX_ELBOW_ANGLE + 25:
            form_errors.append("Extend your arm fully")
        elif elbow_angle < MIN_ELBOW_ANGLE - 45:
            form_errors.append("Don't squeeze too much at the top")

        # Shoulder stability check
        shoulder_history.append(shoulder_angle)
        if len(shoulder_history) > 10:
            shoulder_variance = np.var(shoulder_history[-10:])
            if shoulder_variance > SHOULDER_ANGLE_THRESHOLD:
                form_errors.append("Keep your shoulders steady")
            shoulder_history.pop(0)

        # Body sway detection
        hip_shoulder_distance_history.append(horizontal_distance)
        if len(hip_shoulder_distance_history) > 10:
            distance_variance = np.var(hip_shoulder_distance_history[-10:])
            if distance_variance > HIP_SWAY_THRESHOLD:
                form_errors.append("Reduce body sway")
            hip_shoulder_distance_history.pop(0)

        # Wrist alignment
        if not 160 < wrist_angle < 210:
            form_errors.append("Keep your wrist straight")

        # Rep speed monitoring
        if len(shoulder_history) > 1:
            rep_speed = abs(shoulder_history[-1] - shoulder_history[-2])
            if rep_speed > 5:
                form_errors.append("Slow down movement")

        # Rep counting logic
        if not form_errors:
            if progress_percentage >= 95 and elbow_angle <= MIN_ELBOW_ANGLE + 15:
                current_stage = "Up"
                if movement_dir == 1:
                    counter += 0.5
                    movement_dir = 0
                    shoulder_history.clear()
                    hip_shoulder_distance_history.clear()
            elif progress_percentage <= 5 and elbow_angle >= MAX_ELBOW_ANGLE - 15:
                current_stage = "Down"
                if movement_dir == 0:
                    counter += 0.5
                    movement_dir = 1

    # UI Drawing
    bar_color = PRIMARY_COLOR
    if form_errors:
        bar_color = ERROR_COLOR
    elif current_stage == "Up":
        bar_color = SECONDARY_COLOR

    # Draw progress bar
    draw_gradient_rect(frame, (1150, 50), (1200, 650), (50, 50, 50), (20, 20, 20))
    cv2.rectangle(frame, (1160, 100), (1180, 600), (40, 40, 40), -1)
    cv2.rectangle(frame, (1160, progress_bar_y), (1180, 600), bar_color, -1)
    cv2.circle(frame, (1170, progress_bar_y), 10, bar_color, -1)

    # Draw counter
    rounded_rect(frame, (30, 30), (200, 120), (30, 30, 30), alpha=BG_TRANSPARENCY)
    cv2.putText(frame, "REPS", (50, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, PRIMARY_COLOR, 2)
    cv2.putText(
        frame,
        str(int(counter)),
        (40, 145),
        cv2.FONT_HERSHEY_SIMPLEX,
        3,
        SECONDARY_COLOR if counter % 1 != 0 else SUCCESS_COLOR,
        4,
    )

    # Draw feedback panel
    rounded_rect(frame, (30, 180), (400, 300), (30, 30, 30), alpha=BG_TRANSPARENCY)
    cv2.putText(
        frame,
        "FORM FEEDBACK",
        (50, 220),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        PRIMARY_COLOR,
        2,
    )

    error_text_y = 260
    for error in form_errors:
        cv2.circle(frame, (50, error_text_y - 10), 5, ERROR_COLOR, -1)
        cv2.putText(
            frame,
            error,
            (80, error_text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )
        error_text_y += 40

    # Error message handling
    current_errors = set(form_errors)
    new_errors = current_errors - previous_form_errors
    resolved_errors = previous_form_errors - current_errors

    # Add new messages to queues
    for error in new_errors:
        message_queue.append((current_time, f"⚠️ FORM ERROR: {error}"))
        tts_text = error.lower().replace("your", "").replace("you", "")

    previous_form_errors = current_errors.copy()

    # Process console messages
    if message_queue and current_time - last_message_time >= MESSAGE_DELAY:
        msg_time, message = message_queue.pop(0)
        print(f"[{current_time:.1f}] {message}")
        message = message.split(":")[-1].strip()
        if message == "Don't squeeze too much at the top":
            tts_queue.put("Avoid over-squeezing at the top position")
        else:
            tts_queue.put(f"Please {message}")
        last_message_time = current_time

    # Apply vignette effect
    vignette = np.ones(frame.shape, dtype=np.float32)
    cv2.circle(
        vignette,
        (frame.shape[1] // 2, frame.shape[0] // 2),
        int(frame.shape[1] * 0.6),
        (0.7, 0.7, 0.7),
        -1,
    )
    frame = (frame * vignette).astype(np.uint8)

    # Show frame
    cv2.imshow("Bicep Curl Coach Pro", frame)
    if cv2.waitKey(10) & 0xFF == ord("q"):
        break

# Cleanup
video_capture.release()
cv2.destroyAllWindows()
tts_queue.put(None)
tts_thread.join()
