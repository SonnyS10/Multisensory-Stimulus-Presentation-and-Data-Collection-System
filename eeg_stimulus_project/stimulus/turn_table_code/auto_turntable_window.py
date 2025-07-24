"""
Automatic Turntable Display Window

This module provides an automatic turntable controller that integrates with the main GUI
system, similar to how display_window.py works but for physical turntable operations.
"""

import os
import sys
import time
import threading
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import with fallback for testing
try:
    from eeg_stimulus_project.stimulus.turn_table_code.turntable_gui import TurntableWindow
except ImportError:
    # Mock class for testing
    class TurntableWindow:
        def __init__(self, auto_mode=False, bay_sequence=None):
            self.auto_mode = auto_mode
            self.bay_sequence = bay_sequence or []
        def start_auto_test(self): pass
        def pause_auto_test(self): pass
        def resume_auto_test(self): pass
        def stop_auto_test(self): pass

from eeg_stimulus_project.stimulus.turn_table_code.bay_mapping import bay_mapper
try:
    from eeg_stimulus_project.gui.stimulus_order_frame import CravingRatingAsset
except ImportError:
    # Mock class for testing
    class CravingRatingAsset:
        def __init__(self):
            self.asset_type = 'craving_rating'


class AutoTurntableWindow(QMainWindow):
    """
    Automatic turntable window that follows stimulus presentation order.
    Similar to DisplayWindow but controls physical turntable instead of showing images.
    """
    
    experiment_started = pyqtSignal()
    test_complete = pyqtSignal()
    
    def __init__(self, connection, log_queue, label_stream, parent_frame, current_test, 
                 base_dir, test_number, eyetracker=None, shared_status=None, client=False, 
                 alcohol_folder=None, non_alcohol_folder=None, randomize_cues=False, 
                 seed=None, repetitions=None, local_mode=None):
        super().__init__()
        
        # Store parameters similar to DisplayWindow
        self.shared_status = shared_status if shared_status else {}
        self.connection = connection
        self.client = client
        self.current_test = current_test
        self.base_dir = base_dir
        self.test_number = test_number
        self.frame = parent_frame
        
        # Get stimulus assets
        from eeg_stimulus_project.assets.asset_handler import Display
        self.images = Display.get_assets(
            alcohol_folder=alcohol_folder,
            non_alcohol_folder=non_alcohol_folder,
            randomize_cues=randomize_cues,
            seed=seed,
            repetitions=repetitions
        ).get(current_test, [])
        
        # Generate bay sequence from assets
        self.bay_sequence = bay_mapper.get_bay_sequence_for_assets(self.images)
        
        # State tracking
        self.current_image_index = 0
        self.stopped = False
        self.paused = False
        self.waiting_for_next = False
        
        # Setup window
        self.setWindowTitle("Automatic Turntable Control")
        self.setGeometry(200, 200, 800, 600)
        
        # Create central widget with status display
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Status display
        self.status_label = QLabel("Turntable Control Ready")
        self.status_label.setFont(QFont("Arial", 18, QFont.Bold))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("padding: 20px; background-color: #f0f0f0; border: 2px solid #ccc;")
        layout.addWidget(self.status_label)
        
        # Create turntable window with auto mode
        self.turntable_window = TurntableWindow(auto_mode=True, bay_sequence=self.bay_sequence)
        self.turntable_window.test_complete.connect(self.on_test_complete)
        
        # Add turntable widget to layout
        layout.addWidget(self.turntable_window)
        
        # Timers for coordination
        self.start_timer = QTimer()
        self.start_timer.setSingleShot(True)
        self.start_timer.timeout.connect(self.begin_experiment)
        
        # Show window
        self.show()
        
        # Start with instructions
        self.show_instructions()
        
    def show_instructions(self):
        """Show initial instructions."""
        self.status_label.setText(
            f"Turntable Test: {self.current_test}\n\n"
            f"Ready to present {len(self.bay_sequence)} objects\n"
            f"Bay sequence: {[b+1 for b in self.bay_sequence]}\n\n"
            "Press SPACE to begin"
        )
        
    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key_Space and not self.stopped:
            self.start_countdown()
        else:
            super().keyPressEvent(event)
            
    def start_countdown(self):
        """Start countdown before beginning experiment."""
        self.status_label.setText("Starting in 3...")
        QTimer.singleShot(1000, lambda: self.status_label.setText("Starting in 2..."))
        QTimer.singleShot(2000, lambda: self.status_label.setText("Starting in 1..."))
        QTimer.singleShot(3000, lambda: self.status_label.setText("Starting experiment!"))
        QTimer.singleShot(4000, self.begin_experiment)
        
    def begin_experiment(self):
        """Begin the automatic turntable experiment."""
        if self.stopped:
            return
            
        self.status_label.setText("Experiment started - Turntable moving automatically")
        self.experiment_started.emit()
        
        # Start the automatic test
        self.turntable_window.start_auto_test()
        
    def pause_trial(self):
        """Pause the turntable experiment."""
        self.paused = True
        self.turntable_window.pause_auto_test()
        self.status_label.setText("Experiment paused")
        
    def resume_trial(self):
        """Resume the turntable experiment."""
        self.paused = False
        self.turntable_window.resume_auto_test()
        self.status_label.setText("Experiment resumed")
        
    @pyqtSlot()
    def proceed_from_next_button(self):
        """Handle next button press (for tactile tests)."""
        if self.waiting_for_next:
            self.waiting_for_next = False
            if hasattr(self.frame, 'next_button'):
                self.frame.next_button.setEnabled(False)
            # Continue with turntable sequence
            self.turntable_window.resume_auto_test()
    
    def on_test_complete(self):
        """Handle completion of turntable test."""
        self.status_label.setText("Turntable test complete!")
        self.test_complete.emit()
        
    def closeEvent(self, event):
        """Handle window close event."""
        if not self.stopped:
            self.stopped = True
            if hasattr(self, 'turntable_window'):
                self.turntable_window.stop_auto_test()
        event.accept()