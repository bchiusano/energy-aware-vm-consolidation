from pathlib import Path
from vm_selection import random_choice_policy, minimization_of_migrations
from consolidation_pipeline import run_consolidation
from preprocessing import con


EXPERIMENTS = [
    ("MM_CPU_BFD_5_25_again", minimization_of_migrations, "cpu_bfd"),
    #("RC_CPU_BFD_5_25", random_choice_policy, "cpu_bfd"),

    #("MM_PBFD_5_25", minimization_of_migrations, "power_bfd"),
    #("RC_PBFD_5_25_again", random_choice_policy, "power_bfd"),
]


timestamps = con.execute("""
        SELECT DISTINCT timestamp AT TIME ZONE 'UTC'
        FROM vm_final
        WHERE timestamp >= '2025-01-01 00:00:00 UTC'
        AND timestamp < '2025-02-01 00:00:00 UTC'
        ORDER BY timestamp                 
    """).fetchall()

ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = ROOT / "src/sql"
DATA_DIR = ROOT / "datasets/cloud_energy_consumption"

for name, selection, placement in EXPERIMENTS:

    print(f"Running {name}")

    run_consolidation(
        timestamps=timestamps,
        selection_policy=selection,
        placement_policy=placement,
        upper_threshold=25,
        lower_threshold=5,
        name=name,
        con=con
    )