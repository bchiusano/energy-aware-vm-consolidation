import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import duckdb as ddb

ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = ROOT / "results/"
DATA_DIR = ROOT / "datasets/cloud_energy_consumption/processed"


def get_simulated_power(experiment, power_name="total_power"):

    simulated_power = con.execute(f"""
        SELECT
            timestamp,
            SUM(simulated_power) AS {power_name}
        FROM {experiment}
        GROUP BY timestamp
        ORDER BY timestamp
    """).df()

    return simulated_power


def get_total_power_consumption(experiment):

    con.query(f"""
        SELECT 
            'Original' as scenario,
            SUM(simulated_power) as total_power_w,
            ROUND(AVG(simulated_power), 2) as avg_power_w,
            COUNT(*) as host_count,
            SUM(simulated_power) * 0.05 / 1000000 as total_energy_mwh
        FROM baseline

        UNION ALL

        SELECT 
            'Simulated' as scenario,
            SUM(simulated_power) as total_power_w,
            ROUND(AVG(simulated_power), 2) as avg_power_w,
            COUNT(*) as host_count,
            SUM(simulated_power) * 0.05 / 1000000 as total_energy_mwh
        FROM {experiment}
    """).show()

if __name__ == "__main__":

    con = ddb.connect(database=':memory:')

    # Baseline
    con.execute(f"""CREATE OR REPLACE VIEW baseline AS SELECT * FROM read_parquet('{DATA_DIR}/node_snapshot.parquet')""")

    # MM + BFD
    #con.execute(f"""CREATE OR REPLACE VIEW mm_bfd AS SELECT * FROM read_parquet('{RESULTS_DIR}/MM_BFD_CPU/simulated_MM_BFD_CPU.parquet')""")
    # RC + BFD
    #con.execute(f"""CREATE OR REPLACE VIEW rc_bfd AS SELECT * FROM read_parquet('{RESULTS_DIR}/RC_BFD_CPU/simulated_RC_BFD_CPU.parquet')""")


    # MM + PBFD
    #con.execute(f"""CREATE OR REPLACE VIEW mm_pbfd AS SELECT * FROM read_parquet('{RESULTS_DIR}/MM_PBFD/simulated_MM_PBFD.parquet')""")
    # RC + PBFD
    #con.execute(f"""CREATE OR REPLACE VIEW rc_pbfd AS SELECT * FROM read_parquet('{RESULTS_DIR}/RC_PBFD/simulated_RC_PBFD.parquet')""")

    #### 20 threshold ######
    # MM + BFD
    #con.execute(f"""CREATE OR REPLACE VIEW mm_bfd_20 AS SELECT * FROM read_parquet('{RESULTS_DIR}/MM_CPU_BFD_20/simulated_MM_CPU_BFD_20.parquet')""")
    # RC + BFD
    #con.execute(f"""CREATE OR REPLACE VIEW rc_bfd_20 AS SELECT * FROM read_parquet('{RESULTS_DIR}/RC_CPU_BFD_20/simulated_RC_CPU_BFD_20.parquet')""")

    # MM + PBFD
    #con.execute(f"""CREATE OR REPLACE VIEW mm_pbfd_20 AS SELECT * FROM read_parquet('{RESULTS_DIR}/MM_PBFD_20/simulated_MM_PBFD_20.parquet')""")
    # RC + PBFD
    #con.execute(f"""CREATE OR REPLACE VIEW rc_pbfd_20 AS SELECT * FROM read_parquet('{RESULTS_DIR}/RC_PBFD_20/simulated_RC_PBFD_20.parquet')""")


    # calculations
    print("MM + CPU")
    get_total_power_consumption("mm_bfd")
    print("RC + CPU")
    get_total_power_consumption("rc_bfd")
    print("MM + POWER")
    get_total_power_consumption("mm_pbfd")
    print("RC + POWER")
    get_total_power_consumption("rc_pbfd")

    print("MM + CPU + 20")
    get_total_power_consumption("mm_bfd_20")
    print("RC + CPU + 20")
    get_total_power_consumption("rc_bfd_20")
    print("MM + POWER + 20")
    get_total_power_consumption("mm_pbfd_20")
    print("RC + POWER + 20")
    get_total_power_consumption("rc_pbfd_20")

    baseline_power = con.execute("""
        SELECT
            timestamp,
            SUM(ipmi_system_power_watts) AS baseline_power
        FROM baseline
        GROUP BY timestamp
        ORDER BY timestamp
    """).df()

    # Baseline 2 where I set simulated power to 0 for empty hosts - this is to check if the power saving is due to empty hosts or not
    baseline_2_power = con.execute("""
        SELECT
            timestamp,
            SUM(
                CASE
                    WHEN vm_power_allocated > 0 THEN simulated_power
                    ELSE 0
                END
            ) AS baseline_2_power
        FROM baseline
        GROUP BY timestamp
        ORDER BY timestamp
    """).df()

    print("Total power consumption for baseline 2")
    con.query("""
        SELECT 
            'Original' as scenario,

            SUM(
                CASE
                    WHEN vm_power_allocated > 0
                    THEN simulated_power
                    ELSE 0
                END
            ) as total_power_w,

            AVG(
                CASE
                    WHEN vm_power_allocated > 0
                    THEN simulated_power
                    ELSE 0
                END
            ) as avg_power_w,

            COUNT(*) as host_count

        FROM baseline
    """).show()

    # Experiments simulated power
    mm_bfd_power = get_simulated_power("mm_bfd", "mm_bfd_power")
    rc_bfd_power = get_simulated_power("rc_bfd", "rc_bfd_power")

    mm_pbfd_power = get_simulated_power("mm_pbfd", "mm_pbfd_power")
    rc_pbfd_power = get_simulated_power("rc_pbfd", "rc_pbfd_power")

    mm_bfd_20_power = get_simulated_power("mm_bfd_20", "mm_bfd_20_power")
    rc_bfd_20_power = get_simulated_power("rc_bfd_20", "rc_bfd_20_power")

    mm_pbfd_20_power = get_simulated_power("mm_pbfd_20", "mm_pbfd_20_power")
    rc_pbfd_20_power = get_simulated_power("rc_pbfd_20", "rc_pbfd_20_power")

    

    # Combine into a single DataFrame for plotting
    power_df = (
        baseline_power
        .merge(baseline_2_power, on="timestamp")
        .merge(mm_bfd_power, on="timestamp")
        .merge(rc_bfd_power, on="timestamp")
        .merge(mm_pbfd_power, on="timestamp")
        .merge(rc_pbfd_power, on="timestamp")
        .merge(mm_bfd_20_power, on="timestamp")
        .merge(rc_bfd_20_power, on="timestamp")
        .merge(mm_pbfd_20_power, on="timestamp")
        .merge(rc_pbfd_20_power, on="timestamp")
    )

    day_df = power_df[
        (power_df["timestamp"] >= "2025-02-01") &
        (power_df["timestamp"] < "2025-02-08")
    ]

    #day_df = power_df[
    #    (power_df["timestamp"] >= "2025-04-01") &
    #    (power_df["timestamp"] < "2025-04-02")
    #]

    fig, axes = plt.subplots(
        2, 1,              # 2 rows, 1 column
        figsize=(12, 8),
        sharex=True
    )

    # -------------------------
    # MM comparison
    # -------------------------
    #axes[0].plot(
    #    day_df["timestamp"],
    #    day_df["baseline_power"],
    #    label="Baseline",
    #    linewidth=2
    #)

    axes[0].plot(
        day_df["timestamp"],
        day_df["baseline_2_power"],
        label="Baseline 2",
        linewidth=2
    )
    
    axes[0].plot(
        day_df["timestamp"],
        day_df["mm_bfd_power"],
        label="MM + CPU",
        linewidth=2
    )

    axes[0].plot(
        day_df["timestamp"],
        day_df["mm_pbfd_power"],
        label="MM + POWER",
        linewidth=2
    )

    axes[0].plot(
        day_df["timestamp"],
        day_df["mm_bfd_20_power"],
        label="MM + CPU + 20",
        linewidth=2
    )

    axes[0].plot(
        day_df["timestamp"],
        day_df["mm_pbfd_20_power"],
        label="MM + POWER + 20",
        linewidth=2
    )

    axes[0].set_ylabel("Power (W)")
    axes[0].set_title("MM Policy Comparison")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    # -------------------------
    # RC comparison
    # -------------------------
    #axes[1].plot(
    #    day_df["timestamp"],
    #    day_df["baseline_power"],
    #    label="Baseline",
    #    linewidth=2
    #)

    axes[1].plot(
        day_df["timestamp"],
        day_df["baseline_2_power"],
        label="Baseline 2",
        linewidth=2
    )

    axes[1].plot(
        day_df["timestamp"],
        day_df["rc_bfd_power"],
        label="RC + CPU",
        linewidth=2
    )

    axes[1].plot(
        day_df["timestamp"],
        day_df["rc_pbfd_power"],
        label="RC + POWER",
        linewidth=2
    )

    axes[1].plot(
        day_df["timestamp"],
        day_df["rc_bfd_20_power"],
        label="RC + CPU + 20",
        linewidth=2
    )

    axes[1].plot(
        day_df["timestamp"],
        day_df["rc_pbfd_20_power"],
        label="RC + POWER + 20",
        linewidth=2
    )

    axes[1].set_xlabel("Timestamp")
    axes[1].set_ylabel("Power (W)")
    axes[1].set_title("RC Policy Comparison")
    axes[1].legend()
    axes[1].grid(alpha=0.3)

    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save figure
    plt.savefig(
        "results/policy_comparison.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.show()