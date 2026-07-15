# Data Collection Host Guide

This guide describes the current host-side workflow for the active application.

## What The Host Actually Does

The host machine is the coordination node for distributed experiments. In the current codebase it:

- waits for the experimenter client on TCP port `9999`
- launches the host control window after the client connects
- creates the subject/test output tree after that connection is established
- tracks hardware connection state through the control window
- controls LabRecorder through its remote-control socket on port `22345`

If you want to run the control and experiment windows on a single machine, use `Developer Mode` instead of host mode.

## Startup Order

### Required Sequence

1. Launch the application on the data-collection machine.
2. Enter `Subject ID` and `Test Number`.
3. Click `Start as Data Collection Computer (Host)`.
4. Wait for the client to connect.
5. After the client connects, the control window opens and the subject/test directories are created.

Important: in host mode, data directories are not created before the client connects.

## Current Control Window Layout

The current host control window includes these device rows:

- `Actichamp`
- `LabRecorder`
- `Eye Tracker`
- `Tactile Box`
- `Virtual Reality`
- `Turntable`
- `Olfactory System`

It also includes:

- device status indicators
- a log output panel
- `Validate Olfactory Ports`

Do not rely on older documentation that refers to generic `Connect ...` button names. The visible row labels above are the current UI surface.

## Hardware Workflow

### Actichamp

- The `Actichamp` row launches the configured executable path from platform settings.
- On Windows, the current default path is still lab-specific and should be reviewed before deployment.

### LabRecorder

- The `LabRecorder` row opens LabRecorder and then connects to its remote-control socket.
- The active code uses TCP remote control on port `22345`.
- XDF files are written into the current subject/test tree, inside the relevant test folder.

### Eye Tracker

- The `Eye Tracker` row opens an IP dialog.
- Confirm the eye-tracker IP before connecting.
- The codebase still includes lab-specific eye-tracker defaults, so verify them on each machine.

### Tactile Box

- The `Tactile Box` row launches the tactile setup process.
- The tactile workflow depends on SSH access to the configured remote machine.
- Review `eeg_stimulus_project/config/settings.yaml` before use.

### Turntable

- The `Turntable` row sends a turntable-connect action to the experiment side.
- Passive tests can warn and continue without turntable connection.
- Turntable usage is more tightly coupled to tactile workflows in some tasks.

### Olfactory System

- The `Olfactory System` row sends the connect action to the experiment side.
- `Validate Olfactory Ports` runs an operator confirmation loop that dispenses scent outputs and can issue a port-swap command.

## Data Layout

The current host workflow writes under:

```text
eeg_stimulus_project/saved_data/
  subject_<subject_id>/
    test_<test_number>/
      <Test Name>/
        data.csv  (Stroop response tasks only)
        subj_<subject_id>_<condition_alias>_<timestamp>.xdf
```

Important details:

- Test folder names use the display names shown in the GUI.
- XDF filenames use short ASCII condition aliases to keep LabRecorder remote filename control stable.
- During recording, LabRecorder may briefly write through an internal `_labrecorder_tmp/` folder; completed XDFs are moved back into the test folder on stop.
- XDF files contain EEG streams and precise LSL event markers, including the `labels` marker stream.
- `data.csv` is written by the Stroop stop/save path and contains response labels plus elapsed-time values.
- Passive conditions do not currently write `data.csv`; their event timing is in the XDF marker stream.
- `label_timestamps.txt` is no longer generated; marker timing should be read from the XDF.
- Existing `data.csv` files are cleared when the host creates the directory tree.
- Running the same Stroop test again in the same session can overwrite behavioral CSV output for that test.

## Host Responsibilities During A Session

Before the participant session:

1. Confirm the client can reach the host IP.
2. Confirm port `9999` is available.
3. Confirm LabRecorder is available on port `22345`.
4. Review site-specific values in `settings.yaml`.
5. Confirm output location under `eeg_stimulus_project/saved_data/`.

During the session:

1. Watch the device status indicators in the control window.
2. Use the log panel for connection and startup events.
3. Coordinate hardware readiness before telling the client to begin.
4. Use `Validate Olfactory Ports` before olfactory sessions when routing needs to be confirmed.

After the session:

1. Verify the subject/test directory exists.
2. Verify expected XDF output and any applicable behavioral CSV output are present.
3. Archive or back up the subject directory before reusing the same identifiers.

## Network Notes

### Current Ports

- host/client control: `9999`
- LabRecorder remote control: `22345`

### Important Port Conflict

The repository also contains `eeg_stimulus_project/stimulus/tactile_box_code/tactile_receive.py`, which binds port `9999` when run directly. If that script is running on the same machine as the host launcher, host mode can fail with an address-in-use error.

## Host-Side Warnings To Expect

The experiment window can still start after some warning dialogs, depending on the test type.

Examples:

- passive tactile tests can proceed after a tactile warning
- passive olfactory tests can proceed after an olfactory warning
- passive turntable tests can proceed after a turntable warning

But some test types are stricter:

- Stroop tactile tests require the tactile box connection
- Stroop olfactory tests require the olfactory connection

## Practical Troubleshooting

### Host Never Reaches The Control Window

Likely causes:

- no client has connected yet
- port `9999` is unavailable
- the host IP was not reachable from the client

### LabRecorder Row Turns Red Again

Check:

- LabRecorder is actually running
- remote control is enabled
- port `22345` is open
- the subject/test base directory exists

### Unexpected Missing CSV Files

Check:

- whether the test was stopped cleanly
- whether the same test was re-run and overwrote its CSV
- whether the run happened in client-only mode instead of host/local mode

## Recommended Daily Host Checklist

1. Review the current `settings.yaml` values.
2. Confirm the host IP the client should use.
3. Confirm `saved_data` write access.
4. Confirm LabRecorder port `22345` responds.
5. Confirm port `9999` is free before starting the launcher.
6. Run `test_troubleshooting.bat` on Windows when diagnosing machine-level issues.
