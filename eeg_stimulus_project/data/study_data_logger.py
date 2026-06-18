"""
Study data logger for multisensory alcohol cue-reactivity experiments.

Creates and appends two CSV streams per participant session:
  1. Subjective craving ratings (baseline + 18 block ratings)
  2. Cross-modal Stroop task behavioral trials

Directory layout:
  eeg_stimulus_project/saved_data/subject_<subject_id>/test_<test_number>/<task_name>/

Files are never overwritten: microsecond timestamps plus version suffixes (_v2, _v3, ...)
guarantee unique filenames when hardware re-triggers the same session label.
"""

from __future__ import annotations

import csv
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Map client-side scent port / dispenser IDs to human-readable labels.
# Extend this table as new scents are commissioned on the olfactory rig.
SCENT_MAP: Dict[int, str] = {
    1: "Beer",
    2: "Plastic",
    3: "Wine",
    4: "Neutral_Clean",
    5: "Whiskey",
}

# Project root is three levels above this file: .../eeg_stimulus_project/data/
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DATA_ROOT = _PROJECT_ROOT / "eeg_stimulus_project" / "saved_data"

CRAVING_COLUMNS: List[str] = [
    "timestamp",
    "subject_id",
    "test_number",
    "block_index",
    "realism_condition",
    "sensory_condition",
    "cue_type",
    "craving_score",
]

STROOP_COLUMNS: List[str] = [
    "timestamp",
    "subject_id",
    "test_number",
    "trial_number",
    "image_shown",
    "scent_number",
    "scent_name",
    "has_tactile_trigger",
    "congruence_condition",
    "key_pressed",
    "reaction_time_ms",
    "is_correct",
]

AFFIRMATIVE_KEYS = frozenset({"yes", "y"})
NEGATIVE_KEYS = frozenset({"no", "n"})


# ---------------------------------------------------------------------------
# Path and filename helpers
# ---------------------------------------------------------------------------

def _sanitize_part(value: Union[str, int]) -> str:
    """Return a filesystem-safe token (alphanumeric, underscore, hyphen)."""
    text = str(value).strip()
    safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in text)
    return safe.strip("._-") or "unknown"


def _sanitize_task_name(task_name: str) -> str:
    """
    Preserve human-readable task folder names (spaces, parentheses) while
    stripping characters that are illegal on common filesystems.
    """
    text = str(task_name).strip()
    illegal = '<>:"|?*\\'
    safe = "".join(ch if ch not in illegal else "_" for ch in text)
    return safe.strip("._- ") or "unknown_task"


def build_session_directory(
    subject_id: Union[str, int],
    test_number: Union[str, int],
    task_name: str,
    data_root: Optional[Union[str, Path]] = None,
) -> Path:
    """
    Build and create the session task directory without raising on existing paths.

    Returns:
        Path to eeg_stimulus_project/saved_data/subject_<id>/test_<n>/<task_name>/
    """
    root = Path(data_root) if data_root is not None else DEFAULT_DATA_ROOT
    task_dir = (
        root
        / f"subject_{_sanitize_part(subject_id)}"
        / f"test_{_sanitize_part(test_number)}"
        / _sanitize_task_name(task_name)
    )
    task_dir.mkdir(parents=True, exist_ok=True)
    return task_dir


def _microsecond_timestamp() -> str:
    """Wall-clock stamp for unique filenames: YYYYMMDD_HHMMSS_ffffff."""
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def _event_timestamp() -> str:
    """ISO-8601 event timestamp with millisecond precision for CSV rows."""
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]


def resolve_unique_filepath(directory: Path, basename: str, extension: str = ".csv") -> Path:
    """
    Return a path that does not yet exist on disk.

    If basename.csv exists, tries basename_v2.csv, basename_v3.csv, etc.
    """
    directory.mkdir(parents=True, exist_ok=True)
    candidate = directory / f"{basename}{extension}"
    if not candidate.exists():
        return candidate

    version = 2
    while True:
        versioned = directory / f"{basename}_v{version}{extension}"
        if not versioned.exists():
            return versioned
        version += 1


