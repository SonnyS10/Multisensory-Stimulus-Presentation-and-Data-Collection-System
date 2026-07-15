from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox,
    QComboBox, QGroupBox, QGridLayout, QDoubleSpinBox, QCheckBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer


class OlfactoryTestFrame(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.olfactory_controller = None
        self.active_timers = {}
        
        self.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border-radius: 10px;
            }
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        # Title
        title = QLabel("Olfactory System Test")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(title)

        # Scent Selection
        scent_layout = QHBoxLayout()
        scent_label = QLabel("Scent Number:")
        scent_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.scent_spinbox = QSpinBox()
        self.scent_spinbox.setRange(1, 8)
        self.scent_spinbox.setValue(1)
        self.scent_spinbox.setMinimumWidth(60)
        scent_layout.addWidget(scent_label)
        scent_layout.addWidget(self.scent_spinbox)
        scent_layout.addStretch()
        self.layout.addLayout(scent_layout)

        # Test Mode Selection
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Test Mode:")
        mode_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Combined (o#)", "Individual Components"])
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        self.layout.addLayout(mode_layout)

        # Combined Mode Controls
        self.combined_group = QGroupBox("Combined Mode (o#)")
        self.combined_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        combined_layout = QVBoxLayout()

        combined_button_layout = QHBoxLayout()
        self.combined_test_btn = QPushButton("Trigger Scent")
        self.combined_test_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.combined_test_btn.clicked.connect(self.trigger_combined)
        combined_button_layout.addWidget(self.combined_test_btn)

        self.combined_stop_btn = QPushButton("Stop")
        self.combined_stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border-radius: 5px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.combined_stop_btn.clicked.connect(self.stop_scent)
        combined_button_layout.addWidget(self.combined_stop_btn)
        combined_button_layout.addStretch()

        combined_layout.addLayout(combined_button_layout)
        self.combined_group.setLayout(combined_layout)
        self.layout.addWidget(self.combined_group)

        # Individual Components Mode
        self.individual_group = QGroupBox("Individual Components")
        self.individual_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.individual_group.setVisible(False)
        individual_layout = QGridLayout()
        individual_layout.setSpacing(15)

        components = [
            ("Humidifier (h#)", "humidifier"),
            ("Pump (p#)", "pump"),
            ("Solenoid (s#)", "solenoid")
        ]

        self.component_controls = {}

        for row, (label_text, component_name) in enumerate(components):
            # Label
            label = QLabel(label_text)
            label.setFont(QFont("Segoe UI", 10, QFont.Bold))
            individual_layout.addWidget(label, row, 0)

            # Duration spinbox
            duration_label = QLabel("Duration (s):")
            duration_label.setFont(QFont("Segoe UI", 9))
            individual_layout.addWidget(duration_label, row, 1)

            duration_spinbox = QDoubleSpinBox()
            duration_spinbox.setRange(0.1, 10.0)
            duration_spinbox.setValue(1.0)
            duration_spinbox.setSingleStep(0.1)
            duration_spinbox.setMinimumWidth(80)
            individual_layout.addWidget(duration_spinbox, row, 2)

            # Test button
            test_btn = QPushButton("Test")
            test_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border-radius: 5px;
                    padding: 5px 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #0b7dda;
                }
            """)
            component_name_copy = component_name
            test_btn.clicked.connect(lambda checked, comp=component_name_copy: self.trigger_individual(comp))
            individual_layout.addWidget(test_btn, row, 3)

            # Stop button
            stop_btn = QPushButton("Stop")
            stop_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border-radius: 5px;
                    padding: 5px 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #da190b;
                }
            """)
            stop_btn.clicked.connect(lambda checked, comp=component_name_copy: self.stop_component(comp))
            individual_layout.addWidget(stop_btn, row, 4)

            self.component_controls[component_name] = {
                'duration': duration_spinbox,
                'test_btn': test_btn,
                'stop_btn': stop_btn
            }

        individual_layout.setColumnStretch(5, 1)
        self.individual_group.setLayout(individual_layout)
        self.layout.addWidget(self.individual_group)

        # Status area
        status_layout = QVBoxLayout()
        status_label = QLabel("Status:")
        status_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        status_layout.addWidget(status_label)

        self.status_text = QLabel("Ready")
        self.status_text.setFont(QFont("Segoe UI", 10))
        self.status_text.setStyleSheet("color: #4CAF50; padding: 5px;")
        status_layout.addWidget(self.status_text)

        self.layout.addLayout(status_layout)
        self.layout.addStretch()

        # Back button
        back_btn = QPushButton("Back")
        back_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border-radius: 5px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        back_btn.clicked.connect(self.go_back)
        self.layout.addWidget(back_btn)

    def set_olfactory_controller(self, controller):
        """Set the olfactory controller instance"""
        self.olfactory_controller = controller

    def on_mode_changed(self, text):
        """Toggle visibility of mode-specific controls"""
        if text == "Combined (o#)":
            self.combined_group.setVisible(True)
            self.individual_group.setVisible(False)
        else:
            self.combined_group.setVisible(False)
            self.individual_group.setVisible(True)

    def update_status(self, message):
        """Update status text"""
        self.status_text.setText(message)

    def trigger_combined(self):
        """Trigger combined scent command"""
        if not self.olfactory_controller:
            self.update_status("Error: Olfactory controller not available")
            return

        scent_num = self.scent_spinbox.value()
        success = self.olfactory_controller.trigger_scent(scent_num)
        if success:
            self.update_status(f"Triggered combined scent {scent_num}")
        else:
            self.update_status(f"Failed to trigger scent {scent_num}")

    def trigger_individual(self, component):
        """Trigger individual component"""
        if not self.olfactory_controller:
            self.update_status("Error: Olfactory controller not available")
            return

        scent_num = self.scent_spinbox.value()
        duration_sec = self.component_controls[component]['duration'].value()
        duration_ms = int(duration_sec * 1000)

        if component == "humidifier":
            success = self.olfactory_controller.trigger_humidifier(scent_num, duration_ms)
            status_msg = f"Humidifier (h{scent_num}) triggered for {duration_sec}s"
        elif component == "pump":
            success = self.olfactory_controller.trigger_pump(scent_num, duration_ms)
            status_msg = f"Pump (p{scent_num}) triggered for {duration_sec}s"
        elif component == "solenoid":
            success = self.olfactory_controller.trigger_solenoid(scent_num, duration_ms)
            status_msg = f"Solenoid (s{scent_num}) triggered for {duration_sec}s"
        else:
            success = False
            status_msg = f"Unknown component: {component}"

        if success:
            self.update_status(status_msg)
            # Set a timer to stop the component after duration
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self.stop_component(component))
            timer.start(duration_ms)
            self.active_timers[component] = timer
        else:
            self.update_status(f"Failed to trigger {component}")

    def stop_component(self, component):
        """Stop a specific component"""
        if not self.olfactory_controller:
            return

        scent_num = self.scent_spinbox.value()
        self.olfactory_controller.stop_scent(scent_num)
        
        # Kill the timer if it exists
        if component in self.active_timers:
            self.active_timers[component].stop()
            del self.active_timers[component]

        self.update_status(f"{component.title()} stopped")

    def stop_scent(self):
        """Stop all scents"""
        if not self.olfactory_controller:
            return

        scent_num = self.scent_spinbox.value()
        self.olfactory_controller.stop_scent(scent_num)
        
        # Stop all active timers
        for timer in self.active_timers.values():
            timer.stop()
        self.active_timers.clear()

        self.update_status("All components stopped")

    def go_back(self):
        """Go back to the previous frame"""
        if hasattr(self.parent, 'toggle_olfactory_test'):
            self.parent.toggle_olfactory_test()
