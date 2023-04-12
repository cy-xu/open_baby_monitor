import cv2
import datetime
import numpy as np

def choose_contrast_color(color):
    if len(color) == 1:
        # Grayscale image
        luminance = color[0]
    else:
        # Color image
        luminance = 0.2126 * color[0] + 0.7152 * color[1] + 0.0722 * color[2]
    
    if luminance > 128:
        return (0, 0, 0)  # Black color
    else:
        return (255, 255, 255)  # White color

def date_and_time(image):
    # Get the current date and time
    now = datetime.datetime.now()
    date_time_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # Set the font, scale, and color
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1
    font_thickness = 2

    # Calculate the text size and position
    text_size, _ = cv2.getTextSize(date_time_str, font, font_scale, font_thickness)
    text_x = image.shape[1] - text_size[0] - 10  # 10 pixels from the right edge
    text_y = image.shape[0] - 10  # 10 pixels from the bottom edge

    # Get the background color in the text area
    if len(image.shape) == 2:
        # Grayscale image
        bg_color = (np.mean(image[text_y - text_size[1]:text_y, text_x:text_x + text_size[0]]),)
    else:
        # Color image
        bg_color = np.mean(image[text_y - text_size[1]:text_y, text_x:text_x + text_size[0]], axis=(0, 1))

    # Choose a high-contrast text color
    font_color = choose_contrast_color(bg_color)

    # Add the date and time to the image
    cv2.putText(image, date_time_str, (text_x, text_y), font, font_scale, font_color, font_thickness)

    return image