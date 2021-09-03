from recognize_objects import ObjectRecognition
from PIL import Image
import picar_4wd as fc
import picamera


def main():
    with ObjectRecognition() as recognizer:
        while True:
            recognized_objects = [recognized_object["class_id"] for recognized_object in recognizer.detect()]
            if "stop sign" in recognized_objects:
                fc.stop()
            else:
                fc.forward(20)


if __name__ == "__main__":
    try:
        main()
    finally:
        fc.stop()
