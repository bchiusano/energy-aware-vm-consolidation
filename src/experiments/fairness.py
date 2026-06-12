import matplotlib.pyplot as plt
import duckdb as ddb
import numpy as np
from pathlib import Path
import pandas as pd


def load_experiment(name, path):
    con.execute(f"""
        CREATE OR REPLACE VIEW {name} AS
        SELECT *
        FROM read_parquet('{RESULTS_DIR / path["path"]}')
    """)

def gini(x):
    x = np.array(x)
    if len(x) == 0:
        return 0
    if np.amin(x) < 0:
        x = x - np.amin(x)
    x = np.sort(x)
    cumx = np.cumsum(x)
    return (len(x) + 1 - 2 * np.sum(cumx) / cumx[-1]) / len(x)


def plot_gini_comparison(summary):
    plt.figure()
    plt.bar(summary["Experiment"], summary["Gini"])
    plt.ylabel("Gini Coefficient")
    plt.title("Fairness Comparison Across Experiments (Gini)")
    plt.xticks(rotation=45)
    plt.grid(axis="y")
    plt.show()


def lorenz(ax, data, label):
    x = np.sort(np.array(data))
    cum = np.cumsum(x) / np.sum(x)
    pop = np.arange(1, len(x)+1) / len(x)
    ax.plot(pop, cum, label=label)


def plot_lorenz_comparison(results, type = "migrations_per_vm"):
    for name, res in results.items():
        lorenz(plt, res["data"][type], name)

    plt.plot([0,1],[0,1],'--',label="Perfect equality")

    plt.xlabel("Cumulative share of users")
    plt.ylabel("Cumulative share of migrations")
    plt.title(f"Lorenz Curve Comparison for {type}")
    plt.legend()
    plt.grid()
    plt.savefig(f"lorenz_curves_{type}.png", dpi=300, bbox_inches="tight")
    plt.show()


def jains_fairness(x):
    x = np.array(x)
    if len(x) == 0:
        return 0
    return (np.sum(x) ** 2) / (len(x) * np.sum(x ** 2))


def plot_jain_comparison(summary):
    plt.figure()
    plt.bar(summary["Experiment"], summary["Jain"])
    plt.ylabel("Jain Fairness Index")
    plt.title("Fairness Comparison Across Experiments (Jain)")
    plt.xticks(rotation=45)
    plt.grid(axis="y")
    plt.show()


def compute_fairness(experiment, vm_user):

    vm_migrations = con.query(f"""
        SELECT vm_id, COUNT(*) AS migrations
        FROM {experiment}
        GROUP BY vm_id
    """).df()

    user_migrations = (
        vm_migrations
        .merge(vm_user, on="vm_id", how="left")
        .groupby("user_id")["migrations"]
        .sum()
        .reset_index()
    )

    # full user support (IMPORTANT for fairness)
    all_users = vm_user[["user_id"]].drop_duplicates()

    user_vm_count = (
        vm_user.groupby("user_id")["vm_id"]
        .nunique()
        .reset_index(name="num_vms")
    )

    user_migrations = (
        all_users
        .merge(user_migrations, on="user_id", how="left")
        .merge(user_vm_count, on="user_id", how="left")
        .fillna(0)
    )

    # avoid division issues
    user_migrations["migrations_per_vm"] = (
        user_migrations["migrations"] / user_migrations["num_vms"].replace(0, np.nan)
    ).fillna(0)

    return {
        "gini_burden": gini(user_migrations["migrations"]),
        "jain_burden": jains_fairness(user_migrations["migrations"]),
        "gini_normalised": gini(user_migrations["migrations_per_vm"]),
        "jain_normalised": jains_fairness(user_migrations["migrations_per_vm"]),
        "data": user_migrations
    }


def show_count(experiment):

    print(f"Count unique for {experiment} simulation")

    con.query(f"""
        SELECT
            COUNT(DISTINCT vm_id) AS unique_vm_ids,
            COUNT(DISTINCT source_node) AS unique_source_nodes,
            COUNT(DISTINCT target_node) AS unique_target_nodes
        FROM {experiment}
    """).show()


