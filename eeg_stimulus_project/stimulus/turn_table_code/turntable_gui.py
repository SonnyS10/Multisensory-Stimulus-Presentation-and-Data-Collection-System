import sys
import math
import logging
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QDialog, QMessageBox,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem, QCheckBox, QSpinBox, QFrame
)
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont
from PyQt5.QtCore import Qt, QPoint, QTimer, pyqtSlot

from eeg_stimulus_project.stimulus.turn_table_code.turntable_controller import TurntableController
from eeg_stimulus_project.stimulus.turn_table_code.doorcode import DoorController


# Time to wait after releasing a scent before opening the booth doors (revealing the
# object). Kept equal to the 2D display's SCENT_DISPENSE_DELAY_MS so the scent->object
# order and timing is identical across every olfactory realism block, with or without
# tactile.
SCENT_DISPENSE_DELAY_MS = 4000


def get_turntable_instruction_text(test_name):
    """Participant-facing instructions shown at the very start of a turntable test.

    Text is provided verbatim by the study lead; do not edit the wording. Neutral and
    Alcohol variants of a modality share the same instructions. Returns None for tests
    that have no turntable instructions (e.g. Stroop tasks, which are display-only).
    """
    name = str(test_name or "").strip()
    if name in ("Unisensory Neutral Visual", "Unisensory Alcohol Visual"):
        return (
            "During this task, you will see objects presented one at a time in the viewing booth. "
            "Please view each object as it is presented. In between each object, you will see an empty slot. "
            "While viewing the objects, please try to minimize movements including blinks. "
            "At the end of a series, you will be asked to answer a question by pressing a button on the keyboard."
        )
    if name in ("Multisensory Neutral Visual & Olfactory", "Multisensory Alcohol Visual & Olfactory"):
        return (
            "During this task, you will see objects presented one at a time in the viewing booth. "
            "Please view each object as it is presented. In between each object, you will see an empty slot. "
            "while breathing through your nose to pick up the scent that will be released at the same time."
        )
    if name in ("Multisensory Neutral Visual, Tactile & Olfactory", "Multisensory Alcohol Visual, Tactile & Olfactory"):
        return (
            "Once prompted, lightly place your left hand on the object in the touchbox. "
            "This will trigger an object to be presented in the viewing booth and a scent to be released. "
            "Please breathe through your nose the entire time. After 2-3 seconds, please remove your hand from the object but keep it on the handrest. "
            "Please try to minimize any additional movements, including eye blinks while the task is ongoing."
        )
    return None


def bay_label_to_index(bay_label):
    """Map displayed bay labels to physical 0-based positions around the 16-step ring."""
    if 1 <= bay_label <= 8:
        # Inner ring labels occupy odd physical indices: 1, 3, 5, ... 15
        return 2 * bay_label - 1
    if 9 <= bay_label <= 16:
        # Outer ring labels occupy even physical indices: 0, 2, 4, ... 14
        return 2 * (bay_label - 9)
    raise ValueError(f"Bay label out of range: {bay_label}")


