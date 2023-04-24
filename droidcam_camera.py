import cv2
import numpy as np
import queue
import threading
import time

from img_utils import missing_frame_placeholder, resize_n_rotate

class PeekableQueue(queue.Queue):
    def peek(self):
        with self.mutex:
            return self.queue[0]

class DroidCam:
    def __init__(self, camera_ip, buffer_size=1, target_height=720):
        self.current_camera = 0
        self.camera_ip = camera_ip

        self.cap = cv2.VideoCapture(camera_ip)
        # give the camera time to warm up
        time.sleep(0.5)

        # get the width and height of the frame
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # draw a square image with a red warning sign in the middle
        self.warning_image = missing_frame_placeholder(256)

        # Initialize a queue to store frames
        self.frame_queue = PeekableQueue(maxsize=buffer_size)

        # Start a thread to read frames from the camera and update the queue
        self.frame_reader_thread = threading.Thread(target=self._frame_reader)
        self.frame_reader_thread.daemon = True
        self.frame_reader_thread.start()

    def _frame_reader(self):
        while True:
            ret, frame = self.cap.read()
            if ret:
                if self.frame_queue.full():
                    self.frame_queue.get()

                frame = resize_n_rotate(frame, target_height=720)
                self.frame_queue.put(frame)

            # Wait for the frame reader thread to read at least one frame
            while self.frame_queue.empty():
                # re-establish the connection
                self.cap = cv2.VideoCapture(self.camera_ip)
                time.sleep(0.5)
                print(f'reconnecting to {self.camera_ip}...')

    def set_current_camera(self, camera):
        self.current_camera = camera

    def get_frame(self):
        # print the size of the queue  
        if not self.frame_queue.empty():
            return self.frame_queue.peek()
        else:
            return self.warning_image
