import sys
import math
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QDialog, QMessageBox,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem
)
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtCore import pyqtSlot
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

class AssignmentTableWidget(QTableWidget):
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self.viewport())
        painter.setPen(QColor("#bbbbbb"))
        font = self.font()
        font.setItalic(True)
        painter.setFont(font)
        for row in range(self.rowCount()):
            item = self.item(row, 1)
            if item is not None and item.text().strip() == "":
                rect = self.visualItemRect(item)
                painter.drawText(rect, Qt.AlignCenter, "Input Bay Number Here")
        painter.end()

class TurntableWindow(QWidget):
    def __init__(self, test_order=None, object_to_bay=None, tactile_mode=False, send_message=None):
        super().__init__()
        print(test_order)
        self.tactile_mode = tactile_mode
        self.send_message = send_message
        self.controller = TurntableController()
        self.door_controller = DoorController()
        self.setWindowTitle("Turntable GUI")

        # Top bar with Connection and Zero buttons
        top_bar = QHBoxLayout()
        self.open_btn = QPushButton("Open")
        self.close_btn = QPushButton("Close")
        self.de_energize_btn = QPushButton("De-energize")
        self.energize_btn = QPushButton("Energize")
        self.start_btn = QPushButton("Start Test")
        self.pause_btn = QPushButton("Pause")
        self.resume_btn = QPushButton("Resume")
        self.stop_btn = QPushButton("Stop")

        self.open_btn.clicked.connect(self.door_controller.open)
        self.close_btn.clicked.connect(self.door_controller.close)
        self.de_energize_btn.clicked.connect(self.controller.de_energize)
        self.energize_btn.clicked.connect(self.controller.energize)
        self.start_btn.clicked.connect(self.run_test_sequence)
        self.pause_btn.clicked.connect(self.pause_test_sequence)
        self.resume_btn.clicked.connect(self.resume_test_sequence)
        self.stop_btn.clicked.connect(self.stop_test_sequence)

        top_bar.addWidget(self.open_btn)
        top_bar.addWidget(self.close_btn)
        top_bar.addWidget(self.de_energize_btn)
        top_bar.addWidget(self.energize_btn)
        top_bar.addWidget(self.start_btn)
        top_bar.addWidget(self.pause_btn)
        top_bar.addWidget(self.resume_btn)
        top_bar.addWidget(self.stop_btn)
        top_bar.addStretch()

        # Centered turntable
        self.turntable = TurntableWidget(self, controller=self.controller)
        self.turntable.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Assignment list widget (editable bay column)
        self.assignment_list = AssignmentTableWidget(self)
        self.assignment_list.setColumnCount(2)
        self.assignment_list.setHorizontalHeaderLabels(["Object", "Bay"])
        self.assignment_list.horizontalHeader().setStretchLastSection(True)
        self.assignment_list.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.SelectedClicked)
        self.assignment_list.setMinimumWidth(240)
        self.assignment_list.setAlternatingRowColors(True)
        self.assignment_list.setStyleSheet("""
            QTableWidget {
                background: #f8f8ff;
                alternate-background-color: #e6e6fa;
                border: 2px solid #b0c4de;
                border-radius: 10px;
                font-size: 15px;
            }
            QHeaderView::section {
                background-color: #b0c4de;
                color: #22223b;
                font-weight: bold;
                font-size: 16px;
                border: none;
                border-radius: 6px;
                padding: 6px;
            }
            QTableWidget::item {
                border: none;
                padding: 6px;
            }
        """)
        font = QFont("Segoe UI", 12)
        self.assignment_list.setFont(font)
        self.assignment_list.verticalHeader().setVisible(False)
        self.assignment_list.horizontalHeader().setHighlightSections(False)
        self.assignment_list.setShowGrid(False)

        # Main layout: turntable left, assignments right
        center_layout = QHBoxLayout()
        center_layout.addWidget(self.turntable, alignment=Qt.AlignCenter)
        center_layout.addWidget(self.assignment_list)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(top_bar)
        main_layout.addLayout(center_layout)
        self.setLayout(main_layout)
        self.resize(850, 700)

        self.test_order = test_order or []
        self.object_to_bay = object_to_bay or {}
        self.current_index = 0

        # State variables for pause/resume/stop
        self._paused = False
        self._stopped = False
        self._pending_timer = QTimer(self)
        self._pending_timer.setSingleShot(True)
        self._pending_timer.timeout.connect(self._timer_callback)
        self._timer_callback_func = None

        self.assignment_list.cellChanged.connect(self.handle_bay_edit)
        self._updating_table = False  # Prevent recursion

        self.update_assignment_list()

    def update_assignment_list(self):
        self._updating_table = True
        self.assignment_list.setRowCount(len(self.test_order))
        for i, obj in enumerate(self.test_order):
            obj_item = QTableWidgetItem(str(obj))
            obj_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)  # Not editable
            bay = self.object_to_bay.get(obj)
            if bay is None or str(bay).strip() == "":
                bay_item = QTableWidgetItem("")
                bay_item.setTextAlignment(Qt.AlignCenter)
                bay_item.setForeground(QColor("#888"))
                font = bay_item.font()
                font.setItalic(True)
                bay_item.setFont(font)
                # Set placeholder text visually
                bay_item.setData(Qt.DisplayRole, "")
                bay_item.setData(Qt.UserRole, "Input Bay Number Here")
            else:
                bay_item = QTableWidgetItem(str(bay))
                bay_item.setTextAlignment(Qt.AlignCenter)
                bay_item.setForeground(QColor("#222"))
                font = bay_item.font()
                font.setItalic(False)
                bay_item.setFont(font)
                bay_item.setData(Qt.UserRole, "")
            obj_item.setTextAlignment(Qt.AlignCenter)
            self.assignment_list.setItem(i, 0, obj_item)
            self.assignment_list.setItem(i, 1, bay_item)
            self.assignment_list.setRowHeight(i, 34)
        self._updating_table = False

    def handle_bay_edit(self, row, column):
        if self._updating_table or column != 1:
            return
        obj = self.test_order[row]
        text = self.assignment_list.item(row, 1).text().strip()
        if text == "":
            self.object_to_bay[obj] = None
            # Set placeholder style
            self.assignment_list.item(row, 1).setForeground(QColor("#888"))
            font = self.assignment_list.item(row, 1).font()
            font.setItalic(True)
            self.assignment_list.item(row, 1).setFont(font)
        else:
            try:
                bay = int(text)
                if 1 <= bay <= 16:
                    self.object_to_bay[obj] = bay
                    self.assignment_list.item(row, 1).setForeground(QColor("#222"))
                    font = self.assignment_list.item(row, 1).font()
                    font.setItalic(False)
                    self.assignment_list.item(row, 1).setFont(font)
                else:
                    raise ValueError
            except ValueError:
                self.assignment_list.item(row, 1).setText("")
                self.object_to_bay[obj] = None
                self.assignment_list.item(row, 1).setForeground(QColor("#888"))
                font = self.assignment_list.item(row, 1).font()
                font.setItalic(True)
                self.assignment_list.item(row, 1).setFont(font)

    def run_test_sequence(self):
        # Only reset if stopped, not at end
        if self._stopped:
            self._stopped = False
            self._paused = False
            self.current_index = 0

        if self._stopped:
            print("Test stopped.")
            return
        if self._paused:
            print("Test paused.")
            return
        if self.current_index >= len(self.test_order):
            print("Test complete!")
            return
        object_name = self.test_order[self.current_index]
        bay = self.object_to_bay.get(object_name)
        if bay is None:
            print(f"No bay assigned for object: {object_name}")
            self.current_index += 1
            self._start_timer(1000, self.run_test_sequence)
            return
        print(f"Moving to bay {bay} for object {object_name}")
        self.controller.move_to_bay(bay - 1, wait=True)
        if self.tactile_mode:
            print("Waiting for touch signal from tactile box...")
            self.waiting_for_touch = True
            if self.send_message:
                self.send_message({"action": "touchbox_lsl_true"})
            # Do not open doors yet; wait for touch signal
        else:
            self.door_controller.open()
            self._start_timer(2000, self.close_doors_and_continue)

    @pyqtSlot()
    def on_object_touched(self):
        if self.tactile_mode and self.waiting_for_touch:
            print("Touch detected! Opening doors.")
            self.waiting_for_touch = False
            self.door_controller.open()
            self._start_timer(2000, self.close_doors_and_continue)

    def close_doors_and_continue(self):
        if self._stopped or self._paused:
            return
        self.door_controller.close()
        self.current_index += 1
        self._start_timer(1000, self.run_test_sequence)

    def _start_timer(self, ms, callback):
        self._timer_callback_func = callback
        self._pending_timer.stop()
        self._pending_timer.setInterval(ms)
        self._pending_timer.start()

    def _timer_callback(self):
        if self._timer_callback_func:
            self._pending_timer.stop()
            self._timer_callback_func()

    def pause_test_sequence(self):
        print("Pausing test sequence.")
        self._paused = True

    def resume_test_sequence(self):
        if not self._paused:
            return
        print("Resuming test sequence.")
        self._paused = False
        # Resume immediately if not stopped and not at end
        if not self._stopped and self.current_index < len(self.test_order):
            self.run_test_sequence()

    def stop_test_sequence(self):
        print("Stopping test sequence.")
        self._stopped = True
        self._paused = False
        self.current_index = 0
        self._pending_timer.stop()  # Immediately stop any pending timer

    def open_assign_bays_dialog(self):
        from eeg_stimulus_project.stimulus.turn_table_code.object_to_bay_dialog import ObjectToBayDialog
        dlg = ObjectToBayDialog(self.test_order, num_bays=16, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self.object_to_bay = dlg.get_assignments()
            QMessageBox.information(self, "Assignments Saved", "Object-to-bay assignments have been saved.")
            self.update_assignment_list()  # Update display
        else:
            QMessageBox.information(self, "Cancelled", "No changes made to object-to-bay assignments.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TurntableWindow()
    window.show()
    sys.exit(app.exec_())