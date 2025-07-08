import sys
import math
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
)
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor
from PyQt5.QtCore import Qt, QPoint

class TurntableWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(500, 500)
        self.inner_buttons = []
        self.outer_buttons = []
        self.init_buttons()

    def init_buttons(self):
        for btn in self.inner_buttons + self.outer_buttons:
            btn.setParent(None)
        self.inner_buttons = []
        self.outer_buttons = []

        cx, cy = self.width() // 2, self.height() // 2
        r_inner = min(cx, cy) * 0.55
        r_outer = min(cx, cy) * 0.80

        for i in range(8):
            angle = -90 + (i + 0.5) * (360 / 8)
            rad = math.radians(angle)
            x = cx + r_inner * math.cos(rad)
            y = cy + r_inner * math.sin(rad)
            btn = QPushButton(str(i + 1), self)
            btn.setFixedSize(40, 40)
            btn.move(int(x - 20), int(y - 20))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #e0e0e0;
                    border-radius: 20px;
                }
                QPushButton:hover {
                    background-color: #ffd700;
                }
                QPushButton:pressed {
                    background-color: #bbbbbb;
                    border: 2px inset #888888;
                }
            """)
            btn.clicked.connect(lambda checked, n=i+1: print(f"Button {n} Pressed"))
            self.inner_buttons.append(btn)

            angle_outer = -90 + i * (360 / 8)
            rad_outer = math.radians(angle_outer)
            x2 = cx + r_outer * math.cos(rad_outer)
            y2 = cy + r_outer * math.sin(rad_outer)
            btn2 = QPushButton(str(i + 9), self)
            btn2.setFixedSize(36, 36)
            btn2.move(int(x2 - 18), int(y2 - 18))
            btn2.setStyleSheet("""
                QPushButton {
                    background-color: #b0c4de;
                    border-radius: 18px;
                }
                QPushButton:hover {
                    background-color: #ffa500;
                }
                QPushButton:pressed {
                    background-color: #7a9cc6;
                    border: 2px inset #555555;
                }
            """)
            btn2.clicked.connect(lambda checked, n=i+9: print(f"Button {n} Pressed"))
            self.outer_buttons.append(btn2)

    def resizeEvent(self, event):
        self.init_buttons()
        super().resizeEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        cx, cy = self.width() // 2, self.height() // 2
        radius = min(cx, cy) * 0.65

        painter.setPen(QPen(Qt.black, 3))
        painter.setBrush(QBrush(QColor(230, 230, 250)))
        painter.drawEllipse(QPoint(cx, cy), int(radius), int(radius))

        for i in range(8):
            angle = i * (360 / 8)
            rad = math.radians(angle)
            x = cx + radius * math.cos(rad)
            y = cy + radius * math.sin(rad)
            painter.drawLine(cx, cy, int(x), int(y))

        painter.setPen(QPen(Qt.gray, 1, Qt.DashLine))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPoint(cx, cy), int(radius * 1.23), int(radius * 1.23))

class TurntableWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Turntable GUI")

        # Top bar with Connection and Zero buttons
        top_bar = QHBoxLayout()
        self.connection_btn = QPushButton("Connection")
        self.zero_btn = QPushButton("Zero")
        self.connection_btn.clicked.connect(lambda: print("Connection Button Pressed"))
        self.zero_btn.clicked.connect(lambda: print("Zero Button Pressed"))
        top_bar.addWidget(self.connection_btn)
        top_bar.addWidget(self.zero_btn)
        top_bar.addStretch()

        # Centered turntable
        self.turntable = TurntableWidget(self)
        self.turntable.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(top_bar)
        main_layout.addWidget(self.turntable, alignment=Qt.AlignCenter)
        self.setLayout(main_layout)
        self.resize(650, 700)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TurntableWindow()
    window.show()
    sys.exit(app.exec_())