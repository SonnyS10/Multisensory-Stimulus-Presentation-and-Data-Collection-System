# Experimenter Client Guide

This guide describes the current client-side workflow for the active application.

## What The Client Actually Does

The client machine is the presentation node. In the current codebase it:

- connects to the host on port `9999`
- opens the experiment window after the connection succeeds
- presents stimuli and operator controls
- sends status and experiment actions back to the host
- does not create the primary subject/test output tree in client-only mode

That last point matters: the client is not the main storage node.

## Before You Connect

Confirm all of the following with the host operator:

1. The host launcher is already waiting for a client.
2. You have the correct host IP.
3. The correct `Subject ID` and `Test Number` were entered on the host side.
4. The recording hardware is either connected or intentionally bypassed for a dry run.

## Starting The Client

1. Launch the application.
2. In `Experimenter Computer (Client)`, enter the host IP.
3. Optionally browse for custom alcohol and neutral image folders.
4. Click `Start Experimenter Computer (Client)`.

Important:

- The launcher currently pre-fills a lab-specific host IP default (`169.254.37.25`). Treat it as a placeholder, not a guaranteed correct address.
- If the host is not already listening, the client will fail to connect.

## Custom Asset Behavior

The client accepts optional folders for:

- alcohol images
- non-alcohol images

Current behavior is additive, not exclusive:

- default packaged images are loaded first when available
- custom folders are added on top of those defaults
- if no neutral images are available, fallback behavior can use personalized images

If your protocol requires strict category control, verify the final stimulus order in the `Stimulus Order` page before starting participants.

## Current Experiment Window Surface

### Sidebar Tools

The sidebar currently exposes:

- test pages
- `Instructions`
- `Stimulus Order`
- `Latency Checker`
- `Record Baseline`

### Test Controls

Depending on the test page, the current controls include:

- `Start`
- `Stop`
- `Pause`
- `Resume`
- `Next`
- `Display`
- `VR`
- `Turntable`

For passive tests, one of `Display`, `VR`, or `Turntable` must be selected before pressing `Start`.

## Running A Session

### Suggested First Sequence

1. Open `Instructions` and confirm the participant-facing flow.
2. Open `Stimulus Order` if you need to review randomization or repetitions.
3. Select the desired test page.
4. Choose exactly one output mode.
5. Click `Start`.
6. Monitor the mirrored view in the experiment page.
7. Click `Stop` to end the run cleanly.

## Hardware Warnings And Requirements

The client-side experiment flow currently enforces these rules:

- Stroop tactile tests require tactile connection.
- Stroop olfactory tests require olfactory connection.
- Passive tactile tests can continue after a warning.
- Passive olfactory tests can continue after a warning.
- Passive turntable runs can continue after a warning.
- Missing LabRecorder or eye-tracker connections trigger a confirmation dialog before the run proceeds.

This means dry runs are possible, but not every test can proceed without its hardware.

## Baseline Workflow

The sidebar includes `Record Baseline`.

Current behavior:

- it opens a dedicated baseline display flow
- it prevents a second display window from opening at the same time
- in local mode, if LabRecorder is connected, it can start a `Baseline` recording path

For distributed sessions, confirm with the host operator how baseline output should be handled before participant use.

## Latency Checker

The sidebar includes `Latency Checker`, and the page includes `Check Latency`.

Current behavior:

- 5-second measurement window
- 10 pings per second
- 50 total samples
- average latency displayed at the end

Use this before distributed sessions when network timing is important.

## What The Client Does Not Do

In client-only mode, the application does not create the primary subject/test directory tree under `eeg_stimulus_project/saved_data/`.

Treat the client as:

- the presentation interface
- the operator workflow interface
- a networked partner to the host

Do not treat it as the authoritative storage node for participant output.

## Practical Troubleshooting

### Connection Refused Or Timeout

Check:

- the host is already listening
- the host IP is correct
- port `9999` is not blocked

### Stimuli Do Not Start

Check:

- an output mode is selected
- the host connection is still active
- required hardware warnings were not cancelled

### Image Set Looks Wrong

Check:

- whether default images are still being included
- whether a neutral folder was actually supplied
- the resulting order in `Stimulus Order`

### Participant Session Needs To Stop Immediately

Use the current UI controls:

- click `Stop`
- close the active display window if needed
- coordinate with the host operator immediately

Do not rely on undocumented keyboard shortcuts that are not implemented in the current app.