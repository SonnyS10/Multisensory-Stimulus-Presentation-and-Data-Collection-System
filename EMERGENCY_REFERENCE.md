# Emergency Quick Reference Card

Keep this page available during sessions.

## Immediate Participant Safety Actions

### If The Participant Needs The Session To Stop Now

1. Click `Stop` in the active experiment page if the UI is responsive.
2. Close or remove the participant-facing display if needed.
3. Remove or pause any attached hardware that is actively stimulating.
4. Check participant wellbeing and follow institutional emergency procedures.
5. Record the time, active test name, and subject ID.

Important: do not rely on undocumented keyboard shortcuts. Use the visible UI controls.

## Immediate System Failure Actions

1. Preserve data first.
2. Do not force-kill the app immediately unless it is completely unresponsive.
3. Note the active test, current machine role, and failure time.
4. Keep `app.log` and the subject folder intact.
5. Coordinate host/client shutdown in the correct order if possible.

## Quick Checks

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

## Critical Ports

- `9999`: host/client control channel
- `22345`: LabRecorder remote control

Note: `tactile_receive.py` also binds `9999` if run directly, which can block host mode.

## Fast Failure Triage

### Host Will Not Start

- Check whether port `9999` is already in use.
- Confirm no other copy of the app is still running.

### Client Will Not Connect

- Confirm the host was started first.
- Confirm the host IP is correct.
- Confirm the host is waiting for a client.

### LabRecorder Not Recording

- Confirm LabRecorder is open.
- Confirm remote control is enabled.
- Confirm port `22345` is listening.

### No Saved Data Appears

- Confirm whether the run was local, host, or client-only.
- Client-only mode does not create the main subject/test output tree.
- Re-running a Stroop test can overwrite that test's `data.csv`.

## Incident Notes To Capture

- Date and time
- Subject ID
- Test name
- Machine role: host, client, or local
- Error message text
- Whether CSV or XDF files were created
- What recovery steps were attempted

## Detailed References

- `TROUBLESHOOTING.md`
- `GETTING_STARTED.md`
- `DEVELOPER_DOCUMENTATION.md`

Last updated: 2026-05-07
