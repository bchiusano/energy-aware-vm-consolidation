import matplotlib.pyplot as plt
import duckdb as ddb
import numpy as np
from pathlib import Path
import pandas as pd

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


def plot_lorenz_comparison(results):
    for name, res in results.items():
        lorenz(plt, res["data"]["migrations_per_vm"], name)

    plt.plot([0,1],[0,1],'--',label="Perfect equality")

    plt.xlabel("Cumulative share of users")
    plt.ylabel("Cumulative share of migrations")
    plt.title("Lorenz Curve Comparison Across Experiments")
    plt.legend()
    plt.grid()
    plt.savefig("lorenz_curves.png", dpi=300, bbox_inches="tight")
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
    
    # select vms and migrations per vm for specific experiment
    vm_migrations = con.query(f"""
        SELECT vm_id, COUNT(*) AS migrations
        FROM {experiment}
        GROUP BY vm_id
    """).df()

    user_migrations = vm_migrations.merge(vm_user, on="vm_id", how="left")
    
    user_migrations = user_migrations.groupby("user_id")["migrations"].sum().reset_index()
    
    user_vm_count = vm_user.groupby("user_id")["vm_id"].count().reset_index(name="num_vms")

    user_migrations = user_migrations.merge(user_vm_count, on="user_id")

    user_migrations["migrations_per_vm"] = (
        user_migrations["migrations"] / user_migrations["num_vms"]
    )

    # fairness metrics
    return {
        "gini": gini(user_migrations["migrations_per_vm"]),
        "jain": jains_fairness(user_migrations["migrations_per_vm"]),
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

    # MM + BFD
    con.execute(f"""CREATE OR REPLACE VIEW mm_bfd AS SELECT * FROM read_parquet('{RESULTS_DIR}/MM_BFD/placements_MM_BFD.parquet')""")

    # MM + PBFD
    con.execute(f"""CREATE OR REPLACE VIEW mm_pbfd AS SELECT * FROM read_parquet('{RESULTS_DIR}/MM_PBFD/placements_MM_PBFD.parquet')""")

    # RC + BFD
    con.execute(f"""CREATE OR REPLACE VIEW rc_bfd AS SELECT * FROM read_parquet('{RESULTS_DIR}/RC_BFD/placements_RC_BFD.parquet')""")

    # RC + PBFD
    con.execute(f"""CREATE OR REPLACE VIEW rc_pbfd AS SELECT * FROM read_parquet('{RESULTS_DIR}/RC_PBFD/placements_RC_PBFD.parquet')""")

    show_count("rc_pbfd")
    show_count("mm_pbfd")
    show_count("rc_bfd")
    show_count("mm_bfd")

    vm_user = con.query("""SELECT vm_id, user_id from vmhardware""").df()

    results = {}

    results["RC+PBFD"] = compute_fairness("rc_pbfd", vm_user)
    results["MM+PBFD"] = compute_fairness("mm_pbfd", vm_user)
    results["RC+BFD"] = compute_fairness("rc_bfd", vm_user)
    results["MM+BFD"] = compute_fairness("mm_bfd", vm_user)

    summary = pd.DataFrame({
        "Experiment": results.keys(),
        "Gini": [results[k]["gini"] for k in results],
        "Jain": [results[k]["jain"] for k in results]
    })

    print(summary)

    # plots
    plot_gini_comparison(summary)
    plot_jain_comparison(summary)
    plot_lorenz_comparison(results)

