# Troubleshooting Guide

This guide covers the current failure modes of the active application in `eeg_stimulus_project/`.

## First Priorities In Any Failure

1. Stop or pause participant-facing stimulation from the current UI.
2. Do not force-kill processes immediately unless the system is completely unresponsive.
3. Note the subject ID, test name, and approximate time of failure.
4. Check whether CSV or XDF output has already been written.
5. Keep `app.log` and the subject folder intact for review.

Important: the current application does not expose a confirmed `Ctrl+Alt+Q` emergency shortcut. Use the visible UI controls instead.

## Startup Failures

### Import Errors

Typical symptoms:

- `ModuleNotFoundError: No module named 'eeg_stimulus_project'`
- `ImportError: No module named 'PyQt5'`

Checks:

```bash
python --version
pip install -r requirements.txt
python -c "import eeg_stimulus_project; print('OK')"
```

On Windows, `test_troubleshooting.bat` is the fastest built-in environment check.

### Configuration File Errors

Typical symptoms:

- YAML parse errors
- missing `settings.yaml`
- wrong site-specific IP or path values

Check:

```bash
python -c "import yaml; yaml.safe_load(open('eeg_stimulus_project/config/settings.yaml', 'r', encoding='utf-8'))"
```

## Host/Client Connection Problems

### Host Cannot Start

Typical symptoms:

- `Address already in use`
- host never reaches `Waiting for client`

Most common causes:

1. Another process is already using port `9999`.
2. Another copy of the app is still running.
3. `eeg_stimulus_project/stimulus/tactile_box_code/tactile_receive.py` is already bound to `9999`.

Windows check:

```powershell
netstat -ano | findstr :9999
```

Linux/macOS check:

```bash
netstat -an | grep 9999
```

### Client Cannot Connect

Typical symptoms:

- timeout
- connection refused
- client window never opens

Check:

1. The host was started first.
2. The host is already waiting for a client.
3. The correct host IP is entered.
4. Port `9999` is reachable.

Important behavior: in host mode, the control window and subject/test directories are not created until a client actually connects.

### Connection Drops During Session

Check:

- network cable and switch status
- WiFi versus ethernet use
- whether the host process is still alive
- whether the client closed unexpectedly

If the host reports client disconnects, preserve logs before restarting.

## Hardware Connection Problems

### LabRecorder Fails To Connect

Current implementation detail: LabRecorder is controlled through its remote-control socket on port `22345`.

Check:

```powershell
netstat -ano | findstr :22345
```

Then verify:

1. LabRecorder is open.
2. Remote control is enabled.
3. The configured executable path is valid for the current machine.
4. The subject/test base directory exists.

### Eye Tracker Fails To Connect

Current behavior:

- the control window prompts for an IP address
- the codebase still contains lab-specific default eye-tracker IP values

Check:

1. The operator entered the correct eye-tracker IP.
2. The eye-tracker service is actually running.
3. The machine can reach that IP.

### Tactile System Fails

Current behavior:

- tactile setup depends on SSH access to the configured remote system
- current defaults are site-specific

Check:

1. `settings.yaml` has the correct tactile host.
2. SSH credentials are valid.
3. The remote script path and virtual environment command are valid.
4. The remote machine is reachable.

### Turntable Or Olfactory State Looks Wrong

Check:

1. The client is connected.
2. The relevant connect action was sent from the control window.
3. `Validate Olfactory Ports` has been run when needed.
4. The session is not proceeding past a warning dialog that the operator dismissed.

## Experiment Start Problems

### Start Button Does Nothing

Most common cause: no output mode is selected.

For passive tests, one of these must be selected before `Start`:

- `Display`
- `VR`
- `Turntable`

### Test Refuses To Start

Check whether the test is enforcing required hardware:

- Stroop tactile tests require tactile connection.
- Stroop olfactory tests require olfactory connection.

Passive tests can still proceed after warnings, but only if the operator confirms the dialog.

## Data Problems

### No Data Was Saved

Check which mode the app was running in:

- `Developer Mode`: local directories are created immediately.
- `Host Mode`: directories are created after the client connects.
- `Client Mode`: no primary subject/test directory is created locally.

This is a common source of confusion. Client mode is presentation-only from a persistence standpoint.

### Behavioral CSV Was Overwritten

Current behavior:

- when the host creates the test folders, old `data.csv` files for that subject/test can be cleared
- re-running a test in the same session can overwrite that test's CSV output

If you need preservation across retries, copy the subject folder before re-running.

### XDF File Is Missing

Check:

1. LabRecorder was actually connected.
2. The test was started through the normal UI path.
3. The run was local or host-backed rather than client-only.

## Legacy And Documentation Confusion

### EEG Stream Window References

The repository contains a legacy EEG stream viewer only under `Old_Code/`.

The active package does not currently ship a dedicated EEG Stream Window. If someone follows old documentation that mentions one, treat that as stale guidance.

### Old Code Dependency

`eeg_stimulus_project/data/data_saving.py` still imports from `Old_Code.stream_manager`. If you are debugging data collection internals, keep that dependency in mind.

## Useful Diagnostics

### Windows

```text
test_troubleshooting.bat
```

```powershell
netstat -ano | findstr :9999
netstat -ano | findstr :22345
tasklist | findstr python
type app.log
```

### Linux Or macOS

```bash
netstat -an | grep 9999
netstat -an | grep 22345
ps aux | grep python
tail -f app.log
```

## Safe Restart Order

1. Stop the active test from the experiment window if possible.
2. Let LabRecorder stop cleanly if it is connected.
3. Close the client before the host in distributed sessions.
4. Restart the application only after port `9999` is free again.

## Document Status

Document version: 2026-05-07
Last updated: 2026-05-07