# gui.py
from __future__ import annotations
import tkinter as tk
from typing import Optional, Tuple, List

from board import Board
from piece import generate_moves, Piece
import random

Pos = Tuple[int, int]


PIECE_CHAR = {
    ('K', 'white'): '♔', ('Q', 'white'): '♕',
    ('R', 'white'): '♖', ('B', 'white'): '♗',
    ('N', 'white'): '♘', ('P', 'white'): '♙',
    ('K', 'black'): '♚', ('Q', 'black'): '♛',
    ('R', 'black'): '♜', ('B', 'black'): '♝',
    ('N', 'black'): '♞', ('P', 'black'): '♟',
}


class ChessGUI:
    CELL = 80

    def __init__(self, root: tk.Tk, board: Board) -> None:
        self.root = root
        self.board = board
        self.game_over = False

        self.canvas = tk.Canvas(root, width=8*self.CELL, height=8*self.CELL)
        self.canvas.pack()

        self.status = tk.Label(root, text="")
        self.status.pack(pady=6)
        
        # --- FEN bar ---
        fen_frame = tk.Frame(root)
        fen_frame.pack(pady=4)

        tk.Label(fen_frame, text="FEN:").pack(side=tk.LEFT)
        self.fen_entry = tk.Entry(fen_frame, width=60)
        self.fen_entry.pack(side=tk.LEFT, padx=4)

        tk.Button(fen_frame, text="Load", command=self.load_fen_from_ui).pack(side=tk.LEFT)
        tk.Button(fen_frame, text="Copy", command=self.copy_fen_to_clipboard).pack(side=tk.LEFT, padx=4)
        tk.Button(fen_frame, text="Random", command=self.random_setup).pack(side=tk.LEFT, padx=4)

        self.selected: Optional[Pos] = None
        self.legal_moves: List[Pos] = []

        self.canvas.bind("<Button-1>", self.on_click)

        self.redraw()
    
    def random_setup(self) -> None:
        try:
            self.board.setup_random(forbid_mate_in_1=True)
            self.selected = None
            self.legal_moves = []
            self.game_over = False
            # FEN欄にも反映（便利）
            if hasattr(self, "fen_entry"):
                self.fen_entry.delete(0, "end")
                self.fen_entry.insert(0, self.board.to_fen())
            self.redraw()
        except Exception as e:
            self.status.config(text=f"Random gen error: {e}")
    
    def load_fen_from_ui(self) -> None:
        fen = self.fen_entry.get().strip()
        if not fen:
            return
        try:
            self.board.load_fen(fen)
            self.selected = None
            self.legal_moves = []
            self.status.config(text=f"Loaded FEN. Turn: {self.board.turn}")
            self.redraw()
        except Exception as e:
            self.status.config(text=f"FEN error: {e}")

    def copy_fen_to_clipboard(self) -> None:
        fen = self.board.to_fen()
        self.root.clipboard_clear()
        self.root.clipboard_append(fen)
        self.status.config(text="FEN copied to clipboard!")


    def redraw(self) -> None:
        self.canvas.delete("all")
        self._draw_squares()
        self._draw_highlights()
        self._draw_pieces()
        self.update_status()

    def _draw_squares(self) -> None:
        for r in range(8):
            for c in range(8):
                color = "#EEE" if (r + c) % 2 == 0 else "#555"
                x1, y1 = c*self.CELL, r*self.CELL
                x2, y2 = (c+1)*self.CELL, (r+1)*self.CELL
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

    def _draw_highlights(self) -> None:
        # 選択中のマス
        if self.selected is not None:
            r, c = self.selected
            self._rect_outline(r, c, width=4)

        # 合法手のマス
        for r, c in self.legal_moves:
            self._rect_outline(r, c, width=3)

    def _rect_outline(self, r: int, c: int, width: int = 3) -> None:
        x1, y1 = c*self.CELL, r*self.CELL
        x2, y2 = (c+1)*self.CELL, (r+1)*self.CELL
        self.canvas.create_rectangle(x1+2, y1+2, x2-2, y2-2, outline="gold", width=width)

    def _draw_pieces(self) -> None:
        for r in range(8):
            for c in range(8):
                p = self.board.get(r, c)
                if p is None:
                    continue
                ch = PIECE_CHAR[(p.kind, p.color)]
                self.canvas.create_text(
                    c*self.CELL + self.CELL//2,
                    r*self.CELL + self.CELL//2,
                    text=ch,
                    font=("Arial", 36)
                )

    def on_click(self, event) -> None:
        if self.game_over:
            return

        c = event.x // self.CELL
        r = event.y // self.CELL
        if not (0 <= r < 8 and 0 <= c < 8):
            return

        clicked = (r, c)
        piece = self.board.get(r, c)

        # 何も選んでない → 自分の番の駒なら選択
        if self.selected is None:
            if piece is not None and piece.color == self.board.turn:
                self.selected = clicked
                self.legal_moves = generate_moves(self.board, clicked)
            else:
                self.selected = None
                self.legal_moves = []
            self.redraw()
            return

        # 選択中
        if clicked in self.legal_moves:
            # 移動実行
            self.board.move(self.selected, clicked)
            self.board.switch_turn()

            # いま手番になった側（相手）の状態をチェック
            side = self.board.turn
            if self.board.is_checkmate(side):
                winner = 'white' if side == 'black' else 'black'
                self.status.config(text=f"Checkmate! Winner: {winner}")
            elif self.board.is_stalemate(side):
                self.status.config(text="Stalemate! Draw.")
            elif self.board.in_check(side):
                self.status.config(text=f"Turn: {side}  (CHECK!)")
            else:
                self.status.config(text=f"Turn: {side}")

            self.selected = None
            self.legal_moves = []
            self.redraw()
            return

        # 別の自分駒をクリック → 選択切り替え
        if piece is not None and piece.color == self.board.turn:
            self.selected = clicked
            self.legal_moves = self.board.legal_moves_for_piece(clicked)
            self.redraw()
            return

        self.board.move(self.selected, clicked)
        self.board.switch_turn()
        self.selected = None
        self.legal_moves = []
        self.redraw()
        return
        
    def update_status(self) -> None:
        side = self.board.turn  # いま手番の側

        if self.board.is_checkmate(side):
            winner = 'white' if side == 'black' else 'black'
            self.status.config(text=f"Checkmate! Winner: {winner}")
            self.game_over = True
            return

        if self.board.is_stalemate(side):
            self.status.config(text="Draw (stalemate).")
            self.game_over = True
            return

        self.game_over = False
        if self.board.in_check(side):
            self.status.config(text=f"Turn: {side}  (CHECK!)")
        else:
            self.status.config(text=f"Turn: {side}")