if __name__ == "__main__":

    ROOT = Path(__file__).resolve().parents[2]
    RESULTS_DIR = ROOT / "results/"
    DATA_DIR = ROOT / "datasets/cloud_energy_consumption"

    con = ddb.connect(database=':memory:')

    # User data
    con.query(f"""CREATE OR REPLACE TABLE vmhardware AS SELECT * FROM read_csv('{DATA_DIR}/vms/2024-12-14T000000Z_2025-04-13T235959Z/vms_fixed.csv')""")

    '''
    "rc_pbfd": {
            "path": "RC_PBFD/placements_RC_PBFD.parquet",
            "label": "RC + POWER - 10-90",
            "group": "RC",
        },
        "mm_pbfd": {
            "path": "MM_PBFD/placements_MM_PBFD.parquet",
            "label": "MM + POWER + 10-90",
            "group": "MM",
        },
         "mm_bfd": {
            "path": "MM_BFD_CPU/placements_MM_BFD_CPU.parquet",
            "label": "MM + CPU + 10-90",
            "group": "MM",
        },
        "rc_bfd": {
            "path": "RC_BFD_CPU/placements_RC_BFD_CPU.parquet",
            "label": "RC + CPU + 10-90",
            "group": "RC",
        },    
        "mm_pbfd_30_no_cpu": {
            "path": "MM_PBFD_0_30_NO_CPU/placements_MM_PBFD_0_30_NO_CPU.parquet",
            "label": "MM + POWER + 0-30",
            "group": "MM",
        },
        "mm_pbfd_10_30_no_cpu": {
            "path": "MM_PBFD_10_30_NO_CPU/placements_MM_PBFD_10_30_NO_CPU.parquet",
            "label": "MM + POWER + 10-30 + NO CPU",
            "group": "MM",
        },
        "mm_pbfd_10_30": {
            "path": "MM_PBFD_10_30/placements_MM_PBFD_10_30.parquet",
            "label": "MM + POWER + 10-30",
            "group": "MM",
        },
        "rc_pbfd_10_30": {
            "path": "RC_PBFD_10_30/placements_RC_PBFD_10_30.parquet",
            "label": "RC + POWER + 10-30",
            "group": "RC",
        },
        "rc_pbfd_20": {
            "path": "RC_PBFD_20/placements_RC_PBFD_20.parquet",
            "label": "RC + POWER + 20-90",
            "group": "RC",
        },
        "rc_cpu_bfd_20": {
            "path": "RC_CPU_BFD_20/placements_RC_CPU_BFD_20.parquet",
            "label": "RC + CPU + 20-90",
            "group": "RC",
        },
    '''
    EXPERIMENTS = {
        "mm_pbfd": {
            "path": "MM_PBFD/placements_MM_PBFD.parquet",
            "label": "MM/POWER (10-90)",
            "group": "MM",
        },
        "mm_pbfd_10_30": {
            "path": "MM_PBFD_10_30/placements_MM_PBFD_10_30.parquet",
            "label": "MM/POWER (10-30)",
            "group": "MM",
        },
        "rc_pbfd_20": {
            "path": "RC_PBFD_20/placements_RC_PBFD_20.parquet",
            "label": "RC/POWER (20-90)",
            "group": "RC",
        },
    }

    vm_user = con.query("""SELECT vm_id, user_id from vmhardware""").df()
    results = {}

    for view_name, val in EXPERIMENTS.items():
        
        print(val["label"])
        load_experiment(view_name, val)
        show_count(view_name)
        results[val["label"]] = compute_fairness(view_name, vm_user)


    summary_burden = pd.DataFrame({
        "Experiment": results.keys(),
        "Gini": [results[k]["gini_burden"] for k in results],
        "Jain": [results[k]["jain_burden"] for k in results]
    })

    summary_normalised = pd.DataFrame({
        "Experiment": results.keys(),
        "Gini": [results[k]["gini_normalised"] for k in results],
        "Jain": [results[k]["jain_normalised"] for k in results]
    })

    print(summary_burden)
    print(summary_normalised)

    # plots
    plot_gini_comparison(summary_burden)
    plot_jain_comparison(summary_burden)
    plot_lorenz_comparison(results, type="migrations")

    plot_gini_comparison(summary_normalised)
    plot_jain_comparison(summary_normalised)
    plot_lorenz_comparison(results, type="migrations_per_vm")
    