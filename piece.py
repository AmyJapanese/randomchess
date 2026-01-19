# piece.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional

Pos = Tuple[int, int]  # (row, col)


@dataclass(frozen=True)
class Piece:
    kind: str   # 'K','Q','R','B','N','P'
    color: str  # 'white' or 'black'


def generate_moves(board, pos: Pos) -> List[Pos]:
    """
    駒の種類ごとに「動ける候補マス（チェック無視）」を返す。
    board は以下のメソッドを持つ想定（duck typing）:
      - in_bounds(r, c) -> bool
      - get(r, c) -> Optional[Piece]
    """
    r, c = pos
    piece = board.get(r, c)
    if piece is None:
        return []

    k = piece.kind
    if k == 'N':
        return _knight_moves(board, pos, piece.color)
    if k == 'B':
        return _slider_moves(board, pos, piece.color, directions=[(-1, -1), (-1, 1), (1, -1), (1, 1)])
    if k == 'R':
        return _slider_moves(board, pos, piece.color, directions=[(-1, 0), (1, 0), (0, -1), (0, 1)])
    if k == 'Q':
        return _slider_moves(
            board, pos, piece.color,
            directions=[(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]
        )
    if k == 'K':
        return _king_moves(board, pos, piece.color)
    if k == 'P':
        return _pawn_moves(board, pos, piece.color)

    return []


def _knight_moves(board, pos: Pos, color: str) -> List[Pos]:
    r, c = pos
    moves: List[Pos] = []
    jumps = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
             (1, -2), (1, 2), (2, -1), (2, 1)]
    for dr, dc in jumps:
        nr, nc = r + dr, c + dc
        if not board.in_bounds(nr, nc):
            continue
        target = board.get(nr, nc)
        if target is None:
            moves.append((nr, nc))
        elif target.color != color and target.kind != 'K':
            moves.append((nr, nc))
    return moves


def _slider_moves(board, pos: Pos, color: str, directions: List[Pos]) -> List[Pos]:
    r, c = pos
    moves: List[Pos] = []
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        while board.in_bounds(nr, nc):
            target = board.get(nr, nc)
            if target is None:
                moves.append((nr, nc))
            else:
                if target.color != color and target.kind != 'K':
                    moves.append((nr, nc))
                break
            nr += dr
            nc += dc
    return moves


def _king_moves(board, pos: Pos, color: str) -> List[Pos]:
    r, c = pos
    moves: List[Pos] = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if not board.in_bounds(nr, nc):
                continue
            target = board.get(nr, nc)
            if target is None:
                moves.append((nr, nc))
            elif target.color != color and target.kind != 'K':
                moves.append((nr, nc))
    return moves


def _pawn_moves(board, pos: Pos, color: str) -> List[Pos]:
    """
    まずは通常チェス想定：
      - 前に1歩（空きマスのみ）
      - 初期位置なら2歩（間も含めて空き）
      - 斜め前に敵がいれば取れる
    en passant / 昇格 は次の段階。
    """
    r, c = pos
    moves: List[Pos] = []

    # 白は上に進む（rowが減る）、黒は下に進む（rowが増える）
    dir_r = -1 if color == 'white' else 1
    start_row = 6 if color == 'white' else 1

    one_r = r + dir_r
    # 前1歩
    if board.in_bounds(one_r, c) and board.get(one_r, c) is None:
        moves.append((one_r, c))

        # 初手2歩
        two_r = r + 2 * dir_r
        if r == start_row and board.in_bounds(two_r, c) and board.get(two_r, c) is None:
            moves.append((two_r, c))

    # 斜め取り
    for dc in (-1, 1):
        nr, nc = r + dir_r, c + dc
        if not board.in_bounds(nr, nc):
            continue
        target = board.get(nr, nc)
        if target is not None and target.color != color and target.kind != 'K':
            moves.append((nr, nc))
        # アンパッサン
        ep = getattr(board, "en_passant", None)
        if ep is not None:
            epr, epc = ep
            # 斜め前のマスが en_passant と一致するなら候補に入れる
            if epr == r + dir_r and abs(epc - c) == 1:
                moves.append((epr, epc))

    return moves

def attacked_squares(board, pos: Pos) -> List[Pos]:
    """
    駒が「攻撃しているマス」を返す（チェック判定用）。
    キングがいるマスも攻撃に含めるのが重要。
    """
    r, c = pos
    piece = board.get(r, c)
    if piece is None:
        return []

    k = piece.kind
    color = piece.color

    if k == 'P':
        return _pawn_attacks(board, pos, color)
    if k == 'N':
        return _knight_attacks(board, pos, color)
    if k == 'B':
        return _slider_attacks(board, pos, color, directions=[(-1,-1),(-1,1),(1,-1),(1,1)])
    if k == 'R':
        return _slider_attacks(board, pos, color, directions=[(-1,0),(1,0),(0,-1),(0,1)])
    if k == 'Q':
        return _slider_attacks(board, pos, color, directions=[(-1,-1),(-1,1),(1,-1),(1,1),(-1,0),(1,0),(0,-1),(0,1)])
    if k == 'K':
        return _king_attacks(board, pos, color)

    return []


def _knight_attacks(board, pos: Pos, color: str) -> List[Pos]:
    r, c = pos
    res: List[Pos] = []
    for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
        nr, nc = r+dr, c+dc
        if board.in_bounds(nr, nc):
            t = board.get(nr, nc)
            if t is None or t.color != color:
                res.append((nr, nc))
    return res


def _king_attacks(board, pos: Pos, color: str) -> List[Pos]:
    r, c = pos
    res: List[Pos] = []
    for dr in (-1,0,1):
        for dc in (-1,0,1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r+dr, c+dc
            if board.in_bounds(nr, nc):
                t = board.get(nr, nc)
                if t is None or t.color != color:
                    res.append((nr, nc))
    return res


def _slider_attacks(board, pos: Pos, color: str, directions: List[Pos]) -> List[Pos]:
    r, c = pos
    res: List[Pos] = []
    for dr, dc in directions:
        nr, nc = r+dr, c+dc
        while board.in_bounds(nr, nc):
            t = board.get(nr, nc)
            if t is None:
                res.append((nr, nc))
            else:
                if t.color != color:
                    # ここで敵キングのマスもちゃんと「攻撃」に入る
                    res.append((nr, nc))
                break
            nr += dr
            nc += dc
    return res

def _pawn_attacks(board, pos: Pos, color: str) -> List[Pos]:
    r, c = pos
    dir_r = -1 if color == 'white' else 1
    attacks: List[Pos] = []
    for dc in (-1, 1):
        nr, nc = r + dir_r, c + dc
        if board.in_bounds(nr, nc):
            attacks.append((nr, nc))
    return attacks