import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from experiment_names import *
import numpy as np
import duckdb as ddb

# combinations
scopes = ["operational", "life-cycle"]
footprint_types = ["carbon", "water"]
coverage = ["global", "local"]

# load dataframe
def load_wattnet(dir):
    wattnet_data = pd.read_csv(f"{dir}/wattnet_footprints.csv")
    wattnet_data["timestamp"] = pd.to_datetime(wattnet_data["timestamp"], utc=True)

    return wattnet_data

# load baseline and experiment (simulations)
def load_simulation(path, footprints, baseline=None):
    
    if path:
        sim = ddb.sql(f"""
            SELECT timestamp, simulated_power
            FROM read_parquet('{path}')
        """).df()
    else:
        sim = baseline

    sim["timestamp"] = pd.to_datetime(sim["timestamp"], utc=True)
    
    sim = sim[["timestamp", "simulated_power"]].copy()
    # convert to energy in kwh
    sim["simulated_energy"] =  sim['simulated_power'] * 0.05 / 1000
    
    sim_agg = (
        sim
        .groupby("timestamp", as_index=False)["simulated_energy"]
        .sum()
        .rename(columns={"simulated_energy": "total_simulated_energy"})
    )

    
    merged = footprints.merge(sim_agg, on="timestamp", how="left")

    return merged


def calculate_footprints(merged_df):
    """
    Calculate total carbon and water footprints
    CO2 = ∑_t Energy(t) * CI(t)
    WF = ∑_t Energy(t) * WI(t)
    """
    results = []
    
    for ft in footprint_types:
        for scope in scopes:
            for cover in coverage:
                column_name = f"{ft}_{scope}_{cover}"
                
                # Total footprint = sum(energy(t) × intensity(t))
                total_footprint = (merged_df["total_simulated_energy"] * merged_df[column_name]).sum()
                
                # Unit depends on footprint type
                if ft == "carbon":
                    total_kg = total_footprint / 1000
                    total_metric_tons = total_footprint / 1_000_000
                    results.append({
                        "footprint_type": ft,
                        "scope": scope,
                        "coverage": cover,
                        "total": total_footprint,
                        "total_kg": total_kg,
                        "total_metric_tons": total_metric_tons,
                        "unit": "grams CO2"
                    })
                else:  # water
                    total_m3 = total_footprint / 1000
                    results.append({
                        "footprint_type": ft,
                        "scope": scope,
                        "coverage": cover,
                        "total": total_footprint,
                        "total_m3": total_m3,
                        "unit": "liters"
                    })
    
    return pd.DataFrame(results)


def calculate_reduction(baseline_footprints, experiment_footprints):
    """
    Calculate percent reduction in emissions
    """
    merged = baseline_footprints.merge(
        experiment_footprints,
        on=["footprint_type", "scope", "coverage"],
        suffixes=("_baseline", "_experiment")
    )
    
    merged["reduction_percent"] = (
        (merged["total_baseline"] - merged["total_experiment"]) 
        / merged["total_baseline"] * 100
    )
    
    return merged[["footprint_type", "scope", "coverage", "total_kg_baseline", "total_kg_experiment", "total_m3_baseline", "total_m3_experiment", "reduction_percent"]]

