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
            AVG(simulated_power) as avg_power_w,
            COUNT(*) as host_count
        FROM baseline
        UNION ALL
        SELECT 
            'Simulated' as scenario,
            SUM(simulated_power) as total_power_w,
            AVG(simulated_power) as avg_power_w,
            COUNT(*) as host_count
        FROM {experiment}
    """).show()


if __name__ == "__main__":

    con = ddb.connect(database=':memory:')

    # Baseline
    con.execute(f"""CREATE OR REPLACE VIEW baseline AS SELECT * FROM read_parquet('{DATA_DIR}/node_snapshot.parquet')""")

    # MM + BFD
    con.execute(f"""CREATE OR REPLACE VIEW mm_bfd AS SELECT * FROM read_parquet('{RESULTS_DIR}/MM_BFD/simulated_MM_BFD.parquet')""")

    # MM + PBFD
    con.execute(f"""CREATE OR REPLACE VIEW mm_pbfd AS SELECT * FROM read_parquet('{RESULTS_DIR}/MM_PBFD/simulated_MM_PBFD.parquet')""")

    # RC + BFD
    con.execute(f"""CREATE OR REPLACE VIEW rc_bfd AS SELECT * FROM read_parquet('{RESULTS_DIR}/RC_BFD/simulated_RC_BFD.parquet')""")

    # RC + PBFD
    con.execute(f"""CREATE OR REPLACE VIEW rc_pbfd AS SELECT * FROM read_parquet('{RESULTS_DIR}/RC_PBFD/simulated_RC_PBFD.parquet')""")

    # calculations
    get_total_power_consumption("mm_bfd")
    get_total_power_consumption("mm_pbfd")
    get_total_power_consumption("rc_bfd")
    get_total_power_consumption("rc_pbfd")

    baseline_power = con.execute("""
        SELECT
            timestamp,
            SUM(ipmi_system_power_watts) AS baseline_power
        FROM baseline
        GROUP BY timestamp
        ORDER BY timestamp
    """).df()

    mm_bfd_power = get_simulated_power("mm_bfd", "mm_bfd_power")
    mm_pbfd_power = get_simulated_power("mm_pbfd", "mm_pbfd_power")
    rc_bfd_power = get_simulated_power("rc_bfd", "rc_bfd_power")
    rc_pbfd_power = get_simulated_power("rc_pbfd", "rc_pbfd_power")

    # Combine into a single DataFrame for plotting
    power_df = (
        baseline_power
        .merge(mm_bfd_power, on="timestamp")
        .merge(mm_pbfd_power, on="timestamp")
        .merge(rc_bfd_power, on="timestamp")
        .merge(rc_pbfd_power, on="timestamp")
    )

    #week_df = power_df[
    #    (power_df["timestamp"] >= "2025-02-01") &
    #    (power_df["timestamp"] < "2025-02-08")
    #]

    day_df = power_df[
        (power_df["timestamp"] >= "2025-04-01") &
        (power_df["timestamp"] < "2025-04-02")
    ]

    plt.figure(figsize=(12,6))

    plt.plot(
        day_df["timestamp"],
        day_df["baseline_power"],
        label="Baseline"
    )

    plt.plot(
        day_df["timestamp"],
        day_df["mm_bfd_power"],
        label="MM + BFD"
    )

    plt.plot(
        day_df["timestamp"],
        day_df["mm_pbfd_power"],
        label="MM + PBFD"
    )

    plt.plot(
        day_df["timestamp"],
        day_df["rc_bfd_power"],
        label="RC + BFD"
    )

    plt.plot(
        day_df["timestamp"],
        day_df["rc_pbfd_power"],
        label="RC + PBFD"
    )

    plt.xlabel("Timestamp")
    plt.ylabel("Total Power (W)")
    #plt.title("Total Datacenter Power Consumption Over 7 Days")
    plt.legend()
    plt.tight_layout()
    plt.show()
    plt.savefig("power_comparison_day.png")

    
