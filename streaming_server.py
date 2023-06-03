import os
import cv2
import numpy as np
import uuid
from dotenv import load_dotenv
import time
import threading
import datetime
import pandas as pd

from flask import Flask, Response, render_template, request, jsonify, session
from flask_session import Session
from flask_httpauth import HTTPBasicAuth

from src import *

load_dotenv()

auth = HTTPBasicAuth()
# Define your username and password here
USER_AUTH = {os.getenv("FLASK_USERNAME"): os.getenv("FLASK_PASSWORD")}


@auth.verify_password
def verify_password(username, password):
    if username in USER_AUTH and USER_AUTH[username] == password:
        return username


app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv(
    "FLASK_SECRET_KEY"
)  # Set this to a secure random value
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

target_height = 640
compression_quality = 60
deteciton_buffer = 30
motion_threshold = 0.5
sleep_data_path = "baby_sleep_data.csv"

user_data = {}
user_data[0] = {
    "rgb_frame": None,
    "night_frame": None,
    "is_baby_moving": False,
    "baby_in_crib": {},
}
user_data[0]["motion_detector"] = BabyMotionDetector(
    buffer_size=deteciton_buffer, motion_threshold=motion_threshold
)

# camear_hardware = "depthai-oak-d"
camear_hardware = "droidcam"

# droidcam_ip = "http://192.168.50.2:4747"
droidcam_ip = "http://192.168.50.2:8080"
# droidcam_ip = 0

if camear_hardware == "depthai-oak-d":
    camera_instance = DepthAI()
elif camear_hardware == "droidcam":
    camera_instance = DroidCam(droidcam_ip, buffer_size=1, target_height=target_height)
    # camera_instance.toggle_flash = 1

clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

# draw a square image with a red warning sign in the middle
warning_image = missing_frame_placeholder(256)


# running in a separate thread to constantly update the frame
def update_frame():
    global user_data

    while True:
        frame_rgb = camera_instance.get_frame()

        if frame_rgb is not None:
            user_data[0]["rgb_frame"] = date_and_time(frame_rgb.copy())

            # a series of image processing steps to improve the image quality
            # convert to grayscale
            frame_gray = cv2.cvtColor(frame_rgb, cv2.COLOR_BGR2GRAY)
            frame_clahe = clahe.apply(frame_gray)
            # Apply gamma correction
            frame_gamma = np.power(frame_clahe / 255.0, 1.0 / 1.5)
            frame_gray = np.uint8(frame_gamma * 255)

            is_baby_moving, frame_gray = user_data[0]["motion_detector"].is_baby_moving(
                frame_gray
            )
            user_data[0]["is_baby_moving"] = 1 if is_baby_moving else 0
            # print(f'is baby moving: {is_baby_moving}')

            # add date and time
            user_data[0]["night_frame"] = date_and_time(frame_gray)

        else:
            user_data[0]["night_frame"] = warning_image
            user_data[0]["rgb_frame"] = warning_image
            # print("No frame received from camera. Trying again...")

        time.sleep(1 / 10)  # Sleep for a duration corresponding to 10 FPS


def reset_timer(time, flag_key):
    flags[flag_key] = 1
    timer = threading.Timer(time, reset_timer, args=[time, flag_key])
    timer.start()


def save_and_predict():
    global user_data
    positive_counter = 0
    total_counter = 0

    while True:
        frame = user_data[0]["night_frame"]
        # check if frame is a real image
        if frame is None:
            time.sleep(30)
            continue

        filename = "current_frame.jpg"
        try:
            cv2.imwrite(filename, frame)
            class_name, confidence_score = predict_image(filename)
            # print("Class:", class_name, "Confidence Score:", confidence_score)
        except:
            class_name = "not_in_crib"
            confidence_score = 0.0

        # Increase total counter
        total_counter += 1
        # If baby is in crib, increase positive counter
        if class_name == "in_crib":
            positive_counter += 1

        user_data[0]["baby_in_crib"] = {
            "class_name": class_name,
            "confidence_score": float(confidence_score),
        }

        # If total counter reaches 5 (indicating 5 minutes have passed)
        # record the result for this five-minute slot
        if total_counter == 5:
            slot_result = 1 if positive_counter >= 3 else 0

            # Prepare data to be stored - in this case, current time, prediction and confidence_score
            sleep_date, sleep_time = date_time_five_min()
            data_to_save = {
                "date": sleep_date,
                "time": sleep_time,
                "baby_in_crib": slot_result,
                "baby_moving": user_data[0]["is_baby_moving"],
            }

            # Convert your data into a DataFrame
            df = pd.DataFrame([data_to_save])

            # Append the data to your CSV file
            df.to_csv(sleep_data_path, mode="a", header=False, index=False)

            # Reset counters for the next slot
            positive_counter = 0
            total_counter = 0

        time.sleep(60)  # sleep for 1 minute


