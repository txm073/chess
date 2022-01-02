# Core modules
import time
import os
import sys
import threading

try:
    # GUI library
    from PyQt5.QtWidgets import *
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    # Store the internal state of the board as a Numpy array
    import numpy as np
except ImportError:
    os.system("pip install PyQt5")
    os.system("pip install PyQt5-tools")
    os.system("pip install numpy")

try:
    os.chdir(os.path.dirname(sys.argv[0]))
except OSError:
    pass

from internal import InternalBoard, Piece


class GameUI(QWidget):

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
        self.squares = {}
        self.piece_padding = 3
        self.piece_size = self.square_size - self.piece_padding * 2
        self.selected = self.old_square = None
        self.show_move_pos = (20, 20, 15, 15)

        # Border variables
        self.border_size = 528
        self.border_x = (self.width - self.border_size) // 2
        self.border_y = (self.height + self.offset - self.border_size) // 2

        # Game variables
        self.internal = InternalBoard()

        # Initialisation methods
        self.init_styles()
        self.init_ui()
        self.update_window(self.internal.start())
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

        self.btns_frame = QFrame(self)
        self.btns_frame.setGeometry(36, 36, self.border_size, 50)
        self.btns_frame.setStyleSheet("")
        
        self.menu_btn = QPushButton(self.btns_frame)
        self.menu_btn.setGeometry(0, 0, 150, 50)
        self.menu_btn.setStyleSheet(self.btn_style)
        self.menu_btn.setText("Main Menu")
        self.menu_btn.setCursor(QCursor(Qt.PointingHandCursor))

        self.timer_label = QLabel(self.btns_frame)
        self.timer_label.setGeometry(200, 0, 128, 50)
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet(self.timer_style)
        
        self.timer_thread = threading.Thread(target=self.timer)
        self.timer_thread.start()

        self.exit_btn = QPushButton(self.btns_frame)
        self.exit_btn.setGeometry(378, 0, 150, 50)
        self.exit_btn.setStyleSheet(self.btn_style)
        self.exit_btn.setText("Save And Exit")
        self.exit_btn.setCursor(QCursor(Qt.PointingHandCursor))

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
        for i in range(8):
            for j in range(8):
                if (i + j) % 2 == 0:
                    colour = self.white
                else:
                    colour = self.brown
                square = QFrame(self.board_frame)
                square.setGeometry(j * self.square_size, i * self.square_size, self.square_size, self.square_size)
                square.setStyleSheet(f"background-color: rgb{str(colour)}; border: 2px solid rgb{str(colour)};")
                piece = QLabel(square)
                piece.setScaledContents(True)
                piece.setGeometry(self.piece_padding, self.piece_padding, self.piece_size, self.piece_size)
                self.squares[(i, j)] = piece

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

        self.timer_style = """
                        background-color: rgb(217, 200, 168);
                        border: 3px solid rgb(68, 40, 28);
                        border-radius: 10px;
                        font-size: 20px;
                            """

        self.btn_style = """
                        QPushButton {
                            """ + self.timer_style + """
                        }

                        QPushButton::hover {
                            background-color: rgb(135, 120, 100);
                        }
                            """

    def timer(self):
        minutes, seconds = 0, 0
        while True:
            time.sleep(1)
            seconds += 1
            if seconds == 60:
                minutes += 1
                seconds = 0
            if minutes < 10:
                minutes_text = "0" + str(minutes)
            else:
                minutes_text = str(minutes)
            if seconds < 10:
                seconds_text = "0" + str(seconds)
            else:
                seconds_text = str(seconds)
            if minutes_text == "99" and seconds_text == "99":
                break
            self.timer_label.setText(f"{minutes_text}:{seconds_text}")

    def update_window(self, board, highlighted=[]):
        for i, row in enumerate(board):
            for j, square in enumerate(row):
                label = self.squares[(i, j)]
                if square != 0:
                    label.setPixmap(QPixmap(os.path.join(self.base_path, square.image)))
                else:
                    label.setPixmap(QPixmap(os.path.join(self.base_path, "transparent.png")))      
                if (i, j) in highlighted:   
                    label.setStyleSheet("background-color: rgba(120, 150, 20, 160); border-radius: 24px;")
                else:
                    label.setStyleSheet("background-color: rgba(0, 0, 0, 0)")          

    def mousePressEvent(self, event):
        for i, s in enumerate(list(self.squares.values())):
            if s.underMouse():
                new_board, highlighted = self.internal.process_click(self.internal.to_xy(i))
                self.update_window(new_board, highlighted)
                break


if __name__ == "__main__":
    app = QApplication(sys.argv)
    game = GameUI()
    sys.exit(app.exec_())

