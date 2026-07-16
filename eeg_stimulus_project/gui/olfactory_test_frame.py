from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox,
    QComboBox, QGroupBox, QGridLayout, QDoubleSpinBox, QCheckBox, QMessageBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer
import logging


class OlfactoryTestFrame(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.olfactory_controller = None
        self.active_timers = {}
        self.sequential_timers = {}
        self.sequential_running = False
        
        self.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border-radius: 10px;
            }
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)

        # Title
        title = QLabel("Olfactory System Test")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(title)

        # Scent Selection
        scent_layout = QHBoxLayout()
        scent_label = QLabel("Scent Number:")
        scent_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.scent_spinbox = QSpinBox()
        self.scent_spinbox.setRange(1, 8)
        self.scent_spinbox.setValue(1)
        self.scent_spinbox.setMinimumWidth(100)
        self.scent_spinbox.setFont(QFont("Segoe UI", 12))
        self.scent_spinbox.setMinimumHeight(40)
        scent_layout.addWidget(scent_label)
        scent_layout.addWidget(self.scent_spinbox)
        scent_layout.addStretch()
        self.layout.addLayout(scent_layout)

        # Test Mode Selection
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Test Mode:")
        mode_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Combined (o#)", "Individual Components"])
        self.mode_combo.setFont(QFont("Segoe UI", 12))
        self.mode_combo.setMinimumHeight(40)
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        self.layout.addLayout(mode_layout)

        # Combined Mode Controls
        self.combined_group = QGroupBox("Combined Mode (o#)")
        self.combined_group.setFont(QFont("Segoe UI", 12, QFont.Bold))
        combined_layout = QVBoxLayout()

        combined_button_layout = QHBoxLayout()
        self.combined_test_btn = QPushButton("Trigger Scent")
        self.combined_test_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.combined_test_btn.setMinimumHeight(50)
        self.combined_test_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                padding: 10px 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.combined_test_btn.clicked.connect(self.trigger_combined)
        combined_button_layout.addWidget(self.combined_test_btn)

        self.combined_stop_btn = QPushButton("Stop")
        self.combined_stop_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.combined_stop_btn.setMinimumHeight(50)
        self.combined_stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border-radius: 5px;
                padding: 10px 30px;
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
        self.individual_group.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.individual_group.setVisible(False)
        individual_layout = QGridLayout()
        individual_layout.setSpacing(20)

        components = [
            ("Humidifier (h#)", "humidifier"),
            ("Pump (p#)", "pump"),
            ("Solenoid (s#)", "solenoid")
        ]

        self.component_controls = {}

        for row, (label_text, component_name) in enumerate(components):
            # Label
            label = QLabel(label_text)
            label.setFont(QFont("Segoe UI", 12, QFont.Bold))
            individual_layout.addWidget(label, row, 0)

            # Duration spinbox
            duration_label = QLabel("Duration (s):")
            duration_label.setFont(QFont("Segoe UI", 11))
            individual_layout.addWidget(duration_label, row, 1)

            duration_spinbox = QDoubleSpinBox()
            duration_spinbox.setRange(0.1, 10.0)
            duration_spinbox.setValue(1.0)
            duration_spinbox.setSingleStep(0.1)
            duration_spinbox.setMinimumWidth(120)
            duration_spinbox.setFont(QFont("Segoe UI", 11))
            duration_spinbox.setMinimumHeight(40)
            individual_layout.addWidget(duration_spinbox, row, 2)

            # Test button
            test_btn = QPushButton("Test")
            test_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
            test_btn.setMinimumHeight(40)
            test_btn.setMinimumWidth(80)
            test_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border-radius: 5px;
                    padding: 8px 20px;
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
            stop_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
            stop_btn.setMinimumHeight(40)
            stop_btn.setMinimumWidth(80)
            stop_btn.setStyleSheet("""
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
            stop_btn.clicked.connect(lambda checked, comp=component_name_copy: self.stop_component(comp))
            individual_layout.addWidget(stop_btn, row, 4)

            self.component_controls[component_name] = {
                'duration': duration_spinbox,
                'test_btn': test_btn,
                'stop_btn': stop_btn
            }

        individual_layout.setColumnStretch(5, 1)

        # Add delay controls section
        delay_section_label = QLabel("\nDelays Between Components (seconds):")
        delay_section_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        individual_layout.addWidget(delay_section_label, 3, 0, 1, 6)

        # Delay after Humidifier (before Pump)
        delay1_label = QLabel("Delay after Humidifier:")
        delay1_label.setFont(QFont("Segoe UI", 11))
        individual_layout.addWidget(delay1_label, 4, 0)

        self.delay_after_humidifier = QDoubleSpinBox()
        self.delay_after_humidifier.setRange(0.0, 10.0)
        self.delay_after_humidifier.setValue(0.0)
        self.delay_after_humidifier.setSingleStep(0.1)
        self.delay_after_humidifier.setFont(QFont("Segoe UI", 11))
        self.delay_after_humidifier.setMinimumHeight(40)
        self.delay_after_humidifier.setMinimumWidth(120)
        individual_layout.addWidget(self.delay_after_humidifier, 4, 1)

        # Delay after Pump (before Solenoid)
        delay2_label = QLabel("Delay after Pump:")
        delay2_label.setFont(QFont("Segoe UI", 11))
        individual_layout.addWidget(delay2_label, 5, 0)

        self.delay_after_pump = QDoubleSpinBox()
        self.delay_after_pump.setRange(0.0, 10.0)
        self.delay_after_pump.setValue(0.0)
        self.delay_after_pump.setSingleStep(0.1)
        self.delay_after_pump.setFont(QFont("Segoe UI", 11))
        self.delay_after_pump.setMinimumHeight(40)
        self.delay_after_pump.setMinimumWidth(120)
        individual_layout.addWidget(self.delay_after_pump, 5, 1)

        # Sequential trigger buttons
        seq_button_layout = QHBoxLayout()
        self.sequential_start_btn = QPushButton("Start Sequential")
        self.sequential_start_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.sequential_start_btn.setMinimumHeight(40)
        self.sequential_start_btn.setMinimumWidth(100)
        self.sequential_start_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border-radius: 5px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        self.sequential_start_btn.clicked.connect(self.start_sequential_trigger)
        seq_button_layout.addWidget(self.sequential_start_btn)

        self.sequential_stop_btn = QPushButton("Stop Sequential")
        self.sequential_stop_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.sequential_stop_btn.setMinimumHeight(40)
        self.sequential_stop_btn.setMinimumWidth(100)
        self.sequential_stop_btn.setStyleSheet("""
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
        self.sequential_stop_btn.clicked.connect(lambda checked: self.stop_sequential_trigger())
        seq_button_layout.addWidget(self.sequential_stop_btn)
        seq_button_layout.addStretch()

        individual_layout.addLayout(seq_button_layout, 6, 0, 1, 6)

        self.individual_group.setLayout(individual_layout)
        self.layout.addWidget(self.individual_group)

        # Status area
        status_layout = QVBoxLayout()
        status_label = QLabel("Status:")
        status_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        status_layout.addWidget(status_label)

        self.status_text = QLabel("Ready")
        self.status_text.setFont(QFont("Segoe UI", 12))
        self.status_text.setStyleSheet("color: #4CAF50; padding: 10px; background-color: #e8f5e9; border-radius: 5px;")
        self.status_text.setMinimumHeight(50)
        status_layout.addWidget(self.status_text)

        self.layout.addLayout(status_layout)
        self.layout.addStretch()

        # Back button
        back_btn = QPushButton("Back")
        back_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        back_btn.setMinimumHeight(50)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border-radius: 5px;
                padding: 10px 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        back_btn.clicked.connect(self.go_back)
        self.layout.addWidget(back_btn)

    def _stop_all_timers(self):
        """Stop any active component or sequential timers."""
        for timer in list(self.active_timers.values()):
            timer.stop()
        self.active_timers.clear()

        for timer in list(self.sequential_timers.values()):
            timer.stop()
        self.sequential_timers.clear()

    def _release_controller(self):
        """Stop any active activity and close the olfactory controller connection."""
        self._stop_all_timers()
        self.sequential_running = False
        if self.sequential_start_btn is not None:
            self.sequential_start_btn.setEnabled(True)

        controller = self.olfactory_controller
        self.olfactory_controller = None
        if controller is not None:
            try:
                controller.close()
            except Exception as e:
                logging.error(f"Error closing olfactory controller: {e}")

        self.update_status("Ready")

    def set_olfactory_controller(self, controller):
        """Set the olfactory controller instance, or initialize one if not provided"""
        if controller:
            self.olfactory_controller = controller
        else:
            # Try to create a new controller if one wasn't provided
            try:
                from eeg_stimulus_project.stimulus.olfactory.olfactory_controller import OlfactoryController
                self.olfactory_controller = OlfactoryController()
                logging.info("Olfactory controller initialized")
            except Exception as e:
                logging.error(f"Failed to initialize olfactory controller: {e}")
                self.olfactory_controller = None

    def on_mode_changed(self, text):
        """Toggle visibility of mode-specific controls"""
        if text == "Combined (o#)":
            self.combined_group.setVisible(True)
            self.individual_group.setVisible(False)
        else:  # Individual Components
            self.combined_group.setVisible(False)
            self.individual_group.setVisible(True)

    def update_status(self, message):
        """Update status text"""
        self.status_text.setText(message)

    def trigger_combined(self):
        """Trigger combined scent command"""
        if not self._ensure_controller():
            return

        scent_num = self.scent_spinbox.value()
        try:
            # Ensure connection is established
            if not self.olfactory_controller.ser1 or not self.olfactory_controller.ser1.is_open:
                if not self.olfactory_controller.connect():
                    self.update_status("Error: Failed to connect to olfactory hardware")
                    return
            
            success = self.olfactory_controller.trigger_scent(scent_num)
            if success:
                self.update_status(f"✓ Triggered combined scent {scent_num}")
            else:
                self.update_status(f"✗ Failed to trigger scent {scent_num}")
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
            logging.error(f"Error triggering combined scent: {e}")

    def _ensure_controller(self):
        """Ensure the olfactory controller is available, initialize if needed"""
        if not self.olfactory_controller:
            try:
                from eeg_stimulus_project.stimulus.olfactory.olfactory_controller import OlfactoryController
                self.olfactory_controller = OlfactoryController()
                logging.info("Olfactory controller initialized on-demand")
            except Exception as e:
                self.update_status(f"Error: Could not initialize olfactory controller: {str(e)}")
                logging.error(f"Failed to initialize olfactory controller: {e}")
                return False
        return True

    def trigger_individual(self, component):
        """Trigger individual component"""
        if not self._ensure_controller():
            return

        scent_num = self.scent_spinbox.value()
        duration_sec = self.component_controls[component]['duration'].value()
        duration_ms = int(duration_sec * 1000)

        try:
            # Ensure connection is established
            if not self.olfactory_controller.ser1 or not self.olfactory_controller.ser1.is_open:
                if not self.olfactory_controller.connect():
                    self.update_status("Error: Failed to connect to olfactory hardware")
                    return
            
            if component == "humidifier":
                success = self.olfactory_controller.trigger_humidifier(scent_num, duration_ms)
                status_msg = f"✓ Humidifier (h{scent_num}) triggered for {duration_sec}s"
            elif component == "pump":
                success = self.olfactory_controller.trigger_pump(scent_num, duration_ms)
                status_msg = f"✓ Pump (p{scent_num}) triggered for {duration_sec}s"
            elif component == "solenoid":
                success = self.olfactory_controller.trigger_solenoid(scent_num, duration_ms)
                status_msg = f"✓ Solenoid (s{scent_num}) triggered for {duration_sec}s"
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
                self.update_status(f"✗ Failed to trigger {component}")
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
            logging.error(f"Error triggering {component}: {e}")

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
        self.stop_sequential_trigger(update_status=False)
        
        # Stop all active timers
        for timer in self.active_timers.values():
            timer.stop()
        self.active_timers.clear()

        self.update_status("All components stopped")

    def start_sequential_trigger(self):
        """Start triggering components sequentially: Humidifier -> Pump -> Solenoid"""
        if not self._ensure_controller():
            return

        scent_num = self.scent_spinbox.value()
        
        try:
            # Ensure connection is established
            if not self.olfactory_controller.ser1 or not self.olfactory_controller.ser1.is_open:
                if not self.olfactory_controller.connect():
                    self.update_status("Error: Failed to connect to olfactory hardware")
                    return
            
            self.stop_sequential_trigger(update_status=False)
            self.sequential_running = True
            self.sequential_start_btn.setEnabled(False)
            
            sequence = [
                ("humidifier", int(self.component_controls['humidifier']['duration'].value() * 1000), int(self.delay_after_humidifier.value() * 1000)),
                ("pump", int(self.component_controls['pump']['duration'].value() * 1000), int(self.delay_after_pump.value() * 1000)),
                ("solenoid", int(self.component_controls['solenoid']['duration'].value() * 1000), 0),
            ]
            
            self._run_sequential_step(scent_num, sequence, 0)
            
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
            self.sequential_running = False
            self.sequential_start_btn.setEnabled(True)
            logging.error(f"Error starting sequential trigger: {e}")

    def _run_sequential_step(self, scent_num, sequence, index):
        """Trigger one component, then schedule its stop before the next component."""
        if not self.sequential_running:
            return
        if index >= len(sequence):
            self._finish_sequential_trigger()
            return

        component, duration_ms, delay_after_ms = sequence[index]
        try:
            if component == "humidifier":
                success = self.olfactory_controller.trigger_humidifier(scent_num)
            elif component == "pump":
                success = self.olfactory_controller.trigger_pump(scent_num)
            elif component == "solenoid":
                success = self.olfactory_controller.trigger_solenoid(scent_num)
            else:
                success = False

            if not success:
                self.update_status(f"✗ Failed to trigger {component}")
                self.stop_sequential_trigger(update_status=False)
                return

            duration_sec = self.component_controls[component]['duration'].value()
            self.update_status(f"▶ {component.title()} triggered ({duration_sec}s)")

            stop_timer = QTimer()
            stop_timer.setSingleShot(True)
            stop_timer.timeout.connect(lambda: self._stop_sequential_step(scent_num, sequence, index, delay_after_ms))
            stop_timer.start(duration_ms)
            self.sequential_timers[f"{component}_stop"] = stop_timer
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
            self.stop_sequential_trigger(update_status=False)
            logging.error(f"Error triggering {component} in sequence: {e}")

    def _stop_sequential_step(self, scent_num, sequence, index, delay_after_ms):
        """Stop the current component, then continue after its configured delay."""
        if not self.sequential_running:
            return

        component = sequence[index][0]
        self.sequential_timers.pop(f"{component}_stop", None)
        self.olfactory_controller.stop_scent(scent_num)

        next_index = index + 1
        if next_index >= len(sequence):
            self._finish_sequential_trigger()
            return

        if delay_after_ms > 0:
            delay_timer = QTimer()
            delay_timer.setSingleShot(True)
            delay_timer.timeout.connect(lambda: self._run_sequential_step(scent_num, sequence, next_index))
            delay_timer.start(delay_after_ms)
            self.sequential_timers[f"{component}_delay"] = delay_timer
            self.update_status(f"✓ {component.title()} stopped; waiting {delay_after_ms / 1000:g}s")
        else:
            self._run_sequential_step(scent_num, sequence, next_index)

    def _finish_sequential_trigger(self):
        """Mark a naturally completed sequence as finished."""
        self.sequential_running = False
        self.sequential_timers.clear()
        self.sequential_start_btn.setEnabled(True)
        self.update_status("✓ Sequence completed")

    def stop_sequential_trigger(self, update_status=True):
        """Stop all sequential timers and components"""
        if not self.olfactory_controller:
            return

        scent_num = self.scent_spinbox.value()
        
        # Stop all sequential timers
        for timer in self.sequential_timers.values():
            timer.stop()
        self.sequential_timers.clear()
        
        # Stop the scent
        self.olfactory_controller.stop_scent(scent_num)
        
        # Re-enable the start button
        self.sequential_running = False
        self.sequential_start_btn.setEnabled(True)
        
        if update_status:
            self.update_status("Sequence stopped")

    def hideEvent(self, event):
        """Ensure the olfactory controller is released when the frame is hidden."""
        self._release_controller()
        super().hideEvent(event)

    def closeEvent(self, event):
        """Ensure the olfactory controller is released when the frame is closed."""
        self._release_controller()
        super().closeEvent(event)

    def go_back(self):
        """Go back to the previous frame"""
        self._release_controller()
        if hasattr(self.parent, 'toggle_olfactory_test'):
            self.parent.toggle_olfactory_test()
