import atexit
import depthai as dai
import numpy as np

class DepthAI:
    # This code uses a Singleton pattern for the DepthAI class, which ensures only one instance of the device is created and shared among all requests. This should resolve the issue with multiple devices accessing the video feed.

    def __init__(self):
        self.pipeline = dai.Pipeline()

        self._init_rgb_camera()
        self._init_mono_camera()
        self.current_camera = 0

        self.device = dai.Device(self.pipeline, usb2Mode=True)

        self.rgb_video_queue = self.device.getOutputQueue(name="rgb", maxSize=1, blocking=False)
        self.left_video_queue = self.device.getOutputQueue(name="left", maxSize=1, blocking=False)

        # Register a callback to close the device when the app exits
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
        camRgb.setBoardSocket(dai.CameraBoardSocket.RGB)
        camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
        camRgb.setVideoSize(1920, 1080)
        camRgb.setFps(10)

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

    # def get_rgb_queue(self):
    #     return self.rgb_video_queue

    # def get_left_queue(self):
    #     return self.left_video_queue
    
    def set_current_camera(self, camera):
        self.current_camera = camera
    
    def get_frame(self):
        if self.current_camera == 1:
            videoIn = self.rgb_video_queue.get()
        elif self.current_camera == 2:
            videoIn = self.left_video_queue.get()
        else:
            print("Camera 3 is not configured yet.")
        
        if videoIn is None:
            print("videoIn is None")
            return None
        
        frame = np.array(videoIn.getCvFrame())
        return frame