import pandas as pd
import numpy as np
import duckdb
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

# Paths
DATA_DIR = Path('/Users/biancachiusano/Desktop/uva/thesis/energy-aware-vm-consolidation/datasets/cloud_energy_consumption')
NODE_CSV_PATTERN = str(DATA_DIR / 'processed_nodes/*.csv')
NODE_GROUPS_PATH = DATA_DIR / 'node-groups/2024-12-14T000000Z_2025-04-13T235959Z/cleaned_node_groups.csv'
OUTPUT_PATH = DATA_DIR /'engineered_features.parquet'

# Feature engineering parameters
LAG_STEPS = [1, 4, 20, 80]
TARGET = 'ipmi_system_power_watts'
ROLLING_WINDOWS = [20, 80]  # in 3-minute intervals

# Columns to keep in final output
INCLUDE_TIME_FEATURES = False
INCLUDE_LAG_FEATURES = False

# HELPER FUNCTIONS
def load_data() -> pd.DataFrame:
    print("Loading data from CSV files...")
    con = duckdb.connect(':memory:')
    df = con.execute(f"""
        SELECT *
        FROM read_csv_auto('{NODE_CSV_PATTERN}',
                           filename=true,
                           union_by_name=true)
    """).df()
    print(f"Loaded {len(df)} rows")
    return df


def load_node_groups() -> pd.DataFrame:
    """Load node group metadata."""
    print(f"Loading node groups from {NODE_GROUPS_PATH}...")
    return pd.read_csv(NODE_GROUPS_PATH)


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and prepare data for feature engineering."""
    print("Preprocessing data...")
    
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    
    # Handle missing node names
    print(f"Rows with missing node_name: {df['node_name'].isna().sum()}")
    df = df.dropna(subset=['node_name'])
    
    # Convert power columns to numeric
    df['ipmi_system_power_watts'] = pd.to_numeric(df['ipmi_system_power_watts'], errors='coerce')
    df['ipmi_system_power_watts_imputed'] = pd.to_numeric(df['ipmi_system_power_watts_imputed'], errors='coerce')
    df['scaphandre_power_total_watts'] = pd.to_numeric(df['scaphandre_power_total_watts'], errors='coerce')
    df['scaphandre_power_total_watts_imputed'] = pd.to_numeric(df['scaphandre_power_total_watts_imputed'], errors='coerce')
    
    # Check for nulls
    print(f"Null values in {TARGET}: {df[TARGET].isna().sum()}")
    print(f"Null values in {TARGET}_imputed: {df[TARGET + '_imputed'].isna().sum()}")
    
    return df


def reindex_node(group: pd.DataFrame) -> pd.DataFrame:
    """Reindex a node's data to fill gaps with NaN at 3-minute intervals."""
    if group.empty or group['timestamp'].isna().all():
        node = group['node_name'].iloc[0] if not group.empty else '??'
        print(f"Skipping node {node}: no valid timestamps")
        return pd.DataFrame()
    
    full_index = pd.date_range(
        start=group['timestamp'].min(),
        end=group['timestamp'].max(),
        freq='3min',
        tz='UTC'
    )
    
    reindexed = group.set_index('timestamp').reindex(full_index).rename_axis('timestamp').reset_index()
    return reindexed


def reindex_all_nodes(df: pd.DataFrame) -> pd.DataFrame:
    """Reindex all nodes to fill gaps."""
    print("Reindexing nodes to fill gaps...")
    nodes = df['node_name'].unique()
    print(f"Processing {len(nodes)} nodes...")
    
    chunks = []
    for node in nodes:
        temp_df = df[df['node_name'] == node]
        if not temp_df.empty and not temp_df['timestamp'].isna().all():
            reindexed = reindex_node(temp_df)
            if not reindexed.empty:
                chunks.append(reindexed)
    
    result = pd.concat(chunks, ignore_index=True)
    print(f"After reindexing: {len(result)} rows")
    return result


def engineer_operational_features(df: pd.DataFrame) -> tuple[pd.DataFrame, list]:
    """Create operational features from system metrics."""
    print("Engineering operational features...")
    
    # Processes
    df['processes_util_ratio'] = df['num_processes_running'] / df['num_processes_total']
    df['processes_blocked_ratio'] = df['num_processes_blocked'] / df['num_processes_total']
    
    # Memory
    df['memory_util_ratio'] = df['memory_used_bytes'] / df['memory_total_bytes']
    
    # Disk
    df['disk_util_ratio'] = df['disk_used_bytes'] / df['disk_total_bytes']
    
    operational_features = [
        # Percentages
        'cpu_usage_percent', 'cpu_user_percent', 'cpu_idle_percent', 
        'cpu_system_percent', 'cpu_wait_percent', 'cpu_nice_percent', 'cpu_interrupt_percent',
        'load_shortterm_percent', 'load_midterm_percent', 'load_longterm_percent',
        # Ratios
        'memory_util_ratio', 'disk_util_ratio', 'processes_util_ratio', 'processes_blocked_ratio',
    ]
    
    return df, operational_features


