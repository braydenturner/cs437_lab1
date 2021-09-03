import numpy as np
from tflite_runtime.interpreter import Interpreter
from PIL import Image
import io
import picamera
import re


CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480


class ObjectRecognition:

    def __init__(self, model="/tmp/detect.tflite"):
        self.interpreter = Interpreter("/tmp/detect.tflite")
        self.interpreter.allocate_tensors()
        self.labels = ObjectRecognition.load_labels("/tmp/coco_labels.txt")
        _, self.input_height, self.input_width, _ = self.interpreter.get_input_details()[0]['shape']

    @staticmethod
    def load_labels(path):
        """Loads the labels file. Supports files with or without index numbers."""
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            labels = {}
            for row_number, content in enumerate(lines):
                pair = re.split(r'[:\s]+', content.strip(), maxsplit=1)
                if len(pair) == 2 and pair[0].strip().isdigit():
                    labels[int(pair[0])] = pair[1].strip()
                else:
                    labels[row_number] = pair[0].strip()
        return labels

    def set_input_tensor(self, image):
        """Sets the input tensor."""
        tensor_index = self.interpreter.get_input_details()[0]['index']
        input_tensor = self.interpreter.tensor(tensor_index)()[0]
        input_tensor[:, :] = image

    def get_output_tensor(self, index):
        """Returns the output tensor at the given index."""
        output_details = self.interpreter.get_output_details()[index]
        tensor = np.squeeze(self.interpreter.get_tensor(output_details['index']))
        return tensor

    def detect_objects(self, image, threshold):
        """Returns a list of detection results, each a dictionary of object info."""
        self.set_input_tensor(image)
        self.interpreter.invoke()

        # Get all output details
        boxes = self.get_output_tensor(0)
        classes = self.get_output_tensor(1)
        scores = self.get_output_tensor(2)
        count = int(self.get_output_tensor(3))

        results = []
        for i in range(count):
            if scores[i] >= threshold:
                result = {
                    'bounding_box': boxes[i],
                    'class_id': classes[i],
                    'score': scores[i]
                }
                results.append(result)
        return results

    def detect(self):
        with picamera.PiCamera(resolution=(CAMERA_WIDTH, CAMERA_HEIGHT), framerate=30) as camera:
            stream = io.BytesIO()
            for _ in camera.capture_continuous(
                    stream, format='jpeg', use_video_port=True):
                image = Image.open(stream).convert('RGB').resize(
                    (self.input_width, self.input_height), Image.ANTIALIAS)
                results = self.detect_objects(image, 0.4)
                objects = [(self.labels[result['class_id']], result['score']) for result in results]
                print(objects)
                stream.seek(0)
                stream.truncate()

if __name__ == "__main__":
    obj_recognition = ObjectRecognition()
    obj_recognition.detect()