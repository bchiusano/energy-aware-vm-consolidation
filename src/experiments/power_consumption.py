import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import duckdb as ddb


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
            SUM(simulated_power) * 0.05 / 1000000 AS total_energy_mwh
        FROM {experiment}
    """).df()


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


# plotting
def plot_policy_comparison():
    
    fig, axes = plt.subplots(
        2, 1,              # 2 rows, 1 column
        figsize=(12, 8),
        sharex=True
    )

    df = power_df[
        (power_df["timestamp"] >= "2025-03-01") &
        (power_df["timestamp"] < "2025-04-01")
    ]

    for experiment, cfg in EXPERIMENTS.items():

        experiment = experiment + "_power"

        if cfg["group"] != "MM":
            continue

        axes[0].plot(
            df["timestamp"],
            df[experiment],
            label=cfg["label"]
        )

    for experiment, cfg in EXPERIMENTS.items():

        experiment = experiment + "_power"

        if cfg["group"] != "RC":
            continue

        axes[1].plot(
            df["timestamp"],
            df[experiment],
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
    plt.savefig(
        "results/rc_vs_mm_policy_comparison.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.show()


# Overall comparison
def plot_energy_comparison(time_df):

    #STYLES = {
    #    "MM/POWER (10-30)": "--",
    #    "MM/POWER (10-90)": "-"
    #}

    #COLORS = {
    #    "MM/POWER (10-30)": "blue",
    #    "MM/POWER (10-90)": "red"
    #}
    
    plt.figure(figsize=(10, 6))
    
    #plt.plot(
    #    power_df["timestamp"],
    #    power_df["baseline_power"],
    #    label="Baseline"
    #)

    #plt.plot(
    #    power_df["timestamp"],
    #    power_df["baseline_2_power"],
    #    label="Modified Baseline (Empty Hosts = 0W)"
    #)

    for experiment, cfg in EXPERIMENTS.items():

        experiment = experiment + "_power"

        if cfg["group"] != "MM":
            continue

        plt.plot(
            time_df["timestamp"],
            time_df[experiment],
            label=cfg["label"],
            #linestyle=STYLES[cfg["label"]],
            #color=COLORS[cfg["label"]],
            linewidth=1.5
        )

    plt.xlabel("Timestamp")
    plt.ylabel("Power (W)")
    #plt.title("MM Policy Comparison")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(
        "results/power_comparison.png",
        dpi=300,
        bbox_inches="tight"
    )
    plt.show()

if __name__ == "__main__":

    ROOT = Path(__file__).resolve().parents[2]
    RESULTS_DIR = ROOT / "results/"
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

    '''
    "rc_pbfd": {
            "path": "RC_PBFD/simulated_RC_PBFD.parquet",
            "label": "RC + POWER - 10-90",
            "group": "RC",
        },
        "mm_pbfd": {
            "path": "MM_PBFD/simulated_MM_PBFD.parquet",
            "label": "MM + POWER + 10-90",
            "group": "MM",
        },
         "mm_bfd": {
            "path": "MM_BFD_CPU/simulated_MM_BFD_CPU.parquet",
            "label": "MM + CPU + 10-90",
            "group": "MM",
        },
        "rc_bfd": {
            "path": "RC_BFD_CPU/simulated_RC_BFD_CPU.parquet",
            "label": "RC + CPU + 10-90",
            "group": "RC",
        },    
        "mm_pbfd_30_no_cpu": {
            "path": "MM_PBFD_0_30_NO_CPU/simulated_MM_PBFD_0_30_NO_CPU.parquet",
            "label": "MM + POWER + 0-30",
            "group": "MM",
        },
        "mm_pbfd_10_30_no_cpu": {
            "path": "MM_PBFD_10_30_NO_CPU/simulated_MM_PBFD_10_30_NO_CPU.parquet",
            "label": "MM + POWER + 10-30 + NO CPU",
            "group": "MM",
        },
        "mm_pbfd_10_30": {
            "path": "MM_PBFD_10_30/simulated_MM_PBFD_10_30.parquet",
            "label": "MM + POWER + 10-30",
            "group": "MM",
        },
        "rc_pbfd_10_30": {
            "path": "RC_PBFD_10_30/simulated_RC_PBFD_10_30.parquet",
            "label": "RC + POWER + 10-30",
            "group": "RC",
        },
        "rc_pbfd_20": {
            "path": "RC_PBFD_20/simulated_RC_PBFD_20.parquet",
            "label": "RC + POWER + 20-90",
            "group": "RC",
        },
        "rc_cpu_bfd_20": {
            "path": "RC_CPU_BFD_20/simulated_RC_CPU_BFD_20.parquet",
            "label": "RC + CPU + 20-90",
            "group": "RC",
        },
    '''
    EXPERIMENTS = {
        #"mm_pbfd_10_90": {
        #    "path": "MM_PBFD/simulated_MM_PBFD.parquet",
        #    "label": "MM/POWER (10-90)",
        #    "group": "MM",
        #},
        "mm_bfd_cpu_10_90": {
            "path": "MM_BFD_CPU/simulated_MM_BFD_CPU.parquet",
            "label": "MM/CPU (10-90)",
            "group": "MM",
        },
        #"mm_pbfd_10_30": {
        #    "path": "MM_PBFD_10_30/simulated_MM_PBFD_10_30.parquet",
        #    "label": "MM/POWER (10-30)",
        #    "group": "MM",
        #},
        "mm_cpu_bfd_10_30": {
            "path": "MM_CPU_BFD_10_30/simulated_MM_CPU_BFD_10_30.parquet",
            "label": "MM/CPU (10-30)",
            "group": "MM",
        },
        "mm_cpu_bfd_20_30": {
            "path": "MM_CPU_BFD_20_30/simulated_MM_CPU_BFD_20_30.parquet",
            "label": "MM/CPU (20-30)",
            "group": "MM",
        },

        #"mm_pbfd_20_30": {
        #    "path": "MM_PBFD_20_30/simulated_MM_PBFD_20_30.parquet",
        #    "label": "MM/POWER (20-30)",
        #    "group": "MM",
        #},
    }

    power_df = baseline_power.copy()
    power_df = power_df.merge(
        baseline_2_power,
        on="timestamp"
    )

    for view_name, cfg in EXPERIMENTS.items():
        
        print(cfg["label"])
    
        load_experiment(view_name, cfg)
        
        power_df = power_df.merge(
            get_simulated_power(view_name, view_name+"_power"),
            on="timestamp"
        )


    # summary
    summary_df = pd.concat(
        [get_power_summary(exp) for exp in EXPERIMENTS],
        ignore_index=True
    )

    print(summary_df)

    df = power_df[
        (power_df["timestamp"] >= "2025-02-01") &
        (power_df["timestamp"] < "2025-02-7")
    ]

    plot_energy_comparison(df)