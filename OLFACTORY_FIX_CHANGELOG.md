# Olfactory Fix Changelog

**Date:** 2026-06-29
**Author:** Code changes assisted by Claude
**Baseline commit (before these edits):** `0e10d07ef5f89c2771092d24e4897000a768de31`
**Files changed:**
- `eeg_stimulus_project/gui/display_window.py`
- `eeg_stimulus_project/stimulus/turn_table_code/turntable_gui.py`

This document records every change made to fix two olfactory problems, the reasoning
behind each change, what each part does, and how to reverse it. A troubleshooting
section at the end lists other things to check if the behavior is still wrong.

---

## Problems being solved

1. **Olfactory did not work for viewing-booth (turntable) passive blocks** that include
   olfactory stimuli — specifically the *Alcohol/Neutral Visual & Olfactory* and
   *Alcohol/Neutral Visual, Tactile & Olfactory* booth conditions.

2. **The order/timing of sensory stimuli was not equivalent across realism blocks.**
   The scent-before-image *order* was already correct everywhere, but the *delay* between
   scent release and image presentation differed by block (0 s, 2 s, or 4 s), which made
   the 2D tactile+olfactory block feel like "image then scent."

---

## Root cause analysis

### Problem 1 — serial-port collision

The olfactory hardware is two Arduinos on COM ports
(`COM9` = scents 1–4, `COM8` = scents 5–8), opened by `OlfactoryController.connect()`
in `eeg_stimulus_project/stimulus/olfactory/olfactory_controller.py`.

**A serial COM port can only be opened by one handle at a time.**

When a turntable test runs, `open_secondary_gui` (in `main_gui.py`) still creates a
`DisplayWindow` in `instruction_only` mode to show the participant the instructions.
That `DisplayWindow.__init__` *unconditionally* opened the COM ports whenever the test
name contained "Olfactory". So the DisplayWindow grabbed `COM8`/`COM9` **first**, and the
`TurntableWindow` then failed to connect (port busy). The failure was silent
(`olfactory_connected = False`), so no scent was ever dispensed in the booth.

### Problem 2 — inconsistent scent→image delay

| Block | Order before | Delay before |
|---|---|---|
| 2D Visual + Olfactory | scent → image | 4 s |
| 2D Visual + Tactile + Olfactory | touch → scent → image | **0 s (immediate)** |
| Booth + Olfactory | scent → reveal | 4 s |
| Booth + Tactile + Olfactory | touch → scent → reveal | **2 s** |

The two tactile blocks did not match the 4 s used by the olfactory-only blocks.

---

## Change 1 — `display_window.py`: do not open scent ports in instruction-only mode

**What it does:** Prevents the instruction-only DisplayWindow (shown during a booth run)
from seizing the olfactory COM ports, so the `TurntableWindow` can connect and dispense
scent.

**Reasoning:** This is the direct fix for Problem 1. In instruction-only mode the booth
is the presentation device and owns the scent controller; the DisplayWindow has no need
for it.

### Code (after change)

Near the top of the file, a supporting comment was added to the original line, and the
condition gained `and not self.instruction_only`:

```python
# Only open the olfactory serial ports when this DisplayWindow is actually
# presenting stimuli. In instruction_only mode the turntable (viewing booth)
# is the presentation device and owns the scent controller; if we connected
# here we would hold COM8/COM9 and the turntable's olfactory connect would
# silently fail (a serial port can only be opened by one handle at a time).
if "Olfactory" in self.current_test and not self.instruction_only:
    self.olfactory_controller = OlfactoryController()
    self.olfactory_connected = self.olfactory_controller.connect()
```

### How to reverse

Change the condition back to:

```python
if "Olfactory" in self.current_test:
    self.olfactory_controller = OlfactoryController()
    self.olfactory_connected = self.olfactory_controller.connect()
```

---

## Change 2 — `display_window.py`: safe olfactory attribute defaults

**What it does:** Initializes `self.olfactory_controller = None` and
`self.olfactory_connected = False` early in `__init__`, before the conditional connect.

**Reasoning:** Because Change 1 means the controller is sometimes never created, any code
that later reads these attributes (e.g. `closeEvent`, `scent_function`) must not hit an
`AttributeError`. These defaults guarantee the attributes always exist.

### Code (after change)

```python
self._dispense_scent_before_next_image = False
self.next_is_craving = False  # Flag to indicate if the next image is a craving rating image
# Olfactory defaults; the controller is only opened below when this window
# actually presents stimuli (see instruction_only guard).
self.olfactory_controller = None
self.olfactory_connected = False
```

### How to reverse

Delete the two assignment lines (and the two comment lines above them):

```python
self.olfactory_controller = None
self.olfactory_connected = False
```

---

## Change 3 — `display_window.py`: unified scent→image timing in passive blocks

**What it does:** Rewrites the scent/image branch in `display_images_passive` so that the
**2D Tactile + Olfactory** block now waits `SCENT_DISPENSE_DELAY_MS` (4 s) after the scent
before showing the image — the same as the olfactory-only block. Order is now
`touch → scent → 4 s → image`.

