try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    import numpy as np
except ImportError:
    import os
    os.system("pip install PyQt5")
    os.system("pip install PyQt5-tools")
    os.system("pip install numpy")

    from PyQt5.QtWidgets import *
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    import numpy as np

import time
import os
import sys


# Complete game class for two players on the same device
class Game(QDialog):

    def __init__(self):
        super().__init__()

        # Window variables
        self.base_path = os.path.join(os.path.dirname(sys.argv[0]), "assets")
        self.width = 600
        self.height = 660
        self.white = (217, 200, 168)
        self.brown = (68, 40, 28)
        self.bg_colour = (49, 24, 11)
        self.offset = self.height - self.width

        # Board variables
        self.board_size = 440
        self.board_x = (self.width - self.board_size) // 2
        self.board_y = (self.height + self.offset - self.board_size) // 2
        self.square_size = self.board_size // 8
        self.n_rows = self.n_cols = 8
        self.squares = {}
        self.piece_padding = 5
        self.piece_size = self.square_size - self.piece_padding * 2
        self.selected = self.old_square = None
        self.show_move_pos = (20, 20, 15, 15)

        # Border variables
        self.border_size = 528
        self.border_x = (self.width - self.border_size) // 2
        self.border_y = (self.height + self.offset - self.border_size) // 2

        # Game variables
        self.turn = "white"
        self.white_taken, self.black_taken = [], []
        self.valid_moves = [32]
        self.checkmate = False

        # Initialisation methods
        self.init_styles()
        self.init_ui()
        self.init_game()
        print(np.array(self.board).reshape(8, 8))
        self.draw_pieces()
        self.setMouseTracking(True)
        self.show()

    def init_ui(self):
        # Create background
        self.bg_path = os.path.join(self.base_path, "background.jpg")
        self.bg = QPixmap(self.bg_path)
        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(True)
        self.bg_label.setGeometry(0, 0, self.width, self.height)
        self.bg_label.setPixmap(self.bg)

        # Create border for the chess board
        self.border_path = os.path.join(self.base_path, "border.png")
        self.border_image = QPixmap(self.border_path)
        self.border_label = QLabel(self)
        self.border_label.setScaledContents(True)
        self.border_label.setGeometry(self.border_x, self.border_y, self.border_size, self.border_size)
        self.border_label.setPixmap(self.border_image)

        # Create the chess board itself
        self.board_frame = QFrame(self)
        self.board_frame.setGeometry(self.board_x, self.board_y, self.board_size, self.board_size)
        nums = self._enumerate()
        for i in range(self.n_rows):
            for j in range(self.n_cols):
                square_num = next(nums)
                if (i + j) % 2 == 0:
                    colour = self.white
                else:
                    colour = self.brown
                square = QFrame(self.board_frame)
                square.setGeometry(j * self.square_size, i * self.square_size, self.square_size, self.square_size)
                square.setStyleSheet(f"background-color: rgb{str(colour)}; border: 2px solid rgb{str(colour)};")
                self.squares[square_num] = square

        # Create window
        self.setGeometry(50, 50, self.width, self.height)
        self.setWindowTitle("Chess")
        self.setWindowIcon(QIcon(os.path.join(self.base_path, "window-icon.png")))

    def init_styles(self):
        self.win_style = f"""
                        background-color: rgb{str(self.bg_colour)};
                        border-radius: 10px;
                        opacity: 100%;
                          """

        self.piece_style = """
                        background-color: rgba(0, 0, 0, 0);
                        border: none;
                           """

    def _enumerate(self):
        for i in range(64):
            yield i

    def init_game(self):
        self.reset()

    def draw_pieces(self):
        for i in range(len(self.board)):
            frame = self.squares[i]
            label = QLabel(frame)
            # If there is a piece, draw it
            if self.board[i] != 0:
                piece = self.board[i]
                piece_image = QPixmap(os.path.join(self.base_path, piece.image))
                label.setGeometry(self.piece_padding, self.piece_padding, self.piece_size, self.piece_size)
                label.setScaledContents(True)
                label.setPixmap(piece_image)

            # Update stylesheet for the current selected piece
            if i == self.selected:
                frame.setStyleSheet(frame.styleSheet())

            # Otherwise keep the stylesheet the same as the parent frame
            # So the pieces aren't seen to be duplicated
            else:
                label.setGeometry(0, 0, self.square_size, self.square_size)
                label.setStyleSheet(frame.styleSheet())

                if i in self.valid_moves and self.selected is not None and self.board[i] == 0:
                    label.setGeometry(*self.show_move_pos)
                    label.setStyleSheet("background-color: rgba(120, 150, 20, 130); border-radius: 6px;")

            label.setParent(frame)
            label.show()

    def reset(self):
        self.turn = "white"
        self.board = []

        for i in range(self.n_rows):
            row = []
            if i == 0:
                for piece in ["rook", "knight", "bishop", "queen", "king", "bishop", "knight", "rook"]:
                    row.append(Piece(piece, "white"))
            elif i == 1:
                for j in range(self.n_cols):
                    row.append(Piece("pawn", "white"))

            elif i == 6:
                for j in range(self.n_cols):
                    row.append(Piece("pawn", "black"))

            elif i == 7:
                for piece in ["rook", "knight", "bishop", "king", "queen", "bishop", "knight", "rook"]:
                    row.append(Piece(piece, "black"))

            else:
                row = [0] * self.n_cols

            self.board.extend(row)

    def change_turn(self):
        if self.turn == "white":
            self.turn = "black"
        else:
            self.turn = "white"
        print("White has taken:", self.white_taken)
        print("Black has taken:", self.black_taken)

    def move_piece(self, piece, square):
        assert isinstance(piece, Piece)
        self.board[square] = piece
        self.board[self.selected] = 0
        self.selected = None
        self.draw_pieces()
        self.change_turn()

    # Handles piece selection and movement
    def mousePressEvent(self, event):
        square = None
        for i in range(len(self.board)):
            if self.squares[i].underMouse():
                square = i
                break
        # If the click is not on the board itself
        if square is None:
            return

        # If a piece is selected move it to the new square as long
        # As long as that square does not contain a piece of the same colour
        if self.selected is not None:
            # Destination square - where the current player wants to move to
            # Or if they want to select a different piece
            square_contents = self.board[square]
            selected_piece = self.board[self.selected]
            # If it's a blank square then move the selected piece there
            if square_contents == 0:
                if square in self.valid_moves:
                    self.valid_moves.remove(square)
                    self.move_piece(selected_piece, square)
                # Break out of the conditions to avoid attribute error for squares containing 0
                return

            # Otherwise we know the player has taken an opponent's piece
            elif square_contents.colour != self.turn:
                if self.turn == "white":
                    self.white_taken.append(square_contents)
                else:
                    self.black_taken.append(square_contents)

                if square in self.valid_moves:
                    self.valid_moves.remove(square)
                    self.move_piece(selected_piece, square)

            # If it's of the same colour as the current turn
            # The player is trying to change their piece selection
            elif square_contents.colour == self.turn:
                if square == self.selected:
                    self.selected = None
                    self.draw_pieces()
                    return
                self.selected = square
                self.get_valid_moves()
                self.draw_pieces()
                print("Piece selected:", self.board[self.selected])

        # Otherwise select a new piece
        else:
            # Player can't select a blank square
            if self.board[square] != 0:
                piece = self.board[square]
                # Player can't select a piece that isn't their colour
                if piece.colour != self.turn:
                    return
                self.selected = square
                self.get_valid_moves()
                # Re-draw the pieces to display the selected one
                self.draw_pieces()
                print("Piece selected:", self.board[self.selected])

    def row(self, square):
        return square // 8

    def col(self, square):
        return square % 8

    # Works out valid moves for a specific piece and position according to the rules of chess
    def get_valid_moves(self):
        self.valid_moves = []
        piece = self.board[self.selected]
        position = self.selected
        return list(range(64))

        if self.is_stopping_check():
            return []

        # Pawns
        if piece.type == "pawn":
            if piece.colour == "white":
                # Forward movement
                print(self.diagonal_left(position, 1))

                # Diagonal movement


        """
        for move in moves:
            try:
                self.board[move]
            except IndexError:
                # If move goes off the board continue to the next iteration
                continue

            if not self.is_stopping_check():
                if self.board[move] == 0:
                    self.valid_moves.append(move)
                elif self.board[move].colour != piece.colour:
                    self.valid_moves.append(move)

        print(self.valid_moves)
        """
    def forward(self, square, amount):
        try:
            return self.board[square + 8 * amount], square + 8 * amount
        except IndexError:
            return None

    def diagonal_left(self, square, amount):
        try:
            return self.board[square + 7 * amount]
        except IndexError:
            return None

    def diagonal_right(self, square, amount):
        try:
            return self.board[square + 9 * amount], square + 9 * amount
        except IndexError:
            return None

    def sideways(self, square, amount):
        try:
            result = square - 1 * amount
            # Prevent pieces 'cascading off the row'
            if self.col(result) == 7 and amount > 0:
                return None

            elif self.col(result) == 0 and amount < 0:
                return None

            return self.board[result]

        except IndexError:
            return None

    # Make sure that a piece can be moved
    # And is not stopping check or the king from being taken
    def is_stopping_check(self):
        pass


class Piece:

    def __init__(self, type, colour):
        self.type = type
        self.colour = colour
        self.image = os.path.join(f"{self.colour} pieces", f"{self.type}.png")

    def __repr__(self):
        letter = self.type[0]
        if self.type == "knight":
            letter = "n"
        if self.colour == "white":
            return letter.upper()
        else:
            return letter.lower()

    def promote(self, new):
        self.type = new


if __name__ == "__main__":
    app = QApplication(sys.argv)
    game = Game()
    sys.exit(app.exec_())

