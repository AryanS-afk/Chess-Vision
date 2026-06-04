import cv2
import numpy as np

from ai_edge_litert.interpreter import Interpreter


class OccupancyColourModel:

    def __init__(
        self,
        model_path="model.tflite"
    ):

        self.interpreter = Interpreter(
            model_path=model_path
        )

        self.interpreter.allocate_tensors()

        self.input_details = (
            self.interpreter.get_input_details()
        )

        self.output_details = (
            self.interpreter.get_output_details()
        )

        shape = (
            self.input_details[0]["shape"]
        )

        self.height = int(shape[1])
        self.width = int(shape[2])

        print(
            f"[INFO] Colour model loaded "
            f"({self.width}x{self.height})"
        )

    def predict(
        self,
        square_img
    ):

        img = cv2.resize(
            square_img,
            (
                self.width,
                self.height
            )
        )

        img = cv2.cvtColor(
            img,
            cv2.COLOR_BGR2RGB
        )

        img = np.expand_dims(
            img,
            axis=0
        )

        img = img.astype(
            np.uint8
        )

        self.interpreter.set_tensor(
            self.input_details[0]["index"],
            img
        )

        self.interpreter.invoke()

        output = self.interpreter.get_tensor(
            self.output_details[0]["index"]
        )[0]

        empty_score = int(output[0])
        black_score = int(output[1])
        white_score = int(output[2])

        best_class = int(
            np.argmax(output)
        )

        confidence = (
            max(output) / 255.0
        )

        if best_class == 0:

            state = "empty"

        elif best_class == 1:

            state = "black"

        else:

            state = "white"

        return {
            "state": state,
            "confidence": confidence,
            "empty_score": empty_score,
            "black_score": black_score,
            "white_score": white_score
        }

    def classify_board(
        self,
        squares
    ):

        result = {}

        for square, img in squares.items():

            result[square] = self.predict(
                img
            )

        return result