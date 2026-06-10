# EEG Stimulus Project Developer Documentation

This document describes the current active architecture under `eeg_stimulus_project/` and calls out the main codebase caveats that matter when modifying behavior.

## Active Versus Legacy Code

The repository has two distinct layers:

- `eeg_stimulus_project/`: active application code
- `Old_Code/`: legacy prototypes and archived experiments

Do not assume that a feature documented in `Old_Code/` exists in the active package. The clearest example is the old EEG stream viewer: the active package does not currently include a dedicated EEG Stream Window.

## Active Entry Point

The main launcher is:

```text
eeg_stimulus_project/main/main.py
```

It starts the Qt launcher and supports three runtime paths:

1. `Developer Mode`
2. `Start as Data Collection Computer (Host)`
3. `Start Experimenter Computer (Client)`

## Process Model

### Developer Mode

Developer mode is the only true single-machine workflow in the active package.

Behavior:

- creates subject/test directories immediately
- spawns the control window and experiment window locally
- uses shared multiprocessing state for device status and logs

### Host Mode

Host mode is asymmetric by design.

Behavior:

- validates `Subject ID` and `Test Number`
- binds `0.0.0.0:9999`
- waits for a client connection
- creates the subject/test output tree only after the client connects
- launches the control window after the client connects

This means the host-side UI and data directories do not appear before the client joins.

### Client Mode

Client mode is also asymmetric.

Behavior:

- connects to host port `9999`
- launches the experiment window
- passes `base_dir = None`
- does not create the primary subject/test directory tree locally

From a persistence standpoint, the client is presentation-only.

## Core Modules

### Launcher

```text
eeg_stimulus_project/main/main.py
```

Responsibilities:

- launcher UI
- mode selection
- host socket lifecycle
- process creation
- subject/test directory creation

### Experiment Window

```text
eeg_stimulus_project/gui/main_gui.py
```

Responsibilities:

- test navigation
- frame-specific run controls
- latency checker
- baseline workflow
- network command handling from the host

Current experiment-frame controls include:

- `Start`
- `Stop`
- `Pause`
- `Resume`
- `Next`
- `Display`
- `VR`
- `Turntable`

### Control Window

```text
eeg_stimulus_project/gui/control_window.py
```

Responsibilities:

- host hardware control surface
- device status indicators
- LabRecorder launch and connection
- eye-tracker connection
- tactile launcher
- turntable and olfactory connect actions
- olfactory port validation flow

Current visible device rows are:

- `Actichamp`
- `LabRecorder`
- `Eye Tracker`
- `Tactile Box`
- `Virtual Reality`
- `Turntable`
- `Olfactory System`

### Data Saving

```text
eeg_stimulus_project/data/data_saving.py
```

Responsibilities:

- stroop CSV writeout
- passive path setup

Important current behavior:

- `save_data_stroop()` deletes the existing `data.csv` before rewriting it
- the data layer still imports `Old_Code.stream_manager`

That legacy import is a real dependency, not just dead documentation.

### Asset Loading

```text
eeg_stimulus_project/assets/asset_handler.py
```

Current behavior:

- loads default alcohol and neutral images when present
- adds custom alcohol and neutral folders on top of the defaults
- falls back to personalized images when neutral content is missing
- supports repetition and seeded randomization

This means client-selected asset folders are additive, not exclusive replacements.

## Data Layout

The active application writes under:

```text
eeg_stimulus_project/saved_data/
  subject_<subject_id>/
    test_<test_number>/
      <Test Name>/
        data.csv
        subj_<subject_id>_<test_name>_<timestamp>.xdf
```

Important implementation details:

- test folders use GUI display names, including spaces and punctuation
- LabRecorder sanitizes filenames by replacing spaces with underscores
- XDF files contain EEG streams and precise LSL event markers, including the `labels` marker stream
- `data.csv` is behavioral response output, not an event-marker timing file
- passive conditions may not produce meaningful CSV rows unless behavioral data is added later
- `label_timestamps.txt` is no longer generated; marker timing should be read from the XDF
- host setup clears existing `data.csv` files for the selected tests when creating the directory tree

