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


class Piece(QLabel):

    def __init__(self, type=None, colour=None, xy=None, **kwargs):
        self.type = type
        self.colour = colour
        self.xy = xy
        self.is_null = (self.type is None and self.colour is None and self.xy is None)
        self.image = os.path.join(BASE_PATH, (os.path.join(f"{self.colour} pieces", f"{self.type}.png") if not self.is_null else "transparent.png"))
        self.raw_image = QImage(self.image)

        super(Piece, self).__init__(**kwargs)
        self.setMouseTracking(True)
        self.setPixmap(QPixmap.fromImage(self.raw_image))
        self.parent = self.parent()

    def __repr__(self):
        if self.is_null:
            return "0"
        letter = self.type[0]
        if self.type == "knight":
            letter = "n"
        if self.colour == "white":
            return letter.upper()
        return letter.lower()

    def clicked_on_piece(self, pos):
        px_x = int(pos.x() * (self.raw_image.width() / SQUARE_SIZE))
        px_y = int(pos.y() * (self.raw_image.height() / SQUARE_SIZE))
        alpha = self.raw_image.pixelColor(px_x, px_y).getRgb()[-1]
        return alpha != 0

    def promote(self, new):
        self.type = new

    def mousePressEvent(self, event):
        self.valid_mouse_move = self.clicked_on_piece(event.pos()) and self.parent.piece_can_move(self)
        print("VALID:", self.valid_mouse_move)
        self.mouse_press_pos = None
        self.mouse_move_pos = None
        self.prev_mouse_pos = self.x(), self.y()
        if event.button() == Qt.LeftButton:
            self.mouse_press_pos = event.globalPos()
            self.mouse_move_pos = event.globalPos()
            valid_moves = self.parent.get_valid_moves(self)
            self.parent.update(highlighted=valid_moves)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            if not self.valid_mouse_move:
                return
            currPos = self.mapToGlobal(self.pos())
            globalPos = event.globalPos()
            diff = globalPos - self.mouse_move_pos
            newPos = self.mapFromGlobal(currPos + diff)
            self.move(newPos)
            self.raise_()
            self.mouse_move_pos = globalPos

    def mouseReleaseEvent(self, event):
        if not self.valid_mouse_move:
            return
        if self.mouse_press_pos is not None:
            moved = event.globalPos() - self.mouse_press_pos 
            event.ignore()
            x, y = self.mouse_move_pos.x() - BOARD_OFFSET[0], self.mouse_move_pos.y() - BOARD_OFFSET[1]
            if x < 5 or x > 5 + BOARD_SIZE or y < 5 or y > 5 + BOARD_SIZE:
                self.move(*self.prev_mouse_pos)           
                return
            prev_pos = self.prev_mouse_pos[0] // SQUARE_SIZE, self.prev_mouse_pos[1] // SQUARE_SIZE
            new_pos = x // SQUARE_SIZE, y // SQUARE_SIZE
            if prev_pos != new_pos:
                self.parent.move_piece(self, prev_pos, new_pos)
            else:
                self.parent.draw_piece(self, prev_pos)

