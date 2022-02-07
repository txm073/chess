import os, sys
import ctypes
import math
import time
import threading

try:
    os.chdir(os.path.dirname(sys.argv[0]))
except OSError:
    pass
finally:
    user32 = ctypes.windll.user32

import numpy as np
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from internal_v2 import InternalBoard


roundToSigFig = lambda x, n: x if x == 0 else round(x, -int(math.floor(math.log10(abs(x)))) + (n - 1))
centerOf = lambda i, j: (j[0] // 2 - i[0] // 2, j[1] // 2 - i[1] // 2)
resolutions = {1280: 520, 1366: 520, 1920: 760, 2560: 920, 3440: 920, 3840: 1160, 4096: 1160}
SCREEN_SIZE = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
BOARD_SIZE = resolutions.get(SCREEN_SIZE[0], 520)
BOARD_OFFSET = centerOf((BOARD_SIZE, BOARD_SIZE), SCREEN_SIZE)
SQUARE_SIZE = BOARD_SIZE // 8
PIECE_SIZE = SQUARE_SIZE - 10
PIECE_OFFSET = (5, 5)
BG = "25, 25, 25"
BROWN = "68, 40, 28"
WHITE = "217, 200, 168"
HIGHLIGHT = "120, 150, 20, 160"
BASE_PATH = os.path.join(os.path.dirname(sys.argv[0]), "assets")
INTERNAL = InternalBoard()


class Piece(QLabel):

    def __init__(self, type, colour, **kwargs):
        self.type = type
        self.colour = colour
        self.null = (self.type is None and self.colour is None)
        self.image = os.path.join(f"{self.colour} pieces", f"{self.type}.png") if not self.null else "transparent.png"
        
        super(Piece, self).__init__(**kwargs)
        self.setMouseTracking(True)

        self.setPixmap(QPixmap(os.path.join(BASE_PATH, self.image)))

    def __repr__(self):
        if self.null:
            return "0"
        letter = self.type[0]
        if self.type == "knight":
            letter = "n"
        if self.colour == "white":
            return letter.upper()
        return letter.lower()

    def promote(self, new):
        self.type = new

    def mousePressEvent(self, event):
        self.mouse_press_pos = None
        self.mouse_move_pos = None
        self.prev_mouse_pos = self.x(), self.y()
        if event.button() == Qt.LeftButton:
            self.mouse_press_pos = event.globalPos()
            self.mouse_move_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            currPos = self.mapToGlobal(self.pos())
            globalPos = event.globalPos()
            diff = globalPos - self.mouse_move_pos
            newPos = self.mapFromGlobal(currPos + diff)
            self.move(newPos)
            self.raise_()
            self.mouse_move_pos = globalPos

    def mouseReleaseEvent(self, event):
        if self.mouse_press_pos is not None:
            moved = event.globalPos() - self.mouse_press_pos 
            event.ignore()
            x, y = self.mouse_move_pos.x() - BOARD_OFFSET[0], self.mouse_move_pos.y() - BOARD_OFFSET[1]
            if x < 5 or x > 5 + BOARD_SIZE or y < 5 or y > 5 + BOARD_SIZE:
                self.move(*self.prev_mouse_pos)           
                return
            prev_pos = self.prev_mouse_pos[0] // SQUARE_SIZE, self.prev_mouse_pos[1] // SQUARE_SIZE
            new_pos = x // SQUARE_SIZE, y // SQUARE_SIZE
            self.parent().draw_piece(self, new_pos)

    def moveSelf(self, pos):
        pass


class BoardWidget(QWidget):

    def __init__(self, *args, **kwargs):
        super(BoardWidget, self).__init__(*args, **kwargs)
        self.setMouseTracking(True)

        self.squares = {}

    def init_ui(self, board):
        for j in range(8):
            for i in range(8):
                frame = QFrame(self) 
                frame.setGeometry(i * SQUARE_SIZE, j * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)    
                frame.setStyleSheet(f"background-color: rgb({BROWN if (i + j) % 2 else WHITE});")
                
                piece = board[j][i]
                piece.resize(SQUARE_SIZE, SQUARE_SIZE)
                piece.setStyleSheet("background-color: transparent; border: none;")
                piece.setScaledContents(True)
                self.squares[(i, j)] = piece
                self.draw_piece(piece, (i, j))
                piece.raise_()

    def widget_at(self, pos):
        return self.squares[pos]

    def draw_piece(self, piece, pos):
        piece.move(pos[0] * SQUARE_SIZE, pos[1] * SQUARE_SIZE)
        print(piece, pos, (piece.x(), piece.y()))

    def update_window(self, board, highlighted=[]):
        for i, row in enumerate(board):
            for j, square in enumerate(row):
                pass


class Window(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)
        self.init_ui()
        self.reset()
        self.board_widget.init_ui(self.board)
        self.setMouseTracking(True)

    def init_ui(self):
        self.board_widget = BoardWidget(self)
        self.board_widget.setGeometry(*BOARD_OFFSET, BOARD_SIZE, BOARD_SIZE)
        self.board_widget.setStyleSheet("""QWidget {border: 3px solid rgb(40, 40, 40);}""")
        self.setStyleSheet(f"background-color: rgb({BG});")

    def reset(self):
        self.board = []
        self.board.append([Piece(p, "white", parent=self.board_widget) for p in ["rook", "knight", "bishop", "queen", "king", "bishop", "knight", "rook"]])
        self.board.append([Piece("pawn", "white", parent=self.board_widget)] * 8)
        for i in range(4):
            self.board.append([Piece(None, None, parent=self.board_widget)] * 8)
        self.board.append([Piece("pawn", "black", parent=self.board_widget)] * 8)
        self.board.append([Piece(p, "black", parent=self.board_widget) for p in ["rook", "knight", "bishop", "queen", "king", "bishop", "knight", "rook"]])
        self.board = np.array(self.board).reshape(8, 8)
        print("BOARD:")
        print(self.board)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.showFullScreen()
    sys.exit(app.exec())
