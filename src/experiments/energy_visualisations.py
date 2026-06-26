import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import duckdb as ddb
from pathlib import Path
from experiment_names import PBFD_SIMULATIONS, CPU_SIMULATIONS


def load_experiment(con, name, path):
    """Load experiment data into a DuckDB view"""
    con.execute(f"""
        CREATE OR REPLACE VIEW {name} AS
        SELECT *
        FROM read_parquet('{path}')
    """)


def get_power_summary(con, experiment):
    """Get total energy for an experiment"""
    return con.execute(f"""
        SELECT
            '{experiment}' AS experiment,
            SUM(simulated_power) * 0.05 / 1000 AS total_energy_kwh
        FROM {experiment}
    """).df()


def load_baseline_data(con, data_dir):
    """Load baseline data and compute baseline energy consumption"""
    con.execute(f"""CREATE OR REPLACE VIEW baseline AS SELECT * FROM read_parquet('{data_dir}/node_snapshot.parquet')""")

    baseline_energy = con.execute("""
        SELECT
            SUM(ipmi_system_power_watts) * 0.05 / 1000 AS total_energy_kwh
        FROM baseline
    """).df()['total_energy_kwh'][0]

    # Baseline 2: set simulated power to 0 for empty hosts
    baseline_2_energy = con.execute("""
        SELECT
            SUM(
                CASE
                    WHEN vm_power_allocated > 0 THEN simulated_power
                    ELSE 0
                END
            ) * 0.05 / 1000 AS total_energy_kwh
        FROM baseline
    """).df()['total_energy_kwh'][0]

    return baseline_energy, baseline_2_energy


def load_all_experiments(results_dir):
    """Load all experiment data and compute energy summaries"""
    con = ddb.connect(database=':memory:')
    
    # Combine PBFD and CPU simulations
    all_experiments = PBFD_SIMULATIONS | CPU_SIMULATIONS
    
    data = []
    
    # Load each experiment and compute energy
    for experiment_name, config in all_experiments.items():
        path = results_dir / config["path"]
        try:
            load_experiment(con, experiment_name, str(path))
            summary = get_power_summary(con, experiment_name)
            
            # Extract threshold and placement type from experiment name
            # e.g., "mm_cpu_bfd_0_30_grid" -> "0-30", "CPU_BFD"
            parts = experiment_name.lower().split('_')
            
            # Find threshold values (they're typically digits)
            threshold = None
            placement = None
            
            if 'cpu' in experiment_name.lower():
                placement = "CPU_BFD"
            elif 'pbfd' in experiment_name.lower() or 'pbdf' in experiment_name.lower():
                placement = "Power_BFD"
            
            # Extract threshold (e.g., "0_30" -> "0-30")
            if len(parts) >= 4:
                threshold = f"{parts[-3]}-{parts[-2]}"
            
            if threshold and placement and not summary.empty:
                data.append({
                    'threshold': threshold,
                    'placement': placement,
                    'energy': summary['total_energy_kwh'].values[0],
                    'experiment': experiment_name
                })
                print(f"Loaded {config['label']}: {summary['total_energy_kwh'].values[0]:.2f} KWh")
        except Exception as e:
            print(f"Error loading {experiment_name}: {e}")
    
    return pd.DataFrame(data), con


def plot_energy_summary(df, baseline_energy, baseline_2_energy):
    """Create summary plot with baselines and experimental data"""
    
    sns.set_style("whitegrid")
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Enforce ordering
    order = ["0-25", "0-30", "5-25", "5-30", "10-25", "10-30", "20-30", "10-90", "20-90"]
    df["threshold"] = pd.Categorical(df["threshold"], categories=order, ordered=True)
    df_sorted = df.sort_values("threshold")
    
    # Plot experimental data
    sns.lineplot(
        data=df_sorted,
        x="threshold",
        y="energy",
        hue="placement",
        style="placement",
        markers=True,
        dashes=True,
        palette=["black", "black"],
        markersize=7,
        ax=ax
    )
    
    # Add baseline lines
    threshold_values = df_sorted["threshold"].unique()
    x_pos = range(len(threshold_values))
    
    # ax.axhline(
    #     y=baseline_energy,
    #     linestyle="-",
    #     color="red",
    #     linewidth=2.0,
    #     alpha=0.7,
    #     label=f"Baseline ({baseline_energy:.0f} KWh)"
    # )
    
    ax.axhline(
        y=baseline_2_energy,
        linestyle="--",
        color="blue",
        linewidth=2.0,
        alpha=0.7,
        label=f"Baseline 2 - Empty=0W ({baseline_2_energy:.0f} KWh)"
    )
    
    ax.set_xlabel("Threshold Range (%)", fontsize=12)
    ax.set_ylabel("Total Energy (KWh)", fontsize=12)
    #ax.set_title("Total Energy Consumption Across VM Consolidation Thresholds", fontsize=14)
    ax.legend(title="Strategy")#, bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(ROOT/"src/plots/energy_consumption_summary_grid.png", dpi=300, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    # Setup paths
    ROOT = Path(__file__).resolve().parents[2]
    RESULTS_DIR = ROOT / "demand_based_results/"
    DATA_DIR = ROOT / "datasets/cloud_energy_consumption/processed"
    
    # Load baseline data
    con = ddb.connect(database=':memory:')
    baseline_energy, baseline_2_energy = load_baseline_data(con, DATA_DIR)
    
    print(f"\nBaseline total energy: {baseline_energy:.2f} KWh")
    print(f"Baseline 2 total energy: {baseline_2_energy:.2f} KWh\n")
    
    # Load all experiments and create dataframe
    df, con = load_all_experiments(RESULTS_DIR)
    
    if not df.empty:
        # Print summary
        print("\n=== Energy Summary ===")
        print(df.sort_values(["placement", "threshold"]))
        
        # Create plot
        plot_energy_summary(df, baseline_energy, baseline_2_energy)
    else:
        print("No experiment data loaded!")
