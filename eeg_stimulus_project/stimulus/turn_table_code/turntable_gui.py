import sys
import math
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QDialog, QMessageBox
)
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor
from PyQt5.QtCore import Qt, QPoint, QTimer
from eeg_stimulus_project.stimulus.turn_table_code.turntable_controller import TurntableController
from eeg_stimulus_project.stimulus.turn_table_code.doorcode import DoorController

class TurntableWidget(QWidget):
    def __init__(self, parent=None, controller=None):
        super().__init__(parent)
        self.controller = controller
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

        # Inner buttons: odd numbers 1-15
        for i in range(8):
            odd_num = 2 * i + 1  # 1, 3, 5, ..., 15
            angle = -90 + (i + 0.5) * (360 / 8)  # Centered between dividers
            rad = math.radians(angle)
            x = cx + r_inner * math.cos(rad)
            y = cy + r_inner * math.sin(rad)
            btn = QPushButton(str(odd_num), self)
            btn.setFixedSize(36, 36)
            btn.move(int(x - 18), int(y - 18))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #e0e0e0;
                    border-radius: 18px;
                }
                QPushButton:hover {
                    background-color: #ffd700;
                }
                QPushButton:pressed {
                    background-color: #bbbbbb;
                    border: 2px inset #888888;
                }
            """)
            btn.clicked.connect(lambda checked, bay=odd_num-1: self.controller.move_to_bay(bay))
            self.inner_buttons.append(btn)

        # Outer buttons: 16 at top, then 2, 4, ..., 14 clockwise
        for i in range(8):
            if i == 0:
                even_num = 16
            else:
                even_num = (2 * i)
            angle_outer = -90 + i * (360 / 8)
            rad_outer = math.radians(angle_outer)
            x2 = cx + r_outer * math.cos(rad_outer)
            y2 = cy + r_outer * math.sin(rad_outer)
            btn2 = QPushButton(str(even_num), self)
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
            btn2.clicked.connect(lambda checked, bay=even_num-1: self.controller.move_to_bay(bay))
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
    def __init__(self, test_order=None, object_to_bay=None):
        super().__init__()
        print(test_order)
        self.controller = TurntableController()
        #self.controller = None
        self.door_controller = DoorController()
        self.setWindowTitle("Turntable GUI")

        # Top bar with Connection and Zero buttons
        top_bar = QHBoxLayout()
        self.open_btn = QPushButton("Open")
        self.close_btn = QPushButton("Close")
        self.de_energize_btn = QPushButton("De-energize")
        self.energize_btn = QPushButton("Energize")
        self.start_btn = QPushButton("Start Test")
        self.assign_bays_btn = QPushButton("Assign Bays")
        self.open_btn.clicked.connect(self.door_controller.open)
        self.close_btn.clicked.connect(self.door_controller.close)
        self.de_energize_btn.clicked.connect(self.controller.de_energize)
        self.energize_btn.clicked.connect(self.controller.energize)
        self.start_btn.clicked.connect(self.run_test_sequence)
        self.assign_bays_btn.clicked.connect(self.open_assign_bays_dialog)
        top_bar.addWidget(self.open_btn)
        top_bar.addWidget(self.close_btn)
        top_bar.addWidget(self.de_energize_btn)
        top_bar.addWidget(self.energize_btn)
        top_bar.addWidget(self.start_btn)
        top_bar.addWidget(self.assign_bays_btn)
        top_bar.addStretch()

        # Centered turntable
        self.turntable = TurntableWidget(self, controller=self.controller)
        self.turntable.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(top_bar)
        main_layout.addWidget(self.turntable, alignment=Qt.AlignCenter)
        self.setLayout(main_layout)
        self.resize(650, 700)

        self.test_order = test_order or []
        self.object_to_bay = object_to_bay or {}
        self.current_index = 0

    def run_test_sequence(self):
        if self.current_index >= len(self.test_order):
            print("Test complete!")
            return
        object_name = self.test_order[self.current_index]
        bay = self.object_to_bay.get(object_name)
        if bay is None:
            print(f"No bay assigned for object: {object_name}")
            self.current_index += 1
            QTimer.singleShot(1000, self.run_test_sequence)
            return
        print(f"Moving to bay {bay} for object {object_name}")
        self.controller.move_to_bay(bay - 1, wait=True)  # bay-1 if 0-based
        self.door_controller.open()
        QTimer.singleShot(2000, self.close_doors_and_continue)

    def close_doors_and_continue(self):
        self.door_controller.close()
        self.current_index += 1
        QTimer.singleShot(1000, self.run_test_sequence)

    def open_assign_bays_dialog(self):
        from eeg_stimulus_project.stimulus.turn_table_code.object_to_bay_dialog import ObjectToBayDialog
        # Use self.test_order as the object list
        dlg = ObjectToBayDialog(self.test_order, num_bays=16, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self.object_to_bay = dlg.get_assignments()
            # Optionally, show a message or update the UI
            QMessageBox.information(self, "Assignments Saved", "Object-to-bay assignments have been saved.")
        else:
            QMessageBox.information(self, "Cancelled", "No changes made to object-to-bay assignments.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TurntableWindow()
    window.show()
    sys.exit(app.exec_())