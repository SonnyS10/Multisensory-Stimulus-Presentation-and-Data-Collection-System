# EEG Stream Notes

## Status

This repository does **not** currently ship an active EEG Stream Window in the main application package.

The previous implementation exists only as legacy code in `Old_Code/eeg_stream_window.py`. The active package under `eeg_stimulus_project/` does not expose:

- an `EEG Stream` button in the current control window
- an active `eeg_stimulus_project/gui/eeg_stream_window.py` module
- a dedicated real-time EEG viewer workflow documented elsewhere in the current operator guides

## What The Current Application Does

In the current codebase, EEG-related workflow is centered around:

- launching the main application with `python -m eeg_stimulus_project.main.main`
- using the host control window to manage hardware state
- controlling LabRecorder through its remote control socket on port `22345`
- storing XDF recordings inside the selected subject/test directory tree under `eeg_stimulus_project/saved_data/`

## If You Need Live EEG Visualization

Treat the legacy viewer as historical reference only unless it is explicitly restored and tested against the current application.

Before reviving that workflow, verify all of the following:

1. A maintained EEG viewer module exists under `eeg_stimulus_project/`.
2. The control window exposes a supported entry point for that viewer.
3. The viewer's LSL discovery logic matches the current EEG acquisition stack.
4. The troubleshooting and operator guides are updated at the same time.

## Current Documentation Guidance

- For host-side EEG recording workflow, use `DATA_COLLECTION_HOST_GUIDE.md`.
- For startup and operator flow, use `GETTING_STARTED.md` and `README.md`.
- For technical implementation details, use `DEVELOPER_DOCUMENTATION.md`.

## Legacy Note

If the EEG Stream Window is intentionally reintroduced later, this file should be rewritten to document the restored feature rather than the removed one.