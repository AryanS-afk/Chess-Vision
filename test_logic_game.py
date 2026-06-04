"""Short simulated game: tests LogicEngine with perfect vision snapshots."""

import chess
from logic import LogicEngine

# 1.e4 e5 2.Nf3 Nc6 3.Bc4 Nf6 4.Ng5 d5 5.exd5 (pawn capture)
MOVES = [
    "e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "g8f6", "f3g5", "d7d5",
    "e4d5",   # white pawn capture
    "f6d5",   # black knight capture
]


def board_to_vision(board):
    out = {}
    for sq in chess.SQUARE_NAMES:
        piece = board.piece_at(chess.parse_square(sq))
        if piece is None:
            state = "empty"
        elif piece.color == chess.WHITE:
            state = "white"
        else:
            state = "black"
        out[sq] = {"state": state}
    return out


def main():
    engine = LogicEngine()
    board = chess.Board()
    engine.start_game(board_to_vision(board))

    ok = 0
    for uci in MOVES:
        move = chess.Move.from_uci(uci)
        if move not in board.legal_moves:
            print(f"\nSKIP illegal: {uci} (turn={'white' if board.turn else 'black'})")
            break

        board.push(move)
        snap = board_to_vision(board)
        print(f"\n--- {uci} ---")
        result = engine.process_move(snap)
        if result:
            print(f"OK: {result}")
            ok += 1
        else:
            print("FAIL")
            break

    print(f"\nResult: {ok}/{len(MOVES)} moves OK")
    print(f"FEN: {board.fen()}")


if __name__ == "__main__":
    main()
