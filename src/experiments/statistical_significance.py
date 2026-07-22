import re
import pandas as pd
import numpy as np
import duckdb as ddb
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.stats import wilcoxon
from statsmodels.stats.multitest import multipletests

from experiment_names import *


def load_experiment(name, path):
    con.execute(f"""
        CREATE OR REPLACE VIEW {name} AS
        SELECT *
        FROM read_parquet('{RESULTS_DIR / path["path"]}')
    """)


def get_simulated_power(experiment, power_name="total_power"):
    
    return con.execute(f"""
        SELECT
            timestamp,
            SUM(simulated_power) AS {power_name}
        FROM {experiment}
        GROUP BY timestamp
        ORDER BY timestamp
    """).df()


def parse_group_and_threshold(label):
    group = "MM" if label.startswith("MM") else "RC"
    variant = "POWER" if "POWER" in label else "CPU"
    threshold_start = label.rfind("(") + 1
    threshold_end = label.rfind(")")
    threshold = label[threshold_start:threshold_end]
    return group, variant, threshold


def build_paired_series(pbfd_cfg, cpu_cfg, value_col="power"):
    
    # timestamp-aligned pair of series 

    power_series = get_simulated_power(pbfd_cfg["view_name"], "power_bfd")
    cpu_series = get_simulated_power(cpu_cfg["view_name"], "cpu_bfd")

    merged = power_series.merge(cpu_series, on="timestamp", how="inner")

    n_power = len(power_series)
    n_cpu = len(cpu_series)
    n_merged = len(merged)
    if n_merged != n_power or n_merged != n_cpu:
        print(
            f"  [warning] timestamp mismatch for {pbfd_cfg['label']} vs "
            f"{cpu_cfg['label']}: power={n_power}, cpu={n_cpu}, merged={n_merged}"
        )

    return merged


def run_wilcoxon(df, col_a, col_b):

    diffs = df[col_a] - df[col_b]
    diffs_nonzero = diffs[diffs != 0]

    stat, p_value = wilcoxon(df[col_a], df[col_b])

    n = len(diffs_nonzero)
    # matched-pairs rank-biserial correlation
    r_rb = 1 - (2 * stat) / (n * (n + 1) / 2) if n > 0 else np.nan

    return {
        "col_a": col_a,
        "col_b": col_b,
        "n_pairs": len(df),
        "n_nonzero_diffs": n,
        "W_statistic": stat,
        "p_value": p_value,
        "effect_size_r": r_rb,
        "median_diff_w": diffs.median(),
        "iqr_diff_w": diffs.quantile(0.75) - diffs.quantile(0.25),
        "mean_diff_w": diffs.mean(),
        "pct_diff_of_mean": 100 * diffs.mean() / df[col_b].mean(),
    }


def effect_size_label(r):
    r_abs = abs(r)
    if r_abs < 0.1:
        return "negligible"
    elif r_abs < 0.3:
        return "small"
    elif r_abs < 0.5:
        return "moderate"
    else:
        return "large"


def win_loss_tie_summary(df, col_a, col_b, label_a="PowerBFD", label_b="CPUBFD"):
    # Percentage of paired timestamps where col_a < col_b 
    
    diffs = df[col_a] - df[col_b]
    n = len(diffs)
 
    n_a_wins = (diffs < 0).sum()   # col_a lower power = better
    n_b_wins = (diffs > 0).sum()
    n_ties = (diffs == 0).sum()
 
    return {
        f"{label_a}_better_pct": int(100 * n_a_wins / n),
        f"{label_b}_better_pct": int(100 * n_b_wins / n),
        "tie_pct": int(100 * n_ties / n)
    }


def plot_diff_histogram(df, col_a, col_b, title, filename):
    """Quick symmetry check for the Wilcoxon assumption."""
    diffs = df[col_a] - df[col_b]
    plt.figure(figsize=(6, 4))
    diffs.hist(bins=60)
    plt.title(title)
    plt.xlabel("Power difference (W)")
    plt.ylabel("Count")
    plt.tight_layout()
    #plt.savefig(
    #    ROOT / f"src/plots/wilcoxon/{filename}.png",
    #    dpi=200,
    #    bbox_inches="tight",
    #)
    #plt.close()

    plt.show()