**Reasoning:** Fixes Problem 2 for the 2D blocks. Before, the tactile branch showed the
image immediately (0 s) after the touch-triggered scent, so the image appeared before the
scent reached the participant. Equalizing the delay makes the scent→image relationship
identical to the olfactory-only block.

### Code (after change)

```python
img = self.images[self.current_image_index]
if hasattr(img, 'filename') and img.filename:
    # Every olfactory block presents the scent first, then waits SCENT_DISPENSE_DELAY_MS
    # before showing the image. This keeps the scent->image order and timing identical
    # across realism blocks: Olfactory-only dispenses here; Tactile+Olfactory dispenses
    # when the touch arms _dispense_scent_before_next_image. Both then delay equally.
    is_olfactory = "Olfactory" in self.current_test
    dispense_after_touch = self.should_dispense_scent_after_touch()

    if is_olfactory and dispense_after_touch and self._dispense_scent_before_next_image:
        # Tactile+Olfactory: touch armed the scent. Dispense, wait, then show image.
        self.scent_function(img)
        self._dispense_scent_before_next_image = False
        QTimer.singleShot(SCENT_DISPENSE_DELAY_MS, lambda: self._display_image_after_scent_delay(img))
    elif is_olfactory and not dispense_after_touch:
        # Olfactory-only: dispense scent, wait for it to reach the participant, then show image.
        self.scent_function(img)
        QTimer.singleShot(SCENT_DISPENSE_DELAY_MS, lambda: self._display_image_after_scent_delay(img))
    else:
        # No scent involved (or scent already handled): display image immediately.
        self._display_image_after_scent_delay(img)
```

### Code (before change) — for reversal

```python
img = self.images[self.current_image_index]
if hasattr(img, 'filename') and img.filename:
    if self.should_dispense_scent_after_touch() and self._dispense_scent_before_next_image:
        self.scent_function(img)
        self._dispense_scent_before_next_image = False

    # For olfactory tests, send scent first and wait 2 seconds before showing image
    should_delay_for_scent = "Olfactory" in self.current_test and not self.should_dispense_scent_after_touch()

    if should_delay_for_scent:
        # Send scent first
        self.scent_function(img)
        # Wait 4 seconds for scent to dispense, then display image
        QTimer.singleShot(4000, lambda: self._display_image_after_scent_delay(img))
    else:
        # No scent delay needed, display image immediately
        self._display_image_after_scent_delay(img)
```

### How to reverse

Replace the new block with the "before change" block above. (Reversing this restores the
0 s immediate-image behavior for the 2D tactile+olfactory block.)

---

## Change 4 — `display_window.py`: `SCENT_DISPENSE_DELAY_MS` constant

**What it does:** Adds a single named module-level constant (`= 4000`) that controls the
scent→image delay for the 2D display blocks.

**Reasoning:** Puts the timing in one obvious place so the value is easy to find and tune,
and so Change 3 reads clearly. The matching constant in the turntable module is kept equal.

### Code (after change)

```python
# Time to wait after releasing a scent before presenting the paired image, so the
# scent reaches the participant at the same point relative to the image in every
# olfactory realism block (2D and viewing booth, with or without tactile).
SCENT_DISPENSE_DELAY_MS = 4000
```

### How to reverse

Delete the constant and replace its uses with the literal `4000`.

### How to tune (not a reversal)

To change the delay for the 2D blocks, edit this one number (milliseconds). To keep all
blocks identical, change the matching constant in `turntable_gui.py` to the same value.

---

## Change 5 — `turntable_gui.py`: `SCENT_DISPENSE_DELAY_MS` constant + unified booth delay

**What it does:**
- Adds `SCENT_DISPENSE_DELAY_MS = 4000` at module level.
- Booth **olfactory-only** path: replaced the literal `4000` with the constant (no behavior change, 4 s → 4 s).
- Booth **tactile+olfactory** path: replaced the literal `2000` with the constant (**behavior change: 2 s → 4 s**).
- Updated a docstring that still said "2 seconds".

**Reasoning:** Fixes Problem 2 for the booth blocks by bringing the tactile path up to the
same 4 s used everywhere else, and centralizes the value.

### Code (after change)

Module-level constant:

```python
# Time to wait after releasing a scent before opening the booth doors (revealing the
# object). Kept equal to the 2D display's SCENT_DISPENSE_DELAY_MS so the scent->object
# order and timing is identical across every olfactory realism block, with or without
# tactile.
SCENT_DISPENSE_DELAY_MS = 4000
```

Booth olfactory-only path (in `run_test_sequence`):

```python
else:
    # Trigger scent first, wait for dispense, then open doors
    self.trigger_scent_for_step(step)
    self._start_timer(SCENT_DISPENSE_DELAY_MS, self._open_doors_after_scent)
```

Booth tactile+olfactory path (in `on_object_touched`):

