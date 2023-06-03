import numpy as np
from PIL import Image, ImageOps  # Install pillow instead of PIL
import tensorflow as tf

CLASSES = ["in_crib", "not_in_crib"]
MODEL_PATH = "crib_model.tflite"

# Load the model outside the function
interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

# Get input and output tensors information
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

def predict_image(image_path):
    # Disable scientific notation for clarity
    np.set_printoptions(suppress=True)

    # Load the labels
    class_names = CLASSES

    # Create the array of the right shape to feed into the interpreter
    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)

    # Open and resize the image
    image = Image.open(image_path).convert("RGB")
    size = (224, 224)
    image = ImageOps.fit(image, size, Image.ANTIALIAS)

    # turn the image into a numpy array
    image_array = np.asarray(image)

    # Normalize the image
    normalized_image_array = (image_array.astype(np.float32) / 127.5) - 1

    # Load the image into the array
    data[0] = normalized_image_array

    # Set the tensor to point to the input data to be inferred
    interpreter.set_tensor(input_details[0]["index"], data)

    # Run the inference
    interpreter.invoke()

    # Retrieve the output from the inference
    output_data = interpreter.get_tensor(output_details[0]["index"])

    # Get the index of the highest confidence score
    index = np.argmax(output_data)

    # Get the class name and the confidence score
    class_name = class_names[index]
    confidence_score = output_data[0][index]

    return class_name, confidence_score