def engineer_time_features(df: pd.DataFrame) -> tuple[pd.DataFrame, list]:
    """Create time-based features with cyclical encoding."""
    print("Engineering time features...")
    
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    
    # Cyclical encoding
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
    df['day_of_week_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
    df['day_of_week_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
    
    time_features = [
        'hour', 'day_of_week', 'is_weekend',
        'hour_sin', 'hour_cos', 'day_of_week_sin', 'day_of_week_cos'
    ]
    
    return df, time_features


def make_lag_features(group: pd.DataFrame) -> pd.DataFrame:
    """Create lag and rolling features for a node group."""
    for lag in LAG_STEPS:
        group[f'power_lag_{lag}'] = group[TARGET].shift(lag)
        group[f'cpu_lag_{lag}'] = group['cpu_usage_percent'].shift(lag)
    
    # Rolling mean windows
    for window in ROLLING_WINDOWS:
        group[f'power_rolling_mean_{window}'] = group[TARGET].rolling(window=window).mean()
    
    # Rolling std
    for window in ROLLING_WINDOWS:
        group[f'power_rolling_std_{window}'] = group[TARGET].rolling(window=window).std()
    
    return group


def engineer_lag_features(df: pd.DataFrame) -> tuple[pd.DataFrame, list]:
    """Create lag and rolling window features."""
    print("Engineering lag features...")
    
    chunks = []
    for node_name, group in df.groupby('node_name'):
        group = make_lag_features(group)
        # Drop NaN values created by lag features (first 80 rows per node)
        chunks.append(group.iloc[80:])
    
    result = pd.concat(chunks, ignore_index=True)
    
    lag_features = (
        [f'power_lag_{lag}' for lag in LAG_STEPS] +
        [f'cpu_lag_{lag}' for lag in LAG_STEPS] +
        [f'power_rolling_mean_{window}' for window in ROLLING_WINDOWS] +
        [f'power_rolling_std_{window}' for window in ROLLING_WINDOWS]
    )
    
    print(f"After lag feature engineering: {len(result)} rows")
    return result, lag_features


def engineer_hardware_features(df: pd.DataFrame) -> tuple[pd.DataFrame, list]:
    """Create hardware-related features."""
    print("Engineering hardware features...")
    
    df['has_gpu'] = (df['#gpus'] > 0).astype(int)
    
    hardware_features = [
        'memory_size_gb', 'total_threads', 'total_cores',
        'rated_power_usable', 'cpu_freq_ghz', 'has_gpu'
    ]
    
    return df, hardware_features


def select_final_columns(df: pd.DataFrame, operational_features: list, hardware_features: list, time_features=None,
                        lag_features=None) -> pd.DataFrame:
    """Select and order final columns."""
    print("Selecting final columns...")
    
    # Core columns to always keep
    core_columns = [
        'timestamp', 'node_name', 'node_group',
        'memory_total_bytes', 'memory_used_bytes', 'memory_free_bytes',
        'ipmi_system_power_watts', 'ipmi_system_power_watts_imputed',
        'scaphandre_power_total_watts', 'scaphandre_power_total_watts_imputed'
    ]
    
    # Build column list
    selected_columns = core_columns + operational_features + hardware_features
    
    if INCLUDE_TIME_FEATURES:
        selected_columns.extend(time_features)
    
    if INCLUDE_LAG_FEATURES:
        selected_columns.extend(lag_features)
    
    # Filter to only columns that exist
    selected_columns = [col for col in selected_columns if col in df.columns]
    
    final_df = df[selected_columns].sort_values(['node_name', 'timestamp']).reset_index(drop=True)
    
    print(f"Final dataset shape: {final_df.shape}")
    print(f"Columns: {len(final_df.columns)}")
    
    return final_df


def save_output(df: pd.DataFrame, output_path: Path) -> None:
    """Save processed dataset to disk."""
    #output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Saving to {output_path} as Parquet")
    df.to_parquet(output_path, index=False)
    
    print(f"✓ Saved successfully")


def main():
    """Run the full feature engineering pipeline."""
    print("=" * 70)
    print("FEATURE ENGINEERING PIPELINE")
    print("=" * 70)
    
    try:
        # Load raw data
        df = load_data()
        node_groups = load_node_groups()
        
        # Preprocess
        df = preprocess_data(df)
        
        # Reindex
        df = reindex_all_nodes(df)
        
        # Merge with node groups
        print("Merging with node group metadata...")
        df = df.merge(node_groups, on='node_group', how='left')
        
        # Engineer features
        df, operational_features = engineer_operational_features(df)
        #df, time_features = engineer_time_features(df)
        #df, lag_features = engineer_lag_features(df)
        df, hardware_features = engineer_hardware_features(df)
        
        # Select final columns
        #df = select_final_columns(df, operational_features, time_features, lag_features, hardware_features)
        df = select_final_columns(df, operational_features, hardware_features)
        
        # Save
        save_output(df, OUTPUT_PATH)
        
        print("✓ Feature engineering completed successfully")
        
    except Exception as e:
        print(f"Error during feature engineering: {e}")
        raise


if __name__ == '__main__':
    main()