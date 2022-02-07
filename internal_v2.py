import os
import numpy as np


class InternalBoard:

    def __init__(self):
        # Game settings
        self.turn = "white"
        self.white_taken, self.black_taken = [], []
        self.valid_moves = []
        self.white_checkmate, self.black_checkmate = False, False
        self.white_in_check, self.black_in_check = False, False
        self.selected = None
        # Rules for castling
        self.white_king_moved, self.black_king_moved = False, False
        self.white_left_rook_moved, self.black_left_rook_moved = False, False
        self.white_right_rook_moved, self.black_right_rook_moved = False, False

    def start(self):
        self.reset()
        return self.board

    def process_click(self, pos):
        square_contents = self.piece_at(pos)
        # If a piece has already been selected then this click indicates the player is either
        # Trying to move that piece or changing the current selected piece
        if self.selected is not None:
            # If it's a blank square then try and move the selected piece to that square
            if square_contents == 0:
                if pos in self.get_valid_moves():
                    print(f"Moved piece {self.piece_at(self.selected)} from {self.selected} to {pos}")
                    self.move_piece(pos)
                    self.selected = None
                return self.board, []
            # If the player clicks on another of their pieces it indicates they want to change their selected piece
            if square_contents.colour == self.turn:
                # Set the new selected square as the current position
                self.selected = pos
                if self.piece_at(self.selected) != 0:  
                    if self.piece_at(self.selected).colour == self.turn: 
                        print("Piece currently selected:", self.selected, self.piece_at(self.selected))
                        # Return a new set of squares to be highlighted
                        return self.board, self.get_valid_moves()
            # If the player clicks on any other square, it must contain an opponent's piece
            if pos in self.get_valid_moves():
                print(f"Moved piece {self.piece_at(self.selected)} from {self.selected} to {pos}")
                if self.turn == "white":
                    self.white_taken.append(self.piece_at(pos))
                else:
                    self.black_taken.append(self.piece_at(pos))
                print(f"Taken piece {self.piece_at(pos)} at position {pos}")
                self.move_piece(pos)
                self.selected = None
            return self.board, []
        # If there is currently no piece selected then the click indicates the player is selecting a piece
        else:
            if self.piece_at(pos) != 0:
                if self.piece_at(pos).colour == self.turn:
                    self.selected = pos
                    print("Piece currently selected:", self.selected, self.piece_at(self.selected))
            try:
                # Ensure that the player is selecting one of their own pieces
                if self.piece_at(self.selected).colour == self.turn:
                    # Return a new set of squares to be highlighted
                    return self.board, self.get_valid_moves()
                else:
                    self.selected = None
                    return self.board, []
            # Catch error that would be thrown if selected square is None
            except (AttributeError, TypeError):
                return self.board, []

    def move_piece(self, new_pos):
        piece = self.piece_at(self.selected)
        self.board[new_pos[0]][new_pos[1]] = piece
        self.board[self.selected[0]][self.selected[1]] = 0
        print("New board:")
        print(self.board)
        self.change_turn()

    def get_valid_moves(self):
        return [self.to_xy(i) for i in range(64)]
        piece = self.piece_at(self.selected)
        row, col = self.selected
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
                if hasattr(square_contents, "colour"):
                    if square_contents.colour != self.turn:
                        valid.append(pos)
                    break
                else:
                    valid.append(pos)
        return valid

    def _valid_pawn(self, piece, row, col):
        valid = []
        starting_row = 1 if piece.colour == "white" else 6
        if piece.colour == "white":
            positions = [(row+1, col), (row+2, col), (row+1, col+1), (row+1, col-1)]
        else:
            positions = [(row-1, col), (row-2, col), (row-1, col+1), (row-1, col-1)]
        for index, pos in enumerate(positions):
            try:
                square_contents = self.piece_at(pos)
            except IndexError:
                continue
            if index == 1 and row == starting_row and square_contents == 0 \
                    and self.piece_at(positions[0]) == 0:
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
            exec(f"""output.append({d})""")
        return output

    def reset(self):
        self.board = []
        self.board.append([Piece(p, "white") for p in ["rook", "knight", "bishop", "queen", "king", "bishop", "knight", "rook"]])
        self.board.append([Piece("pawn", "white")] * 8)
        for i in range(4):
            self.board.append([Piece(None, None)] * 8)
        self.board.append([Piece("pawn", "black")] * 8)
        self.board.append([Piece(p, "black") for p in ["rook", "knight", "bishop", "queen", "king", "bishop", "knight", "rook"]])
        self.board = np.array(self.board).reshape(8, 8)

    def change_turn(self):
        if self.turn == "white":
            print("\nBlack's turn:")
            self.turn = "black"
        else:
            print("\nWhite's turn:")
            self.turn = "white"

    def piece_at(self, pos: tuple):
        return self.board[pos[0]][pos[1]]
   
    def to_xy(self, n):
        return n // 8, n % 8


