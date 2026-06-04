# Chess-Vision

Real-time computer vision for a **physical chess board**. A webcam tracks the board with ArUco markers, warps the image to a top-down view, and uses a TensorFlow Lite model to classify each square as empty, occupied by a white piece, or occupied by a black piece. Move detection is layered on top with [python-chess](https://python-chess.readthedocs.io/) so legal moves are validated and printed in standard algebraic notation (SAN).

## How it works

```mermaid
flowchart LR
    Cam[Webcam] --> ArUco[ArUco corner detection]
    ArUco --> Warp[Perspective warp]
    Warp --> Split[64 square crops]
    Split --> ML[TFLite classifier]
    ML --> Logic[LogicEngine / python-chess]
```

1. **Board localization** — Four ArUco markers (`DICT_4X4_50`, IDs `0`–`3`) define the board corners. Their inner corners are used to compute a homography and warp the feed to an 800×800 board image.
2. **Square classification** — Each of the 64 squares is resized and passed through `model.tflite`, which outputs one of: `empty`, `black`, or `white` (see `labels.txt`).
3. **Move inference** — After you start a game, pressing **Space** compares the current board snapshot to the previous one, infers `from` / `to` squares from occupancy changes, and pushes the move if it is legal.

Calibration corners are saved to `calibration.json` so you can reload them on the next run.

## Requirements

- Python 3.10+ (tested with 3.12)
- A webcam
- A physical board with four ArUco markers placed at the corners (dictionary `4x4_50`, marker IDs `0`–`3`)

### Python dependencies

```bash
pip install opencv-python numpy python-chess ai-edge-litert
```

| Package | Role |
|---------|------|
| `opencv-python` | Camera capture, ArUco detection, warping, UI |
| `numpy` | Array / geometry operations |
| `python-chess` | Board state, legality, SAN |
| `ai-edge-litert` | TFLite inference (`model.tflite`) |

## Project layout

| File | Description |
|------|-------------|
| `vision_updated.py` | Main entry: camera loop, tracking, warping, keyboard controls |
| `occupancy_colour_ml.py` | TFLite wrapper: per-square occupancy + colour |
| `logic.py` | Game state, move detection, legality checks |
| `model.tflite` | Trained classifier (empty / black / white) |
| `labels.txt` | Model class labels |
| `calibration.json` | Saved board corner points (created when you freeze the board) |

## Setup

1. Clone the repository and install dependencies (see above).
2. Place ArUco markers `0`–`3` on the board corners so the camera can see all four.
3. If your webcam is not index `1`, edit `CAMERA_INDEX` at the top of `vision_updated.py`.
4. Run the application:

```bash
python vision_updated.py
```

Two windows open: **Camera** (live feed with board outline) and **Board** (warped, gridded view) once tracking succeeds.

## Controls

| Key | Action |
|-----|--------|
| **S** (Shift+S) | Start a new game from the current board snapshot |
| **Space** | Classify the board and process a move (requires game started) |
| **s** | Freeze board tracking and save calibration to `calibration.json` |
| **r** | Resume live tracking |
| **q** | Quit |

**Typical workflow**

1. Point the camera at the board until all four markers are detected (blue outline on **Camera**).
2. Press **s** to freeze tracking and save calibration when the warp looks correct.
3. Set up pieces on the physical board, then press **Shift+S** to start the game.
4. After each physical move, press **Space** to register it. Legal moves print as `[MOVE] e4`; illegal ones as `[ILLEGAL]`.

If you press **Space** before starting a game, you will see `[ERROR] Press Shift+S first`.

## ArUco marker layout

Markers use OpenCV’s `DICT_4X4_50` with IDs `0`–`3`. Each marker contributes one **inner** corner to the board quadrilateral:

| Marker ID | Corner used |
|-----------|-------------|
| 0 | Bottom-right |
| 1 | Bottom-left |
| 2 | Top-left |
| 3 | Top-right |

All four must be visible at least once before warping works; after freezing (**s**), tracking can stay off while you play.

## Model output

Per square, the classifier returns:

- `state`: `"empty"`, `"black"`, or `"white"`
- `confidence`: normalized score from the model output
- `empty_score`, `black_score`, `white_score`: raw class scores

The logic layer only uses occupancy transitions (`empty` ↔ piece) to infer moves; piece **types** (pawn, knight, etc.) are tracked internally via `STARTING_PIECES` in `logic.py` for SAN generation, not from vision.

## Troubleshooting

- **No Board window** — Ensure all four ArUco markers are in view and IDs match `0`–`3`.
- **Wrong camera** — Change `CAMERA_INDEX` in `vision_updated.py`.
- **Warp drift** — Press **s** again to re-freeze and overwrite `calibration.json`.
- **No move detected** — Make sure at least two squares changed between snapshots; only lift/place one move at a time before pressing **Space**.
- **Illegal move** — The vision snapshot may be wrong; check lighting, piece colour contrast, and that the warped grid aligns with squares.

## License

Add a license file if you plan to distribute this project.
