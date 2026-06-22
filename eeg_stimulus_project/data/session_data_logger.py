"""
Session data logger for multisensory alcohol cue-reactivity experiments.

Participants complete Passive Viewing and Cross-Modal Stroop on separate days.
The experiment code constructs one SessionDataLogger per run and calls exactly
one initializer:

    logger.init_craving_csv()   # Passive_Viewing day
    logger.init_stroop_csv()    # Cross_Modal_Stroop day

Directory layout:
    saved_data/subject_<subject_id>/test_<test_number>/<task_name>/
        subj_<subject_id>_craving_ratings_<YYYYMMDD_HHMMSS_ffffff>.csv
        subj_<subject_id>_stroop_behavioral_<YYYYMMDD_HHMMSS_ffffff>.csv

Filenames never overwrite prior recordings: microsecond timestamps plus _v2,
_v3, ... suffixes when a collision occurs.

Calling init_craving_csv() or init_stroop_csv() again on the same logger
instance opens a fresh CSV (new timestamp / version suffix) and resets that
stream's row counter so subsequent hardware runs never append to a prior file.
"""

from __future__ import annotations

import csv
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCENT_MAP: Dict[int, Dict[str, str]] = {
    1: {"name": "Beer", "type": "Alcohol"},
    2: {"name": "Wine", "type": "Alcohol"},
    3: {"name": "Whiskey", "type": "Alcohol"},
    4: {"name": "Water", "type": "Neutral"},
    5: {"name": "OJ", "type": "Neutral"},
    0: {"name": "None", "type": "Neutral"},
}

VALID_TASK_NAMES = frozenset({"Passive_Viewing", "Cross_Modal_Stroop"})
VALID_REALISM_CONDITIONS = frozenset({"Images", "VR", "Real_Objects"})

APPARATUS_REALISM_MAP: Dict[str, str] = {
    "Display": "Images",
    "VR": "VR",
    "Turntable": "Real_Objects",
}

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DATA_ROOT = _PROJECT_ROOT / "eeg_stimulus_project" / "saved_data"

# apparatus and realism_condition are columns 4 and 5 in both schemas.
CRAVING_COLUMNS: List[str] = [
    "timestamp",
    "subject_id",
    "test_number",
    "apparatus",
    "realism_condition",
    "block_index",
    "sensory_condition",
    "cue_type",
    "craving_score",
]

STROOP_COLUMNS: List[str] = [
    "timestamp",
    "subject_id",
    "test_number",
    "apparatus",
    "realism_condition",
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

TaskName = Literal["Passive_Viewing", "Cross_Modal_Stroop"]
RealismCondition = Literal["Images", "VR", "Real_Objects"]


# ---------------------------------------------------------------------------
# Path and filename helpers
# ---------------------------------------------------------------------------

def _sanitize_part(value: Union[str, int]) -> str:
    """Return a filesystem-safe token for subject/test identifiers."""
    text = str(value).strip()
    safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in text)
    return safe.strip("._-") or "unknown"


def _microsecond_timestamp() -> str:
    """Wall-clock stamp for unique filenames: YYYYMMDD_HHMMSS_ffffff."""
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def _event_timestamp() -> str:
    """ISO-8601 event timestamp with millisecond precision for CSV rows."""
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]


def resolve_realism_condition(apparatus: str) -> str:
    """Map apparatus selection to the canonical realism_condition CSV value."""
    realism = APPARATUS_REALISM_MAP.get(apparatus)
    if realism is None:
        raise ValueError(
            f"apparatus must be one of {sorted(APPARATUS_REALISM_MAP)}, got {apparatus!r}"
        )
    return realism


def build_session_directory(
    subject_id: Union[str, int],
    test_number: Union[str, int],
    task_name: str,
    data_root: Optional[Union[str, Path]] = None,
) -> Path:
    """
    Create and return:
        saved_data/subject_<id>/test_<n>/<task_name>/
    """
    root = Path(data_root) if data_root is not None else DEFAULT_DATA_ROOT
    task_dir = (
        root
        / f"subject_{_sanitize_part(subject_id)}"
        / f"test_{_sanitize_part(test_number)}"
        / task_name
    )
    task_dir.mkdir(parents=True, exist_ok=True)
    return task_dir


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


