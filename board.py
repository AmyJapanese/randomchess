# board.py
from __future__ import annotations
from typing import Optional, List, Tuple, Dict
from piece import Piece
from copy import deepcopy
from piece import generate_moves, attacked_squares
import random

Pos = Tuple[int, int]

# FENデータ
FEN_TO_KIND = {
    'k': ('K', 'black'), 'q': ('Q', 'black'), 'r': ('R', 'black'),
    'b': ('B', 'black'), 'n': ('N', 'black'), 'p': ('P', 'black'),
    'K': ('K', 'white'), 'Q': ('Q', 'white'), 'R': ('R', 'white'),
    'B': ('B', 'white'), 'N': ('N', 'white'), 'P': ('P', 'white'),
}

KIND_TO_FEN = {
    ('K', 'black'): 'k', ('Q', 'black'): 'q', ('R', 'black'): 'r',
    ('B', 'black'): 'b', ('N', 'black'): 'n', ('P', 'black'): 'p',
    ('K', 'white'): 'K', ('Q', 'white'): 'Q', ('R', 'white'): 'R',
    ('B', 'white'): 'B', ('N', 'white'): 'N', ('P', 'white'): 'P',
}

FILES = "abcdefgh"
RANKS = "12345678"


class Board:
    def __init__(self) -> None:
        self.grid = [[None for _ in range(8)] for _ in range(8)]
        self.turn: str = 'white'

        # キャスリング権：True = まだ可能
        self.castling: Dict[str, Dict[str, bool]] = {
            'white': {'K': True, 'Q': True},  # K=キング側, Q=クイーン側
            'black': {'K': True, 'Q': True},
        }

        # アンパッサン可能マス（取られる側のポーンの「通過マス」）
        self.en_passant: Optional[Tuple[int, int]] = None

        self.last_move = None  # 任意（(src, dst, moved_piece_kind) とか）
    
    def _algebraic_to_pos(self, s: str):
        # "e3" -> (row, col)
        if len(s) != 2:
            return None
        file_ch, rank_ch = s[0], s[1]
        if file_ch not in FILES or rank_ch not in RANKS:
            return None
        c = FILES.index(file_ch)
        # rank '8' は row=0, rank '1' は row=7
        r = 8 - int(rank_ch)
        return (r, c)

    def _pos_to_algebraic(self, pos):
        r, c = pos
        if not (0 <= r < 8 and 0 <= c < 8):
            return None
        file_ch = FILES[c]
        rank_ch = str(8 - r)
        return file_ch + rank_ch

    def load_fen(self, fen: str) -> None:
        """
        FEN: "piecePlacement side castling enPassant halfmove fullmove"
        例: "7k/6Q1/7K/8/8/8/8/8 b - - 0 1"
        halfmove/fullmove は今は使わない（読み捨て）
        """
        parts = fen.strip().split()
        if len(parts) < 4:
            raise ValueError("Invalid FEN: needs at least 4 fields")

        placement, side, castling, ep = parts[0], parts[1], parts[2], parts[3]

        # 盤面クリア
        self.grid = [[None for _ in range(8)] for _ in range(8)]

        rows = placement.split('/')
        if len(rows) != 8:
            raise ValueError("Invalid FEN: board must have 8 ranks")

        for r in range(8):
            c = 0
            for ch in rows[r]:
                if ch.isdigit():
                    c += int(ch)
                else:
                    if ch not in FEN_TO_KIND:
                        raise ValueError(f"Invalid FEN piece: {ch}")
                    kind, color = FEN_TO_KIND[ch]
                    if c >= 8:
                        raise ValueError("Invalid FEN: too many files in rank")
                    self.grid[r][c] = Piece(kind, color)
                    c += 1
            if c != 8:
                raise ValueError("Invalid FEN: rank does not sum to 8")

        # 手番
        if side not in ('w', 'b'):
            raise ValueError("Invalid FEN: side must be w or b")
        self.turn = 'white' if side == 'w' else 'black'

        # キャスリング権
        self.castling = {'white': {'K': False, 'Q': False}, 'black': {'K': False, 'Q': False}}
        if castling != '-':
            for ch in castling:
                if ch == 'K': self.castling['white']['K'] = True
                elif ch == 'Q': self.castling['white']['Q'] = True
                elif ch == 'k': self.castling['black']['K'] = True
                elif ch == 'q': self.castling['black']['Q'] = True
                else:
                    raise ValueError(f"Invalid FEN castling: {ch}")

        # アンパッサン
        if ep == '-':
            self.en_passant = None
        else:
            pos = self._algebraic_to_pos(ep)
            if pos is None:
                raise ValueError("Invalid FEN en passant square")
            self.en_passant = pos

        # 最後の手は不明になるのでクリア
        self.last_move = None
    
    def to_fen(self) -> str:
        # 盤面
        ranks = []
        for r in range(8):
            empties = 0
            out = []
            for c in range(8):
                p = self.get(r, c)
                if p is None:
                    empties += 1
                else:
                    if empties:
                        out.append(str(empties))
                        empties = 0
                    out.append(KIND_TO_FEN[(p.kind, p.color)])
            if empties:
                out.append(str(empties))
            ranks.append("".join(out))
        placement = "/".join(ranks)

        # 手番
        side = 'w' if self.turn == 'white' else 'b'

        # キャスリング権
        castling = ""
        if self.castling['white']['K']: castling += "K"
        if self.castling['white']['Q']: castling += "Q"
        if self.castling['black']['K']: castling += "k"
        if self.castling['black']['Q']: castling += "q"
        if castling == "":
            castling = "-"

        # アンパッサン
        ep = "-" if self.en_passant is None else self._pos_to_algebraic(self.en_passant)

        # halfmove / fullmove は今回は固定でOK（実用には十分）
        return f"{placement} {side} {castling} {ep} 0 1"

    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < 8 and 0 <= c < 8

    def get(self, r: int, c: int) -> Optional[Piece]:
        return self.grid[r][c]

    def set(self, r: int, c: int, piece: Optional[Piece]) -> None:
        self.grid[r][c] = piece

    def setup_standard(self) -> None:
        """通常チェスの初期配置。"""
        self.grid = [[None for _ in range(8)] for _ in range(8)]

        order = ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
        # 黒（上）
        for c in range(8):
            self.set(0, c, Piece(order[c], 'black'))
            self.set(1, c, Piece('P', 'black'))
        # 白（下）
        for c in range(8):
            self.set(6, c, Piece('P', 'white'))
            self.set(7, c, Piece(order[c], 'white'))

        self.turn = 'white'
        self.turn = 'white'
        self.castling = {
            'white': {'K': True, 'Q': True},
            'black': {'K': True, 'Q': True},
        }
        self.en_passant = None
        self.last_move = None
        
    def setup_random(self, seed: int | None = None, forbid_mate_in_1: bool = True, max_tries: int = 5000) -> None:
        """
        Random Chess初期配置：
        - 下4段(行4-7)が白、上4段(行0-3)が黒
        - 駒数は通常と同じ
        - 初期チェックなし
        - 初期ステイルメイトなし（両者1手以上）
        - (任意) 白の初手メイト-in-1なし
        - キャスリングはOFFにする（定義が曖昧になるため）
        """
        rng = random.Random(seed)

        white_squares = [(r, c) for r in range(4, 8) for c in range(8)]
        black_squares = [(r, c) for r in range(0, 4) for c in range(8)]

        white_pieces = (
            [Piece('K', 'white'), Piece('Q', 'white')]
            + [Piece('R', 'white')] * 2
            + [Piece('B', 'white')] * 2
            + [Piece('N', 'white')] * 2
            + [Piece('P', 'white')] * 8
        )
        black_pieces = (
            [Piece('K', 'black'), Piece('Q', 'black')]
            + [Piece('R', 'black')] * 2
            + [Piece('B', 'black')] * 2
            + [Piece('N', 'black')] * 2
            + [Piece('P', 'black')] * 8
        )

        for _ in range(max_tries):
            # 盤クリア
            self.grid = [[None for _ in range(8)] for _ in range(8)]

            # 位置選択
            ws = rng.sample(white_squares, 16)
            bs = rng.sample(black_squares, 16)

            # 駒割り当て
            wp = white_pieces[:]
            bp = black_pieces[:]
            rng.shuffle(wp)
            rng.shuffle(bp)

            for (r, c), p in zip(ws, wp):
                self.set(r, c, p)
            for (r, c), p in zip(bs, bp):
                self.set(r, c, p)

            # 状態リセット
            self.turn = 'white'
            self.en_passant = None
            self.last_move = None

            # キャスリング無効（Randomでは曖昧なのでOFF推奨）
            self.castling = {
                'white': {'K': False, 'Q': False},
                'black': {'K': False, 'Q': False},
            }

            # ---- 検証 ----
            # 1) 初期チェックなし
            if self.in_check('white') or self.in_check('black'):
                continue

            # 2) 初期ステイルメイトなし（両方動ける）
            if (not self.any_legal_move('white')) or (not self.any_legal_move('black')):
                continue

            # 3) 白の初手メイト-in-1禁止（任意）
            if forbid_mate_in_1 and self._has_mate_in_one('white'):
                continue

            return  # 成功

        raise RuntimeError("Failed to generate random position (too strict or max_tries too low).")


    def _has_mate_in_one(self, attacker: str) -> bool:
        """attacker が1手で相手をチェックメイトできる手が存在するか？"""
        defender = 'black' if attacker == 'white' else 'white'

        saved_turn = self.turn
        self.turn = attacker
        try:
            for r in range(8):
                for c in range(8):
                    p = self.get(r, c)
                    if p is None or p.color != attacker:
                        continue
                    src = (r, c)
                    for dst in self.legal_moves_for_piece(src):
                        b2 = self.clone()
                        b2.move(src, dst)
                        # 相手番にしてから判定すると自然
                        b2.turn = defender
                        if b2.is_checkmate(defender):
                            return True
            return False
        finally:
            self.turn = saved_turn

    def move(self, src: Pos, dst: Pos) -> None:
        sr, sc = src
        dr, dc = dst
        piece = self.get(sr, sc)
        if piece is None:
            return

        # move前：基本は en_passant を消す（次の手に持ち越さない）
        prev_en_passant = self.en_passant
        self.en_passant = None

        target = self.get(dr, dc)

        # ---- アンパッサン捕獲（移動先が空、かつ斜め前、かつ en_passant 一致）----
        if piece.kind == 'P' and target is None and prev_en_passant == (dr, dc) and sc != dc:
            # 取られるポーンは dst の1つ後ろにいる
            captured_r = dr + (1 if piece.color == 'white' else -1)
            self.set(captured_r, dc, None)

        # ---- キャスリング（キングが2マス動く）----
        if piece.kind == 'K' and abs(dc - sc) == 2 and sr == dr:
            # rookの移動
            if dc > sc:
                # キング側 (e->g)
                rook_src = (sr, 7)
                rook_dst = (sr, 5)
            else:
                # クイーン側 (e->c)
                rook_src = (sr, 0)
                rook_dst = (sr, 3)

            rook_piece = self.get(*rook_src)
            # rookがいる前提（合法手判定で担保）
            self.set(*rook_dst, rook_piece)
            self.set(*rook_src, None)

        # ---- 通常の駒移動（＋取り）----
        self.set(dr, dc, piece)
        self.set(sr, sc, None)

        # ---- ポーン2歩：en_passant マスを設定 ----
        if piece.kind == 'P' and abs(dr - sr) == 2:
            mid_r = (dr + sr) // 2
            self.en_passant = (mid_r, sc)

        # ---- キャスリング権の更新 ----
        if piece.kind == 'K':
            self.castling[piece.color]['K'] = False
            self.castling[piece.color]['Q'] = False

        if piece.kind == 'R':
            # 元の角のルークが動いたら権利を失う
            if piece.color == 'white' and (sr, sc) == (7, 0):
                self.castling['white']['Q'] = False
            if piece.color == 'white' and (sr, sc) == (7, 7):
                self.castling['white']['K'] = False
            if piece.color == 'black' and (sr, sc) == (0, 0):
                self.castling['black']['Q'] = False
            if piece.color == 'black' and (sr, sc) == (0, 7):
                self.castling['black']['K'] = False

        # ルークが取られた場合も権利を失う（角ルークが死んだら無理）
        if target is not None and target.kind == 'R':
            if target.color == 'white' and (dr, dc) == (7, 0):
                self.castling['white']['Q'] = False
            if target.color == 'white' and (dr, dc) == (7, 7):
                self.castling['white']['K'] = False
            if target.color == 'black' and (dr, dc) == (0, 0):
                self.castling['black']['Q'] = False
            if target.color == 'black' and (dr, dc) == (0, 7):
                self.castling['black']['K'] = False

        # ---- 昇格（今回はとりあえず自動クイーン）----
        moved = self.get(dr, dc)
        if moved is not None and moved.kind == 'P':
            if (moved.color == 'white' and dr == 0) or (moved.color == 'black' and dr == 7):
                self.set(dr, dc, Piece('Q', moved.color))

        self.last_move = (src, dst, piece.kind)

    def switch_turn(self) -> None:
        self.turn = 'black' if self.turn == 'white' else 'white'

    def clone(self) -> "Board":
        b = Board()
        b.grid = deepcopy(self.grid)
        b.turn = self.turn
        b.castling = {
            'white': self.castling['white'].copy(),
            'black': self.castling['black'].copy(),
        }
        b.en_passant = self.en_passant
        b.last_move = self.last_move
        return b


    def find_king(self, color: str) -> Pos:
        for r in range(8):
            for c in range(8):
                p = self.get(r, c)
                if p and p.kind == 'K' and p.color == color:
                    return (r, c)
        raise ValueError(f"King not found: {color}")

    def is_square_attacked(self, target: Pos, by_color: str) -> bool:
        tr, tc = target
        for r in range(8):
            for c in range(8):
                p = self.get(r, c)
                if p is None or p.color != by_color:
                    continue
                for ar, ac in attacked_squares(self, (r, c)):
                    if ar == tr and ac == tc:
                        return True
        return False

    def in_check(self, color: str) -> bool:
        try:
            king_pos = self.find_king(color)
        except ValueError:
            # 本来起きないが、キングが盤面から消えた = 異常終了扱い
            return True
        enemy = 'black' if color == 'white' else 'white'
        return self.is_square_attacked(king_pos, enemy)

    def legal_moves_for_piece(self, pos: Pos) -> List[Pos]:
        """
        その駒の「本当の合法手」＝動いた後に自分のキングがチェックじゃない手のみ。
        """
        piece = self.get(*pos)
        if piece is None:
            return []
        if piece.color != self.turn:
            return []

        candidates = generate_moves(self, pos)

        if piece.kind == 'K':
            candidates += self._castling_moves(piece.color)
        
        good: List[Pos] = []
        for dst in candidates:
            b2 = self.clone()
            b2.move(pos, dst)
            # ターンは切り替えない（判定対象は“動かした側”のキング安全性）
            if not b2.in_check(piece.color):
                good.append(dst)
        return good

    def any_legal_move(self, color: str) -> bool:
        """
        color 側に1手でも合法手があるか？
        turn を一時的に切り替えてチェックする（GUIターンとは独立に使える）。
        """
        saved = self.turn
        self.turn = color
        try:
            for r in range(8):
                for c in range(8):
                    p = self.get(r, c)
                    if p and p.color == color:
                        if self.legal_moves_for_piece((r, c)):
                            return True
            return False
        finally:
            self.turn = saved

    def is_checkmate(self, color: str) -> bool:
        return self.in_check(color) and (not self.any_legal_move(color))

    def is_stalemate(self, color: str) -> bool:
        return (not self.in_check(color)) and (not self.any_legal_move(color))
    
    def _castling_moves(self, color: str) -> List[Pos]:
        """
        キャスリング可能なら、キングの行の (row, 6) or (row, 2) を返す。
        条件：
          - キングと対象ルークが未移動（castling権が True）
          - 間のマスが空
          - キングがチェック中でない
          - 通過/到達マスが攻撃されていない
        """
        moves: List[Pos] = []
        row = 7 if color == 'white' else 0

        # キング位置が通常の e-file にいる前提（通常チェス／FEN互換）
        king_pos = (row, 4)
        king = self.get(*king_pos)
        if king is None or king.kind != 'K' or king.color != color:
            return moves

        enemy = 'black' if color == 'white' else 'white'

        # まずチェック中なら不可
        if self.in_check(color):
            return moves

        # キング側
        if self.castling[color]['K']:
            squares_between = [(row, 5), (row, 6)]
            rook_pos = (row, 7)
            rook = self.get(*rook_pos)
            if rook and rook.kind == 'R' and rook.color == color:
                if all(self.get(r, c) is None for (r, c) in squares_between):
                    # 通過・到達が攻撃されてない
                    if (not self.is_square_attacked((row, 5), enemy)) and (not self.is_square_attacked((row, 6), enemy)):
                        moves.append((row, 6))

        # クイーン側
        if self.castling[color]['Q']:
            squares_between = [(row, 1), (row, 2), (row, 3)]
            rook_pos = (row, 0)
            rook = self.get(*rook_pos)
            if rook and rook.kind == 'R' and rook.color == color:
                if all(self.get(r, c) is None for (r, c) in squares_between):
                    if (not self.is_square_attacked((row, 3), enemy)) and (not self.is_square_attacked((row, 2), enemy)):
                        moves.append((row, 2))

        return moves