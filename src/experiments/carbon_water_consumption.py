import pandas as pd
from pathlib import Path

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
        "mm_cpu_bfd_10_30": {
            "path": "MM_CPU_BFD_10_30/simulated_MM_CPU_BFD_10_30.parquet",
            "label": "MM/CPU (10-30)",
            "group": "MM",
        },
        
        ########### 20-30 ###########
        "mm_pbfd_20_30": {
            "path": "MM_PBFD_20_30/simulated_MM_PBFD_20_30.parquet",
            "label": "MM/POWER (20-30)",
            "group": "MM",
        },
        "mm_cpu_bfd_20_30": {
            "path": "MM_CPU_BFD_20_30/simulated_MM_CPU_BFD_20_30.parquet",
            "label": "MM/CPU (20-30)",
            "group": "MM",
        },

        ########### 10-90 ###########
        "mm_pbfd_10_90": {
            "path": "MM_PBFD/simulated_MM_PBFD.parquet",
            "label": "MM/POWER (10-90)",
            "group": "MM",
        },
        "mm_bfd_cpu_10_90": {
            "path": "MM_BFD_CPU/simulated_MM_BFD_CPU.parquet",
            "label": "MM/CPU (10-90)",
            "group": "MM",
        },
    }
    
    for view_name, cfg in EXPERIMENTS.items():
        print("EXPERIMENT: ", view_name)
        exp_merged_data = load_simulation(path=f"{RESULTS_DIR}/{cfg["path"]}", footprints=wattnet)
        #print(exp_merged_data)
        exp_footprints = calculate_footprints(exp_merged_data)
        print(exp_footprints)