## Hardware Integrations

### LabRecorder

```text
eeg_stimulus_project/utils/labrecorder.py
```

Current integration is not just general LSL coordination. It uses LabRecorder's remote-control socket.

Behavior:

- opens a TCP connection to the configured host on port `22345`
- sends `filename` and `start` commands
- writes XDF output into the current test directory

### Eye Tracker

```text
eeg_stimulus_project/utils/eye_tracking_software.py
```

Current integration targets Pupil Labs.

Important caveat:

- the codebase still contains lab-specific default IP addresses
- the control window also prompts the operator for an IP

### Tactile System

```text
eeg_stimulus_project/stimulus/tactile_box_code/tactile_setup.py
```

Current integration depends on:

- SSH access
- remote environment activation
- a remote tactile script path
- network reachability to the configured tactile host

### Turntable And Olfactory

Turntable and olfactory connection are currently command-driven from the control window into the experiment side.

Olfactory routing also has an operator-facing validation loop that can swap ports after confirmation.

## Baseline And Latency Utilities

### Baseline

The experiment sidebar exposes `Record Baseline`.

Current behavior:

- prevents a second display from opening while baseline is active
- uses the same display pipeline as experiment runs
- starts a `Baseline` LabRecorder path in local mode when LabRecorder is connected

### Latency Checker

The experiment sidebar exposes `Latency Checker` and `Check Latency`.

Current behavior:

- 5-second run
- 10 pings per second
- 50 total samples
- average latency report at completion

## Configuration System

### Primary Source

```text
eeg_stimulus_project/config/settings.yaml
```

### Manager

```text
eeg_stimulus_project/config/config_manager.py
```

The config manager resolves environment variables and path values, but the application is not fully free of site-specific defaults.

Known caveats:

- `settings.yaml` currently sets tactile host to `129.21.60.54`
- the config manager fallback still uses `10.115.12.225`
- the launcher pre-fills host IP `169.254.37.25`
- eye-tracker code includes hardcoded default IPs
- `main_gui.py` still contains a developer-specific `sys.path.append(...)`

Any claim that the codebase is fully free of hardcoded paths or lab-specific defaults is currently inaccurate.

## Networking Model

### Active Ports

- `9999`: host/client control channel
- `22345`: LabRecorder remote control

### Important Port Conflict

```text
eeg_stimulus_project/stimulus/tactile_box_code/tactile_receive.py
```

This script also binds port `9999` when run directly. That can block host startup if both are run on the same machine.

## Current Missing Or Legacy Surfaces

These are important when triaging docs or features:

- no active `eeg_stimulus_project/gui/eeg_stream_window.py`
- no active package-level `tests/` directory in `eeg_stimulus_project/`
- older docs may still describe removed or legacy features

## Testing Guidance

Because the active package has limited formal test coverage, the most useful validation is still workflow-based:

1. import validation
2. launcher startup
3. local `Developer Mode` run
4. host/client connection on port `9999`
5. LabRecorder socket availability on port `22345`
6. CSV and XDF output verification

On Windows, `test_troubleshooting.bat` is the current built-in environment check.

## Safe Areas To Edit Versus High-Risk Areas

Relatively safer areas:

- markdown docs
- asset-ordering and display text
- config defaults
- launcher copy and labels

High-risk areas:

- host/client startup sequencing in `main.py`
- display lifecycle in `main_gui.py`
- control-window network message handling
- LabRecorder command flow
- tactile SSH lifecycle

## Development Priorities Suggested By Current State

1. Remove remaining machine-specific paths and IP defaults.
2. Decouple active data collection from `Old_Code.stream_manager`.
3. Resolve the `9999` port overlap between host mode and `tactile_receive.py`.
4. Add active-package tests for startup, networking, and data saving.
5. Keep docs synchronized whenever UI labels or hardware workflows change.

Document version: 2026-05-07
Last updated: 2026-05-07
