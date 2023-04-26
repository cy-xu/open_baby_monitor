import os
import cv2

def model_prep():
    # directories for saving images
    positive_dir = "./data/baby_in_crib"
    negative_dir = "./data/not_in_crib"

    os.makedirs(positive_dir, exist_ok=True)
    os.makedirs(negative_dir, exist_ok=True)

    return positive_dir, negative_dir