```python
# Trigger scent first, wait for dispense, then open doors
self.trigger_scent_for_step(step)
self._start_timer(SCENT_DISPENSE_DELAY_MS, self._open_doors_after_scent)
```

### Code (before change) — for reversal

Olfactory-only path:

```python
else:
    # Trigger scent first, wait 4 seconds for dispense, then open doors
    self.trigger_scent_for_step(step)
    self._start_timer(4000, self._open_doors_after_scent)
```

Tactile+olfactory path:

```python
# Trigger scent first, wait 2 seconds for dispense, then open doors
self.trigger_scent_for_step(step)
self._start_timer(2000, self._open_doors_after_scent)
```

Docstring:

```python
def _open_doors_after_scent(self):
    """Open doors after scent has had 2 seconds to dispense."""
```

### How to reverse

Restore the literals (`4000` and `2000`) and the original docstring as shown above, and
delete the module-level `SCENT_DISPENSE_DELAY_MS` constant.

> Note: `_open_doors_after_scent` also contains `self._start_timer(2000, self.close_doors_and_continue)`.
> That `2000` is the **door-open dwell time** (how long the booth stays open), *not* the
> scent delay, and was intentionally left unchanged.

---

## Net behavior after all changes

| Block | Order/timing now |
|---|---|
| 2D Visual + Olfactory | scent → 4 s → image |
| 2D Visual + Tactile + Olfactory | touch → scent → 4 s → image |
| Booth + Olfactory | scent → 4 s → reveal |
| Booth + Tactile + Olfactory | touch → scent → 4 s → reveal |

Plus: the booth now actually receives the COM ports, so scent dispenses in the booth.

---

## How to reverse everything at once (git)

If these are the only uncommitted changes, discard them with:

```bash
git checkout -- eeg_stimulus_project/gui/display_window.py \
                eeg_stimulus_project/stimulus/turn_table_code/turntable_gui.py
```

Or return the whole tree to the baseline commit:

```bash
git checkout 0e10d07 -- eeg_stimulus_project/gui/display_window.py \
                        eeg_stimulus_project/stimulus/turn_table_code/turntable_gui.py
```

(If the changes are already committed, use `git revert <that-commit>` instead.)

---

## If it still does not work — other things to check

These changes assume the rest of the olfactory chain is healthy. If scent still does not
dispense in the booth, or timing still looks wrong, check the following in order:

1. **COM port names / wiring.** `olfactory_controller.py` defaults to `COM9` (scents 1–4)
   and `COM8` (scents 5–8), overridable via `config` → `hardware.olfactory.arduino1_port` /
   `arduino2_port` in `settings.yaml`. If Windows assigned different COM numbers, connect
   will fail. The two Arduinos can also be swapped (`swap_ports()` / the "Validate Olfactory
   Ports" button in the control window).

2. **Olfactory marked connected in the Control Window.** The run is blocked unless
   `shared_status['olfactory_connected']` is `True` (mandatory check in `main_gui.py`).
   Confirm the olfactory system shows connected before starting.

3. **A stale process is still holding the port.** If a previous run crashed without closing
   the controller, `COM8`/`COM9` may still be locked by a zombie Python process. Close all
   app windows (or kill the process) and retry. A port held elsewhere produces the same
   silent failure this fix was about.

4. **Scent numbers actually assigned.** No scent fires if the stimulus has no scent number.
   For the booth, every filled olfactory bay must have a scent number 1–8
   (`missing_scent_assignments_for_sequence` / "Missing Scent Assignments" dialog). For 2D,
   `scent_numbers` come from the Stimulus Order frame; `scent_number_for_image` returns
   `None` for blanks and no scent is sent.

5. **Combined Display + Booth selection.** The Problem 1 fix keys off `instruction_only`,
   which is `True` only when the turntable is selected and the 2D display is **not**. If a
   user selects **both** Display and Turntable at once, `instruction_only` is `False`, the
   DisplayWindow again opens the ports, and the booth will fail to get them. This combo is
   unusual, but if it is a real workflow the ownership logic needs an explicit rule for who
   controls the scent.

6. **The "scent" Arduino command quirks.** `trigger_scent` remaps scents 5–8 to the second
   Arduino's `o1`–`o4`, with a special case sending `o5` for scent 8 ("workaround for Arduino
   issue with 'o4'"). If a specific scent number misbehaves, verify the firmware matches this
   mapping.

7. **Delay too short/long for the hardware.** 4 s is the assumption for scent travel time.
   If the scent physically arrives later/earlier than the image, tune
   `SCENT_DISPENSE_DELAY_MS` in **both** modules (keep them equal) rather than per-block.

8. **`stop_scent` timing.** Scents auto-stop 3 s after triggering
   (`QTimer.singleShot(3000, ... stop_scent)`). With a 4 s image delay, the scent valve
   closes ~1 s before the image appears. If you want the scent to persist into image
   onset, that 3 s stop time may also need raising.
