import cv2
import numpy as np
from collections import deque

class BabyMotionDetector:
    def __init__(self, buffer_size=30, motion_threshold=0.8):
        self.frames_buffer = deque(maxlen=2)
        self.motion_buffer = deque(maxlen=buffer_size)
        self.motion_threshold = motion_threshold

    def detect_motion(self, new_frame, threshold=30):
        # check if image is color or grayscale
        if len(new_frame.shape) == 3:
            gray_frame = cv2.cvtColor(new_frame, cv2.COLOR_BGR2GRAY)
        else:
            gray_frame = new_frame

        gray_frame = cv2.GaussianBlur(gray_frame, (21, 21), 0)

        self.frames_buffer.append(gray_frame)

        if len(self.frames_buffer) == 1:
            return False, new_frame

        frame_diff = cv2.absdiff(self.frames_buffer[-2], self.frames_buffer[-1])
        _, thresh = cv2.threshold(frame_diff, threshold, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion_detected = bool(contours)

        # If motion is detected, draw rectangles around the motion areas
        if motion_detected:
            for contour in contours:
                (x, y, w, h) = cv2.boundingRect(contour)
                cv2.rectangle(new_frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

        return motion_detected, new_frame


    def is_baby_moving(self, new_frame):
        motion_detected, annotated_frame = self.detect_motion(new_frame)

        # Store the motion detection result in the motion_buffer
        self.motion_buffer.append(motion_detected)

        # Calculate the ratio of moving frames to the total number of frames in the buffer
        moving_ratio = sum(self.motion_buffer) / len(self.motion_buffer)

        return moving_ratio >= self.motion_threshold, annotated_frame
