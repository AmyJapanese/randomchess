# main.py
import tkinter as tk
from board import Board
from gui import ChessGUI


def main() -> None:
    board = Board()
    board.setup_standard()

    root = tk.Tk()
    root.title("Random Chess (dev) - Fixed Setup")
    ChessGUI(root, board)

    root.mainloop()


if __name__ == "__main__":
    main()
