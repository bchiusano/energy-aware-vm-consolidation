from pathlib import Path
from vm_selection import random_choice_policy, minimization_of_migrations
from consolidation_pipeline import run_consolidation
from preprocessing import con

'''
EXPERIMENTS = [
    ("MM_PBFD", minimization_of_migrations, "power_bfd"),
    ("RC_PBFD", random_choice_policy, "power_bfd"),
    ("MM_BFD", minimization_of_migrations, "cpu_bfd"),
    ("RC_BFD", random_choice_policy, "cpu_bfd"),
    ("MM_PBFD_20", minimization_of_migrations, "power_bfd", 20),
    ("RC_PBFD_20", random_choice_policy, "power_bfd", 20),
    ("MM_BFD_20", minimization_of_migrations, "cpu_bfd", 20),
    ("RC_BFD_20", random_choice_policy, "cpu_bfd", 20)
]
'''

EXPERIMENTS = [
    ("GROUP_ALLOCATION_P_PFD", random_choice_policy, "power_bfd"),
    #("MM_BFD", minimization_of_migrations, "cpu_bfd"),
    #("RC_BFD", random_choice_policy, "cpu_bfd"),
]

timestamps = con.execute("""
        SELECT DISTINCT timestamp AT TIME ZONE 'UTC'
        FROM vm_final
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
        upper_threshold=90,
        #lower_threshold=lower_threshold,
        name=name,
        con=con
    )