update_thread = threading.Thread(target=update_frame)
update_thread.daemon = True
update_thread.start()

predict_thread = threading.Thread(target=save_and_predict)
predict_thread.daemon = True
predict_thread.start()

# data collection
flags = {"save_negative": 1, "save_positive": 0, "save_frame": 1, "predict_crib": 1}
# this resets the flag to 1 again after 600 seconds
reset_timer(600.0, "save_negative")


def gen_frames(user_uuid):
    global user_data, save_negative, save_positive

    # Create a dictionary for the user in user_data if it doesn't exist
    # if user_uuid not in user_data:
    #     user_data[user_uuid] = {
    #         "motion_detector": BabyMotionDetector(buffer_size=deteciton_buffer, motion_threshold=motion_threshold),
    #     }

    # motion_detector = user_data[user_uuid]['motion_detector']

    while True:
        selected_camera = user_data[user_uuid]["selected_camera"]
        current_camera = user_data[user_uuid]["current_camera"]

        # print(f'current camera: {current_camera}, selected camera: {selected_camera}')
        if current_camera != selected_camera:
            camera_instance.set_current_camera(selected_camera)
            user_data[user_uuid]["is_baby_moving"] = False
            user_data[user_uuid]["current_camera"] = selected_camera
            continue

        # frame = camera_instance.get_frame()
        if current_camera == "night_cam":
            frame = user_data[0]["night_frame"]
        else:
            frame = user_data[0]["rgb_frame"]

        # Apply Non-local Means Denoising
        # frame = cv2.fastNlMeansDenoising(frame, None, h=10, templateWindowSize=7, searchWindowSize=21)

        ret, buffer = cv2.imencode(
            ".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), compression_quality]
        )

        # debug: Calculate the size of the resulting buffer (in kilobytes)
        # size = buffer.nbytes
        # size_kb = size / 1024
        # print(f"Quality: {compression_quality}, Size: {size_kb:.2f} KB")

        frame_bytes = buffer.tobytes()
        yield (
            b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )

        # data collection
        if flags["save_negative"] == 1:
            flags["save_negative"] = 0
            save_frame_to_file(frame, prefix="negative_")

        if flags["save_positive"] == 1:
            flags["save_positive"] = 0
            save_frame_to_file(frame, "positive_")

        # Sleep for a duration corresponding to 10 FPS
        time.sleep(1 / 10)


def set_user_uuid():
    global user_data

    # Generate a random code for each user session
    new_uuid = str(uuid.uuid4())
    session["user_uuid"] = new_uuid

    motion_detector = BabyMotionDetector(
        buffer_size=deteciton_buffer, motion_threshold=motion_threshold
    )

    user_data[new_uuid] = {
        "selected_camera": "day_cam",
        "current_camera": "day_cam",
        "is_baby_moving": False,
        "motion_detector": motion_detector,
    }

    return session["user_uuid"]


@app.route("/")
@auth.login_required
def index():
    return render_template("index.html")


@app.route("/video_feed")
@auth.login_required
def video_feed():
    user_uuid = session.get("user_uuid")
    # check if user_uuid in user_data
    if user_uuid not in user_data:
        user_uuid = set_user_uuid()

    return Response(
        gen_frames(user_uuid), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/moving_status")
@auth.login_required
def moving_status():
    global user_data
    user_uuid = session.get("user_uuid")
    if user_uuid not in user_data:
        user_uuid = set_user_uuid()

    is_baby_moving = user_data[user_uuid]["is_baby_moving"]
    return jsonify(is_moving=is_baby_moving)


@app.route("/in_crib")
def prediction():
    return jsonify(user_data[0]["baby_in_crib"])


@app.route("/sleep_grid")
def drawSleepGrid():
    # get the past week's sleep data
    sleep_list = get_sleep_data()
    return jsonify(sleep_list)


@app.route("/switch_camera", methods=["POST"])
@auth.login_required
def switch_camera():
    global user_data, flags
    command = request.form.get("command")
    if command == "toggle_flash":
        camera_instance.toggleFlash()
    elif command in ["day_cam", "night_cam"]:
        user_data[session["user_uuid"]]["selected_camera"] = command
    elif command == "save_positive_sample":
        flags["save_positive"] = 1
    elif command == "save_negative_sample":
        flags["save_negative"] = 1
    return "", 204  # Return an empty response with a 204 No Content status


@app.errorhandler(400)
def bad_request(error):
    response = jsonify({"error": "Bad Request", "message": error.description})
    response.status_code = 400
    print("print inside errorhandler")
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
