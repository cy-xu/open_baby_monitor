import os
import cv2
import numpy as np
import depthai as dai
from flask import Flask, Response, render_template, request, jsonify
from flask_httpauth import HTTPBasicAuth
import atexit
from dotenv import load_dotenv
import queue

from img_utils import date_and_time
from motion_detection import BabyMotionDetector

load_dotenv()

auth = HTTPBasicAuth()
# Define your username and password here
USER_DATA = {
    os.getenv("FLASK_USERNAME"): os.getenv("FLASK_PASSWORD")
}

@auth.verify_password
def verify_password(username, password):
    if username in USER_DATA and USER_DATA[username] == password:
        return username

app = Flask(__name__)
selected_camera = 1
current_camera = 1
is_baby_moving = False
deteciton_buffer = 300
motion_threshold = 0.5

class DepthAI:
    # This code uses a Singleton pattern for the DepthAI class, which ensures only one instance of the device is created and shared among all requests. This should resolve the issue with multiple devices accessing the video feed.

    def __init__(self):
        self.pipeline = dai.Pipeline()
        # create a queue as buffer for the frames
        self.rgb_buffer = queue.Queue(maxsize=10)
        self.left_buffer = queue.Queue(maxsize=10)

        self._init_rgb_camera()
        self._init_mono_camera()

        self.device = dai.Device(self.pipeline, usb2Mode=True)

        self.rgb_video_queue = self.device.getOutputQueue(name="rgb", maxSize=1, blocking=False)
        self.left_video_queue = self.device.getOutputQueue(name="left", maxSize=1, blocking=False)

        atexit.register(self._close_device)

    def _close_device(self):
        if self.device is not None:
            self.device.close()

    def create_mono(self, p, socket):
        mono = p.create(dai.node.MonoCamera)
        mono.setBoardSocket(socket)
        mono.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)

    def _init_rgb_camera(self):

        camRgb = self.pipeline.create(dai.node.ColorCamera)

        camRgb.setFps(10)
        camRgb.setBoardSocket(dai.CameraBoardSocket.RGB)
        camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
        camRgb.setVideoSize(1920, 1080)

        xoutRGB = self.pipeline.create(dai.node.XLinkOut)
        xoutRGB.setStreamName("rgb")

        camRgb.video.link(xoutRGB.input)

    def _init_mono_camera(self):

        # Define sources and outputs
        monoLeft = self.pipeline.create(dai.node.MonoCamera)
        monoLeft.setBoardSocket(dai.CameraBoardSocket.LEFT)
        monoLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_720_P)
        monoLeft.setFps(10)

        xoutLeft = self.pipeline.create(dai.node.XLinkOut)
        xoutLeft.setStreamName('left')

        # Linking
        monoLeft.out.link(xoutLeft.input)

    def get_rgb_queue(self):
        return self.rgb_video_queue

    def get_left_queue(self):
        return self.left_video_queue

depthai_instance = DepthAI()

clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

def gen_frames():
    global selected_camera
    global current_camera
    global is_baby_moving

    rgb_queue = depthai_instance.get_rgb_queue()
    left_queue = depthai_instance.get_left_queue()

    motion_detector = BabyMotionDetector(buffer_size=deteciton_buffer, motion_threshold=motion_threshold)

    while True:
        if selected_camera == 1:
            videoIn = rgb_queue.get()
            # videoIn = video_queue_rgb.get()
            # video = device.getOutputQueue(name="rgb_video", maxSize=1, blocking=False)
        elif selected_camera == 2:
            videoIn = left_queue.get()
        #     # video = device.getOutputQueue(name="left_video", maxSize=1, blocking=False)
        else:
            f"Camera 3 is not configured yet."

        if videoIn is None:
            print("videoIn is None")
            continue

        print(f'current camera: {current_camera}, selected camera: {selected_camera}')
        if current_camera != selected_camera:
            motion_detector = BabyMotionDetector(buffer_size=deteciton_buffer, motion_threshold=motion_threshold)
            is_baby_moving = False
            current_camera = selected_camera
            continue

        frame = np.array(videoIn.getCvFrame())

        # Apply CLAHE
        # frame = clahe.apply(frame)

        # if frame is grayscale, convert to 3 channel for denoising
        # frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        # Apply Non-local Means Denoising
        # frame = cv2.fastNlMeansDenoising(frame, None, h=10, templateWindowSize=7, searchWindowSize=21)

        is_baby_moving, frame = motion_detector.is_baby_moving(frame)
        # print(f'is baby moving: {is_baby_moving}')

        # add date and time
        frame = date_and_time(frame)

        ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
@auth.login_required
def index():
    return render_template('index.html')

@app.route('/video_feed')
@auth.login_required
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/moving_status')
def moving_status():
    return jsonify(is_moving=is_baby_moving)

@app.route('/switch_camera', methods=['POST'])
@auth.login_required
def switch_camera():
    global selected_camera
    camera = request.form.get('camera')
    if camera:
        selected_camera = int(camera)
        print(f'selected camera: {selected_camera}')
    return '', 204  # Return an empty response with a 204 No Content status

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