def build_csv_filepath(
    subject_id: Union[str, int],
    dataset_stem: str,
    directory: Path,
    timestamp: Optional[str] = None,
) -> Path:
    """
    Build a non-colliding CSV path.

    Args:
        dataset_stem: 'craving_ratings' or 'stroop_behavioral'.
    """
    stamp = timestamp or _microsecond_timestamp()
    basename = f"subj_{_sanitize_part(subject_id)}_{dataset_stem}_{stamp}"
    return resolve_unique_filepath(directory, basename)


def lookup_scent_entry(scent_number: Optional[Union[int, str]]) -> Dict[str, str]:
    """Resolve scent_number to name/type metadata; unknown IDs use 'Unknown'."""
    if scent_number is None or scent_number == "":
        return {"name": "Unknown", "type": "Unknown"}
    try:
        key = int(scent_number)
    except (TypeError, ValueError):
        return {"name": "Unknown", "type": "Unknown"}
    return SCENT_MAP.get(key, {"name": "Unknown", "type": "Unknown"})


def lookup_scent_name(scent_number: Optional[Union[int, str]]) -> str:
    return lookup_scent_entry(scent_number)["name"]


def lookup_scent_type(scent_number: Optional[Union[int, str]]) -> str:
    return lookup_scent_entry(scent_number)["type"]


def determine_congruence_condition(
    image_type: str,
    scent_number: Optional[Union[int, str]],
) -> str:
    """Congruent when image_type matches the scent SCENT_MAP type."""
    scent_type = lookup_scent_type(scent_number)
    if image_type == scent_type:
        return "Congruent"
    return "Incongruent"


def _evaluate_stroop_correctness(key_pressed: str, expected_key: str) -> bool:
    """True when key_pressed matches expected_key (case-insensitive)."""
    return key_pressed.strip().lower() == expected_key.strip().lower()


def push_lsl_marker(label: str, perf_counter_time: Optional[float] = None) -> None:
    """
    Placeholder for LabRecorder / LSL marker outlet integration.

        from eeg_stimulus_project.lsl.labels import LSLLabelStream
        LSLLabelStream().push_label(label)
    """
    _ = (label, perf_counter_time)
    # LSLLabelStream().push_label(label)


# ---------------------------------------------------------------------------
# Session logger
# ---------------------------------------------------------------------------