# Bar Plot
def plot_specific_footprints(all_footprints_dict, scope_param, coverage_param):
    """
    Plot water and carbon footprints grouped by threshold,
    with POWER and CPU as adjacent bars within each threshold group.
    
    Args:
        all_footprints_dict: Dict with keys = scenario names, values = footprints DataFrames
    """
    # Parse scenarios into threshold and variant
    parsed_data = []
    
    for scenario_name, fp_df in all_footprints_dict.items():
        # Extract variant (POWER or CPU) and threshold from scenario name
        if "POWER" in scenario_name:
            variant = "POWER"
        elif "CPU" in scenario_name:
            variant = "CPU"
        else:
            continue
        
        # Extract threshold (e.g., "0-30" from "MM/POWER (0-30)")
        threshold_start = scenario_name.rfind("(") + 1
        threshold_end = scenario_name.rfind(")")
        threshold = scenario_name[threshold_start:threshold_end]
        
        # Get water and carbon values
        water_val = fp_df[
            (fp_df["footprint_type"] == "water") & 
            (fp_df["scope"] == scope_param) & 
            (fp_df["coverage"] == coverage_param)
        ]["total_m3"].values[0]
        
        carbon_val = fp_df[
            (fp_df["footprint_type"] == "carbon") & 
            (fp_df["scope"] == scope_param) & 
            (fp_df["coverage"] == coverage_param)
        ]["total_kg"].values[0]
        
        parsed_data.append({
            "threshold": threshold,
            "variant": variant,
            "water_m3": water_val,
            "carbon_kg": carbon_val
        })
    
    parse_df = pd.DataFrame(parsed_data)
    
    # Get unique thresholds in order
    thresholds = parse_df["threshold"].unique()
    thresholds_sorted = sorted(thresholds, key=lambda x: tuple(map(int, x.split("-"))))
    
    # Prepare data for grouped bars
    x = np.arange(len(thresholds_sorted))
    width = 0.35  # width of bars
    
    carbon_power = []
    carbon_cpu = []
    water_power = []
    water_cpu = []
    
    for thresh in thresholds_sorted:
        power_data = parse_df[(parse_df["threshold"] == thresh) & (parse_df["variant"] == "POWER")]
        cpu_data = parse_df[(parse_df["threshold"] == thresh) & (parse_df["variant"] == "CPU")]
        
        carbon_power.append(power_data["carbon_kg"].values[0] if len(power_data) > 0 else 0)
        carbon_cpu.append(cpu_data["carbon_kg"].values[0] if len(cpu_data) > 0 else 0)
        water_power.append(power_data["water_m3"].values[0] if len(power_data) > 0 else 0)
        water_cpu.append(cpu_data["water_m3"].values[0] if len(cpu_data) > 0 else 0)
    
    # Create subplots
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Plot 1: Carbon (kg)
    axes[0].bar(x - width/2, carbon_power, width, label="POWER", color="steelblue", alpha=0.7)
    axes[0].bar(x + width/2, carbon_cpu, width, label="CPU", color="steelblue", alpha=0.5)
    axes[0].set_title(f"Carbon Emissions ({scope_param}, {coverage_param})", fontsize=12, fontweight="bold")
    axes[0].set_ylabel("CO₂ (kg)", fontsize=11)
    axes[0].set_xlabel("Threshold", fontsize=11)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(thresholds_sorted)
    axes[0].legend(loc="upper left", fontsize=10)
    axes[0].grid(axis="y", alpha=0.3)
    # Cut y-axis to show differences better
    carbon_min = min(min(carbon_cpu), min(carbon_power))
    carbon_max = max(max(carbon_cpu), max(carbon_power))
    carbon_range = carbon_max - carbon_min
    axes[0].set_ylim(carbon_min - 0.1 * carbon_range, carbon_max + 0.1 * carbon_range)
    
    # Plot 2: Water (m3)
    axes[1].bar(x - width/2, water_power, width, label="POWER", color="seagreen", alpha=0.7)
    axes[1].bar(x + width/2, water_cpu, width, label="CPU", color="seagreen", alpha=0.5)
    axes[1].set_title(f"Water Consumption ({scope_param}, {coverage_param})", fontsize=12, fontweight="bold")
    axes[1].set_ylabel("Water (m³)", fontsize=11)
    axes[1].set_xlabel("Threshold", fontsize=11)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(thresholds_sorted)
    axes[1].legend(loc="upper left", fontsize=10)
    axes[1].grid(axis="y", alpha=0.3)
    # Same for water
    water_min = min(min(water_cpu), min(water_power))
    water_max = max(max(water_cpu), max(water_power))
    water_range = water_max - water_min
    axes[1].set_ylim(water_min - 0.1 * water_range, water_max + 0.1 * water_range)
    
    plt.tight_layout()
    plt.savefig(ROOT/f"src/plots/footprints/capacity_based_footprint_comparison_{scope_param}_{coverage_param}.png", dpi=300, bbox_inches="tight")
    plt.show()
    
    return fig, parse_df


