import copy
import chess

STARTING_PIECES = {
    "a1": "wR", "b1": "wN", "c1": "wB", "d1": "wQ",
    "e1": "wK", "f1": "wB", "g1": "wN", "h1": "wR",

    "a2": "wP", "b2": "wP", "c2": "wP", "d2": "wP",
    "e2": "wP", "f2": "wP", "g2": "wP", "h2": "wP",

    "a7": "bP", "b7": "bP", "c7": "bP", "d7": "bP",
    "e7": "bP", "f7": "bP", "g7": "bP", "h7": "bP",

    "a8": "bR", "b8": "bN", "c8": "bB", "d8": "bQ",
    "e8": "bK", "f8": "bB", "g8": "bN", "h8": "bR",
}

CASTLING_MAP = {
    frozenset(("e1", "h1", "f1", "g1")): "e1g1",
    frozenset(("e1", "a1", "d1", "c1")): "e1c1",
    frozenset(("e8", "h8", "f8", "g8")): "e8g8",
    frozenset(("e8", "a8", "d8", "c8")): "e8c8",
}


def count_pieces(board_snapshot):
    white = black = 0

    for data in board_snapshot.values():
        state = data["state"]

        if state == "white":
            white += 1

        elif state == "black":
            black += 1

    return white, black


class LogicEngine:

    def __init__(self, debug=False):

        self.board = chess.Board()

        self.piece_map = STARTING_PIECES.copy()

        self.last_board = None

        self.last_white = 0
        self.last_black = 0

        self.game_started = False

        self.debug = debug

    def _log(self, *args):

        if self.debug:
            print(*args)

    def start_game(self, board_snapshot):

        self.board = chess.Board()

        self.piece_map = STARTING_PIECES.copy()

        self.last_board = copy.deepcopy(board_snapshot)

        self.last_white, self.last_black = count_pieces(
            board_snapshot
        )

        self.game_started = True

        print("[INFO] Game started")

    def get_changed_squares(self, old_board, new_board):

        changed = []

        for sq in old_board:

            if (
                old_board[sq]["state"]
                !=
                new_board[sq]["state"]
            ):
                changed.append(sq)

        return changed

    def classify_changes(
        self,
        old_board,
        new_board,
        changed
    ):

        became_empty = []
        became_occupied = []
        color_changed = []

        for sq in changed:

            old_state = old_board[sq]["state"]
            new_state = new_board[sq]["state"]

            if (
                old_state != "empty"
                and
                new_state == "empty"
            ):
                became_empty.append(sq)

            elif (
                old_state == "empty"
                and
                new_state != "empty"
            ):
                became_occupied.append(sq)

            elif (
                old_state != "empty"
                and
                new_state != "empty"
                and
                old_state != new_state
            ):
                color_changed.append(sq)

        return (
            became_empty,
            became_occupied,
            color_changed
        )

    def update_piece_map(
        self,
        move,
        move_type,
        from_sq=None,
        to_sq=None,
        captured_sq=None,
    ):

        if move_type == "castle":

            if move.uci() == "e1g1":

                self.piece_map["g1"] = self.piece_map.pop("e1")
                self.piece_map["f1"] = self.piece_map.pop("h1")

            elif move.uci() == "e1c1":

                self.piece_map["c1"] = self.piece_map.pop("e1")
                self.piece_map["d1"] = self.piece_map.pop("a1")

            elif move.uci() == "e8g8":

                self.piece_map["g8"] = self.piece_map.pop("e8")
                self.piece_map["f8"] = self.piece_map.pop("h8")

            elif move.uci() == "e8c8":

                self.piece_map["c8"] = self.piece_map.pop("e8")
                self.piece_map["d8"] = self.piece_map.pop("a8")

            return

        moving_piece = self.piece_map.pop(from_sq)

        if move_type == "en_passant":
            self.piece_map.pop(captured_sq, None)

        else:
            self.piece_map.pop(to_sq, None)

        if move.promotion:

            if moving_piece.startswith("w"):
                self.piece_map[to_sq] = "wQ"
            else:
                self.piece_map[to_sq] = "bQ"

        else:
            self.piece_map[to_sq] = moving_piece

    def process_move(self, current_board):

        if not self.game_started:

            print("[ERROR] Start game first")
            return False

        current_board = copy.deepcopy(current_board)

        changed = self.get_changed_squares(
            self.last_board,
            current_board
        )

        if len(changed) < 2:

            print("[ERROR] No move detected")
            return False

        self._log("Changed:", sorted(changed))

        move = None
        move_type = None

        from_sq = None
        to_sq = None
        captured_sq = None

        (
            became_empty,
            became_occupied,
            color_changed
        ) = self.classify_changes(
            self.last_board,
            current_board,
            changed
        )

        #
        # CASTLING
        #
        if len(changed) == 4:

            uci = CASTLING_MAP.get(
                frozenset(changed)
            )

            if uci:

                move = chess.Move.from_uci(uci)
                move_type = "castle"

        #
        # EN PASSANT
        #
        elif (
            len(became_empty) == 2
            and
            len(became_occupied) == 1
        ):

            moving_color = (
                "w"
                if self.board.turn == chess.WHITE
                else "b"
            )

            for sq in became_empty:

                piece = self.piece_map.get(sq)

                if (
                    piece
                    and
                    piece.startswith(moving_color)
                ):
                    from_sq = sq
                else:
                    captured_sq = sq

            to_sq = became_occupied[0]

            move = chess.Move.from_uci(
                from_sq + to_sq
            )

            move_type = "en_passant"

        #
        # NORMAL MOVE
        #
        elif (
            len(became_empty) == 1
            and
            len(became_occupied) == 1
        ):

            from_sq = became_empty[0]
            to_sq = became_occupied[0]

        #
        # CAPTURE
        #
        elif (
            len(became_empty) == 1
            and
            len(color_changed) == 1
        ):

            from_sq = became_empty[0]
            to_sq = color_changed[0]

        else:

            print("[ERROR] Unknown move pattern")
            return False

        #
        # build move
        #
        if move is None:

            moving_piece = self.piece_map.get(from_sq)

            promotion = (
                moving_piece == "wP"
                and to_sq.endswith("8")
            ) or (
                moving_piece == "bP"
                and to_sq.endswith("1")
            )

            if promotion:

                move = chess.Move.from_uci(
                    from_sq + to_sq + "q"
                )

            else:

                move = chess.Move.from_uci(
                    from_sq + to_sq
                )

            if move_type is None:

                if len(color_changed):
                    move_type = "capture"
                else:
                    move_type = "normal"

        #
        # legality check
        #
        if move not in self.board.legal_moves:

            print(
                "[ILLEGAL]",
                move.uci()
            )

            return False

        san = self.board.san(move)

        self.update_piece_map(
            move,
            move_type,
            from_sq,
            to_sq,
            captured_sq,
        )

        self.board.push(move)

        self.last_board = current_board

        self.last_white, self.last_black = count_pieces(
            current_board
        )

        print("[MOVE]", san)

        return san