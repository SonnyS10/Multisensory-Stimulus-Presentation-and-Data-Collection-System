from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox,
    QComboBox, QGroupBox, QGridLayout, QDoubleSpinBox, QCheckBox, QMessageBox,
    QTabWidget, QWidget
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer
import logging

from eeg_stimulus_project.stimulus.olfactory.olfactory_timing import (
    get_olfactory_timing_settings,
    MODE_COMBINED,
    MODE_INDIVIDUAL,
    DEFAULT_COMBINED_DURATION_MS,
    DEFAULT_SCENT_DISPENSE_DELAY_MS,
)


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

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.layout.addWidget(self.tabs)

        self.tabs.addTab(self._build_combined_tab(), "Combined (o#)")
        self.tabs.addTab(self._build_individual_tab(), "Individual Components")
        self.tabs.addTab(self._build_override_tab(), "Task Timing Override")

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

        self._refresh_override_ui_from_settings()

    # ------------------------------------------------------------------
    # Tab builders
    # ------------------------------------------------------------------

    def _build_combined_tab(self):
        tab = QWidget()
        combined_layout = QVBoxLayout(tab)

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
        combined_layout.addStretch()
        return tab

    def _build_individual_tab(self):
        tab = QWidget()
        individual_layout = QGridLayout(tab)
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

        return tab

    def _build_override_tab(self):
        """Task Timing Override tab.

        Lets the real tasks (Display window & Turntable) be run with timings
        other than the hardcoded defaults (3s combined scent pulse, 4s total
        delay before the next image/object) -- including switching them over
        to the individual humidifier/pump/solenoid sequence instead of the
        combined "o#" command. Backed by the process-wide singleton in
        olfactory_timing.py, so it applies immediately to any task started
        after it's enabled here, and resets to defaults on app restart.
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)

        description = QLabel(
            "Override the olfactory timings used by the Display and Turntable tasks. "
            "When disabled, tasks use the defaults: a 3s combined scent pulse, then a "
            "1s gap, so the next image/object appears 4s after scent onset."
        )
        description.setWordWrap(True)
        description.setFont(QFont("Segoe UI", 11))
        layout.addWidget(description)

        self.override_enabled_checkbox = QCheckBox("Override default timings for Display & Turntable tasks")
        self.override_enabled_checkbox.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.override_enabled_checkbox.toggled.connect(self.on_override_enabled_toggled)
        layout.addWidget(self.override_enabled_checkbox)

        mode_layout = QHBoxLayout()
        mode_label = QLabel("Dispense Mode:")
        mode_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.override_mode_combo = QComboBox()
        self.override_mode_combo.addItems(["Combined (o#)", "Individual Components (h/p/s)"])
        self.override_mode_combo.setFont(QFont("Segoe UI", 12))
        self.override_mode_combo.setMinimumHeight(40)
        self.override_mode_combo.currentIndexChanged.connect(self.on_override_mode_changed)
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.override_mode_combo)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        # Combined mode timing
        self.override_combined_group = QGroupBox("Combined Mode Timing")
        self.override_combined_group.setFont(QFont("Segoe UI", 12, QFont.Bold))
        combined_grid = QGridLayout()
        combined_grid.setSpacing(15)

        on_duration_label = QLabel("Scent On Duration (s):")
        on_duration_label.setFont(QFont("Segoe UI", 11))
        combined_grid.addWidget(on_duration_label, 0, 0)

        self.override_combined_duration = QDoubleSpinBox()
        self.override_combined_duration.setRange(0.1, 10.0)
        self.override_combined_duration.setSingleStep(0.1)
        self.override_combined_duration.setFont(QFont("Segoe UI", 11))
        self.override_combined_duration.setMinimumHeight(40)
        self.override_combined_duration.setMinimumWidth(120)
        self.override_combined_duration.valueChanged.connect(self.on_override_value_changed)
        combined_grid.addWidget(self.override_combined_duration, 0, 1)
        combined_grid.setColumnStretch(2, 1)

        self.override_combined_group.setLayout(combined_grid)
        layout.addWidget(self.override_combined_group)

        # Individual components timing
        self.override_individual_group = QGroupBox("Individual Components Timing")
        self.override_individual_group.setFont(QFont("Segoe UI", 12, QFont.Bold))
        individual_grid = QGridLayout()
        individual_grid.setSpacing(15)

        rows = [
            ("Humidifier Duration (s):", "override_humidifier_duration"),
            ("Pump Duration (s):", "override_pump_duration"),
            ("Solenoid Duration (s):", "override_solenoid_duration"),
            ("Delay after Humidifier (s):", "override_delay_after_humidifier"),
            ("Delay after Pump (s):", "override_delay_after_pump"),
        ]
        for row, (label_text, attr_name) in enumerate(rows):
            label = QLabel(label_text)
            label.setFont(QFont("Segoe UI", 11))
            individual_grid.addWidget(label, row, 0)

            spinbox = QDoubleSpinBox()
            spinbox.setRange(0.0, 10.0)
            spinbox.setSingleStep(0.1)
            spinbox.setFont(QFont("Segoe UI", 11))
            spinbox.setMinimumHeight(40)
            spinbox.setMinimumWidth(120)
            spinbox.valueChanged.connect(self.on_override_value_changed)
            individual_grid.addWidget(spinbox, row, 1)
            setattr(self, attr_name, spinbox)
        individual_grid.setColumnStretch(2, 1)

        self.override_individual_group.setLayout(individual_grid)
        layout.addWidget(self.override_individual_group)

        # Scent dispense delay (time before next image/object)
        dispense_group = QGroupBox("Scent Dispense Delay")
        dispense_group.setFont(QFont("Segoe UI", 12, QFont.Bold))
        dispense_grid = QGridLayout()
        dispense_grid.setSpacing(15)

        dispense_label = QLabel("Delay before next image/object (s):")
        dispense_label.setFont(QFont("Segoe UI", 11))
        dispense_grid.addWidget(dispense_label, 0, 0)

        self.override_dispense_delay = QDoubleSpinBox()
        self.override_dispense_delay.setRange(0.1, 20.0)
        self.override_dispense_delay.setSingleStep(0.1)
        self.override_dispense_delay.setFont(QFont("Segoe UI", 11))
        self.override_dispense_delay.setMinimumHeight(40)
        self.override_dispense_delay.setMinimumWidth(120)
        self.override_dispense_delay.valueChanged.connect(self.on_override_value_changed)
        dispense_grid.addWidget(self.override_dispense_delay, 0, 1)

        dispense_note = QLabel(
            "This is measured from scent onset, not from when dispensing finishes. "
            "It overrides scent_dispense_delay_ms and applies regardless of dispense mode."
        )
        dispense_note.setWordWrap(True)
        dispense_note.setFont(QFont("Segoe UI", 10))
        dispense_note.setStyleSheet("color: #666666;")
        dispense_grid.addWidget(dispense_note, 1, 0, 1, 3)
        dispense_grid.setColumnStretch(2, 1)

        dispense_group.setLayout(dispense_grid)
        layout.addWidget(dispense_group)

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        reset_btn.setMinimumHeight(40)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                border-radius: 5px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #455A64;
            }
        """)
        reset_btn.clicked.connect(self.reset_override_to_defaults)
        layout.addWidget(reset_btn)

        self.override_status_label = QLabel()
        self.override_status_label.setWordWrap(True)
        self.override_status_label.setFont(QFont("Segoe UI", 11))
        self.override_status_label.setStyleSheet(
            "padding: 10px; background-color: #eeeeee; border-radius: 5px;"
        )
        layout.addWidget(self.override_status_label)

        layout.addStretch()
        return tab

    # ------------------------------------------------------------------
    # Task Timing Override handlers
    # ------------------------------------------------------------------

    def _refresh_override_ui_from_settings(self):
        """Sync the override tab's widgets to the shared settings singleton
        without re-triggering the change handlers (e.g. on frame init)."""
        settings = get_olfactory_timing_settings()

        widgets = [
            self.override_enabled_checkbox, self.override_mode_combo,
            self.override_combined_duration, self.override_humidifier_duration,
            self.override_pump_duration, self.override_solenoid_duration,
            self.override_delay_after_humidifier, self.override_delay_after_pump,
            self.override_dispense_delay,
        ]
        for widget in widgets:
            widget.blockSignals(True)

        self.override_enabled_checkbox.setChecked(settings.enabled)
        self.override_mode_combo.setCurrentIndex(0 if settings.mode == MODE_COMBINED else 1)
        self.override_combined_duration.setValue(settings.combined_duration_ms / 1000)
        self.override_humidifier_duration.setValue(settings.humidifier_duration_ms / 1000)
        self.override_pump_duration.setValue(settings.pump_duration_ms / 1000)
        self.override_solenoid_duration.setValue(settings.solenoid_duration_ms / 1000)
        self.override_delay_after_humidifier.setValue(settings.delay_after_humidifier_ms / 1000)
        self.override_delay_after_pump.setValue(settings.delay_after_pump_ms / 1000)
        self.override_dispense_delay.setValue(settings.scent_dispense_delay_ms / 1000)

        for widget in widgets:
            widget.blockSignals(False)

        self._update_override_enabled_state()
        self._update_override_status_label()

    def _update_override_enabled_state(self):
        """Grey out mode-specific groups based on enabled state + selected mode."""
        enabled = self.override_enabled_checkbox.isChecked()
        is_individual = self.override_mode_combo.currentIndex() == 1

        self.override_mode_combo.setEnabled(enabled)
        self.override_combined_group.setEnabled(enabled and not is_individual)
        self.override_individual_group.setEnabled(enabled and is_individual)
        # Dispense delay applies in both modes, so it only depends on enabled.
        self.override_dispense_delay.setEnabled(enabled)

    def _update_override_status_label(self):
        settings = get_olfactory_timing_settings()
        if not settings.enabled:
            self.override_status_label.setText(
                f"Overrides OFF — tasks use defaults "
                f"({DEFAULT_COMBINED_DURATION_MS / 1000:g}s on, "
                f"{DEFAULT_SCENT_DISPENSE_DELAY_MS / 1000:g}s total before next image/object)."
            )
            self.override_status_label.setStyleSheet(
                "padding: 10px; background-color: #eeeeee; border-radius: 5px; color: #444444;"
            )
            return

        if settings.mode == MODE_INDIVIDUAL:
            mode_desc = (
                f"Individual: h={settings.humidifier_duration_ms / 1000:g}s, "
                f"gap={settings.delay_after_humidifier_ms / 1000:g}s, "
                f"p={settings.pump_duration_ms / 1000:g}s, "
                f"gap={settings.delay_after_pump_ms / 1000:g}s, "
                f"s={settings.solenoid_duration_ms / 1000:g}s"
            )
        else:
            mode_desc = f"Combined: {settings.combined_duration_ms / 1000:g}s on"

        self.override_status_label.setText(
            f"Overrides ON — {mode_desc}; next image/object appears "
            f"{settings.scent_dispense_delay_ms / 1000:g}s after scent onset."
        )
        self.override_status_label.setStyleSheet(
            "padding: 10px; background-color: #fff3e0; border-radius: 5px; color: #e65100;"
        )

    def on_override_enabled_toggled(self, checked):
        get_olfactory_timing_settings().enabled = checked
        self._update_override_enabled_state()
        self._update_override_status_label()

    def on_override_mode_changed(self, index):
        get_olfactory_timing_settings().mode = MODE_INDIVIDUAL if index == 1 else MODE_COMBINED
        self._update_override_enabled_state()
        self._update_override_status_label()

    def on_override_value_changed(self, _value):
        settings = get_olfactory_timing_settings()
        settings.combined_duration_ms = int(self.override_combined_duration.value() * 1000)
        settings.humidifier_duration_ms = int(self.override_humidifier_duration.value() * 1000)
        settings.pump_duration_ms = int(self.override_pump_duration.value() * 1000)
        settings.solenoid_duration_ms = int(self.override_solenoid_duration.value() * 1000)
        settings.delay_after_humidifier_ms = int(self.override_delay_after_humidifier.value() * 1000)
        settings.delay_after_pump_ms = int(self.override_delay_after_pump.value() * 1000)
        settings.scent_dispense_delay_ms = int(self.override_dispense_delay.value() * 1000)
        self._update_override_status_label()

    def reset_override_to_defaults(self):
        get_olfactory_timing_settings().reset_to_defaults()
        self._refresh_override_ui_from_settings()

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