def plot_footprints_by_scope_coverage(all_footprints_dict):
    """
    Plot total carbon and water footprints across all scope/coverage combinations.

    Args:
        all_footprints_dict: Dict with keys = experiment names, values = footprints DataFrames
    """
    scope_coverage_order = [
        ("operational", "local"),
        ("operational", "global"),
        ("life-cycle", "local"),
        ("life-cycle", "global"),
    ]
    x_labels = [f"{scope}\n{cover}" for scope, cover in scope_coverage_order]
    x = np.arange(len(scope_coverage_order))

    plot_rows = []
    for experiment_name, fp_df in all_footprints_dict.items():
        for scope, cover in scope_coverage_order:
            carbon_match = fp_df[
                (fp_df["footprint_type"] == "carbon") &
                (fp_df["scope"] == scope) &
                (fp_df["coverage"] == cover)
            ]
            water_match = fp_df[
                (fp_df["footprint_type"] == "water") &
                (fp_df["scope"] == scope) &
                (fp_df["coverage"] == cover)
            ]

            if carbon_match.empty or water_match.empty:
                continue

            plot_rows.append({
                "experiment": experiment_name,
                "scope": scope,
                "coverage": cover,
                "scope_coverage": f"{scope}/{cover}",
                "carbon_kg": carbon_match["total_kg"].iloc[0],
                "water_m3": water_match["total_m3"].iloc[0],
            })

    plot_df = pd.DataFrame(plot_rows)

    fig, axes = plt.subplots(1, 2, figsize=(15, 5), sharex=True)

    for experiment_name in all_footprints_dict.keys():
        experiment_df = plot_df[plot_df["experiment"] == experiment_name]
        if experiment_df.empty:
            continue

        axes[0].plot(
            x,
            experiment_df["carbon_kg"],
            marker="o",
            linewidth=1,
            label=experiment_name,
        )
        axes[1].plot(
            x,
            experiment_df["water_m3"],
            marker="o",
            linewidth=1,
            label=experiment_name,
        )

    axes[0].set_title("Carbon Footprint by Scope and Coverage", fontsize=11, fontweight="bold")
    axes[0].set_ylabel("CO₂ (kg)", fontsize=11)
    axes[0].set_xlabel("Scope / Coverage", fontsize=11)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(x_labels)
    axes[0].grid(axis="y", alpha=0.3)

    axes[1].set_title("Water Footprint by Scope and Coverage", fontsize=11, fontweight="bold")
    axes[1].set_ylabel("Water (m³)", fontsize=11)
    axes[1].set_xlabel("Scope / Coverage", fontsize=11)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(x_labels)
    axes[1].grid(axis="y", alpha=0.3)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper left", ncol=2, fontsize=6)
    plt.tight_layout(rect=[0, 0, 1, 0.9])
    plt.savefig(ROOT/f"src/plots/footprints/capacity_based_footprint_summary_new.png", dpi=300, bbox_inches="tight")
    plt.show()

    return fig, plot_df

# Scatter plot

# carbon footprint reduction vs migration count

if __name__ == "__main__":
    con = ddb.connect(":memory:")
    ROOT = Path(__file__).resolve().parents[2]
    RESULTS_DIR = ROOT / "capacity_based_results/"
    WATTNET_DIR = ROOT / "datasets/entsoe_wattnet"
    BASELINE_DIR = ROOT / "datasets/cloud_energy_consumption/processed/node_snapshot.parquet"

    wattnet = load_wattnet(WATTNET_DIR)

    # baseline
    baseline_merged_data = load_simulation(path=BASELINE_DIR,footprints=wattnet)
    con.execute(f"""CREATE OR REPLACE VIEW baseline AS SELECT * FROM read_parquet('{BASELINE_DIR}')""")

    baseline_2 = con.execute("""
        SELECT
            timestamp,
            SUM(
                CASE
                    WHEN vm_count > 0 THEN simulated_power
                    ELSE 0
                END
            ) AS simulated_power
        FROM baseline
        GROUP BY timestamp
        ORDER BY timestamp
    """).df()

    baseline_2_merged = load_simulation(path=None, footprints=wattnet, baseline=baseline_2)

    # calculate for baseline
    baseline_footprints = calculate_footprints(baseline_merged_data)
    print(baseline_footprints)
    
    baseline_2_footprints = calculate_footprints(baseline_2_merged)
    print(baseline_2_footprints)
    
    # load experiment
    EXPERIMENTS = CAP_PBFD_SIMULATIONS | CAP_CPU_SIMULATIONS
    
    #all_footprints = {"Baseline": baseline_footprints, "Baseline2": baseline_2_footprints}
    all_footprints = {}
    
    for view_name, cfg in EXPERIMENTS.items():
        
        print("EXPERIMENT: ", view_name)
        
        if cfg["group"] != "MM":
            continue
        
        exp_merged_data = load_simulation(path=f"{RESULTS_DIR}/{cfg['path']}", footprints=wattnet)
        exp_footprints = calculate_footprints(exp_merged_data)

        #print("reduction compared to baseline")
        # print(calculate_reduction(baseline_footprints=baseline_footprints, experiment_footprints=exp_footprints))
        # print("reduction compared to baseline 2")
        # print(calculate_reduction(baseline_footprints=baseline_2_footprints, experiment_footprints=exp_footprints).head(10))
        
        all_footprints[cfg["label"]] = exp_footprints

    #plotting
    scopes = ["operational", "life-cycle"]
    coverages = ["global", "local"]

    for scope in scopes:
         for coverage in coverages:
             fig, plot_df = plot_specific_footprints(all_footprints_dict=all_footprints, scope_param=scope, coverage_param=coverage)
    
    fig, scope_coverage_plot_df = plot_footprints_by_scope_coverage(all_footprints)
    print("\nComparison summary:")
    print(scope_coverage_plot_df)
