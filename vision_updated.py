
import cv2
import numpy as np
import json
from pathlib import Path
from occupancy_colour_ml import (
    OccupancyColourModel
)
from logic import LogicEngine
from digital_board import DigitalBoard


CAMERA_INDEX = 1
BOARD_SIZE = 800
CALIBRATION_FILE = "calibration.json"

MARKER_IDS = [0,1,2,3]
MARKER_INNER_CORNER = {
    0: 2,  # BR
    1: 3,  # BL
    2: 0,  # TL
    3: 1   # TR
}

FILES = "abcdefgh"
RANKS = "87654321"


class VisionSystem:
    def __init__(self):
        self.cap = cv2.VideoCapture(CAMERA_INDEX)
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(
            cv2.aruco.DICT_4X4_50
        )
        self.detector = cv2.aruco.ArucoDetector(
            self.aruco_dict,
            cv2.aruco.DetectorParameters()
        )

        self.tracking = True
        self.saved_board_pts = None
        self.board_pts = None
        self.last_marker_positions = {}
        self.load_calibration()

    def load_calibration(self):
        p = Path(CALIBRATION_FILE)
        if p.exists():
            data = json.loads(p.read_text())
            self.board_pts = np.array(
                data["board_pts"],
                dtype=np.float32
            )
            self.locked = True
            print("[INFO] Calibration loaded")

    def save_calibration(self):
        if self.board_pts is None:
            return

        with open(CALIBRATION_FILE, "w") as f:
            json.dump(
                {"board_pts": self.board_pts.tolist()},
                f,
                indent=2
            )

        print("[INFO] Calibration saved")

    def detect_board(self, frame):
        corners, ids, _ = self.detector.detectMarkers(frame)

        if ids is None:
            return None

        ids = ids.flatten()

        found = {}

        for c, marker_id in zip(corners, ids):
            if marker_id not in MARKER_IDS:
                continue

            pts = c[0]
            found[marker_id] = pts[MARKER_INNER_CORNER[marker_id]]

        # Update stored marker positions

        for marker_id, point in found.items():
            self.last_marker_positions[marker_id] = point

        # Need all four markers only once
        if len(self.last_marker_positions) < 4:
            return None

        return np.array([
            self.last_marker_positions[0],
            self.last_marker_positions[1],
            self.last_marker_positions[2],
            self.last_marker_positions[3]
        ], dtype=np.float32)

    def warp_board(self, frame):
        if self.board_pts is None:
            return None

        dst = np.array([
            [0, 0],
            [BOARD_SIZE - 1, 0],
            [BOARD_SIZE - 1, BOARD_SIZE - 1],
            [0, BOARD_SIZE - 1]
        ], dtype=np.float32)

        M = cv2.getPerspectiveTransform(
            self.board_pts,
            dst
        )

        return cv2.warpPerspective(
            frame,
            M,
            (BOARD_SIZE, BOARD_SIZE)
        )

    def split_squares(self, warped):
        squares = {}

        cell = BOARD_SIZE // 8

        for r in range(8):
            for c in range(8):
                name = FILES[c] + RANKS[r]

                y1 = r * cell
                y2 = (r + 1) * cell
                x1 = c * cell
                x2 = (c + 1) * cell

                squares[name] = warped[y1:y2, x1:x2]

        return squares

    def occupancy_map(
            self,
            warped,
            model
    ):

        squares = self.split_squares(
            warped
        )

        return model.classify_board(
            squares
        )

    def draw_grid(self, warped):
        out = warped.copy()

        step = BOARD_SIZE // 8

        for i in range(9):
            p = i * step

            cv2.line(out, (p, 0), (p, BOARD_SIZE),
                     (0,255,0), 1)

            cv2.line(out, (0, p), (BOARD_SIZE, p),
                     (0,255,0), 1)

        return out



def print_ascii_board(board):

    print()
    print("  a b c d e f g h")

    for rank in range(8):

        rank_num = 8 - rank

        row = []

        for file in "abcdefgh":

            sq = file + str(rank_num)

            state = board[sq]["state"]

            if state == "empty":
                row.append(".")

            elif state == "white":
                row.append("W")

            else:
                row.append("B")

        print(
            f"{rank_num} "
            + " ".join(row)
        )

    print()


def main():
    vision = VisionSystem()

    model = OccupancyColourModel(
        "model.tflite"
    )

    logic = LogicEngine()
    gui = DigitalBoard()
    gui.update_board(logic.piece_map)

    while True:

        ret, frame = vision.cap.read()

        if not ret:
            continue

        if vision.tracking:
            pts = vision.detect_board(frame)

            if pts is not None:
                vision.board_pts = pts

                cv2.polylines(
                    frame,
                    [pts.astype(np.int32)],
                    True,
                    (255,0,0),
                    2
                )

        warped = vision.warp_board(frame)

        if not vision.tracking and vision.saved_board_pts is not None:
            vision.board_pts = vision.saved_board_pts

        if warped is not None:
            warped = vision.draw_grid(warped)

            mode = "TRACKING" if vision.tracking else "FROZEN"
            cv2.putText(
                frame,
                f"MODE: {mode}",
                (10,30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0,255,0),
                2
            )

            cv2.imshow("Board", warped)

        cv2.imshow("Camera", frame)

        key = cv2.waitKey(1) & 0xFF


        if key == ord("p"):
            print("[INFO] P key unused. Use S to freeze board.")

        elif key == ord("r"):

            vision.tracking = True

            print("[INFO] Tracking enabled")

        elif key == ord("s"):

            if vision.board_pts is not None:

                vision.saved_board_pts = vision.board_pts.copy()

                vision.board_pts = vision.saved_board_pts.copy()

                vision.tracking = False

                vision.save_calibration()

                print("[INFO] Board frozen and calibration saved")




        elif key == ord(" "):

            if warped is not None:

                board = vision.occupancy_map(
                    warped,
                    model
                )

                san = logic.process_move(board)

                if san:
                    print(san)
                    gui.update_board(logic.piece_map)


        elif key == ord("S"):

            if warped is not None:

                board = vision.occupancy_map(
                    warped,
                    model
                )

                logic.start_game(board)

                gui.update_board(logic.piece_map)

                print("Game started")
        elif key == ord("q"):
            break

    vision.cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