def build_csv_filename(
    subject_id: Union[str, int],
    dataset_kind: str,
    directory: Path,
    timestamp: Optional[str] = None,
) -> Path:
    """
    Build a non-colliding CSV path for craving or Stroop data.

    Args:
        subject_id: Participant identifier (e.g. '005').
        dataset_kind: 'craving_ratings' or 'stroop_behavioral'.
        directory: Target task directory.
        timestamp: Optional pre-generated stamp; defaults to microsecond clock.
    """
    stamp = timestamp or _microsecond_timestamp()
    basename = f"subj_{_sanitize_part(subject_id)}_{dataset_kind}_{stamp}"
    return resolve_unique_filepath(directory, basename)


def lookup_scent_name(scent_number: Optional[Union[int, str]]) -> str:
    """Resolve scent_number to descriptive text; unknown IDs become 'Unknown'."""
    if scent_number is None or scent_number == "":
        return "Unknown"
    try:
        key = int(scent_number)
    except (TypeError, ValueError):
        return "Unknown"
    return SCENT_MAP.get(key, "Unknown")


def evaluate_stroop_correctness(
    congruence_condition: str,
    key_pressed: str,
) -> bool:
    """
    Default correctness rule for the cross-modal Stroop task.

    Congruent trials expect an affirmative response (yes/y).
    Incongruent trials expect a negative response (no/n).
    """
    key = str(key_pressed).strip().lower()
    condition = str(congruence_condition).strip().lower()
    if condition == "congruent":
        return key in AFFIRMATIVE_KEYS
    if condition == "incongruent":
        return key in NEGATIVE_KEYS
    return False


# ---------------------------------------------------------------------------
# LSL integration placeholder
# ---------------------------------------------------------------------------

def push_lsl_marker(label: str, perf_counter_time: Optional[float] = None) -> None:
    """
    Placeholder for LabRecorder / LSL marker outlet integration.

    Uncomment and wire to your project's LSLLabelStream when ready:

        from eeg_stimulus_project.lsl.labels import LSLLabelStream
        outlet = LSLLabelStream()
        outlet.push_label(label)

    For tighter xdf alignment, pass perf_counter_time to pylsl.local_clock()
    or store it alongside the marker string.
    """
    _ = (label, perf_counter_time)
    # LSLLabelStream().push_label(label)


# ---------------------------------------------------------------------------
# Craving ratings logger
# ---------------------------------------------------------------------------