def bay_index_to_label(bay_index):
    """Map a physical 0-based position back to the displayed bay label."""
    bay_index = bay_index % 16
    if bay_index % 2 == 1:
        return (bay_index + 1) // 2
    return (bay_index // 2) + 9


def paired_empty_bay_slot(bay_label):
    """Return the paired half-bay slot that should remain empty."""
    if bay_label in (2, 4, 6, 8):
        return bay_label - 1
    return None


class TurntableStimulusItem:
    def __init__(self, display_name, sequence_number=None, source_path=None, scent_number=None):
        self.display_name = display_name
        self.sequence_number = sequence_number
        self.source_path = source_path
        self.scent_number = scent_number

    def __str__(self):
        return self.display_name


def stimulus_label(stimulus):
    return getattr(stimulus, "display_name", str(stimulus))


def stimulus_sequence_number(stimulus):
    return getattr(stimulus, "sequence_number", None)


def stimulus_scent_number(stimulus):
    return getattr(stimulus, "scent_number", None)

class TurntableWidget(QWidget):
    def __init__(self, parent=None, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.setMinimumSize(500, 500)
        self.inner_buttons = []
        self.outer_buttons = []
        self.button_by_label = {}
        self.init_buttons()

    def init_buttons(self):
        if self.button_by_label:
            return

        # Inner buttons: 1-8
        for i in range(8):
            inner_num = i + 1
            physical_index = bay_label_to_index(inner_num)
            btn = QPushButton(str(inner_num), self)
            btn.setFixedSize(42, 42)
            btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
            self.apply_bay_button_style(btn, "inner")
            btn.clicked.connect(lambda checked, bay=physical_index: self.controller.move_to_bay(bay))
            btn.clicked.connect(lambda checked, label=inner_num: self.manual_move_complete(label))
            self.inner_buttons.append(btn)
            self.button_by_label[inner_num] = btn

        # Outer buttons: 9-16
        for i in range(8):
            outer_num = i + 9
            physical_index = bay_label_to_index(outer_num)
            btn2 = QPushButton(str(outer_num), self)
            btn2.setFixedSize(42, 42)
            btn2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            btn2.setFont(QFont("Segoe UI", 11, QFont.Bold))
            self.apply_bay_button_style(btn2, "outer")
            btn2.clicked.connect(lambda checked, bay=physical_index: self.controller.move_to_bay(bay))
            btn2.clicked.connect(lambda checked, label=outer_num: self.manual_move_complete(label))
            self.outer_buttons.append(btn2)
            self.button_by_label[outer_num] = btn2
        self.position_buttons()

    def position_buttons(self):
        cx, cy = self.width() // 2, self.height() // 2
        r_inner = min(cx, cy) * 0.55
        r_outer = min(cx, cy) * 0.80

        for i, btn in enumerate(self.inner_buttons):
            angle = -90 + (i + 0.5) * (360 / 8)  # Centered between dividers
            rad = math.radians(angle)
            x = cx + r_inner * math.cos(rad)
            y = cy + r_inner * math.sin(rad)
            btn.move(int(x - btn.width() / 2), int(y - btn.height() / 2))
            btn.raise_()
            btn.show()

        for i, btn in enumerate(self.outer_buttons):
            angle_outer = -90 + i * (360 / 8)
            rad_outer = math.radians(angle_outer)
            x2 = cx + r_outer * math.cos(rad_outer)
            y2 = cy + r_outer * math.sin(rad_outer)
            btn.move(int(x2 - btn.width() / 2), int(y2 - btn.height() / 2))
            btn.raise_()
            btn.show()

    def apply_bay_button_style(self, button, ring="inner", highlight=None):
        if highlight == "front":
            background = "#43A047"
            border = "#1B5E20"
            color = "white"
        elif highlight == "unload":
            background = "#D32F2F"
            border = "#7F1D1D"
            color = "white"
        elif ring == "outer":
            background = "#B0C4DE"
            border = "#7A9CC6"
            color = "#22223b"
        else:
            background = "#E0E0E0"
            border = "#BDBDBD"
            color = "#22223b"
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {background};
                color: {color};
                border-radius: 21px;
                border: 3px solid {border};
                min-width: 42px;
                max-width: 42px;
                min-height: 42px;
                max-height: 42px;
                padding: 0px;
                margin: 0px;
                font-weight: 700;
                font-size: 11pt;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: #42A5F5;
                color: white;
            }}
            QPushButton:pressed {{
                background-color: #1976D2;
                border: 3px inset #555555;
            }}
        """)

    def manual_move_complete(self, clicked_label):
        parent = self.parent()
        if parent is not None and hasattr(parent, "manual_bay_move_complete"):
            parent.manual_bay_move_complete(clicked_label)

    def update_bay_highlights(self, front_label, unload_label):
        for label, button in self.button_by_label.items():
            ring = "outer" if label > 8 else "inner"
            if label == front_label:
                self.apply_bay_button_style(button, ring, "front")
            elif label == unload_label:
                self.apply_bay_button_style(button, ring, "unload")
            else:
                self.apply_bay_button_style(button, ring)

    def resizeEvent(self, event):
        self.position_buttons()
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
    def __init__(self, test_order=None, object_to_bay=None, tactile_mode=False, send_message=None,
                 require_scent_assignments=False, olfactory_mode=False,
                 on_sequence_started=None, on_sequence_stopped=None, current_test=None,
                 show_instruction_overlay=True):
        super().__init__()
        print(test_order)
        self.current_test = current_test
        self.tactile_mode = tactile_mode
        self.send_message = send_message
        self.require_scent_assignments = require_scent_assignments
        self.olfactory_mode = olfactory_mode
        self.on_sequence_started = on_sequence_started
        self.on_sequence_stopped = on_sequence_stopped
        self._session_started = False
        self.controller = TurntableController()
        self.controller.set_label_formatter(bay_index_to_label)
        self.door_controller = None
        self.olfactory_controller = None
        self.olfactory_connected = False
        self.setWindowTitle("Turntable GUI")
        self.setMinimumSize(1100, 780)
        self.resize(1200, 850)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5fa;
                color: #22223b;
                font-family: "Segoe UI";
                font-size: 13px;
            }
            QFrame#HeaderFrame {
                background-color: #7E57C2;
                border-radius: 12px;
            }
            QFrame#HeaderFrame QCheckBox {
                background-color: transparent;
                color: white;
            }
            QFrame#Panel {
                background-color: #ede7f6;
                border: 1.5px solid #bc85fa;
                border-radius: 12px;
            }
            QFrame#Panel QLabel {
                background-color: transparent;
            }
            QPushButton {
                background-color: #42A5F5;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 14px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #bdbdbd;
                color: #eeeeee;
            }
            QCheckBox {
                padding: 4px 6px;
                font-weight: 600;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
            QSpinBox {
                background: white;
                border: 1px solid #bc85fa;
                border-radius: 6px;
                padding: 5px 8px;
            }
        """)

        # Top bar with Connection and Zero buttons
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)
        self.open_btn = QPushButton("Open")
        self.close_btn = QPushButton("Close")
        self.de_energize_btn = QPushButton("De-energize")
        self.energize_btn = QPushButton("Energize")
        self.start_btn = QPushButton("Start Test")
        self.pause_btn = QPushButton("Pause")
        self.resume_btn = QPushButton("Resume")
        self.stop_btn = QPushButton("Stop")
        self.auto_doors_checkbox = QCheckBox("Auto Doors")
        self.auto_doors_checkbox.setChecked(False)
        self.manual_replacement_checkbox = QCheckBox("Manual replacement pause")
        self.manual_replacement_checkbox.setChecked(True)
        self.replacement_dwell_box = QSpinBox()
        self.replacement_dwell_box.setRange(1, 300)
        self.replacement_dwell_box.setValue(20)
        self.replacement_dwell_box.setSuffix(" sec")
        self.replacement_continue_btn = QPushButton("Replacement complete / Continue")
        self.replacement_continue_btn.setEnabled(False)

        self.open_btn.clicked.connect(self.open_doors_manually)
        self.close_btn.clicked.connect(self.close_doors_manually)
        self.de_energize_btn.clicked.connect(self.controller.de_energize)
        self.energize_btn.clicked.connect(self.controller.energize)
        self.start_btn.clicked.connect(self.run_test_sequence)
        self.pause_btn.clicked.connect(self.pause_test_sequence)
        self.resume_btn.clicked.connect(self.resume_test_sequence)
        self.stop_btn.clicked.connect(self.stop_test_sequence)
        self.replacement_continue_btn.clicked.connect(self.continue_replacement_pause)

        top_bar.addWidget(self.open_btn)
        top_bar.addWidget(self.close_btn)
        top_bar.addWidget(self.de_energize_btn)
        top_bar.addWidget(self.energize_btn)
        top_bar.addWidget(self.start_btn)
        top_bar.addWidget(self.pause_btn)
        top_bar.addWidget(self.resume_btn)
        top_bar.addWidget(self.stop_btn)
        top_bar.addWidget(self.auto_doors_checkbox)
        top_bar.addStretch()

        header_frame = QFrame(self)
        header_frame.setObjectName("HeaderFrame")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 14, 16, 14)
        header_layout.setSpacing(10)

        header_label = QLabel("Turntable Control", self)
        header_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("background: transparent; color: white;")
        header_layout.addWidget(header_label)
        header_layout.addLayout(top_bar)

        # Centered turntable
        self.turntable = TurntableWidget(self, controller=self.controller)
        self.turntable.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Assignment list widget (editable bay column)
        self.assignment_list = AssignmentTableWidget(self)
        self.assignment_list.setColumnCount(3)
        self.assignment_list.setHorizontalHeaderLabels(["Object", "Bay", "Empty Slot Bay"])
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

        self.auto_bay_btn = QPushButton("Auto-Bay 1-8")
        self.auto_bay_gap_btn = QPushButton("Auto-Bay 1-8 (Half-Bays Empty)")
        self.auto_bay_btn.clicked.connect(self.auto_bay_sequential)
        self.auto_bay_gap_btn.clicked.connect(self.auto_bay_with_gaps)

        self.sequence_status_label = QLabel("Status: Ready")
        self.sequence_status_label.setWordWrap(True)
        self.sequence_status_label.setStyleSheet("color: #22223b; font-size: 13px; padding: 4px;")

        self.instructions_toggle_btn = QPushButton("Hide Instructions")
        self.instructions_toggle_btn.clicked.connect(self.toggle_instructions)
        self.instructions_panel = QLabel(
            "<b>Button guide</b><br>"
            "<b>Open / Close:</b> manually moves the booth door. These buttons initialize the door motor on demand.<br>"
            "<b>Energize / De-energize:</b> powers the turntable motor on or off. Moves auto-energize when needed.<br>"
            "<b>Start Test:</b> runs the current bay sequence. <b>Pause</b> holds the sequence; <b>Resume</b> continues; <b>Stop</b> resets it.<br>"
            "<b>Auto-Bay 1-8:</b> assigns objects to bays 1 through 8 in order.<br>"
            "<b>Auto-Bay 1-8 (Half-Bays Empty):</b> assigns objects to filled bays 2, 4, 6, and 8, then runs one empty/control bay before each filled stimulus bay.<br><br>"
            "<b>Doors and replacement</b><br>"
            "<b>Auto Doors:</b> when checked, filled/stimulus bays open, dwell, close, and continue. Manual Open/Close always works even when Auto Doors is off.<br>"
            "<b>Manual replacement pause:</b> waits for Replacement complete / Continue during replacement steps. When unchecked, the Dwell timer advances automatically.<br>"
            "Replacement starts after 4 total half-empty moves. Odd bays are empty/control; even bays hold bottles.<br><br>"
            "<b>Bay labels</b><br>"
            "GUI bay labels are the experiment-facing bay numbers used in the table, status text, and command-line logs.<br><br>"
            "<b>Safety notes</b><br>"
            "Empty/control bays never arm the tactile box and never trigger Auto Doors. Confirm bay assignments before Start Test, keep hands clear while moving, and use Stop before changing the sequence."
        )
        self.instructions_panel.setTextFormat(Qt.RichText)
        self.instructions_panel.setWordWrap(True)
        self.instructions_panel.setStyleSheet("""
            QLabel {
                background: #eef4ff;
                border: 1px solid #b0c4de;
                border-radius: 8px;
                padding: 10px;
                color: #22223b;
                font-size: 15px;
            }
        """)

        replacement_row = QHBoxLayout()
        replacement_row.addWidget(self.manual_replacement_checkbox)
        replacement_row.addWidget(QLabel("Dwell:"))
        replacement_row.addWidget(self.replacement_dwell_box)

        assignment_panel = QVBoxLayout()
        assignment_panel.setSpacing(10)
        assignment_panel.addWidget(self.auto_bay_btn)
        assignment_panel.addWidget(self.auto_bay_gap_btn)
        assignment_panel.addWidget(self.instructions_toggle_btn)
        assignment_panel.addWidget(self.instructions_panel)
        assignment_panel.addLayout(replacement_row)
        assignment_panel.addWidget(self.replacement_continue_btn)
        assignment_panel.addWidget(self.sequence_status_label)
        assignment_panel.addWidget(self.assignment_list)

        # Main layout: turntable left, assignments right
        turntable_panel = QFrame(self)
        turntable_panel.setObjectName("Panel")
        turntable_panel_layout = QVBoxLayout(turntable_panel)
        turntable_panel_layout.setContentsMargins(16, 16, 16, 16)
        turntable_panel_layout.setSpacing(12)
        turntable_panel_layout.addWidget(self.turntable, alignment=Qt.AlignCenter)

        assignment_frame = QFrame(self)
        assignment_frame.setObjectName("Panel")
        assignment_frame.setMinimumWidth(380)
        assignment_frame_layout = QVBoxLayout(assignment_frame)
        assignment_frame_layout.setContentsMargins(16, 16, 16, 16)
        assignment_frame_layout.addLayout(assignment_panel)

        center_layout = QHBoxLayout()
        center_layout.setSpacing(18)
        center_layout.addWidget(turntable_panel, stretch=3)
        center_layout.addWidget(assignment_frame, stretch=2)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(18)
        main_layout.addWidget(header_frame)
        main_layout.addLayout(center_layout)
        self.setLayout(main_layout)

        self.test_order = test_order or []
        self.object_to_bay = object_to_bay or {}
        self.current_index = 0
        self.sequence_steps = []

        # State variables for pause/resume/stop
        self._paused = False
        self._stopped = False
        self._sequence_running = False
        self._waiting_for_replacement = False
        self._pending_timer = QTimer(self)
        self._pending_timer.setSingleShot(True)
        self._pending_timer.timeout.connect(self._timer_callback)
        self._timer_callback_func = None
        self._auto_doors_opened_for_current_item = False

        self.assignment_list.cellChanged.connect(self.handle_bay_edit)
        self._updating_table = False  # Prevent recursion
        self._gap_replacement_objects = set()
        self._show_empty_slot_bays = False
        self._half_empty_mode = False
        self.replacement_start_after_moves = 4
        self.starting_bay_label = 1
        self._starting_bay_label_emitted = False

        if not self.object_to_bay and self.test_order:
            self.auto_assign_bays(list(range(1, 9)), "1-8", show_message=False)

        self.update_assignment_list()
        self.update_position_indicators()

        # Participant instructions are usually shown in the display window when
        # launched from the main GUI, leaving this window for experimenter control.
        if show_instruction_overlay:
            self._build_instruction_overlay()
            self.show_instruction_overlay()

    def _build_instruction_overlay(self):
        self.instruction_overlay = QFrame(self)
        self.instruction_overlay.setObjectName("InstructionOverlay")
        self.instruction_overlay.setStyleSheet("""
            QFrame#InstructionOverlay {
                background-color: white;
            }
            QFrame#InstructionOverlay QLabel {
                background: transparent;
                color: black;
            }
        """)
        overlay_layout = QVBoxLayout(self.instruction_overlay)
        overlay_layout.setContentsMargins(80, 60, 80, 60)
        overlay_layout.setSpacing(40)
        overlay_layout.addStretch()

        self.instruction_overlay_label = QLabel("", self.instruction_overlay)
        self.instruction_overlay_label.setWordWrap(True)
        self.instruction_overlay_label.setAlignment(Qt.AlignCenter)
        self.instruction_overlay_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Maximum)
        self._update_instruction_overlay_font()
        overlay_layout.addWidget(self.instruction_overlay_label, alignment=Qt.AlignHCenter)

        overlay_layout.addStretch()

        self.instruction_overlay.hide()

    def _update_instruction_overlay_font(self):
        self.instruction_overlay_label.setFont(QFont("Arial", 22))
        available_width = max(0, self.width() - 160)
        paragraph_width = max(520, min(700, available_width))
        self.instruction_overlay_label.setFixedWidth(paragraph_width)
        self.instruction_overlay_label.adjustSize()

    def show_instruction_overlay(self):
        text = get_turntable_instruction_text(self.current_test)
        if not text:
            # No turntable instructions for this test; leave controls visible.
            return
        self.instruction_overlay_label.setText(
            f"{text}\n\nPress the SPACE BAR when you have finished reading the instructions, "
            "then wait for the test to begin."
        )
        self._update_instruction_overlay_font()
        self.instruction_overlay.setGeometry(self.rect())
        self.instruction_overlay.raise_()
        self.instruction_overlay.show()
        self.setFocus(Qt.ActiveWindowFocusReason)

    def hide_instruction_overlay(self):
        self.instruction_overlay.hide()

    def keyPressEvent(self, event):
        if (
            getattr(self, "instruction_overlay", None) is not None
            and self.instruction_overlay.isVisible()
            and event.key() in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter)
        ):
            self.hide_instruction_overlay()
            event.accept()
            return
        super().keyPressEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        if getattr(self, "instruction_overlay", None) is not None and self.instruction_overlay.isVisible():
            self.instruction_overlay.setGeometry(self.rect())
            self.instruction_overlay.raise_()
            self._update_instruction_overlay_font()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if getattr(self, "instruction_overlay", None) is not None and self.instruction_overlay.isVisible():
            self.instruction_overlay.setGeometry(self.rect())
            self._update_instruction_overlay_font()

    def front_bay_label(self):
        return bay_index_to_label(getattr(self.controller, "current_bay", 0))

    def unload_bay_label(self):
        front_label = self.front_bay_label()
        return ((front_label - 1 + 3) % 8) + 1

    def update_position_indicators(self):
        # Diagram highlighting is intentionally disabled for now.
        # Keep front/unload helpers and update_bay_highlights() available for a later UI pass.
        return

    def manual_bay_move_complete(self, clicked_label):
        self.update_position_indicators()
        front_label = self.front_bay_label()
        if front_label == clicked_label:
            self.sequence_status_label.setText(f"Manual move complete. Front: Bay {front_label}.")
        else:
            self.sequence_status_label.setText(
                f"Manual move did not complete to Bay {clicked_label}. Front remains Bay {front_label}."
            )

    def toggle_instructions(self):
        show_instructions = not self.instructions_panel.isVisible()
        self.instructions_panel.setVisible(show_instructions)
        self.instructions_toggle_btn.setText("Hide Instructions" if show_instructions else "Show Instructions")

    def auto_doors_enabled(self):
        return self.auto_doors_checkbox.isChecked()

    def get_door_controller(self):
        if self.door_controller is not None:
            return self.door_controller
        try:
            self.door_controller = DoorController()
            return self.door_controller
        except Exception as e:
            self.report_door_error("initialize", e)
            return None

    def report_door_error(self, action, error):
        message = f"Could not {action} doors: {error}"
        print(message)
        QMessageBox.warning(self, "Door Control Error", message)

    def run_door_command(self, command_name, action_label):
        door_controller = self.get_door_controller()
        if door_controller is None:
            return False
        try:
            getattr(door_controller, command_name)()
            return True
        except Exception as e:
            self.report_door_error(action_label, e)
            return False

    def open_doors_manually(self):
        self.run_door_command("open", "open")

    def close_doors_manually(self):
        self.run_door_command("close", "close")

    def open_doors_automatically(self):
        return self.run_door_command("open", "open")

    def close_doors_automatically(self):
        return self.run_door_command("close", "close")

    def auto_assign_bays(self, bay_sequence, mode_name, show_message=True):
        self._gap_replacement_objects.clear()
        self._show_empty_slot_bays = False
        self._half_empty_mode = False
        self.sequence_steps = []
        self.object_to_bay = {}
        for i, obj in enumerate(self.test_order):
            if i < len(bay_sequence):
                self.object_to_bay[obj] = bay_sequence[i]
            else:
                self.object_to_bay[obj] = None

        self.update_assignment_list()

        if show_message and len(self.test_order) > len(bay_sequence):
            QMessageBox.information(
                self,
                "Auto-Bay Complete",
                f"Assigned first {len(bay_sequence)} items using pattern {mode_name}. Remaining items were left empty.",
            )

    def auto_bay_sequential(self):
        self.auto_assign_bays(list(range(1, 9)), "1-8")

    def auto_bay_with_gaps(self):
        self._gap_replacement_objects.clear()
        self._show_empty_slot_bays = True
        self._half_empty_mode = True
        self.sequence_steps = []

        # Keep odd bays empty/control and assign objects to even filled bays.
        self.object_to_bay = {}
        filled_bays = [2, 4, 6, 8]

        for i, obj in enumerate(self.test_order):
            bay = filled_bays[i % len(filled_bays)]
            self.object_to_bay[obj] = bay
            if i >= len(filled_bays):
                self._gap_replacement_objects.add(obj)

        self.update_assignment_list()

        if len(self.test_order) > len(filled_bays):
            QMessageBox.information(
                self,
                "Auto-Bay Complete",
                "Assigned filled bays using 2, 4, 6, 8. Odd bays 1, 3, 5, 7 remain empty/control. Items beyond 4 wrapped and duplicate earlier bay assignments.",
            )

    def update_assignment_list(self):
        self._updating_table = True
        self.assignment_list.setRowCount(len(self.test_order))

        bay_counts = {}
        for obj in self.test_order:
            bay = self.object_to_bay.get(obj)
            if isinstance(bay, int) and 1 <= bay <= 16:
                bay_counts[bay] = bay_counts.get(bay, 0) + 1
        duplicate_bays = {bay for bay, count in bay_counts.items() if count > 1}

        for i, obj in enumerate(self.test_order):
            seq = stimulus_sequence_number(obj)
            label = stimulus_label(obj)
            display_text = f"{seq}. {label}" if seq is not None else label
            obj_item = QTableWidgetItem(display_text)
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
                bay_item.setToolTip("")
                empty_slot_item = QTableWidgetItem("")
                empty_slot_item.setTextAlignment(Qt.AlignCenter)
                empty_slot_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                empty_slot_item.setForeground(QColor("#888"))
            else:
                bay_item = QTableWidgetItem(str(bay))
                bay_item.setTextAlignment(Qt.AlignCenter)
                bay_item.setForeground(QColor("#222"))
                font = bay_item.font()
                font.setItalic(False)
                bay_item.setFont(font)
                bay_item.setData(Qt.UserRole, "")
                paired_slot = paired_empty_bay_slot(bay) if self._show_empty_slot_bays else None
                empty_slot_item = QTableWidgetItem(str(paired_slot) if paired_slot is not None else "")
                empty_slot_item.setTextAlignment(Qt.AlignCenter)
                empty_slot_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                if bay in duplicate_bays:
                    bay_item.setBackground(QColor("#ffe7ad"))
                    bay_item.setToolTip("Duplicate bay assignment: multiple stimuli share this bay.")
                    if self._show_empty_slot_bays:
                        empty_slot_item.setBackground(QColor("#fff4d1"))
                        empty_slot_item.setToolTip("Paired empty slot for this duplicated bay.")
                    else:
                        empty_slot_item.setBackground(QColor("#ffffff"))
                        empty_slot_item.setToolTip("")
                elif obj in self._gap_replacement_objects:
                    bay_item.setBackground(QColor("#e6f0ff"))
                    bay_item.setToolTip("Wrapped assignment after bay 8 (shares bay number by design).")
                    empty_slot_item.setToolTip("Paired empty slot.")
                else:
                    bay_item.setBackground(QColor("#ffffff"))
                    bay_item.setToolTip("")
                    empty_slot_item.setToolTip("Paired empty slot." if self._show_empty_slot_bays else "")
            obj_item.setTextAlignment(Qt.AlignCenter)
            self.assignment_list.setItem(i, 0, obj_item)
            self.assignment_list.setItem(i, 1, bay_item)
            self.assignment_list.setItem(i, 2, empty_slot_item)
            self.assignment_list.setRowHeight(i, 34)
        self._updating_table = False

    def handle_bay_edit(self, row, column):
        if self._updating_table or column != 1:
            return
        obj = self.test_order[row]
        self._gap_replacement_objects.discard(obj)
        self._show_empty_slot_bays = False
        self._half_empty_mode = False
        self.sequence_steps = []
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

    def build_run_sequence(self):
        if self._half_empty_mode:
            return self.build_half_empty_sequence()

        steps = []
        for obj in self.test_order:
            bay = self.object_to_bay.get(obj)
            if bay is None:
                print(f"No bay assigned for object: {stimulus_label(obj)}")
                continue
            steps.append({"type": "stimulus", "bay": bay, "object": obj})
        return steps

    def build_half_empty_sequence(self):
        bay_pairs = [(1, 2), (3, 4), (5, 6), (7, 8)]
        valid_filled_bays = {filled for _, filled in bay_pairs}
        pair_by_filled_bay = {filled: (empty, filled) for empty, filled in bay_pairs}

        objects_by_bay = {filled: [] for _, filled in bay_pairs}
        for obj in self.test_order:
            bay = self.object_to_bay.get(obj)
            if bay in objects_by_bay:
                objects_by_bay[bay].append(obj)
            elif bay is not None:
                print(f"Ignoring {stimulus_label(obj)}: half-empty mode only uses filled bays 2, 4, 6, 8.")

        steps = []
        last_filled_bay = None
        for obj in self.test_order:
            bay = self.object_to_bay.get(obj)
            if bay not in valid_filled_bays:
                continue
            empty_bay, filled_bay = pair_by_filled_bay[bay]
            steps.append({"type": "empty_control", "bay": empty_bay})
            steps.append({"type": "stimulus", "bay": filled_bay, "object": obj})
            last_filled_bay = filled_bay

        if last_filled_bay is not None:
            empty_bay, _ = pair_by_filled_bay[last_filled_bay]
            steps.append({"type": "empty_control", "bay": empty_bay})
        return steps

    def start_new_sequence(self):
        self.sequence_steps = self.build_run_sequence()
        self.current_index = 0
        self._sequence_running = True
        self._waiting_for_replacement = False
        self._auto_doors_opened_for_current_item = False
        self._starting_bay_label_emitted = False
        self.replacement_continue_btn.setEnabled(False)
        self.update_position_indicators()

    def missing_scent_assignments_for_sequence(self):
        if not self.require_scent_assignments:
            return []
        missing = []
        for step in self.sequence_steps:
            if step.get("type") != "stimulus":
                continue
            obj = step.get("object")
            scent_number = stimulus_scent_number(obj)
            try:
                scent_number = int(scent_number)
            except (TypeError, ValueError):
                scent_number = None
            if scent_number is None or not 1 <= scent_number <= 8:
                missing.append(f"Bay {step.get('bay')}: {stimulus_label(obj)}")
        return missing

    def object_assigned_to_bay(self, bay):
        for obj in self.test_order:
            if self.object_to_bay.get(obj) == bay:
                return obj
        return None

    def starting_bay_step(self):
        obj = self.object_assigned_to_bay(self.starting_bay_label)
        if obj is None:
            return {"type": "empty_start", "bay": self.starting_bay_label}
        return {"type": "stimulus_start", "bay": self.starting_bay_label, "object": obj}

    def emit_starting_bay_label_if_needed(self):
        if self._starting_bay_label_emitted:
            return
        self._starting_bay_label_emitted = True
        if self.sequence_steps and self.sequence_steps[0].get("bay") == self.starting_bay_label:
            return
        self.emit_bay_label(self.starting_bay_step(), phase="start_position")

    def emit_bay_label(self, step, phase="shown"):
        if not self.send_message:
            return
        bay = step.get("bay")
        step_type = step.get("type", "unknown")
        obj = step.get("object")
        object_name = stimulus_label(obj) if obj is not None else "Empty"
        sequence_number = stimulus_sequence_number(obj) if obj is not None else None
        scent_number = stimulus_scent_number(obj) if obj is not None else None
        current_step = self.current_index + 1 if self.sequence_steps else 0
        total_steps = len(self.sequence_steps)
        label_parts = [
            f"Turntable Bay {bay} Shown",
            f"phase={phase}",
            f"type={step_type}",
            f"object={object_name}",
            f"step={current_step}/{total_steps}",
        ]
        if sequence_number is not None:
            label_parts.append(f"stimulus_order={sequence_number}")
        if self.olfactory_mode and scent_number is not None:
            label_parts.append(f"scent={scent_number}")
        label = " | ".join(label_parts)
        self.emit_turntable_label(label)

    def ensure_olfactory_controller(self):
        if self.olfactory_controller is not None and self.olfactory_connected:
            return True
        try:
            from eeg_stimulus_project.stimulus.olfactory.olfactory_controller import OlfactoryController
            self.olfactory_controller = OlfactoryController()
            self.olfactory_connected = self.olfactory_controller.connect()
            return self.olfactory_connected
        except Exception as e:
            print(f"Could not connect olfactory controller: {e}")
            self.olfactory_controller = None
            self.olfactory_connected = False
            return False

    def stop_scent_if_connected(self, scent_number):
        if self.olfactory_controller is not None and self.olfactory_connected:
            self.olfactory_controller.stop_scent(scent_number)

    def close_olfactory_controller(self):
        if self.olfactory_controller is not None:
            self.olfactory_controller.close()
        self.olfactory_controller = None
        self.olfactory_connected = False

    def trigger_scent_for_step(self, step):
        if not self.olfactory_mode:
            return
        obj = step.get("object")
        scent_number = stimulus_scent_number(obj)
        if scent_number is None:
            return
        try:
            scent_number = int(scent_number)
        except (TypeError, ValueError):
            print(f"Ignoring invalid scent number for {stimulus_label(obj)}: {scent_number}")
            return
        if not 1 <= scent_number <= 8:
            print(f"Ignoring out-of-range scent number for {stimulus_label(obj)}: {scent_number}")
            return
        if not self.ensure_olfactory_controller():
            print(f"Could not trigger scent {scent_number}: olfactory controller is not connected.")
            return
        if self.olfactory_controller.trigger_scent(scent_number):
            QTimer.singleShot(3000, lambda scent=scent_number: self.stop_scent_if_connected(scent))
            if self.send_message:
                bay = step.get("bay")
                label = (
                    f"Scent {scent_number} Dispensed"
                    f" | bay={bay}"
                    f" | object={stimulus_label(obj)}"
                )
                self.emit_turntable_label(label)

    def replacement_due_for_step(self, step):
        move_number = self.current_index + 1
        return (
            self._half_empty_mode
            and step.get("type") == "empty_control"
            and move_number > self.replacement_start_after_moves
        )

    def handle_control_step(self, step):
        if self.replacement_due_for_step(step):
            bay = step.get("bay")
            if self.manual_replacement_checkbox.isChecked():
                self._waiting_for_replacement = True
                self.replacement_continue_btn.setEnabled(True)
                self.sequence_status_label.setText(
                    f"Replacement pause at empty bay {bay}. Replace bottles, then click Continue."
                )
                return

            dwell_ms = self.replacement_dwell_box.value() * 1000
            self.sequence_status_label.setText(
                f"Replacement dwell at empty bay {bay} for {self.replacement_dwell_box.value()} seconds."
            )
            self._start_timer(dwell_ms, self.complete_current_step)
            return

        bay = step.get("bay")
        self.sequence_status_label.setText(f"Control dwell at bay {bay}.")
        self._start_timer(2000, self.complete_current_step)

    def continue_replacement_pause(self):
        if not self._waiting_for_replacement:
            return
        if self._paused:
            self.sequence_status_label.setText("Sequence is paused. Resume before continuing replacement.")
            return
        self._waiting_for_replacement = False
        self.replacement_continue_btn.setEnabled(False)
        self.sequence_status_label.setText("Replacement complete. Continuing sequence.")
        self.complete_current_step()

    def complete_current_step(self):
        if self._stopped or self._paused:
            return
        self.current_index += 1
        self._start_timer(1000, self.run_test_sequence)

    def run_test_sequence(self):
        # Only reset if stopped, not at end
        if self._stopped:
            self._stopped = False
            self._paused = False
            self.current_index = 0
            self._sequence_running = False

        if self._paused:
            print("Test paused.")
            return
        if not self._sequence_running:
            self.start_new_sequence()
            missing_scents = self.missing_scent_assignments_for_sequence()
            if missing_scents:
                preview = "\n".join(f"- {item}" for item in missing_scents[:12])
                extra = "" if len(missing_scents) <= 12 else f"\n...and {len(missing_scents) - 12} more"
                QMessageBox.critical(
                    self,
                    "Missing Scent Assignments",
                    "Every filled olfactory bay must have a scent number assigned before starting.\n\n"
                    f"Missing scent number for:\n{preview}{extra}",
                )
                self.sequence_status_label.setText("Cannot start: missing scent assignments.")
                self._sequence_running = False
                return
        if not self.sequence_steps:
            print("No assigned turntable sequence to run.")
            self.sequence_status_label.setText("No assigned turntable sequence to run.")
            self._sequence_running = False
            return
        if self.current_index >= len(self.sequence_steps):
            print("Test complete!")
            self.sequence_status_label.setText("Test complete.")
            self._sequence_running = False
            self._notify_sequence_stopped()
            return

        self._notify_sequence_started()
        self.emit_starting_bay_label_if_needed()

        step = self.sequence_steps[self.current_index]
        bay = step.get("bay")
        self._auto_doors_opened_for_current_item = False
        if step.get("type") != "stimulus":
            self._move_to_bay(step)
            self.handle_control_step(step)
            return

        if self.tactile_mode:
            print("Waiting for touch signal from tactile box...")
            self.waiting_for_touch = True
            if self.send_message:
                self.send_message({"action": "touchbox_lsl_true"})
            self.sequence_status_label.setText(
                f"Waiting for touch to reveal bay {bay}: {stimulus_label(step.get('object'))}"
            )
            return

        if self.olfactory_mode:
            self.trigger_scent_for_step(step)
            self._start_timer(
                SCENT_DISPENSE_DELAY_MS,
                lambda: self._move_to_bay_and_open_doors(step),
            )
            return

        self._move_to_bay_and_open_doors(step)

    @pyqtSlot()
    def on_object_touched(self):
        if self.tactile_mode and self.waiting_for_touch:
            print("Touch detected!")
            self.waiting_for_touch = False
            step = self.sequence_steps[self.current_index]
            if self.send_message:
                label = (
                    f"Turntable Touch Detected"
                    f" | bay={step.get('bay')}"
                    f" | object={stimulus_label(step.get('object'))}"
                )
                self.emit_turntable_label(label)
            if self.olfactory_mode:
                self.trigger_scent_for_step(step)
                self._start_timer(
                    SCENT_DISPENSE_DELAY_MS,
                    lambda: self._move_to_bay_and_open_doors(step),
                )
            else:
                self._move_to_bay_and_open_doors(step)

    def _move_to_bay(self, step):
        if self._stopped or self._paused:
            return

        bay = step.get("bay")
        obj = step.get("object")
        if step.get("type") == "stimulus":
            print(f"Moving to bay {bay} for object {stimulus_label(obj)}")
            self.sequence_status_label.setText(f"Moving to filled bay {bay}: {stimulus_label(obj)}")
        else:
            print(f"Moving to control bay {bay}")
            self.sequence_status_label.setText(f"Moving to control bay {bay}")

        try:
            move_success = self.controller.move_to_bay(bay_label_to_index(bay))
        except Exception as e:
            message = f"Could not move to bay {bay}: {e}"
            print(message)
            self.sequence_status_label.setText(message)
            QMessageBox.warning(self, "Turntable Movement Error", message)
            self._sequence_running = False
            self._notify_sequence_stopped()
            return

        self.update_position_indicators()
        if not move_success:
            message = f"Turntable move to bay {bay} timed out. Sequence stopped."
            print(message)
            self.sequence_status_label.setText(message)
            QMessageBox.warning(self, "Turntable Movement Timeout", message)
            self._sequence_running = False
            self._notify_sequence_stopped()
            return

        self.emit_bay_label(step)

    def _move_to_bay_and_open_doors(self, step):
        self._move_to_bay(step)
        if self._stopped or self._paused:
            return
        if self.auto_doors_enabled():
            self._auto_doors_opened_for_current_item = self.open_doors_automatically()
        self._start_timer(2000, self.close_doors_and_continue)

    def close_doors_and_continue(self):
        if self._stopped or self._paused:
            return
        if self._auto_doors_opened_for_current_item:
            self.close_doors_automatically()
            self._auto_doors_opened_for_current_item = False
        self.complete_current_step()

    def _open_doors_after_scent(self):
        """Open doors after scent has had SCENT_DISPENSE_DELAY_MS to dispense."""
        if self.auto_doors_enabled():
            self._auto_doors_opened_for_current_item = self.open_doors_automatically()
        self._start_timer(2000, self.close_doors_and_continue)

    def _start_timer(self, ms, callback):
        self._timer_callback_func = callback
        self._pending_timer.stop()
        self._pending_timer.setInterval(ms)
        self._pending_timer.start()

    def _timer_callback(self):
        if self._timer_callback_func:
            self._pending_timer.stop()
            self._timer_callback_func()

    def emit_turntable_label(self, label):
        if not self.send_message:
            return
        self.send_message({"action": "label", "label": label})
        self.send_message({"action": "client_log", "message": f"Current label: {label}"})
        logging.info(f"Turntable label emitted: {label}")

    def pause_test_sequence(self):
        print("Pausing test sequence.")
        self._paused = True
        self.update_position_indicators()

    def resume_test_sequence(self):
        if not self._paused:
            return
        print("Resuming test sequence.")
        self._paused = False
        self.update_position_indicators()
        # Resume immediately if not stopped and not at end
        if self._waiting_for_replacement:
            self.sequence_status_label.setText("Replacement pause active. Click Continue when ready.")
            return
        if not self._stopped and self._sequence_running and self.current_index < len(self.sequence_steps):
            self.run_test_sequence()

    def stop_test_sequence(self):
        print("Stopping test sequence.")
        self._stopped = True
        self._paused = False
        self.current_index = 0
        self.sequence_steps = []
        self._sequence_running = False
        self._waiting_for_replacement = False
        self.replacement_continue_btn.setEnabled(False)
        self.sequence_status_label.setText("Status: Stopped")
        self._pending_timer.stop()  # Immediately stop any pending timer
        self._notify_sequence_stopped()
        self.update_position_indicators()

    def _notify_sequence_started(self):
        if self._session_started:
            return
        self._session_started = True
        if self.on_sequence_started:
            self.on_sequence_started()

    def _notify_sequence_stopped(self):
        if not self._session_started:
            return
        self._session_started = False
        if self.on_sequence_stopped:
            self.on_sequence_stopped()
        self.close_olfactory_controller()

    def closeEvent(self, event):
        self.close_olfactory_controller()
        super().closeEvent(event)

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
