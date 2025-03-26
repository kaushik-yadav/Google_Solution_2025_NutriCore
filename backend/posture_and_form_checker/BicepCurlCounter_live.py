import cv2
import numpy as np
import PoseModule as pm_modified
import time
import pyttsx3

# Initialize video capture and pose detector
video_capture = cv2.VideoCapture(0)
pose_detector = pm_modified.PoseDetectorModified()

# UI Constants
PRIMARY_COLOR = (0, 255, 255)  # Cyan
SECONDARY_COLOR = (255, 0, 150)  # Pink
ERROR_COLOR = (0, 0, 255)  # Red
SUCCESS_COLOR = (0, 255, 0)  # Green
BG_TRANSPARENCY = 0.7

# Exercise parameters
frame_count = 0
counter = 0
movement_dir = 0
form_errors = []
shoulder_history = []
hip_shoulder_distance_history = []

# Error logging variables
frame_count = 0
previous_form_errors = set()
error_cooldown = (
    60  # Number of frames to wait before repeating same error (about 1 second))
)
message_queue = []
last_message_time = 0
MESSAGE_DELAY = 3
error_last_shown = {}

last_error_print_time = {}  # Track last print time for each error type
last_success_print_time = {}  # Track last print time for resolved errors
DEBOUNCE_SECONDS = 10  # Minimum seconds between repeated messages

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


engine = pyttsx3.init()
while video_capture.isOpened():
    current_time = time.time()
    success, frame = video_capture.read()
    if not success:
        break
    frame_count += 1  # Increment frame counter
    frame = cv2.resize(frame, (1280, 720))
    frame = pose_detector.findPose(frame, draw=True)
    landmarks_list = pose_detector.findPosition(frame, draw=False)
    form_errors = []
    current_stage = "Start"

    if len(landmarks_list) != 0:

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

        # Enhanced Form Checks #################################################
        # 1. Elbow Range of Motion
        # 160
        if elbow_angle > MAX_ELBOW_ANGLE + 25:
            form_errors.append("Extend arm fully")
        # 60
        elif elbow_angle < MIN_ELBOW_ANGLE - 45:
            form_errors.append("Don't Squeeze too much at the top")

        # 2. Shoulder Stability
        shoulder_history.append(shoulder_angle)
        if len(shoulder_history) > 10:
            shoulder_variance = np.var(shoulder_history[-10:])
            if shoulder_variance > SHOULDER_ANGLE_THRESHOLD:
                form_errors.append("Keep shoulders steady")
            shoulder_history.pop(0)

        # 3. Body Sway Detection
        hip_shoulder_distance_history.append(horizontal_distance)
        if len(hip_shoulder_distance_history) > 10:
            distance_variance = np.var(hip_shoulder_distance_history[-10:])
            if distance_variance > HIP_SWAY_THRESHOLD:
                form_errors.append("Reduce body sway")
            hip_shoulder_distance_history.pop(0)

        # 4. Wrist Alignment
        if not 160 < wrist_angle < 210:
            form_errors.append("Keep wrist straight")

        # 5. Rep Quality Monitoring
        rep_speed = 0
        if len(shoulder_history) > 1:
            rep_speed = abs(shoulder_history[-1] - shoulder_history[-2])
            if rep_speed > 5:
                form_errors.append("Slow down movement")

        # Rep Counting Logic ##################################################
        if len(form_errors) == 0:
            if progress_percentage >= 95:
                if elbow_angle <= MIN_ELBOW_ANGLE + 15:
                    current_stage = "Up"
                    if movement_dir == 1:
                        counter += 0.5
                        movement_dir = 0
                        shoulder_history = []
                        hip_shoulder_distance_history = []
            elif progress_percentage <= 5:
                if elbow_angle >= MAX_ELBOW_ANGLE - 15:
                    current_stage = "Down"
                    if movement_dir == 0:
                        counter += 0.5
                        movement_dir = 1
            else:
                current_stage = "Moving"

        # Enhanced UI Drawing ##################################################
        # Progress bar with dynamic color
        bar_color = PRIMARY_COLOR
        if len(form_errors) > 0:
            bar_color = ERROR_COLOR
        elif current_stage == "Up":
            bar_color = SECONDARY_COLOR

        draw_gradient_rect(frame, (1150, 50), (1200, 650), (50, 50, 50), (20, 20, 20))
        cv2.rectangle(frame, (1160, 100), (1180, 600), (40, 40, 40), -1)
        cv2.rectangle(frame, (1160, progress_bar_y), (1180, 600), bar_color, -1)
        cv2.circle(frame, (1170, progress_bar_y), 10, bar_color, -1)

        # Counter with animation
        rounded_rect(frame, (30, 30), (200, 120), (30, 30, 30), alpha=BG_TRANSPARENCY)
        cv2.putText(
            frame, "REPS", (50, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, PRIMARY_COLOR, 2
        )
        cv2.putText(
            frame,
            str(int(counter)),
            (40, 145),
            cv2.FONT_HERSHEY_SIMPLEX,
            3,
            SECONDARY_COLOR if counter % 1 != 0 else SUCCESS_COLOR,
            4,
        )

        # Dynamic Feedback Panel ##############################################
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
            # Icon and animated text
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

        # Stage Indicator with animation
        stage_color = SUCCESS_COLOR
        rounded_rect(frame, (1000, 30), (250, 80), (30, 30, 30), alpha=BG_TRANSPARENCY)
        cv2.putText(
            frame,
            current_stage.upper(),
            (1020, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            stage_color,
            2,
        )
    current_errors = set(form_errors)
    new_errors = current_errors - previous_form_errors
    resolved_errors = previous_form_errors - current_errors

    # Add new messages to queue
    for error in new_errors:
        message_queue.append((current_time, f"⚠️ FORM ERROR: {error}"))

    previous_form_errors = current_errors.copy()

    # Message printing system (3-second throttling)
    if message_queue and current_time - last_message_time >= MESSAGE_DELAY:
        msg_time, message = message_queue.pop(0)  # Get oldest message
        print(f"[{current_time:.1f}] {message}")
        engine.say(f"You should {error}")
        engine.runAndWait()
        last_message_time = current_time
    # Vignette Effect
    vignette = np.ones(frame.shape, dtype=np.float32)
    cv2.circle(
        vignette,
        (frame.shape[1] // 2, frame.shape[0] // 2),
        int(frame.shape[1] * 0.6),
        (0.7, 0.7, 0.7),
        -1,
    )
    frame = (frame * vignette).astype(np.uint8)

    cv2.imshow("Bicep Curl Coach Pro", frame)
    if cv2.waitKey(10) & 0xFF == ord("q"):
        break

video_capture.release()
cv2.destroyAllWindows()