class SessionDataLogger:
    """
    Single-task session logger. Initialize exactly one CSV per instance:

        logger = SessionDataLogger(
            subject_id="005",
            test_number="1",
            task_name="Passive_Viewing",
            apparatus="Display",
            realism_condition="Images",
        )
        logger.init_craving_csv()
        logger.append_craving_rating(...)
    """

    def __init__(
        self,
        subject_id: Union[str, int],
        test_number: Union[str, int],
        task_name: TaskName,
        apparatus: str,
        realism_condition: RealismCondition,
        data_root: Optional[Union[str, Path]] = None,
    ) -> None:
        if task_name not in VALID_TASK_NAMES:
            raise ValueError(
                f"task_name must be one of {sorted(VALID_TASK_NAMES)}, got {task_name!r}"
            )
        if realism_condition not in VALID_REALISM_CONDITIONS:
            raise ValueError(
                f"realism_condition must be one of {sorted(VALID_REALISM_CONDITIONS)}, "
                f"got {realism_condition!r}"
            )

        self.subject_id = str(subject_id)
        self.test_number = str(test_number)
        self.task_name = task_name
        self.apparatus = apparatus
        self.realism_condition = realism_condition
        self.data_root = data_root

        self.task_dir = build_session_directory(
            self.subject_id,
            self.test_number,
            self.task_name,
            data_root=self.data_root,
        )

        self._lock = threading.Lock()
        self._craving_filepath: Optional[Path] = None
        self._stroop_filepath: Optional[Path] = None
        self._craving_rows = 0
        self._stroop_trials = 0

    # ------------------------------------------------------------------
    # CSV initialization (call exactly one per session)
    # ------------------------------------------------------------------

    def init_craving_csv(self, timestamp: Optional[str] = None) -> Path:
        """
        Create a craving-ratings CSV header for a Passive_Viewing session.

        Safe to call multiple times on the same logger: each call resolves a
        brand-new filepath via resolve_unique_filepath() and resets the craving
        row counter for that new file.

        Raises:
            ValueError: If task_name is not Passive_Viewing.
        """
        if self.task_name != "Passive_Viewing":
            raise ValueError(
                "init_craving_csv() requires task_name='Passive_Viewing', "
                f"got {self.task_name!r}"
            )

        filepath = build_csv_filepath(
            self.subject_id,
            "craving_ratings",
            self.task_dir,
            timestamp=timestamp,
        )
        with self._lock:
            with open(filepath, "w", newline="", encoding="utf-8") as handle:
                csv.DictWriter(handle, fieldnames=CRAVING_COLUMNS).writeheader()
            self._craving_filepath = filepath
            self._craving_rows = 0

        return filepath

    def init_stroop_csv(self, timestamp: Optional[str] = None) -> Path:
        """
        Create a Stroop behavioral CSV header for a Cross_Modal_Stroop session.

        Safe to call multiple times on the same logger: each call resolves a
        brand-new filepath via resolve_unique_filepath() and resets the Stroop
        trial counter for that new file.

        Raises:
            ValueError: If task_name is not Cross_Modal_Stroop.
        """
        if self.task_name != "Cross_Modal_Stroop":
            raise ValueError(
                "init_stroop_csv() requires task_name='Cross_Modal_Stroop', "
                f"got {self.task_name!r}"
            )

        filepath = build_csv_filepath(
            self.subject_id,
            "stroop_behavioral",
            self.task_dir,
            timestamp=timestamp,
        )
        with self._lock:
            with open(filepath, "w", newline="", encoding="utf-8") as handle:
                csv.DictWriter(handle, fieldnames=STROOP_COLUMNS).writeheader()
            self._stroop_filepath = filepath
            self._stroop_trials = 0

        return filepath

    # ------------------------------------------------------------------
    # Append methods
    # ------------------------------------------------------------------

    def append_craving_rating(
        self,
        block_index: int,
        sensory_condition: str,
        cue_type: str,
        craving_score: Union[int, float],
        *,
        push_marker: bool = True,
    ) -> Dict[str, Any]:
        """
        Append one craving rating (thread-safe).

        Args:
            block_index: 0 for baseline, 1-18 after each experimental sub-block.
            sensory_condition: e.g. 'Unisensory_Visual'.
            cue_type: 'Alcohol' or 'Neutral'.
            craving_score: Participant response on the 1-7 scale.
        """
        if self._craving_filepath is None:
            raise RuntimeError("Call init_craving_csv() before append_craving_rating().")
        if not 0 <= int(block_index) <= 18:
            raise ValueError(f"block_index must be 0-18, got {block_index}")

        event_perf = time.perf_counter()
        row = {
            "timestamp": _event_timestamp(),
            "subject_id": self.subject_id,
            "test_number": self.test_number,
            "apparatus": self.apparatus,
            "realism_condition": self.realism_condition,
            "block_index": int(block_index),
            "sensory_condition": sensory_condition,
            "cue_type": cue_type,
            "craving_score": craving_score,
        }

        with self._lock:
            with open(self._craving_filepath, "a", newline="", encoding="utf-8") as handle:
                csv.DictWriter(handle, fieldnames=CRAVING_COLUMNS).writerow(row)
            self._craving_rows += 1

        if push_marker:
            marker = (
                f"craving_rating_subj{self.subject_id}_block{block_index}"
                f"_score{craving_score}"
            )
            push_lsl_marker(marker, perf_counter_time=event_perf)

        return row

    def append_stroop_trial(
        self,
        trial_number: int,
        image_shown: str,
        image_type: str,
        scent_number: Optional[Union[int, str]],
        has_tactile_trigger: bool,
        key_pressed: str,
        expected_key: str,
        reaction_time_ms: Union[int, float],
        *,
        push_marker: bool = True,
    ) -> Dict[str, Any]:
        """
        Append one Stroop trial (thread-safe).

        Congruence is derived automatically from image_type and scent_number.
        Accuracy is determined by comparing key_pressed to expected_key, which
        the display layer supplies based on the active task instructions.
        """
        if self._stroop_filepath is None:
            raise RuntimeError("Call init_stroop_csv() before append_stroop_trial().")

        event_perf = time.perf_counter()
        congruence_condition = determine_congruence_condition(image_type, scent_number)
        resolved_correct = _evaluate_stroop_correctness(key_pressed, expected_key)

        row = {
            "timestamp": _event_timestamp(),
            "subject_id": self.subject_id,
            "test_number": self.test_number,
            "apparatus": self.apparatus,
            "realism_condition": self.realism_condition,
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
            with open(self._stroop_filepath, "a", newline="", encoding="utf-8") as handle:
                csv.DictWriter(handle, fieldnames=STROOP_COLUMNS).writerow(row)
            self._stroop_trials += 1

        if push_marker:
            marker = (
                f"stroop_trial{trial_number}_{congruence_condition}"
                f"_img{image_shown}_key{key_pressed}"
            )
            push_lsl_marker(marker, perf_counter_time=event_perf)

        return row

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def craving_filepath(self) -> Optional[Path]:
        return self._craving_filepath

    @property
    def stroop_filepath(self) -> Optional[Path]:
        return self._stroop_filepath

    @property
    def craving_rows_logged(self) -> int:
        return self._craving_rows

    @property
    def stroop_trials_logged(self) -> int:
        return self._stroop_trials


# ---------------------------------------------------------------------------
# Demonstration — separate day workflows
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    SUBJECT_ID = "005"
    DEMO_DATA_ROOT = DEFAULT_DATA_ROOT

    print("=== Passive Viewing day (craving ratings only) ===\n")

    passive_logger = SessionDataLogger(
        subject_id=SUBJECT_ID,
        test_number="1",
        task_name="Passive_Viewing",
        apparatus="Display",
        realism_condition="Images",
        data_root=DEMO_DATA_ROOT,
    )
    craving_path = passive_logger.init_craving_csv()
    print(f"Craving CSV: {craving_path}")

    baseline = passive_logger.append_craving_rating(
        block_index=0,
        sensory_condition="Unisensory_Visual",
        cue_type="Neutral",
        craving_score=2,
    )
    print(f"Baseline rating: {baseline}")

    post_block = passive_logger.append_craving_rating(
        block_index=1,
        sensory_condition="Multisensory_Visuo_Olfactory",
        cue_type="Alcohol",
        craving_score=5,
    )
    print(f"Post-block rating: {post_block}\n")

    print("=== Cross-Modal Stroop day (behavioral trials only) ===\n")

    stroop_logger = SessionDataLogger(
        subject_id=SUBJECT_ID,
        test_number="2",
        task_name="Cross_Modal_Stroop",
        apparatus="Turntable",
        realism_condition="Real_Objects",
        data_root=DEMO_DATA_ROOT,
    )
    stroop_path = stroop_logger.init_stroop_csv()
    print(f"Stroop CSV: {stroop_path}")

    stimulus_onset = time.perf_counter()
    time.sleep(0.35)
    reaction_ms = round((time.perf_counter() - stimulus_onset) * 1000, 1)

    congruent_trial = stroop_logger.append_stroop_trial(
        trial_number=1,
        image_shown="beer_mug_01.png",
        image_type="Alcohol",
        scent_number=1,
        has_tactile_trigger=False,
        key_pressed="yes",
        expected_key="yes",
        reaction_time_ms=reaction_ms,
    )
    print(f"Congruent trial: {congruent_trial}")

    incongruent_trial = stroop_logger.append_stroop_trial(
        trial_number=2,
        image_shown="beer_mug_02.png",
        image_type="Alcohol",
        scent_number=4,
        has_tactile_trigger=False,
        key_pressed="no",
        expected_key="yes",
        reaction_time_ms=412.0,
    )
    print(f"Incongruent trial: {incongruent_trial}")

    # Re-init opens a separate execution file on the same logger instance
    second_stroop_path = stroop_logger.init_stroop_csv()
    print(f"\nRe-init Stroop CSV: {second_stroop_path}")
    print(f"  distinct from first: {second_stroop_path != stroop_path}")

    # Overwrite protection demo
    fixed_stamp = "20260101_120000_000000"
    demo_dir = build_session_directory(SUBJECT_ID, "1", "Passive_Viewing", DEMO_DATA_ROOT)
    first = build_csv_filepath(SUBJECT_ID, "craving_ratings", demo_dir, timestamp=fixed_stamp)
    first.touch()
    second = build_csv_filepath(SUBJECT_ID, "craving_ratings", demo_dir, timestamp=fixed_stamp)
    print(f"\nOverwrite protection:")
    print(f"  existing: {first.name}")
    print(f"  next:     {second.name}")

    print(
        f"\nDone — craving rows: {passive_logger.craving_rows_logged}, "
        f"Stroop trials: {stroop_logger.stroop_trials_logged}"
    )
