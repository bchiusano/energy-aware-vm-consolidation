import matplotlib.pyplot as plt
import duckdb as ddb
import numpy as np
from pathlib import Path
import pandas as pd
from experiment_names import *


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


def extract_threshold(label):
    """Extract threshold from label like 'MM (10-30)' -> '10-30'"""
    return label.split("(")[1].rstrip(")")


def plot_gini_comparison_grouped(summary, type="migrations_per_vm"):
    """Grouped bar chart: Power vs CPU for each threshold."""
    # Separate by type
    power_data = summary[summary["Type"] == "POWER"].copy()
    cpu_data = summary[summary["Type"] == "CPU"].copy()
    
    # Extract thresholds and sort
    power_data["Threshold"] = power_data["Experiment"].apply(extract_threshold)
    cpu_data["Threshold"] = cpu_data["Experiment"].apply(extract_threshold)
    
    thresholds = sorted(power_data["Threshold"].unique())
    
    # Get values in threshold order
    power_gini = [power_data[power_data["Threshold"] == t]["Gini"].values[0] if t in power_data["Threshold"].values else 0 for t in thresholds]
    cpu_gini = [cpu_data[cpu_data["Threshold"] == t]["Gini"].values[0] if t in cpu_data["Threshold"].values else 0 for t in thresholds]
    
    x = np.arange(len(thresholds))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.bar(x - width/2, power_gini, width, label="Power BFD", color="steelblue", alpha=0.8)
    ax.bar(x + width/2, cpu_gini, width, label="CPU BFD", color="coral", alpha=0.8)
    
    ax.set_xlabel("Threshold Configuration", fontsize=11)
    ax.set_ylabel("Gini Coefficient", fontsize=11)
    ax.set_title("Fairness Comparison: Power vs CPU BFD (Gini)", fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(thresholds, rotation=45, ha="right")
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f"gini_comparison_{type}_NEW.png", dpi=300, bbox_inches="tight")
    plt.show()


def lorenz(ax, data, label):
    x = np.sort(np.array(data))
    cum = np.cumsum(x) / np.sum(x)
    pop = np.arange(1, len(x)+1) / len(x)
    ax.plot(pop, cum, label=label)


def plot_lorenz_comparison(results, type="migrations_per_vm"):
    for name, res in results.items():
        lorenz(plt, res["data"][type], name)

    plt.plot([0,1],[0,1],'--',label="Perfect equality")

    plt.xlabel("Cumulative share of users")
    plt.ylabel("Cumulative share of migrations")
    plt.title(f"Lorenz Curve Comparison for {type}")
    plt.legend()
    plt.grid()
    plt.savefig(f"lorenz_curves_{type}_NEW.png", dpi=300, bbox_inches="tight")
    plt.show()


def jains_fairness(x):
    x = np.array(x)
    if len(x) == 0:
        return 0
    return (np.sum(x) ** 2) / (len(x) * np.sum(x ** 2))


def plot_jain_comparison(summary, type="migrations_per_vm"):
    """Grouped bar chart: Power vs CPU for each threshold."""
    # Separate by type
    power_data = summary[summary["Type"] == "POWER"].copy()
    cpu_data = summary[summary["Type"] == "CPU"].copy()
    
    # Extract thresholds and sort
    power_data["Threshold"] = power_data["Experiment"].apply(extract_threshold)
    cpu_data["Threshold"] = cpu_data["Experiment"].apply(extract_threshold)
    
    thresholds = sorted(power_data["Threshold"].unique())
    
    # Get values in threshold order
    power_jain = [power_data[power_data["Threshold"] == t]["Jain"].values[0] if t in power_data["Threshold"].values else 0 for t in thresholds]
    cpu_jain = [cpu_data[cpu_data["Threshold"] == t]["Jain"].values[0] if t in cpu_data["Threshold"].values else 0 for t in thresholds]
    
    x = np.arange(len(thresholds))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.bar(x - width/2, power_jain, width, label="Power BFD", color="seagreen", alpha=0.8)
    ax.bar(x + width/2, cpu_jain, width, label="CPU BFD", color="goldenrod", alpha=0.8)
    
    ax.set_xlabel("Threshold Configuration", fontsize=11)
    ax.set_ylabel("Jain Fairness Index", fontsize=11)
    ax.set_title("Fairness Comparison: Power vs CPU BFD (Jain)", fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(thresholds, rotation=45, ha="right")
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f"jain_comparison_{type}_NEW.png", dpi=300, bbox_inches="tight")
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
    RESULTS_DIR = ROOT / "newResults/"
    DATA_DIR = ROOT / "datasets/cloud_energy_consumption"

    con = ddb.connect(database=':memory:')

    # User data
    con.query(f"""CREATE OR REPLACE TABLE vmhardware AS SELECT * FROM read_csv('{DATA_DIR}/vms/2024-12-14T000000Z_2025-04-13T235959Z/vms_fixed.csv')""")

    EXPERIMENTS = PBFD_PLACEMENTS | CPU_PLACEMENTS

    vm_user = con.query("""SELECT vm_id, user_id from vmhardware""").df()
    results = {}

    for view_name, val in EXPERIMENTS.items():

        if val["group"] != "MM":
            continue
        
        print(f"{val['label']} ({val['type']})")
        load_experiment(view_name, val)
        show_count(view_name)
        results[view_name] = {
            "label": val["label"],
            "type": val["type"],
            "fairness": compute_fairness(view_name, vm_user)
        }

    # Build summaries with Type column
    summary_burden = pd.DataFrame({
        "Experiment": [results[k]["label"] for k in results],
        "Type": [results[k]["type"] for k in results],
        "Gini": [results[k]["fairness"]["gini_burden"] for k in results],
        "Jain": [results[k]["fairness"]["jain_burden"] for k in results]
    })

    summary_normalised = pd.DataFrame({
        "Experiment": [results[k]["label"] for k in results],
        "Type": [results[k]["type"] for k in results],
        "Gini": [results[k]["fairness"]["gini_normalised"] for k in results],
        "Jain": [results[k]["fairness"]["jain_normalised"] for k in results]
    })

    print("\n=== Burden (Total Migrations) ===")
    print(summary_burden)
    
    print("\n=== Normalised (Per-VM Migrations) ===")
    print(summary_normalised)

    # Grouped bar plots
    plot_gini_comparison_grouped(summary_burden, type="migrations_burden")
    plot_jain_comparison(summary_burden, type="migrations_burden")
    plot_lorenz_comparison({results[k]["label"]: results[k]["fairness"] for k in results}, type="migrations")

    plot_gini_comparison_grouped(summary_normalised, type="migrations_per_vm")
    plot_jain_comparison(summary_normalised, type="migrations_per_vm")
    plot_lorenz_comparison({results[k]["label"]: results[k]["fairness"] for k in results}, type="migrations_per_vm")