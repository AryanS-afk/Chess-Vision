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

def count_pieces(board_snapshot):
    white = black = 0
    for data in board_snapshot.values():
        state = data["state"]
        if state == "white":
            white += 1
        elif state == "black":
            black += 1
    return white, black

def capture_hint_from_counts(old_white, old_black, new_white, new_black):
    if new_white == old_white and new_black == old_black - 1:
        return "white_captured_black"
    if new_white == old_white - 1 and new_black == old_black:
        return "black_captured_white"
    return None

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
        self.last_white, self.last_black = count_pieces(board_snapshot)
        self.game_started = True

        total = self.last_white + self.last_black
        if total != 32:
            print(
                f"[WARN] Expected 32 pieces, vision sees {total} "
                f"(white={self.last_white}, black={self.last_black})"
            )

        print("[INFO] Game started")

    def get_changed_squares(self, old_board, new_board):
        changed = []
        for sq in old_board:
            if old_board[sq]["state"] != new_board[sq]["state"]:
                changed.append(sq)
        return changed

    def _infer_from_to(self, changed, old_board, new_board, capture_hint):
        from_sq = None
        to_sq = None
        capture_candidates = []

        for sq in changed:
            old_state = old_board[sq]["state"]
            new_state = new_board[sq]["state"]
            self._log(sq, old_state, "->", new_state)

            if old_state != "empty" and new_state == "empty":
                from_sq = sq
            elif old_state == "empty" and new_state != "empty":
                to_sq = sq
            elif (
                old_state != "empty"
                and new_state != "empty"
                and old_state != new_state
            ):
                capture_candidates.append(sq)

        if to_sq is None and capture_candidates:
            if capture_hint == "white_captured_black":
                for sq in capture_candidates:
                    if old_board[sq]["state"] == "black":
                        to_sq = sq
                        break
            elif capture_hint == "black_captured_white":
                for sq in capture_candidates:
                    if old_board[sq]["state"] == "white":
                        to_sq = sq
                        break
            if to_sq is None:
                to_sq = capture_candidates[0]

        return from_sq, to_sq

    def _match_legal_move(self, changed, old_board, new_board, capture_hint):
        changed_set = set(changed)
        matches = []

        for move in self.board.legal_moves:
            from_sq = chess.square_name(move.from_square)
            to_sq = chess.square_name(move.to_square)

            if from_sq not in changed_set or to_sq not in changed_set:
                continue

            old_from = old_board[from_sq]["state"]
            new_from = new_board[from_sq]["state"]
            old_to = old_board[to_sq]["state"]
            new_to = new_board[to_sq]["state"]

            if old_from == "empty" or new_from != "empty":
                continue
            if new_to == "empty":
                continue

            if self.board.is_capture(move):
                if old_to == "empty" or old_to == new_to:
                    continue
            elif old_to != "empty":
                continue

            if capture_hint == "white_captured_black" and not self.board.is_capture(move):
                continue
            if capture_hint == "black_captured_white" and not self.board.is_capture(move):
                continue

            matches.append(move)

        if len(matches) == 1:
            return matches[0]
        return None

    def process_move(self, current_board):
        if not self.game_started:
            print("[ERROR] Start game first")
            return False

        current_board = copy.deepcopy(current_board)
        changed = self.get_changed_squares(self.last_board, current_board)

        self._log("\nChanged squares:", sorted(changed))

        if len(changed) < 2:
            print("[ERROR] No move detected")
            return False

        new_white, new_black = count_pieces(current_board)
        capture_hint = capture_hint_from_counts(
            self.last_white, self.last_black, new_white, new_black
        )
        if capture_hint:
            self._log("[INFO] Capture hint:", capture_hint)

        from_sq, to_sq = self._infer_from_to(
            changed, self.last_board, current_board, capture_hint
        )

        move = None
        if from_sq and to_sq:
            candidate = chess.Move.from_uci(from_sq + to_sq)
            if candidate in self.board.legal_moves:
                move = candidate

        if move is None:
            move = self._match_legal_move(
                changed, self.last_board, current_board, capture_hint
            )

        if move is None:
            self._log("FROM:", from_sq, "TO:", to_sq)
            print("[ERROR] Could not determine move")
            return False

        if move not in self.board.legal_moves:
            print(
                "[ILLEGAL]",
                chess.square_name(move.from_square),
                "->",
                chess.square_name(move.to_square),
            )
            return False

        san = self.board.san(move)
        from_sq = chess.square_name(move.from_square)
        to_sq = chess.square_name(move.to_square)

        if from_sq in self.piece_map:
            moving_piece = self.piece_map[from_sq]
            if to_sq in self.piece_map:
                del self.piece_map[to_sq]
            self.piece_map[to_sq] = moving_piece
            del self.piece_map[from_sq]

        self.board.push(move)
        self.last_board = current_board
        self.last_white, self.last_black = new_white, new_black

        print("[MOVE]", san)
        return san