class Board(QWidget):

    def __init__(self, parent, *args, **kwargs):
        super(Board, self).__init__(parent, *args, **kwargs)
        self.setMouseTracking(True)
        self.init()

        self.init_ui()
        self.update()
        self.parent = parent
        self.squares = {}

    def init(self):
        self.turn = "white"
        self.white_taken, self.black_taken = [], []

        self.board = []
        self.board.append([Piece(p, "black", parent=self) for p in ["rook", "knight", "bishop", "queen", "king", "bishop", "knight", "rook"]])
        self.board.append([Piece("pawn", "black", parent=self) for i in range(8)])
        for i in range(4):
            self.board.append([Piece(parent=self) for j in range(8)])
        self.board.append([Piece("pawn", "white", parent=self) for i in range(8)])
        self.board.append([Piece(p, "white", parent=self) for p in ["rook", "knight", "bishop", "queen", "king", "bishop", "knight", "rook"]])
        print("BOARD:")
        self.print_board()
        print()

    def init_ui(self):
        for i in range(8):
            for j in range(8):
                frame = QFrame(self) 
                frame.setGeometry(i * SQUARE_SIZE, j * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)    
                frame.setStyleSheet(f"background-color: rgb({BROWN if (i + j) % 2 else WHITE});")
                piece = self.board[i][j]
                piece.setScaledContents(True)
                piece.setStyleSheet("background-color: transparent; border: none;")                

    def print_board(self):
        for row in self.board:
            print(*row, sep=" ")

    def draw_piece(self, piece, pos):
        piece.move(pos[0] * SQUARE_SIZE, pos[1] * SQUARE_SIZE)

    def move_piece(self, piece, old_pos, new_pos):
        print(f"MOVING PIECE FROM {old_pos} TO {new_pos}:")
        self.draw_piece(piece, new_pos)
        self.board[old_pos[1]][old_pos[0]] = Piece()
        self.board[new_pos[1]][new_pos[0]] = piece    
        piece.xy = new_pos
        
        print("NEW BOARD:")
        self.print_board()
        print() 
        self.change_turn()

    def get_valid_moves(self, piece):
        row, col = piece.xy
        print(piece, row, col, piece.type)
        if piece.type == "pawn":
            return self._valid_pawn(piece, row, col)
        elif piece.type == "bishop":
            return self._valid_direction(row, col, ["ne", "nw", "se", "sw"])
        elif piece.type == "rook":
            return self._valid_direction(row, col, ["up", "down", "left", "right"])
        elif piece.type == "knight":
            return self._valid_knight(row, col)
        elif piece.type == "queen":
            return self._valid_direction(row, col, ["up", "down", "left", "right", "ne", "nw", "se", "sw"])

        return self._valid_king(row, col)

    def _valid_direction(self, row, col, directions):
        valid = []
        for direction in self._get_directions(row, col, directions):
            for pos in direction:
                square_contents = self.piece_at(pos)
                if square_contents.colour != self.turn:
                    valid.append(pos)
                break
        return valid

    def _valid_pawn(self, piece, row, col):
        valid = []
        starting_row = 1 if piece.colour == "black" else 6
        # All posible moves for a pawn
        if piece.colour == "black":
            positions = [(row+1, col), (row+2, col), (row+1, col+1), (row+1, col-1)]
        else:
            positions = [(row-1, col), (row-2, col), (row-1, col+1), (row-1, col-1)]
        # Check which positions are legal
        for index, pos in enumerate(positions):
            try:
                square_contents = self.piece_at(pos)
            except IndexError:
                continue
            if index == 1 and row == starting_row and square_contents == 0 and self.piece_at(positions[0]) == 0:
                valid.append(pos)
            elif index == 0 and square_contents == 0:
                valid.append(pos)
            elif index in [2, 3] and square_contents != 0:
                if square_contents.colour != self.turn:
                    valid.append(pos)
        return valid

    def _valid_knight(self, row, col):
        valid = []
        positions = [
            (row+1, col+2), (row+1, col-2), 
            (row+2, col+1), (row+2, col-1),
            (row-1, col-2), (row-1, col+2),
            (row-2, col-1), (row-2, col+1)
        ]
        for pos in positions:
            try:
                square_contents = self.piece_at(pos)
            except IndexError:
                continue
            if square_contents == 0:
                valid.append(pos)
            else:
                if square_contents.colour != self.turn:
                    valid.append(pos)
        return valid

    def _valid_king(self, row, col):
        valid = []
        positions = [
            (row+1, col), (row, col+1),
            (row-1, col), (row, col-1),
            (row+1, col+1), (row+1, col-1), 
            (row-1, col+1), (row-1, col-1)
        ]
        for pos in positions:
            try:
                square_contents = self.piece_at(pos)
            except IndexError:
                continue
            if square_contents == 0:
                valid.append(pos)
            else:
                if square_contents.colour != self.turn:
                    valid.append(pos)
        """
        if piece.colour == "white":
            if self.white_king_moved is False and self.white_right_rook_moved is False:
                if self.piece_at((row, col+1)) == 0 and self.piece_at((row, col+2)) == 0:
                    valid.append(pos)
            elif self.white_king_moved is False and self.white_left_rook_moved is False:
                if self.piece_at((row, col-1)) == 0 and self.piece_at((row, col-2)) == 0 \
                        and self.piece_at((row, col-3)) == 0:
                    valid.append(pos)

        if piece.colour == "black":
            if self.black_king_moved is False and self.black_right_rook_moved is False:
                if self.piece_at((row, col+1)) == 0 and self.piece_at((row, col+2)) == 0:
                    valid.append(pos)
            elif self.black_king_moved is False and self.right_left_rook_moved is False:
                if self.piece_at((row, col-1)) == 0 and self.piece_at((row, col-2)) == 0 \
                        and self.piece_at((row, col-3)) == 0:
                    valid.append(pos)
        """
        return valid

    def _get_directions(self, row, col, directions):
        output = []
        up = [(row-i, col) for i in range(1, 8) if (row-i) >= 0]
        down = [(row+i, col) for i in range(1, 8) if (row+i) < 8]
        left = [(row, col-i) for i in range(1, 8) if (col-i) >= 0]
        right = [(row, col+i) for i in range(1, 8) if (col+i) < 8]
        ne = [(row-i, col+i) for i in range(1, 8) if (row-i) >= 0 and (col+i) < 8]
        nw = [(row-i, col-i) for i in range(1, 8) if (row-i) >= 0 and (col-i) >= 0]
        se = [(row+i, col+i) for i in range(1, 8) if (row+i) < 8 and (col+i) < 8]
        sw = [(row+i, col-i) for i in range(1, 8) if (row+i) < 8 and (col-i) >= 0]
        for d in directions:
            output.append(eval(d))
        return output

    def piece_can_move(self, piece):
        return piece.colour == self.turn

    def update(self, highlighted=None):
        print(highlighted)
        for i in range(8):
            for j in range(8):
                piece = self.board[j][i]
                piece.xy = (i, j)
                piece.setGeometry(i * SQUARE_SIZE, j * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                piece.raise_()
                

    def piece_at(self, pos):
        return self.board[pos[1]][pos[0]]

    def change_turn(self):
        self.turn = "black" if self.turn == "white" else "white"


class Window(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)
        self.board = Board(self)
        self.init_ui()

        self.setMouseTracking(True)

    def init_ui(self):
        self.board.setGeometry(*BOARD_OFFSET, BOARD_SIZE, BOARD_SIZE)
        self.board.setStyleSheet("""QWidget {border: 3px solid rgb(40, 40, 40);}""")
        self.setStyleSheet(f"background-color: rgb({BG});")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.showFullScreen()
    win.showMinimized()
    sys.exit(app.exec())
