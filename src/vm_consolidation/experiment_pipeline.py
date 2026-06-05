from pathlib import Path
from vm_selection import random_choice_policy, minimization_of_migrations
from consolidation_pipeline import run_consolidation
from preprocessing import con


EXPERIMENTS = [
    #("MM_PBFD", minimization_of_migrations, "power_bfd"),
    #("RC_PBFD", random_choice_policy, "power_bfd"),
    #("MM_BFD", minimization_of_migrations, "cpu_bfd"),
    #("RC_BFD", random_choice_policy, "cpu_bfd"),
    #("MM_PBFD_20_NEW", minimization_of_migrations, "power_bfd"),
    #("RC_PBFD_20", random_choice_policy, "power_bfd"),
    #("MM_CPU_BFD_20_NEW", minimization_of_migrations, "cpu_bfd"),
    #("RC_CPU_BFD_20", random_choice_policy, "cpu_bfd"),
    #("GROUP_ALLOCATION_P_PFD", random_choice_policy, "power_bfd"),
    #("MM_BFD", minimization_of_migrations, "cpu_bfd"),
    #("RC_BFD", random_choice_policy, "cpu_bfd"),
    #("MM_BFD_CPU", minimization_of_migrations, "cpu_bfd"),
    #("RC_BFD_CPU", random_choice_policy, "cpu_bfd")
    ("MM_PBFD_10_30_NO_CPU", minimization_of_migrations, "power_bfd"),
    #("MM_PBFD_0_30_NO_CPU", minimization_of_migrations, "power_bfd"),
    #("RC_PBFD_0_30_NO_CPU", random_choice_policy, "power_bfd"),
]


timestamps = con.execute("""
        SELECT DISTINCT timestamp AT TIME ZONE 'UTC'
        FROM vm_final
        ORDER BY timestamp
    """).fetchall()

ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = ROOT / "src/sql"
DATA_DIR = ROOT / "datasets/cloud_energy_consumption"

# TODO: current experiment # 30/10 no CPU
for name, selection, placement in EXPERIMENTS:

    print(f"Running {name}")

    run_consolidation(
        timestamps=timestamps,
        selection_policy=selection,
        placement_policy=placement,
        upper_threshold=30,
        lower_threshold=10,
        name=name,
        con=con
    )