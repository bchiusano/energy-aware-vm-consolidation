from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from consolidation_pipeline import run_consolidation
from preprocessing import con
from vm_selection import minimization_of_migrations, random_choice_policy


@dataclass(frozen=True)
class ExperimentConfig:
    name: str
    selection_policy: Callable
    placement_policy: str
    lower_threshold: int
    upper_threshold: int
    selection_label: str
    placement_label: str


SELECTION_POLICIES = {
    "MM": minimization_of_migrations,
    #"RC": random_choice_policy,
}

PLACEMENT_POLICIES = {
    #"CPU_BFD": "cpu_bfd",
    "PBFD": "power_bfd",
}

LOWER_THRESHOLDS = range(10, 15, 5)
UPPER_THRESHOLDS = range(25, 31, 5)
MIN_THRESHOLD_GAP = 15
EXPERIMENT_SUFFIX = "grid"


def build_threshold_grid():
    return [
        (lower, upper)
        for lower in LOWER_THRESHOLDS
        for upper in UPPER_THRESHOLDS
        if upper - lower >= MIN_THRESHOLD_GAP
    ]


def build_experiments():
    return [
        ExperimentConfig(
            name=(
                f"{selection_label}_{placement_label}_"
                f"{lower}_{upper}_{EXPERIMENT_SUFFIX}"
            ),
            selection_policy=selection_policy,
            placement_policy=placement_policy,
            lower_threshold=lower,
            upper_threshold=upper,
            selection_label=selection_label,
            placement_label=placement_label,
        )
        for selection_label, selection_policy in SELECTION_POLICIES.items()
        for placement_label, placement_policy in PLACEMENT_POLICIES.items()
        for lower, upper in build_threshold_grid()
    ]


def load_timestamps():
    return con.execute("""
        SELECT DISTINCT timestamp AT TIME ZONE 'UTC'
        FROM vm_final
        ORDER BY timestamp
    """).fetchall()


def run_experiment(experiment, timestamps):
    print(f"Running {experiment.name}")

    run_consolidation(
        timestamps=timestamps,
        selection_policy=experiment.selection_policy,
        placement_policy=experiment.placement_policy,
        upper_threshold=experiment.upper_threshold,
        lower_threshold=experiment.lower_threshold,
        name=experiment.name,
        con=con,
    )


if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parents[2]
    SQL_DIR = ROOT / "src/sql"
    DATA_DIR = ROOT / "datasets/cloud_energy_consumption"

    experiments = build_experiments()
    timestamps = load_timestamps()

    print(f"Generated {len(experiments)} experiments")

    for experiment in experiments:
        run_experiment(experiment, timestamps)
