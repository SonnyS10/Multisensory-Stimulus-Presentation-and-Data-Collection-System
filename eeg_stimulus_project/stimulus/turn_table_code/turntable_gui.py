import os
import sys
import time
import threading
import math
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
)
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor
from PyQt5.QtCore import Qt, QPoint, QTimer, pyqtSignal

# Import with fallback for testing
try:
    from turntable_controller import TurntableController
    from doorcode import DoorController
except ImportError:
    # Mock classes for testing
    class TurntableController:
        def __init__(self):
            self.current_bay = 0
        def move_to_bay(self, bay, wait=True): pass
        def de_energize(self): pass
        def energize(self): pass
    
    class DoorController:
        def __init__(self): pass
        def open(self): pass
        def close(self): pass

from bay_mapping import bay_mapper

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
    # Signal to notify when turntable movement is complete
    movement_complete = pyqtSignal()
    test_complete = pyqtSignal()
    
    def __init__(self, auto_mode=False, bay_sequence=None):
        super().__init__()
        self.controller = TurntableController()
        self.door_controller = DoorController()
        self.setWindowTitle("Turntable GUI")
        
        # Auto mode properties
        self.auto_mode = auto_mode
        self.bay_sequence = bay_sequence or []
        self.current_sequence_index = 0
        self.auto_timer = QTimer()
        self.auto_timer.timeout.connect(self.advance_to_next_bay)
        
        # Status tracking
        self.is_running = False
        self.is_paused = False
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface."""
        # Top bar with controls
        top_bar = QHBoxLayout()
        
        # Manual controls
        self.open_btn = QPushButton("Open")
        self.close_btn = QPushButton("Close")
        self.de_energize_btn = QPushButton("De-energize")
        self.energize_btn = QPushButton("Energize")
        
        self.open_btn.clicked.connect(self.door_controller.open)
        self.close_btn.clicked.connect(self.door_controller.close)
        self.de_energize_btn.clicked.connect(self.controller.de_energize)
        self.energize_btn.clicked.connect(self.controller.energize)
        
        top_bar.addWidget(self.open_btn)
        top_bar.addWidget(self.close_btn)
        top_bar.addWidget(self.de_energize_btn)
        top_bar.addWidget(self.energize_btn)
        
        # Auto mode controls
        if self.auto_mode:
            self.start_auto_btn = QPushButton("Start Auto Test")
            self.pause_auto_btn = QPushButton("Pause")
            self.resume_auto_btn = QPushButton("Resume")
            self.stop_auto_btn = QPushButton("Stop Test")
            
            self.start_auto_btn.clicked.connect(self.start_auto_test)
            self.pause_auto_btn.clicked.connect(self.pause_auto_test)
            self.resume_auto_btn.clicked.connect(self.resume_auto_test)
            self.stop_auto_btn.clicked.connect(self.stop_auto_test)
            
            # Initially disable pause/resume buttons
            self.pause_auto_btn.setEnabled(False)
            self.resume_auto_btn.setEnabled(False)
            
            top_bar.addWidget(QLabel("|"))  # Separator
            top_bar.addWidget(self.start_auto_btn)
            top_bar.addWidget(self.pause_auto_btn)
            top_bar.addWidget(self.resume_auto_btn)
            top_bar.addWidget(self.stop_auto_btn)
        
        top_bar.addStretch()
        
        # Status display
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-weight: bold; padding: 5px;")
        top_bar.addWidget(self.status_label)
        
        # Centered turntable
        self.turntable = TurntableWidget(self, controller=self.controller)
        self.turntable.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(top_bar)
        main_layout.addWidget(self.turntable, alignment=Qt.AlignCenter)
        self.setLayout(main_layout)
        self.resize(650, 700)
    
    def set_bay_sequence(self, bay_sequence):
        """Set the sequence of bays for automatic mode."""
        self.bay_sequence = bay_sequence
        self.current_sequence_index = 0
        
    def start_auto_test(self):
        """Start the automatic test sequence."""
        if not self.bay_sequence:
            self.status_label.setText("No bay sequence set")
            return
            
        self.is_running = True
        self.is_paused = False
        self.current_sequence_index = 0
        
        # Update button states
        self.start_auto_btn.setEnabled(False)
        self.pause_auto_btn.setEnabled(True)
        self.resume_auto_btn.setEnabled(False)
        
        self.status_label.setText("Starting automatic test...")
        
        # Start with first bay
        self.move_to_bay_with_doors(self.bay_sequence[0])
        
    def pause_auto_test(self):
        """Pause the automatic test."""
        self.is_paused = True
        self.auto_timer.stop()
        
        # Update button states
        self.pause_auto_btn.setEnabled(False)
        self.resume_auto_btn.setEnabled(True)
        
        self.status_label.setText("Test paused")
        
    def resume_auto_test(self):
        """Resume the automatic test."""
        if not self.is_running:
            return
            
        self.is_paused = False
        
        # Update button states
        self.pause_auto_btn.setEnabled(True)
        self.resume_auto_btn.setEnabled(False)
        
        self.status_label.setText("Test resumed")
        
        # Continue with next bay or current sequence
        if self.current_sequence_index < len(self.bay_sequence):
            current_bay = self.bay_sequence[self.current_sequence_index]
            self.move_to_bay_with_doors(current_bay)
        
    def stop_auto_test(self):
        """Stop the automatic test."""
        self.is_running = False
        self.is_paused = False
        self.auto_timer.stop()
        
        # Update button states
        self.start_auto_btn.setEnabled(True)
        self.pause_auto_btn.setEnabled(False)
        self.resume_auto_btn.setEnabled(False)
        
        self.status_label.setText("Test stopped")
        self.test_complete.emit()
        
    def move_to_bay_with_doors(self, bay_number):
        """Move to a bay and automatically handle doors."""
        if not self.is_running or self.is_paused:
            return
            
        self.status_label.setText(f"Moving to bay {bay_number + 1}...")
        
        # Run in separate thread to avoid blocking UI
        def move_and_doors():
            try:
                # Move to the bay
                self.controller.move_to_bay(bay_number, wait=True)
                
                if not self.is_running or self.is_paused:
                    return
                    
                # Open doors
                QTimer.singleShot(0, lambda: self.status_label.setText(f"Opening doors at bay {bay_number + 1}"))
                self.door_controller.open()
                
                # Wait 2 seconds
                time.sleep(2)
                
                if not self.is_running or self.is_paused:
                    return
                    
                # Close doors
                QTimer.singleShot(0, lambda: self.status_label.setText(f"Closing doors at bay {bay_number + 1}"))
                self.door_controller.close()
                
                # Signal completion
                QTimer.singleShot(0, self.on_bay_movement_complete)
                
            except Exception as e:
                QTimer.singleShot(0, lambda: self.status_label.setText(f"Error: {str(e)}"))
                
        # Start movement in separate thread
        threading.Thread(target=move_and_doors, daemon=True).start()
        
    def on_bay_movement_complete(self):
        """Handle completion of bay movement and door cycle."""
        if not self.is_running or self.is_paused:
            return
            
        self.current_sequence_index += 1
        
        if self.current_sequence_index >= len(self.bay_sequence):
            # Test complete
            self.status_label.setText("Test complete!")
            self.stop_auto_test()
        else:
            # Wait before next movement (can be adjusted)
            self.status_label.setText("Waiting for next movement...")
            self.auto_timer.start(1000)  # 1 second delay
            
    def advance_to_next_bay(self):
        """Advance to the next bay in the sequence."""
        self.auto_timer.stop()
        
        if not self.is_running or self.is_paused:
            return
            
        if self.current_sequence_index < len(self.bay_sequence):
            next_bay = self.bay_sequence[self.current_sequence_index]
            self.move_to_bay_with_doors(next_bay)
        else:
            self.stop_auto_test()
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self.is_running:
            self.stop_auto_test()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TurntableWindow()
    window.show()
    sys.exit(app.exec_())