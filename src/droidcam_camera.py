import os
import cv2
import numpy as np
import queue
import threading
import time
import urllib.request as urlreq

from . import model_prep, resize_n_rotate

class PeekableQueue(queue.Queue):
    def peek(self):
        with self.mutex:
            return self.queue[0]

class DroidCam:
    def __init__(self, camera_ip, buffer_size=1, target_height=720):
        # switched from DroidCam to Android ip webcam

        self.current_camera = 0
        self.camera_ip = camera_ip
        self.target_height = target_height
        self.auto_focus = 0
        self.flash_on = 0
        self.reconnect_limit = 100

        self.jpeg_mode = True
        # self.jpeg_mode = False

        self.pos_dir, self.neg_dir = model_prep()

        # Set the camera resolution
        SIZE320x240 = '/video?320X240'
        SIZE640x480 = '/video?640X480'  # Default
        SIZE960x720 = '/video?960X720'
        SIZE_video = '/video'
        SIZE_empty = '/mjpegfeed?640x480'

        if self.jpeg_mode:
            # read from a still jpeg the camera server provides
            self.camera_source = camera_ip + "/shot.jpg"
            self.frame = self.request_latest_frame()
        else:
            camera_source = camera_ip + SIZE_video
            self.cap = cv2.VideoCapture(camera_source)
            self.ret, self.frame = self.cap.read()
            # self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            # self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # get the width and height of the frame
        self.height = self.frame.shape[0]
        self.width = self.frame.shape[1]

        # Initialize a queue to store frames
        # self.frame_queue = PeekableQueue(maxsize=buffer_size)

        # Start a thread to read frames from the camera and update the queue
        self.frame_reader_thread = threading.Thread(target=self._frame_reader)
        self.frame_reader_thread.daemon = True
        self.frame_reader_thread.start()

        # give the camera time to warm up and build up the buffer
        # time.sleep(1)

    def request_latest_frame(self):

        if self.jpeg_mode:
            imgResp = urlreq.urlopen(self.camera_source)

            # Check if the request was successful by looking at the status code
            if imgResp.status == 200:
                img_data = imgResp.read()
                img_np = np.array(bytearray(img_data), dtype=np.uint8)
                frame = cv2.imdecode(img_np, -1)
            else:
                print(f"Error in requesting the image. Status code: {imgResp.status}")
                return None

        else:
            self.ret, frame = self.cap.read()

        # Check if the image was successfully decoded by looking at its shape
        if frame is not None and frame.shape:
            return frame
        else:
            print("Error in decoding the image.")
            return None

    def autoFocus(self):
        autoFocus = self.camera_ip + '/cam/1/af'   # Execute Auto-Focus
        self.auto_focus = 1
        return self.cmdSender(autoFocus)

    def toggleFlash(self):
        if self.flash_on == 0:
            toggleFlash = self.camera_ip + '/enabletorch'
            self.flash_on = 1

            # after 10 seconds, call toggleFlash again to turn off the light
            timer = threading.Timer(10.0, self.toggleFlash)
            timer.start()
        else:
            toggleFlash = self.camera_ip + '/disabletorch'
            self.flash_on = 0
        return self.cmdSender(toggleFlash)

    def _frame_reader(self):
        while True:
        # while self.cap.isOpened():

            # empty queue first
            # if self.frame_queue.full():
            #     self.frame_queue.get()

            try:
                # self.ret, self.frame = self.cap.read()
                self.frame_raw = self.request_latest_frame()
            except Exception as e:
                print(e)
                self.frame_raw = None

            if self.frame_raw is not None:
                self.frame = resize_n_rotate(self.frame_raw, target_height=self.target_height)
                # self.frame_queue.put(frame)
            else:
                self.reconnect_limit -= 1

            # Wait for the frame reader thread to read at least one frame
            if self.reconnect_limit == 0:
                # re-establish the connection
                print(f'reconnecting to {self.camera_ip}...')
                self.cap.release()
                self.cap = cv2.VideoCapture(self.camera_ip)
                self.ret, self.frame = self.cap.read()
        
                if self.ret:
                    print(f'Connected to {self.camera_ip}')
                    self.reconnect_limit = 100
                else:
                    print(f'Failed to connect to {self.camera_ip}. Retrying in 5 seconds...')
                    time.sleep(5)  # Wait before retrying

                # self.frame = None

            # lower frame rate to lower CPU usage
            time.sleep(1/10)

    @staticmethod
    def cmdSender(cmd):
        ret = ''
        try:
            fp = urlreq.urlopen(cmd)
            ret = fp.read().decode("utf8")
            fp.close()
        except Exception as e:
            print(e)
        return ret

    def set_current_camera(self, camera):
        self.current_camera = camera

    def get_frame(self):
        if self.frame is None:
            return None
        else:
            return self.frame.copy()

