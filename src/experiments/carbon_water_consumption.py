import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

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
def load_simulation(path, footprints):
    
    sim = pd.read_parquet(path)

    sim["timestamp"] = pd.to_datetime(sim["timestamp"], utc=True)
    
    sim = sim[["timestamp", "simulated_power"]]
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
        (merged["total_footprint_baseline"] - merged["total_footprint_experiment"]) 
        / merged["total_footprint_baseline"] * 100
    )
    
    return merged

# Bar Plot
def plot_specific_footprints(all_footprints_dict, scope_param, coverage_param):
    """
    Plot water_operational_local (m3) and carbon_operational_local (kg)
    for baseline and all experiments
    
    Args:
        all_footprints_dict: Dict with keys = scenario names, values = footprints DataFrames
    """
    # Extract specific metrics
    data_to_plot = []
    
    for scenario_name, fp_df in all_footprints_dict.items():
        # Water operational local (m3)
        water_local = fp_df[
            (fp_df["footprint_type"] == "water") & 
            (fp_df["scope"] == scope_param) & 
            (fp_df["coverage"] == coverage_param)
        ]["total_m3"].values[0]
        
        # Carbon operational local (kg)
        carbon_local = fp_df[
            (fp_df["footprint_type"] == "carbon") & 
            (fp_df["scope"] == scope_param) & 
            (fp_df["coverage"] == coverage_param)
        ]["total_kg"].values[0]
        
        data_to_plot.append({
            "scenario": scenario_name,
            "water_m3": water_local,
            "carbon_kg": carbon_local
        })
    
    plot_df = pd.DataFrame(data_to_plot)
    
    # Create subplots
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Plot 1: Carbon (kg)
    axes[0].bar(plot_df["scenario"], plot_df["carbon_kg"], color="steelblue", alpha=0.7)
    axes[0].set_title("Carbon Emissions (Operational, Local)", fontsize=12, fontweight="bold")
    axes[0].set_ylabel("CO₂ (kg)", fontsize=11)
    axes[0].set_xlabel("Scenario", fontsize=11)
    axes[0].tick_params(axis="x", rotation=45)
    axes[0].grid(axis="y", alpha=0.3)
    # Cut y-axis to show differences better
    carbon_min = plot_df["carbon_kg"].min()
    carbon_max = plot_df["carbon_kg"].max()
    carbon_range = carbon_max - carbon_min
    axes[0].set_ylim(carbon_min - 0.1 * carbon_range, carbon_max + 0.1 * carbon_range)
    
    # Plot 2: Water (m3)
    axes[1].bar(plot_df["scenario"], plot_df["water_m3"], color="seagreen", alpha=0.7)
    axes[1].set_title("Water Consumption (Operational, Local)", fontsize=12, fontweight="bold")
    axes[1].set_ylabel("Water (m³)", fontsize=11)
    axes[1].set_xlabel("Scenario", fontsize=11)
    axes[1].tick_params(axis="x", rotation=45)
    axes[1].grid(axis="y", alpha=0.3)
    # Cut y-axis to show differences better
    water_min = plot_df["water_m3"].min()
    water_max = plot_df["water_m3"].max()
    water_range = water_max - water_min
    axes[1].set_ylim(water_min - 0.1 * water_range, water_max + 0.1 * water_range)
    
    plt.tight_layout()
    return fig, plot_df

# Scatter plot

# carbon footprint reduction vs migration count

if __name__ == "__main__":

    ROOT = Path(__file__).resolve().parents[2]
    RESULTS_DIR = ROOT / "results/"
    DATA_DIR = ROOT / "datasets/entsoe_wattnet"
    BASELINE_DIR = ROOT / "datasets/cloud_energy_consumption/processed/node_snapshot.parquet"

    wattnet = load_wattnet(DATA_DIR)

    # baseline
    baseline_merged_data = load_simulation(path=BASELINE_DIR,footprints=wattnet)

    # calculate for baseline
    baseline_footprints = calculate_footprints(baseline_merged_data)
    print("carbon and water emissions")
    print(baseline_footprints)

    # TODO: also add baseline 2
    
    # load experiment
    EXPERIMENTS = {
        ########### 10-30 ###########
        "mm_pbfd_10_30": {
            "path": "MM_PBFD_10_30/simulated_MM_PBFD_10_30.parquet",
            "label": "MM/POWER (10-30)",
            "group": "MM",
        },
        "rc_pbfd_10_30": {
            "path": "RC_PBFD_10_30/simulated_RC_PBFD_10_30.parquet",
            "label": "RC/POWER (10-30)",
            "group": "RC",
        },
        
        ########### 20-30 ###########
        "mm_pbfd_20_30": {
            "path": "MM_PBFD_20_30/simulated_MM_PBFD_20_30.parquet",
            "label": "MM/POWER (20-30)",
            "group": "MM",
        },
        "rc_pbfd_20_30": {
            "path": "RC_PBFD_20_30/simulated_RC_PBFD_20_30.parquet",
            "label": "RC/POWER (20-30)",
            "group": "RC",
        },

        ########### 10-90 ###########
        "mm_pbfd_10_90": {
            "path": "MM_PBFD/simulated_MM_PBFD.parquet",
            "label": "MM/POWER (10-90)",
            "group": "MM",
        },
        "rc_pbfd_10_90": {
            "path": "RC_PBFD/simulated_RC_PBFD.parquet",
            "label": "RC/POWER (10-90)",
            "group": "RC",
        },

        ########### 20-90 ###########
        "mm_pbfd_20_90": {
            "path": "MM_PBFD_20/simulated_MM_PBFD_20.parquet",
            "label": "MM/POWER (20-90)",
            "group": "MM",
        },
        "rc_pbfd_20_90": {
            "path": "RC_PBFD_20/simulated_RC_PBFD_20.parquet",
            "label": "RC/POWER (20-90)",
            "group": "RC",
        },
    }
    
    #all_footprints = {"Baseline": baseline_footprints}
    all_footprints = {}

    for view_name, cfg in EXPERIMENTS.items():
        
        print("EXPERIMENT: ", view_name)
        
        exp_merged_data = load_simulation(path=f"{RESULTS_DIR}/{cfg["path"]}", footprints=wattnet)
        exp_footprints = calculate_footprints(exp_merged_data)
        
        all_footprints[cfg["label"]] = exp_footprints

    
    # Plot comparison
    scope = "life-cycle"
    coverage = "global"

    fig, plot_df = plot_specific_footprints(all_footprints_dict=all_footprints, scope_param=scope, coverage_param=coverage)
    plt.savefig("footprint_comparison_global_lc_mm_pbfd.png", dpi=300, bbox_inches="tight")
    print("\nPlot saved to footprint_comparison.png")
    print("\nComparison summary:")
    print(plot_df)