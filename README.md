# Multisensory Stimulus Presentation and Data Collection System

This repository contains the active multisensory experiment application under `eeg_stimulus_project/` and a set of legacy prototypes under `Old_Code/`.

The current application supports:

- local single-computer test runs through `Developer Mode`
- distributed host/client experiments over TCP on port `9999`
- behavioral data saving to CSV
- LabRecorder control for XDF capture on port `22345`
- visual, tactile, olfactory, and turntable-assisted experiment flows

## Repository Status

The active codebase is usable, but it is not fully de-personalized yet. Before deploying on a new lab machine, review the current site-specific defaults in code and configuration, especially:

- host/client IP defaults
- tactile system host and credentials
- eye-tracker IP defaults
- Windows-specific hardware executable paths

`Old_Code/` should be treated as historical reference unless a feature is explicitly restored into `eeg_stimulus_project/`.

## Quick Start

### Installation

```bash
git clone https://github.com/SonnyS10/Multisensory-Stimulus-Presentation-and-Data-Collection-System.git
cd Multisensory-Stimulus-Presentation-and-Data-Collection-System

python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
python -m eeg_stimulus_project.main.main
```

### Launchers

- Windows: `eeg_stimulus_project/utils/run_eeg_stimulus.bat`
- macOS/Linux: `eeg_stimulus_project/utils/run_eeg_stimulus.sh`

## Run Modes

### Developer Mode

Use this for a single-computer test run.

What happens:

1. Enter `Subject ID` and `Test Number` (`1` or `2`) in the launcher.
2. Click `Developer Mode`.
3. The app creates the subject/test folder tree immediately.
4. A control window and an experiment window open on the same machine.

### Data Collection Computer (Host)

Use this when the data collection machine is separate from the experiment presentation machine.

What happens:

1. Enter `Subject ID` and `Test Number` in the launcher.
2. Click `Start as Data Collection Computer (Host)`.
3. The host starts listening on port `9999`.
4. The control window is launched only after a client connects.
5. Subject/test directories are created after that client connection is established.

Important:

- If you want to work without a client, use `Developer Mode` instead.
- The host window refuses to close while a client is still connected.

### Experimenter Computer (Client)

Use this on the stimulus presentation machine.

What happens:

1. Enter the host IP in `Host IP`.
2. Optionally choose custom alcohol and neutral image folders.
3. Click `Start Experimenter Computer (Client)`.
4. The experiment window opens after the client connects to the host.

Important:

- Client mode does not create local `subject_.../test_...` output directories.
- The client is the presentation node, not the primary data-storage node.

## Data Layout

The active application writes data under:

```text
eeg_stimulus_project/saved_data/
  subject_<subject_id>/
    test_<test_number>/
      <Test Name>/
        data.csv
        subj_<subject_id>_<test_name>_<timestamp>.xdf
```

Notes:

- Folder names use the display names of the tests, including spaces and punctuation.
- LabRecorder filenames are sanitized by replacing spaces with underscores.
- Starting the same test again in the same session can overwrite that test's `data.csv`.
- Host mode creates the subject/test tree only after the client connects.

## Control Window Hardware Workflow

The current control window exposes these device rows:

- `Actichamp`
- `LabRecorder`
- `Eye Tracker`
- `Tactile Box`
- `Virtual Reality`
- `Turntable`
- `Olfactory System`

It also includes:

- a log panel
- `Validate Olfactory Ports`
- per-device status indicators

The LabRecorder row launches the configured LabRecorder executable and then connects to its remote-control socket on port `22345`.

## Experiment Window Highlights

The experiment window currently includes:

- passive and Stroop test pages
- `Start`, `Stop`, `Pause`, `Resume`, and `Next` buttons
- output-mode selectors such as `Display`, `VR`, and `Turntable`
- `Instructions`
- `Stimulus Order`
- `Latency Checker`
- `Record Baseline`

The baseline workflow runs a dedicated crosshair-based recording view and writes into a `Baseline` folder when the relevant recording path is available.

## Configuration Checklist

Review these before first use on a new machine:

- `eeg_stimulus_project/config/settings.yaml`
- tactile system host, username, and password
- LabRecorder executable path for the current platform
- Actichamp executable path for Windows setups
- launcher default host IP
- eye-tracker IP used at connect time

Known current defaults worth reviewing:

- host/client communication port: `9999`
- LabRecorder remote control port: `22345`
- launcher host IP default: `169.254.37.25`
- tactile host in `settings.yaml`: `129.21.60.54`
- tactile fallback host in config manager defaults: `10.115.12.225`

## Documentation Map

- `GETTING_STARTED.md`: first-run setup and local workflow
- `DATA_COLLECTION_HOST_GUIDE.md`: host-side setup and operations
- `EXPERIMENTER_CLIENT_GUIDE.md`: client-side operations
- `TROUBLESHOOTING.md`: common failure modes and recovery steps
- `EMERGENCY_REFERENCE.md`: quick incident response card
- `DEVELOPER_DOCUMENTATION.md`: implementation notes and technical caveats
- `EEG_STREAM_README.md`: legacy note for a removed EEG Stream Window workflow

## Troubleshooting Quick Checks

If something fails early, check these first:

1. `python --version`
2. `pip install -r requirements.txt`
3. `test_troubleshooting.bat` on Windows
4. Port `9999` availability for host/client startup
5. Port `22345` availability for LabRecorder remote control

Be aware that `eeg_stimulus_project/stimulus/tactile_box_code/tactile_receive.py` also binds port `9999`, so it can conflict with host mode if run on the same machine.
