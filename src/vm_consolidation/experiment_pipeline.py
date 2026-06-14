from pathlib import Path
from vm_selection import random_choice_policy, minimization_of_migrations
from consolidation_pipeline import run_consolidation
from preprocessing import con


EXPERIMENTS = [
    ("MM_CPU_BFD_0_30", minimization_of_migrations, "cpu_bfd"),
    ("RC_CPU_BFD_0_30", random_choice_policy, "cpu_bfd"),

    ("MM_PBFD_0_30", minimization_of_migrations, "power_bfd"),
    ("RC_PBFD_0_30", random_choice_policy, "power_bfd"),
]


timestamps = con.execute("""
        SELECT DISTINCT timestamp AT TIME ZONE 'UTC'
        FROM vm_final
        ORDER BY timestamp
    """).fetchall()

ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = ROOT / "src/sql"
DATA_DIR = ROOT / "datasets/cloud_energy_consumption"

# TODO: current experiment:  0/30 with CPU both MM and RC
for name, selection, placement in EXPERIMENTS:

    print(f"Running {name}")

    run_consolidation(
        timestamps=timestamps,
        selection_policy=selection,
        placement_policy=placement,
        upper_threshold=30,
        lower_threshold=0,
        name=name,
        con=con
    )