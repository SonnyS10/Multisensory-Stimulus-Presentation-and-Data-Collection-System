# Getting Started Guide

This guide covers the current first-run workflow for the active application in `eeg_stimulus_project/`.

## Before You Start

### Minimum Software Requirements

- Python 3.8+
- A working virtual environment or Python installation with `pip`
- The packages in `requirements.txt`

### Recommended For First Test Runs

- Start with `Developer Mode`
- Use `Test Number` `1` for a passive viewing test
- Use the `Display` output mode for the first run

## Installation

```bash
git clone https://github.com/SonnyS10/Multisensory-Stimulus-Presentation-and-Data-Collection-System.git
cd Multisensory-Stimulus-Presentation-and-Data-Collection-System

python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

Verify the package imports:

```bash
python -c "import eeg_stimulus_project; print('Installation successful')"
```

## First-Time Configuration Review

Before the first run on a new machine, review:

- `eeg_stimulus_project/config/settings.yaml`
- host/client port settings
- tactile system IP and credentials
- platform-specific executable paths for LabRecorder and Actichamp

Important: this project still includes lab-specific defaults. Do not assume the shipped IP addresses and paths are correct for your environment.

## Launch Options

You can start the application in any of these ways:

### Terminal

```bash
python -m eeg_stimulus_project.main.main
```

### Windows Batch Launcher

Double-click:

```text
eeg_stimulus_project/utils/run_eeg_stimulus.bat
```

### Desktop Shortcut On Windows

If you want a shortcut, point it to:

```text
eeg_stimulus_project/utils/run_eeg_stimulus.bat
```

An icon file is available at:

```text
eeg_stimulus_project/utils/Brain_icon.ico
```

## Your First Local Test Run

### Step 1: Open The Launcher

Start the application and use the launcher window.

Fill in:

- `Subject ID`, such as `test001`
- `Test Number`, either `1` or `2`

For a first run, use:

- `Subject ID`: any test identifier
- `Test Number`: `1`

### Step 2: Start Developer Mode

Click `Developer Mode`.

This launches:

- the control window
- the experiment window

On local runs, the data directory tree is created immediately.

### Step 3: Understand The Two Windows

#### Control Window

The current control window includes rows for:

- `Actichamp`
- `LabRecorder`
- `Eye Tracker`
- `Tactile Box`
- `Virtual Reality`
- `Turntable`
- `Olfactory System`

It also includes:

- a log output panel
- status indicators for each device
- `Validate Olfactory Ports`

#### Experiment Window

The experiment window includes:

- passive and Stroop test pages
- `Start`, `Stop`, `Pause`, `Resume`, and `Next`
- output-mode checkboxes such as `Display`, `VR`, and `Turntable`
- `Instructions`
- `Stimulus Order`
- `Latency Checker`
- `Record Baseline`

### Step 4: Run A Simple Passive Test

1. In the experiment window, select `Unisensory Neutral Visual`.
2. Check `Display` as the output mode.
3. Click `Start`.
4. A display window opens and a mirrored view appears in the experiment page.
5. When you are finished, click `Stop`.

If you do not select an output mode, the application blocks startup and prompts you to choose `Display`, `VR`, or `Turntable`.

### Step 5: Review Saved Output

Local runs save under:

```text
eeg_stimulus_project/saved_data/subject_<subject_id>/test_<test_number>/
```

Stroop response CSV output is stored inside each test folder as `data.csv`. Passive conditions do not currently write `data.csv`; precise event marker timing is stored in the XDF `labels` marker stream.

Important: re-running the same Stroop test can overwrite that test's `data.csv`.

## Host And Client Workflow

Use this only when the experiment presentation machine is separate from the data-collection machine.

### Host Steps

1. Enter `Subject ID` and `Test Number`.
2. Click `Start as Data Collection Computer (Host)`.
3. The host listens on port `9999`.
4. The control window opens only after a client connects.
5. Subject/test folders are created after the connection is established.

### Client Steps

1. Enter the host IP in `Host IP`.
2. Optionally choose custom alcohol and neutral image folders.
3. Click `Start Experimenter Computer (Client)`.
4. The experiment window opens after the connection succeeds.

Important client note: the client does not create its own subject/test data tree. It is the stimulus-presentation node.

## Custom Assets

The launcher accepts optional folders for:

- alcohol images
- non-alcohol images

Current behavior:

- default packaged images are still loaded when present
- custom folders are added on top of the defaults, not used as an exclusive replacement
- if neutral images are still missing, fallback behavior may use personalized image content

If you need a tightly controlled neutral set, provide an explicit neutral folder and verify the order in `Stimulus Order` before running participants.

## Useful Built-In Tools

### Latency Checker

The sidebar includes `Latency Checker`.

Current behavior:

- the test runs for 5 seconds
- it sends 10 pings per second
- it reports the average latency after 50 samples

### Record Baseline

The sidebar includes `Record Baseline`.

This opens a dedicated baseline display flow. In local mode, if LabRecorder is connected, the baseline recording is written under a `Baseline` folder in the current subject/test tree.

## Common First-Run Problems

### Import Or Dependency Errors

```bash
pip install -r requirements.txt
```

### Host Cannot Start

Check whether port `9999` is already in use.

### LabRecorder Does Not Connect

Check whether LabRecorder is running and listening on port `22345`.

### Windows Diagnostics

Run:

```text
test_troubleshooting.bat
```

## Next Documents To Read

- `DATA_COLLECTION_HOST_GUIDE.md`
- `EXPERIMENTER_CLIENT_GUIDE.md`
- `TROUBLESHOOTING.md`
- `DEVELOPER_DOCUMENTATION.md`
