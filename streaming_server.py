import os
import cv2
import numpy as np
import uuid
from dotenv import load_dotenv
import time

from flask import Flask, Response, render_template, request, jsonify, session
from flask_session import Session
from flask_httpauth import HTTPBasicAuth

from depthai_camera import DepthAI
from droidcam_camera import DroidCam

from img_utils import date_and_time, missing_frame_placeholder
from model_utils import model_prep
from motion_detection import BabyMotionDetector

load_dotenv()

auth = HTTPBasicAuth()
# Define your username and password here
USER_AUTH = {
    os.getenv("FLASK_USERNAME"): os.getenv("FLASK_PASSWORD")
}

@auth.verify_password
def verify_password(username, password):
    if username in USER_AUTH and USER_AUTH[username] == password:
        return username

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY")  # Set this to a secure random value
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

user_data = {}

target_height = 720
compression_quality = 60
deteciton_buffer = 60
motion_threshold = 0.5

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

pos_dir, neg_dir = model_prep()

def gen_frames(user_uuid):
    global user_data

    # Create a dictionary for the user in user_data if it doesn't exist
    # if user_uuid not in user_data:
    #     user_data[user_uuid] = {
    #         "motion_detector": BabyMotionDetector(buffer_size=deteciton_buffer, motion_threshold=motion_threshold),
    #     }

    motion_detector = user_data[user_uuid]['motion_detector']

    while True:
        selected_camera = user_data[user_uuid]['selected_camera']
        current_camera = user_data[user_uuid]['current_camera']

        # print(f'current camera: {current_camera}, selected camera: {selected_camera}')
        if current_camera != selected_camera:
            camera_instance.set_current_camera(selected_camera)
            motion_detector = BabyMotionDetector(buffer_size=deteciton_buffer, motion_threshold=motion_threshold)
            user_data[user_uuid]['motion_detector'] = motion_detector
            user_data[user_uuid]['is_baby_moving'] = False
            user_data[user_uuid]['current_camera'] = selected_camera
            continue

        frame = camera_instance.get_frame()

        # Apply CLAHE
        # frame = clahe.apply(frame)

        # Apply Non-local Means Denoising
        # frame = cv2.fastNlMeansDenoising(frame, None, h=10, templateWindowSize=7, searchWindowSize=21)

        if frame is not None:
            is_baby_moving, frame = motion_detector.is_baby_moving(frame.copy())
            user_data[user_uuid]['is_baby_moving'] = is_baby_moving
            # print(f'is baby moving: {is_baby_moving}')

            # a series of image processing steps to improve the image quality
            if current_camera == "night_cam":
                # convert to grayscale
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                frame = clahe.apply(frame)
                # Apply gamma correction
                frame = np.power(frame / 255.0, 1.0 / 1.5)
                frame = np.uint8(frame * 255)

            # add date and time
            frame = date_and_time(frame)
        else:
            frame = warning_image
            print("No frame received from camera. Trying again...")

        ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), compression_quality])

        # debug: Calculate the size of the resulting buffer (in kilobytes)
        # size = buffer.nbytes
        # size_kb = size / 1024
        # print(f"Quality: {compression_quality}, Size: {size_kb:.2f} KB")

        frame = buffer.tobytes()
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        # Sleep for a duration corresponding to 30 FPS
        time.sleep(1 / 40)
            
def set_user_uuid():
    global user_data

    # Generate a random code for each user session
    new_uuid = str(uuid.uuid4())
    session['user_uuid'] = new_uuid

    motion_detector = BabyMotionDetector(buffer_size=deteciton_buffer, motion_threshold=motion_threshold)

    user_data[new_uuid] = {
        "selected_camera": "day_cam",
        "current_camera": "day_cam",
        "is_baby_moving": False,
        'motion_detector': motion_detector,
    }

    return session['user_uuid']

@app.route('/')
@auth.login_required
def index():
    return render_template('index.html')

@app.route('/video_feed')
@auth.login_required
def video_feed():
    user_uuid = session.get('user_uuid')
    # check if user_uuid in user_data
    if user_uuid not in user_data:
        user_uuid = set_user_uuid()

    return Response(gen_frames(user_uuid), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/moving_status')
@auth.login_required
def moving_status():
    global user_data
    user_uuid = session.get('user_uuid')
    if user_uuid not in user_data:
        user_uuid = set_user_uuid()

    is_baby_moving = user_data[user_uuid]['is_baby_moving']
    return jsonify(is_moving=is_baby_moving)

@app.route('/switch_camera', methods=['POST'])
@auth.login_required
def switch_camera():
    command = request.form.get('command')
    if command == "toggle_flash":
        camera_instance.toggleFlash()
    elif command in ["day_cam", "night_cam"]:
        user_data[session['user_uuid']]['selected_camera'] = command
    return '', 204  # Return an empty response with a 204 No Content status

@app.errorhandler(400)
def bad_request(error):
    response = jsonify({"error": "Bad Request", "message": error.description})
    response.status_code = 400
    print("print inside errorhandler")
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
