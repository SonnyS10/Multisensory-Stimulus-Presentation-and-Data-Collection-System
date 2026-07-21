"""Process-wide, in-memory overrides for olfactory task timing.

The real tasks (display_window.py, turntable_gui.py) normally dispense scent
with a fixed 3-second "o#" pulse and a fixed 4-second delay before the next
image/object is revealed. The Olfactory Test window's "Task Timing Override"
tab can override those defaults here so different timings -- including
switching the real tasks over to the individual humidifier/pump/solenoid
sequence instead of the combined "o#" command -- can be tried against actual
task playback without editing code. Resets to defaults on app restart.
"""
from PyQt5.QtCore import QObject, QTimer

DEFAULT_COMBINED_DURATION_MS = 3000
DEFAULT_SCENT_DISPENSE_DELAY_MS = 4000
DEFAULT_COMPONENT_DURATION_MS = 1000
DEFAULT_DELAY_AFTER_HUMIDIFIER_MS = 0
DEFAULT_DELAY_AFTER_PUMP_MS = 0

MODE_COMBINED = "combined"
MODE_INDIVIDUAL = "individual"


class OlfactoryTimingSettings:
    """Singleton holding the current (possibly overridden) task timings."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._reset()
        return cls._instance

    def _reset(self):
        self.enabled = False
        self.mode = MODE_COMBINED
        self.combined_duration_ms = DEFAULT_COMBINED_DURATION_MS
        self.humidifier_duration_ms = DEFAULT_COMPONENT_DURATION_MS
        self.pump_duration_ms = DEFAULT_COMPONENT_DURATION_MS
        self.solenoid_duration_ms = DEFAULT_COMPONENT_DURATION_MS
        self.delay_after_humidifier_ms = DEFAULT_DELAY_AFTER_HUMIDIFIER_MS
        self.delay_after_pump_ms = DEFAULT_DELAY_AFTER_PUMP_MS
        self.scent_dispense_delay_ms = DEFAULT_SCENT_DISPENSE_DELAY_MS

    def reset_to_defaults(self):
        self._reset()

    def get_scent_dispense_delay_ms(self):
        """Delay before the next image/object is revealed after scent onset."""
        return self.scent_dispense_delay_ms if self.enabled else DEFAULT_SCENT_DISPENSE_DELAY_MS

    def get_combined_duration_ms(self):
        return self.combined_duration_ms if self.enabled else DEFAULT_COMBINED_DURATION_MS


_settings = OlfactoryTimingSettings()


def get_olfactory_timing_settings():
    """Return the process-wide OlfactoryTimingSettings singleton."""
    return _settings


class ScentDispenseRunner(QObject):
    """Dispenses a scent for one task trial and stops it, per the current
    OlfactoryTimingSettings.

    When overrides are disabled (or mode is "combined"), this reproduces the
    original task behavior: send "o#", stop it after the configured duration
    (default 3s). When overrides are enabled and mode is "individual", it
    instead runs the humidifier -> pump -> solenoid sequence with configured
    per-component durations and inter-component delays, mirroring the
    Olfactory Test window's manual sequential trigger.

    Self-contained: owns its own timers, so the caller only needs to keep a
    reference to the runner alive (e.g. store it on `self`) until it finishes.
    """

    def __init__(self, controller, scent_number, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.scent_number = scent_number
        self._timers = []

    def start(self):
        """Begin dispensing. Returns True if the first trigger command
        was sent successfully (mirrors the pre-override trigger_scent()
        success check)."""
        settings = get_olfactory_timing_settings()
        if settings.enabled and settings.mode == MODE_INDIVIDUAL:
            sequence = [
                (self.controller.trigger_humidifier, settings.humidifier_duration_ms, settings.delay_after_humidifier_ms),
                (self.controller.trigger_pump, settings.pump_duration_ms, settings.delay_after_pump_ms),
                (self.controller.trigger_solenoid, settings.solenoid_duration_ms, 0),
            ]
        else:
            sequence = [(self.controller.trigger_scent, settings.get_combined_duration_ms(), 0)]
        return self._run_step(sequence, 0)

    def _run_step(self, sequence, index):
        if index >= len(sequence):
            return True
        trigger_fn, duration_ms, delay_after_ms = sequence[index]
        if not trigger_fn(self.scent_number):
            return False
        self._schedule(duration_ms, lambda: self._stop_step(sequence, index, delay_after_ms))
        return True

    def _stop_step(self, sequence, index, delay_after_ms):
        self.controller.stop_scent(self.scent_number)
        next_index = index + 1
        if delay_after_ms > 0:
            self._schedule(delay_after_ms, lambda: self._run_step(sequence, next_index))
        else:
            self._run_step(sequence, next_index)

    def _schedule(self, ms, callback):
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(callback)
        timer.start(ms)
        self._timers.append(timer)
