import cv2
import numpy as np
import depthai as dai
from flask import Flask, Response, render_template, request
import atexit

app = Flask(__name__)
selected_camera = 1

class DepthAI:
    # This code uses a Singleton pattern for the DepthAI class, which ensures only one instance of the device is created and shared among all requests. This should resolve the issue with multiple devices accessing the video feed.

    device_rgb = None
    video_queue_rgb = None

    device_mono = None
    video_queue_mono = None

    def __init__(self):
        if DepthAI.device_rgb is not None:
            raise RuntimeError("This class is a singleton!")
        else:
            DepthAI.device_rgb, DepthAI.video_queue_rgb = self._init_rgb_camera()
            # DepthAI.device_rgb, DepthAI.video_queue_rgb = self._init_mono_camera()
            # DepthAI.device_mono, DepthAI.video_queue_mono = self._init_mono_camera()
            atexit.register(self._close_device)

    def _close_device(self):
        if DepthAI.device_rgb is not None:
            DepthAI.device_rgb.close()
        if DepthAI.device_mono is not None:
            DepthAI.device_mono.close()

    def _init_rgb_camera(self):
        pipeline = dai.Pipeline()

        camRgb = pipeline.create(dai.node.ColorCamera)
        camRgb.setFps(30)

        xoutVideo = pipeline.create(dai.node.XLinkOut)
        xoutVideo.setStreamName("video")

        camRgb.setBoardSocket(dai.CameraBoardSocket.RGB)
        camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
        camRgb.setVideoSize(1920, 1080)
        # camRgb.setVideoSize(1280, 720)

        xoutVideo.input.setBlocking(False)
        xoutVideo.input.setQueueSize(1)

        camRgb.video.link(xoutVideo.input)

        device = dai.Device(pipeline)
        video_queue = device.getOutputQueue(name="video", maxSize=1, blocking=False)

        return device, video_queue

    def _init_mono_camera(self):

        # Create pipeline
        pipeline = dai.Pipeline()

        # Define sources and outputs
        monoLeft = pipeline.create(dai.node.MonoCamera)
        monoLeft.setFps(30)

        xoutLeft = pipeline.create(dai.node.XLinkOut)
        xoutLeft.setStreamName('left')

        # Properties
        monoLeft.setBoardSocket(dai.CameraBoardSocket.LEFT)
        monoLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_720_P)

        # Linking
        monoLeft.out.link(xoutLeft.input)

        device = dai.Device(pipeline)
        video_queue = device.getOutputQueue(name="left", maxSize=4, blocking=False)

        return device, video_queue

    def get_device_rgb(self):
        return DepthAI.device_rgb, DepthAI.video_queue_rgb

    def get_device_mono(self):
        return DepthAI.device_mono, DepthAI.video_queue_mono

depthai_instance = DepthAI()

def gen_frames():
    global selected_camera
    device_rgb, video_queue_rgb = depthai_instance.get_device_rgb()
    # device_mono, video_queue_mono = depthai_instance.get_device_mono()

    while True:
        # if selected_camera == 1:
        #     frame = video_queue_rgb.get()
        # elif selected_camera == 2:
        #     frame = video_queue_mono.get()

        # frame = video_queue_rgb.get()
        frame = video_queue_rgb.tryGet()

        if frame is None:
            continue

        frame = np.array(frame.getCvFrame())
        # ret, buffer = cv2.imencode('.jpg', frame)
        ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/switch_camera', methods=['POST'])
def switch_camera():
    global selected_camera
    camera = request.form.get('camera')
    if camera:
        selected_camera = int(camera)
    return '', 204  # Return an empty response with a 204 No Content status

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
