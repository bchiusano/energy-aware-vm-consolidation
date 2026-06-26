import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import duckdb as ddb
from experiment_names import *


def load_experiment(name, path):
    con.execute(f"""
        CREATE OR REPLACE VIEW {name} AS
        SELECT *
        FROM read_parquet('{RESULTS_DIR / path["path"]}')
    """)

def get_power_summary(experiment):

    return con.execute(f"""
        SELECT
            '{experiment}' AS experiment,
            SUM(simulated_power) AS total_power_w,
            AVG(simulated_power) AS avg_power_w,
            SUM(simulated_power) * 0.05 / 1000000 AS total_energy_mwh,
            SUM(simulated_power) * 0.05 / 1000 AS total_energy_kwh
        FROM {experiment}
        
    """).df()

# WHERE timestamp >= '2025-01-01 00:00:00 UTC'
# AND timestamp < '2025-02-01 00:00:00 UTC'


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

# WHERE timestamp >= '2025-01-01 00:00:00 UTC'
# AND timestamp < '2025-02-01 00:00:00 UTC'

# plotting
def plot_policy_comparison(df):
    
    fig, axes = plt.subplots(
        2, 1,              # 2 rows, 1 column
        figsize=(12, 8),
        sharex=True
    )

    experiments = PBFD_SIMULATIONS | CPU_SIMULATIONS

    for experiment, cfg in experiments.items():

        if cfg["group"] != "MM":
            continue

        col = f"{experiment}_{cfg['type'].lower()}"

        if col not in df.columns:
            continue

        axes[0].plot(
            df["timestamp"],
            df[col],
            label=cfg["label"]
        )

    for experiment, cfg in experiments.items():

        if cfg["group"] != "RC":
            continue

        col = f"{experiment}_{cfg['type'].lower()}"

        if col not in df.columns:
            continue

        axes[1].plot(
            df["timestamp"],
            df[col],
            label=cfg["label"]
        )

    axes[0].set_ylabel("Power (W)")
    axes[0].set_title("MM Policy Comparison")
    axes[0].legend()
    axes[0].grid(alpha=0.3)
    axes[1].set_xlabel("Timestamp")
    axes[1].set_ylabel("Power (W)")
    axes[1].set_title("RC Policy Comparison")
    axes[1].legend()
    axes[1].grid(alpha=0.3)

    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save figure
    #plt.savefig(
    #    "results/rc_vs_mm_policy_comparison.png",
    #    dpi=300,
    #    bbox_inches="tight"
    #)

    plt.show()


# Overall comparison
def plot_energy_comparison(df):

    fig, axes = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

    ax_power = axes[0]
    ax_cpu = axes[1]

    # -------------------
    # BASELINES (shared style)
    # -------------------
    ax_power.plot(
        df["timestamp"],
        df["baseline_power"],
        label="Baseline",
        linestyle="-",
        color="black",
        linewidth=1.5,
        alpha=0.8
    )

    ax_power.plot(
        df["timestamp"],
        df["baseline_2_power"],
        label="Baseline 2 (empty=0W)",
        linestyle="--",
        color="black",
        linewidth=1.7,
        alpha=0.8
    )

    # -------------------
    # EXPERIMENTS - POWER
    # -------------------
    for experiment, cfg in PBFD_SIMULATIONS.items():

        col = experiment + "_power"

        if col not in df.columns:
            continue

        if cfg["group"] != "MM":
            continue

        ax_power.plot(
            df["timestamp"],
            df[col],
            label=cfg["label"],
            linewidth=1.0
        )

    ax_power.set_ylabel("Power (W)")
    ax_power.set_title("Power BFD Comparison")
    ax_power.grid(alpha=0.3)
    ax_power.legend()

    # -------------------
    # BASELINES (CPU)
    # -------------------
    ax_cpu.plot(
        df["timestamp"],
        df["baseline_power"],
        label="Baseline",
        linestyle="-",
        color="black",
        linewidth=1.5,
        alpha=0.8
    )

    ax_cpu.plot(
        df["timestamp"],
        df["baseline_2_power"],
        label="Baseline 2 (empty=0W)",
        linestyle="--",
        color="black",
        linewidth=1.7,
        alpha=0.8
    )

    # -------------------
    # EXPERIMENTS - CPU
    # -------------------
    for experiment, cfg in CPU_SIMULATIONS.items():

        col = experiment + "_cpu"

        if col not in df.columns:
            continue

        if cfg["group"] != "MM":
            continue

        ax_cpu.plot(
            df["timestamp"],
            df[col],
            label=cfg["label"],
            linewidth=1.0
        )

    ax_cpu.set_ylabel("Power (W)")
    ax_cpu.set_title("CPU BFD Comparison")
    ax_cpu.grid(alpha=0.3)
    ax_cpu.legend()

    # -------------------
    # COMMON X AXIS
    # -------------------
    plt.xlabel("Timestamp")
    plt.xticks(rotation=45)

    plt.tight_layout()
    #plt.savefig(ROOT/"src/plots/power_comparison_grid.png", dpi=300)
    plt.show()

if __name__ == "__main__":

    ROOT = Path(__file__).resolve().parents[2]
    RESULTS_DIR = ROOT / "demand_based_results/"
    DATA_DIR = ROOT / "datasets/cloud_energy_consumption/processed"

    con = ddb.connect(database=':memory:')

    # Load Baselines
    con.execute(f"""CREATE OR REPLACE VIEW baseline AS SELECT * FROM read_parquet('{DATA_DIR}/node_snapshot.parquet')""")

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

    EXPERIMENTS = PBFD_SIMULATIONS | CPU_SIMULATIONS

    power_df = baseline_power.copy()
    power_df = power_df.merge(
        baseline_2_power,
        on="timestamp"
    )

    for view_name, cfg in EXPERIMENTS.items():
        
        print(cfg["label"])
    
        load_experiment(view_name, cfg)
        

    for view_name, cfg in PBFD_SIMULATIONS.items():
        power_df = power_df.merge(
            get_simulated_power(view_name, view_name+"_power"),
            on="timestamp"
        )
    
    for view_name, cfg in CPU_SIMULATIONS.items():
        power_df = power_df.merge(
            get_simulated_power(view_name, view_name+"_cpu"),
            on="timestamp"
        )

    # summary
    summary_df = pd.concat(
        [get_power_summary(exp) for exp in EXPERIMENTS],
        ignore_index=True
    )

    print(summary_df)

    df = power_df[(power_df["timestamp"] >= "2025-02-01") & (power_df["timestamp"] < "2025-02-07")]

    plot_energy_comparison(df)
    #plot_policy_comparison(df)