if __name__ == "__main__":

    # Wilcoxon signed-rank test: PowerBFD vs CPUBFD

    ROOT = Path(__file__).resolve().parents[2]
    DATA_DIR = ROOT / "datasets/cloud_energy_consumption/processed"

    # Same toggle as power_consumption.py / carbon_water_consumption.py
    RESULTS_DIR = ROOT / "demand_based_results/"
    PBFD_EXPS = PBFD_SIMULATIONS
    CPU_EXPS = CPU_SIMULATIONS

    # RESULTS_DIR = ROOT / "capacity_based_results/"
    # PBFD_EXPS = CAP_PBFD_SIMULATIONS
    # CPU_EXPS = CAP_CPU_SIMULATIONS

    con = ddb.connect(database=":memory:")

    # Register views, same as power_consumption.py main block
    for view_name, cfg in (PBFD_EXPS | CPU_EXPS).items():
        load_experiment(view_name, cfg)
        cfg["view_name"] = view_name  # keep handle for build_paired_series

    # Index PBFD and CPU experiments by (group, threshold) for matching
    pbfd_index = {}
    for view_name, cfg in PBFD_EXPS.items():
        group, variant, threshold = parse_group_and_threshold(cfg["label"])
        pbfd_index[(group, threshold)] = cfg

    cpu_index = {}
    for view_name, cfg in CPU_EXPS.items():
        group, variant, threshold = parse_group_and_threshold(cfg["label"])
        cpu_index[(group, threshold)] = cfg


    pbfd_vs_cpu_results = []

    for key in sorted(pbfd_index.keys() & cpu_index.keys()):
        group, threshold = key
        pbfd_cfg = pbfd_index[key]
        cpu_cfg = cpu_index[key]

        print(f"Testing {group} {threshold}: {pbfd_cfg['label']} vs {cpu_cfg['label']}")

        paired_df = build_paired_series(pbfd_cfg, cpu_cfg)
        res = run_wilcoxon(paired_df, col_a="power_bfd", col_b="cpu_bfd")
        
        print(win_loss_tie_summary(paired_df, "power_bfd", "cpu_bfd", "PowerBFD", "CPUBFD"))

        res["comparison"] = "PowerBFD_vs_CPUBFD"
        res["group"] = group
        res["threshold"] = threshold
        
        pbfd_vs_cpu_results.append(res)

        # Uncomment to save symmetry-check histograms per config
        # plot_diff_histogram(
        #     paired_df, "power_bfd", "cpu_bfd",
        #     title=f"PowerBFD - CPUBFD diffs ({group}, {threshold})",
        #     filename=f"diff_hist_pbfd_vs_cpu_{group}_{threshold}",
        # )

   
    all_results_df = pd.DataFrame(pbfd_vs_cpu_results)

    # BH correction applied across ALL tests run in this script together,
    # since they're all part of the same family of significance claims.
    reject, p_adj, _, _ = multipletests(all_results_df["p_value"], method="fdr_bh")
    all_results_df["p_adj"] = p_adj
    all_results_df["significant_adj"] = reject
    all_results_df["effect_size_label"] = all_results_df["effect_size_r"].apply(effect_size_label)

    # cols = [
    #     "comparison", "group", "threshold", "n_pairs", "W_statistic",
    #     "p_value", "p_adj", "significant_adj", "effect_size_r",
    #     "effect_size_label", "median_diff_w", "mean_diff_w", "pct_diff_of_mean",
    # ]

    cols = [
        "comparison", "threshold", "W_statistic",
        "p_value", "p_adj", "significant_adj", "effect_size_r",
        "effect_size_label", "median_diff_w", "mean_diff_w", "pct_diff_of_mean",
    ]


    print("\n PowerBFD vs CPUBFD")
    print(all_results_df[all_results_df["comparison"] == "PowerBFD_vs_CPUBFD"][cols].to_string(index=False))