class CravingRatingsLogger:
    """Thread-safe CSV logger for subjective craving ratings (19 per session)."""

    def __init__(
        self,
        subject_id: Union[str, int],
        test_number: Union[str, int],
        task_name: str,
        data_root: Optional[Union[str, Path]] = None,
        session_timestamp: Optional[str] = None,
    ) -> None:
        self.subject_id = str(subject_id)
        self.test_number = str(test_number)
        self.task_name = task_name
        self._lock = threading.Lock()
        self._row_count = 0
        self._session_start_perf = time.perf_counter()

        task_dir = build_session_directory(
            subject_id, test_number, task_name, data_root=data_root
        )
        self.filepath = build_csv_filename(
            subject_id,
            "craving_ratings",
            task_dir,
            timestamp=session_timestamp,
        )
        self.initialize_csv()

    def initialize_csv(self) -> Path:
        """Create the CSV file and write the header row."""
        with self._lock:
            with open(self.filepath, "w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=CRAVING_COLUMNS)
                writer.writeheader()
        return self.filepath

    def append_rating(
        self,
        block_index: int,
        realism_condition: str,
        sensory_condition: str,
        cue_type: str,
        craving_score: Union[int, float],
        *,
        push_marker: bool = True,
    ) -> Dict[str, Any]:
        """
        Append one craving rating row (thread-safe).

        Args:
            block_index: 0 for baseline, 1-18 after each experimental sub-block.
            realism_condition: e.g. '2D_Images', '3D_VR', 'Real_Objects'.
            sensory_condition: e.g. 'Unisensory_Visual'.
            cue_type: e.g. 'Alcohol' or 'Neutral'.
            craving_score: Participant keyboard / button response.
            push_marker: When True, call the LSL marker placeholder.
        """
        if not 0 <= int(block_index) <= 18:
            raise ValueError(f"block_index must be 0-18, got {block_index}")

        event_perf = time.perf_counter()
        row = {
            "timestamp": _event_timestamp(),
            "subject_id": self.subject_id,
            "test_number": self.test_number,
            "block_index": int(block_index),
            "realism_condition": realism_condition,
            "sensory_condition": sensory_condition,
            "cue_type": cue_type,
            "craving_score": craving_score,
        }

        with self._lock:
            with open(self.filepath, "a", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=CRAVING_COLUMNS)
                writer.writerow(row)
            self._row_count += 1

        if push_marker:
            marker = (
                f"craving_rating_subj{self.subject_id}_block{block_index}"
                f"_score{craving_score}"
            )
            push_lsl_marker(marker, perf_counter_time=event_perf)

        return row

    @property
    def ratings_logged(self) -> int:
        return self._row_count


# ---------------------------------------------------------------------------
# Stroop behavioral logger
# ---------------------------------------------------------------------------

class StroopBehavioralLogger:
    """Thread-safe CSV logger for cross-modal Stroop trial events."""

    def __init__(
        self,
        subject_id: Union[str, int],
        test_number: Union[str, int],
        task_name: str,
        data_root: Optional[Union[str, Path]] = None,
        session_timestamp: Optional[str] = None,
    ) -> None:
        self.subject_id = str(subject_id)
        self.test_number = str(test_number)
        self.task_name = task_name
        self._lock = threading.Lock()
        self._trial_count = 0
        self._session_start_perf = time.perf_counter()

        task_dir = build_session_directory(
            subject_id, test_number, task_name, data_root=data_root
        )
        self.filepath = build_csv_filename(
            subject_id,
            "stroop_behavioral",
            task_dir,
            timestamp=session_timestamp,
        )
        self.initialize_csv()

    def initialize_csv(self) -> Path:
        """Create the CSV file and write the header row."""
        with self._lock:
            with open(self.filepath, "w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=STROOP_COLUMNS)
                writer.writeheader()
        return self.filepath

    def append_trial(
        self,
        trial_number: int,
        image_shown: str,
        scent_number: Optional[Union[int, str]],
        has_tactile_trigger: bool,
        congruence_condition: str,
        key_pressed: str,
        reaction_time_ms: Union[int, float],
        *,
        is_correct: Optional[bool] = None,
        push_marker: bool = True,
    ) -> Dict[str, Any]:
        """
        Append one Stroop trial row (thread-safe).

        Args:
            trial_number: 1-based trial index within the task.
            image_shown: Visual cue identifier shown on screen.
            scent_number: Integer olfactory cue ID from the client rig.
            has_tactile_trigger: True if a tactile event fired for this trial.
            congruence_condition: 'Congruent' or 'Incongruent'.
            key_pressed: Raw keyboard capture (e.g. 'yes', 'no', 'y', 'n').
            reaction_time_ms: Stimulus onset to key press, in milliseconds.
            is_correct: Override auto-evaluation; computed when omitted.
            push_marker: When True, call the LSL marker placeholder.
        """
        event_perf = time.perf_counter()
        resolved_correct = (
            evaluate_stroop_correctness(congruence_condition, key_pressed)
            if is_correct is None
            else bool(is_correct)
        )

        row = {
            "timestamp": _event_timestamp(),
            "subject_id": self.subject_id,
            "test_number": self.test_number,
            "trial_number": int(trial_number),
            "image_shown": image_shown,
            "scent_number": scent_number if scent_number is not None else "",
            "scent_name": lookup_scent_name(scent_number),
            "has_tactile_trigger": bool(has_tactile_trigger),
            "congruence_condition": congruence_condition,
            "key_pressed": key_pressed,
            "reaction_time_ms": reaction_time_ms,
            "is_correct": resolved_correct,
        }

        with self._lock:
            with open(self.filepath, "a", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=STROOP_COLUMNS)
                writer.writerow(row)
            self._trial_count += 1

        if push_marker:
            marker = (
                f"stroop_trial{trial_number}_{congruence_condition}"
                f"_img{image_shown}_key{key_pressed}"
            )
            push_lsl_marker(marker, perf_counter_time=event_perf)

        return row

    @property
    def trials_logged(self) -> int:
        return self._trial_count


# ---------------------------------------------------------------------------
# Session facade
# ---------------------------------------------------------------------------

class StudySessionLogger:
    """
    Convenience wrapper that opens both CSV files for one participant session.

    Both loggers share the same session timestamp so craving and Stroop files
    from one run are easy to pair during analysis.
    """

    def __init__(
        self,
        subject_id: Union[str, int],
        test_number: Union[str, int],
        craving_task_name: str = "session_craving",
        stroop_task_name: str = "Stroop Multisensory Alcohol (Visual & Olfactory)",
        data_root: Optional[Union[str, Path]] = None,
    ) -> None:
        self.session_timestamp = _microsecond_timestamp()
        self.craving = CravingRatingsLogger(
            subject_id,
            test_number,
            craving_task_name,
            data_root=data_root,
            session_timestamp=self.session_timestamp,
        )
        self.stroop = StroopBehavioralLogger(
            subject_id,
            test_number,
            stroop_task_name,
            data_root=data_root,
            session_timestamp=self.session_timestamp,
        )

    def summary(self) -> Dict[str, str]:
        return {
            "session_timestamp": self.session_timestamp,
            "craving_csv": str(self.craving.filepath),
            "stroop_csv": str(self.stroop.filepath),
        }


# ---------------------------------------------------------------------------
# Demonstration
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    SUBJECT_ID = "005"
    TEST_NUMBER = "2"
    DEMO_DATA_ROOT = DEFAULT_DATA_ROOT

    print("=== Multisensory Study Data Logger — mock session ===\n")

    session = StudySessionLogger(
        subject_id=SUBJECT_ID,
        test_number=TEST_NUMBER,
        craving_task_name="session_craving",
        stroop_task_name="Stroop Multisensory Alcohol (Visual & Olfactory)",
        data_root=DEMO_DATA_ROOT,
    )

    paths = session.summary()
    print("Session files:")
    for key, value in paths.items():
        print(f"  {key}: {value}")
    print()

    # Baseline craving (block_index = 0)
    baseline = session.craving.append_rating(
        block_index=0,
        realism_condition="2D_Images",
        sensory_condition="Unisensory_Visual",
        cue_type="Neutral",
        craving_score=2,
    )
    print(f"Logged baseline craving: {baseline}")

    # Simulate one post-block craving after sub-block 1
    post_block = session.craving.append_rating(
        block_index=1,
        realism_condition="3D_VR",
        sensory_condition="Multisensory_Visuo_Olfactory",
        cue_type="Alcohol",
        craving_score=5,
    )
    print(f"Logged post-block craving: {post_block}")

    # Simulate a Stroop trial with stimulus onset captured via perf_counter
    stimulus_onset_perf = time.perf_counter()
    time.sleep(0.35)  # stand-in for participant reaction
    reaction_time_ms = round((time.perf_counter() - stimulus_onset_perf) * 1000, 1)

    trial = session.stroop.append_trial(
        trial_number=1,
        image_shown="beer_mug_01.png",
        scent_number=1,
        has_tactile_trigger=False,
        congruence_condition="Congruent",
        key_pressed="yes",
        reaction_time_ms=reaction_time_ms,
    )
    print(f"Logged Stroop trial: {trial}")

    # Demonstrate overwrite protection: same timestamp basename would collide
    task_dir = build_session_directory(
        SUBJECT_ID,
        TEST_NUMBER,
        "overwrite_demo",
        data_root=DEMO_DATA_ROOT,
    )
    fixed_stamp = "20260101_120000_000000"
    first = build_csv_filename(SUBJECT_ID, "craving_ratings", task_dir, timestamp=fixed_stamp)
    first.touch()
    second = build_csv_filename(SUBJECT_ID, "craving_ratings", task_dir, timestamp=fixed_stamp)
    print(f"\nOverwrite protection demo:")
    print(f"  existing file: {first.name}")
    print(f"  next unique:   {second.name}")

    print(f"\nDone — craving rows: {session.craving.ratings_logged}, "
          f"Stroop trials: {session.stroop.trials_logged}")
