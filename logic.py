import chess


STARTING_PIECES = {
    "a1":"WR","b1":"WN","c1":"WB","d1":"WQ",
    "e1":"WK","f1":"WB","g1":"WN","h1":"WR",

    "a2":"WP","b2":"WP","c2":"WP","d2":"WP",
    "e2":"WP","f2":"WP","g2":"WP","h2":"WP",

    "a7":"BP","b7":"BP","c7":"BP","d7":"BP",
    "e7":"BP","f7":"BP","g7":"BP","h7":"BP",

    "a8":"BR","b8":"BN","c8":"BB","d8":"BQ",
    "e8":"BK","f8":"BB","g8":"BN","h8":"BR",
}


class LogicEngine:

    def __init__(self):

        self.board = chess.Board()

        self.piece_map = (
            STARTING_PIECES.copy()
        )

        self.last_board = None

        self.game_started = False

    def start_game(self, board_snapshot):

        self.board = chess.Board()

        self.piece_map = (
            STARTING_PIECES.copy()
        )

        self.last_board = board_snapshot

        self.game_started = True

        print(
            "[INFO] Game started"
        )

    def get_changed_squares(
        self,
        old_board,
        new_board
    ):

        changed = []

        for sq in old_board:

            old_state = (
                old_board[sq]["state"]
            )

            new_state = (
                new_board[sq]["state"]
            )

            if old_state != new_state:
                changed.append(sq)

        return changed

    def process_move(
        self,
        current_board
    ):

        if not self.game_started:

            print(
                "[ERROR] Press Shift+S first"
            )

            return False

        changed = (
            self.get_changed_squares(
                self.last_board,
                current_board
            )
        )

        if len(changed) < 2:

            print(
                "[ERROR] No move detected"
            )

            return False

        from_sq = None
        to_sq = None

        for sq in changed:

            old_state = (
                self.last_board[sq]["state"]
            )

            new_state = (
                current_board[sq]["state"]
            )

            if (
                old_state != "empty"
                and
                new_state == "empty"
            ):
                from_sq = sq

            elif (
                old_state == "empty"
                and
                new_state != "empty"
            ):
                to_sq = sq

            elif (
                old_state != new_state
            ):
                to_sq = sq

        if (
            from_sq is None
            or
            to_sq is None
        ):

            print(
                "[ERROR] Could not infer move"
            )

            return False

        move = chess.Move.from_uci(
            from_sq + to_sq
        )

        if move not in self.board.legal_moves:

            print(
                "[ILLEGAL]",
                from_sq,
                "->",
                to_sq
            )

            return False

        san = self.board.san(move)

        moving_piece = (
            self.piece_map[from_sq]
        )

        if to_sq in self.piece_map:
            del self.piece_map[to_sq]

        self.piece_map[to_sq] = (
            moving_piece
        )

        del self.piece_map[from_sq]

        self.board.push(move)

        self.last_board = (
            current_board
        )

        print(
            "[MOVE]",
            san
        )

        return san