
import tkinter as tk
from PIL import Image, ImageTk
from pathlib import Path

FILES = "abcdefgh"
RANKS = "87654321"


class DigitalBoard:
    def __init__(self, image_folder="chesspics", square_size=80):
        self.square_size = square_size
        self.image_folder = Path(image_folder)

        self.root = tk.Tk()
        self.root.title("Chess Vision Digital Board")

        size = square_size * 8

        self.canvas = tk.Canvas(
            self.root,
            width=size,
            height=size,
            highlightthickness=0
        )
        self.canvas.pack()

        self.images = {}
        self._load_images()

    def _load_images(self):
        pieces = [
            "wK","wQ","wR","wB","wN","wP",
            "bK","bQ","bR","bB","bN","bP"
        ]

        for piece in pieces:
            path = self.image_folder / f"{piece}.png"

            if not path.exists():
                print(f"[WARN] Missing image: {path}")
                continue

            img = Image.open(path).convert("RGBA")
            img = img.resize(
                (self.square_size, self.square_size),
                Image.Resampling.LANCZOS
            )

            self.images[piece] = ImageTk.PhotoImage(img)

    def update_board(self, piece_map):
        self.canvas.delete("all")

        light = "#F0D9B5"
        dark = "#B58863"

        for row in range(8):
            for col in range(8):

                x1 = col * self.square_size
                y1 = row * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size

                colour = light if (row + col) % 2 == 0 else dark

                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=colour,
                    outline=colour
                )

        for square, piece in piece_map.items():

            if piece not in self.images:
                continue

            file = square[0]
            rank = square[1]

            col = FILES.index(file)
            row = RANKS.index(rank)

            x = col * self.square_size + self.square_size // 2
            y = row * self.square_size + self.square_size // 2

            self.canvas.create_image(
                x,
                y,
                image=self.images[piece]
            )

        self.root.update_idletasks()
        self.root.update()


if __name__ == "__main__":
    from logic import STARTING_PIECES

    gui = DigitalBoard()
    gui.update_board(STARTING_PIECES)

    gui.root.mainloop()
