import pandas as pd
import numpy as np
import duckdb
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

# Paths
DATA_DIR = Path('/Users/biancachiusano/Desktop/uva/thesis/energy-aware-vm-consolidation/datasets/cloud_energy_consumption')

NODE_CSV_PATTERN = str(DATA_DIR / 'nodes/2024-12-14T000000Z_2025-04-13T235959Z/**/*.csv')

NODE_GROUPS_PATH = (
    DATA_DIR/ 'node-groups/2024-12-14T000000Z_2025-04-13T235959Z/cleaned_node_groups.csv'
)

OUTPUT_PATH = DATA_DIR / 'engineered_features_new.parquet'

# Feature engineering parameters
LAG_STEPS = [1, 4, 20, 80]
TARGET = 'ipmi_system_power_watts'
ROLLING_WINDOWS = [20, 80]  # 3-minute intervals

# Optional features
INCLUDE_TIME_FEATURES = False
INCLUDE_LAG_FEATURES = False

select_cols = "timestamp, node_name, node_group, \
memory_total_bytes, memory_used_bytes, memory_free_bytes, \
disk_total_bytes, disk_used_bytes, \
num_processes_running, num_processes_total, num_processes_blocked \
cpu_usage_percent, cpu_user_percent, cpu_idle_percent ,cpu_system_percent, \
cpu_wait_percent, cpu_nice_percent, cpu_interrupt_percent, \
load_shortterm_percent, load_midterm_percent, load_longterm_percent, \
ipmi_system_power_watts, scaphandre_power_total_watts"

print("Selected columns for duckdb:", select_cols)

# ============================================================================
# LOAD DATA
# ============================================================================

def load_data() -> pd.DataFrame:
    print("Loading node CSV files...")

    con = duckdb.connect(':memory:')

    df = con.execute(f"""
        SELECT *
        FROM read_csv_auto(
            '{NODE_CSV_PATTERN}',
            filename=true,
            union_by_name=true
        )
    """).df()

    print(f"Loaded {len(df)} rows")

    return df


def load_node_groups() -> pd.DataFrame:
    print(f"Loading node groups from {NODE_GROUPS_PATH}")

    return pd.read_csv(NODE_GROUPS_PATH)


# ============================================================================
# PREPROCESSING
# ============================================================================

def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:

    print("Preprocessing data...")

    # Timestamp
    df['timestamp'] = pd.to_datetime(
        df['timestamp'],
        utc=True,
        errors='coerce'
    )

    # Remove rows without node names
    print("Missing node_name rows:",
          df['node_name'].isna().sum())

    df = df.dropna(subset=['node_name'])

    # Remove invalid node names
    invalid_names = ['inf', '-inf', 'nan', 'None']

    df = df[
        ~df['node_name']
        .astype(str)
        .isin(invalid_names)
    ]

    # Numeric conversion
    numeric_columns = [
        'ipmi_system_power_watts',
        'scaphandre_power_total_watts',

        'memory_total_bytes',
        'memory_used_bytes',
        'memory_free_bytes',

        'disk_total_bytes',
        'disk_used_bytes',

        'num_processes_running',
        'num_processes_total',
        'num_processes_blocked',

        'cpu_usage_percent',
        'cpu_user_percent',
        'cpu_idle_percent',
        'cpu_system_percent',
        'cpu_wait_percent',
        'cpu_nice_percent',
        'cpu_interrupt_percent',

        'load_shortterm_percent',
        'load_midterm_percent',
        'load_longterm_percent'
    ]

    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors='coerce'
            )

    # Replace infinities globally
    df = df.replace([np.inf, -np.inf], np.nan)

    print(f"Rows after preprocessing: {len(df)}")

    return df


# ============================================================================
# REINDEXING
# ============================================================================

def reindex_node(group: pd.DataFrame) -> pd.DataFrame:
    """
    Reindex one node to a regular 3-minute time grid.
    Missing telemetry becomes NaN.
    """

    if group.empty:
        return pd.DataFrame()

    if group['timestamp'].isna().all():
        return pd.DataFrame()

    # Static identifiers
    node_name = group['node_name'].iloc[0]
    node_group = group['node_group'].iloc[0]

    full_index = pd.date_range(
        start=group['timestamp'].min(),
        end=group['timestamp'].max(),
        freq='3min',
        tz='UTC'
    )

    reindexed = (
        group
        .set_index('timestamp')
        .reindex(full_index)
        .rename_axis('timestamp')
        .reset_index()
    )

    # Restore static identifiers
    reindexed['node_name'] = node_name
    reindexed['node_group'] = node_group

    # Interpolate numeric telemetry
    numeric_cols = reindexed.select_dtypes(
        include=[np.number]
    ).columns

    reindexed[numeric_cols] = (
        reindexed[numeric_cols]
        .interpolate(method='linear')
    )

    # Replace remaining infinities
    reindexed = reindexed.replace(
        [np.inf, -np.inf],
        np.nan
    )

    return reindexed


def reindex_all_nodes(df: pd.DataFrame) -> pd.DataFrame:

    print("Reindexing all nodes...")

    nodes = df['node_name'].unique()

    print(f"Found {len(nodes)} nodes")

    chunks = []

    for node in nodes:

        temp_df = df[df['node_name'] == node]

        if temp_df.empty:
            continue

        reindexed = reindex_node(temp_df)

        if not reindexed.empty:
            chunks.append(reindexed)

    result = pd.concat(
        chunks,
        ignore_index=True
    )

    # Final cleanup
    result = result.replace(
        [np.inf, -np.inf],
        np.nan
    )

    print("Rows after reindexing:",
          len(result))

    print("Remaining null node names:",
          result['node_name'].isna().sum())

    return result


# ============================================================================
# OPERATIONAL FEATURES
# ============================================================================

def safe_divide(numerator, denominator):

    return np.where(
        denominator > 0,
        numerator / denominator,
        np.nan
    )


def engineer_operational_features(
    df: pd.DataFrame
) -> tuple[pd.DataFrame, list]:

    print("Engineering operational features...")

    # Processes
    df['processes_util_ratio'] = safe_divide(
        df['num_processes_running'],
        df['num_processes_total']
    )

    df['processes_blocked_ratio'] = safe_divide(
        df['num_processes_blocked'],
        df['num_processes_total']
    )

    # Memory
    df['memory_util_ratio'] = safe_divide(
        df['memory_used_bytes'],
        df['memory_total_bytes']
    )

    # Disk
    df['disk_util_ratio'] = safe_divide(
        df['disk_used_bytes'],
        df['disk_total_bytes']
    )

    operational_features = [
        'cpu_usage_percent',
        'cpu_user_percent',
        'cpu_idle_percent',
        'cpu_system_percent',
        'cpu_wait_percent',
        'cpu_nice_percent',
        'cpu_interrupt_percent',

        'load_shortterm_percent',
        'load_midterm_percent',
        'load_longterm_percent',

        'memory_util_ratio',
        'disk_util_ratio',

        'processes_util_ratio',
        'processes_blocked_ratio'
    ]

    return df, operational_features


# ============================================================================
# HARDWARE FEATURES
# ============================================================================

def engineer_hardware_features(
    df: pd.DataFrame
) -> tuple[pd.DataFrame, list]:

    print("Engineering hardware features...")

    df['has_gpu'] = (
        df['#gpus'] > 0
    ).astype(int)

    hardware_features = [
        'memory_size_gb',
        'total_threads',
        'total_cores',
        'rated_power_usable',
        'cpu_freq_ghz',
        'has_gpu'
    ]

    return df, hardware_features


# ============================================================================
# LAG FEATURES
# ============================================================================

def make_lag_features(group: pd.DataFrame) -> pd.DataFrame:

    for lag in LAG_STEPS:

        group[f'power_lag_{lag}'] = (
            group[TARGET].shift(lag)
        )

        group[f'cpu_lag_{lag}'] = (
            group['cpu_usage_percent'].shift(lag)
        )

    for window in ROLLING_WINDOWS:

        group[f'power_rolling_mean_{window}'] = (
            group[TARGET]
            .rolling(window=window)
            .mean()
        )

        group[f'power_rolling_std_{window}'] = (
            group[TARGET]
            .rolling(window=window)
            .std()
        )

    return group


def engineer_lag_features(
    df: pd.DataFrame
) -> tuple[pd.DataFrame, list]:

    print("Engineering lag features...")

    chunks = []

    for node_name, group in df.groupby('node_name'):

        group = make_lag_features(group)

        # remove first rows affected by lag
        group = group.iloc[max(LAG_STEPS):]

        chunks.append(group)

    result = pd.concat(
        chunks,
        ignore_index=True
    )

    lag_features = (
        [f'power_lag_{lag}' for lag in LAG_STEPS]
        +
        [f'cpu_lag_{lag}' for lag in LAG_STEPS]
        +
        [f'power_rolling_mean_{w}' for w in ROLLING_WINDOWS]
        +
        [f'power_rolling_std_{w}' for w in ROLLING_WINDOWS]
    )

    return result, lag_features


# ============================================================================
# FINAL COLUMN SELECTION
# ============================================================================

def select_final_columns(
    df: pd.DataFrame,
    operational_features: list,
    hardware_features: list,
    time_features=None,
    lag_features=None
) -> pd.DataFrame:

    print("Selecting final columns...")

    core_columns = [
        'timestamp',
        'node_name',
        'node_group',

        'memory_total_bytes',
        'memory_used_bytes',
        'memory_free_bytes',

        'ipmi_system_power_watts',
        'scaphandre_power_total_watts',
    ]

    selected_columns = (
        core_columns
        + operational_features
        + hardware_features
    )

    if INCLUDE_TIME_FEATURES and time_features:
        selected_columns.extend(time_features)

    if INCLUDE_LAG_FEATURES and lag_features:
        selected_columns.extend(lag_features)

    selected_columns = [
        col for col in selected_columns
        if col in df.columns
    ]

    final_df = (
        df[selected_columns]
        .sort_values(['node_name', 'timestamp'])
        .reset_index(drop=True)
    )

    print(f"Final shape: {final_df.shape}")

    return final_df


# ============================================================================
# SAVE
# ============================================================================

def save_output(df: pd.DataFrame, output_path: Path):

    print(f"Saving parquet to {output_path}")

    df.to_parquet(
        output_path,
        index=False
    )

    print("✓ Save complete")


# ============================================================================
# MAIN
# ============================================================================

def main():

    print("=" * 70)
    print("FEATURE ENGINEERING PIPELINE")
    print("=" * 70)

    # Load
    df = load_data()

    node_groups = load_node_groups()

    # Preprocess
    df = preprocess_data(df)

    # Reindex
    df = reindex_all_nodes(df)

    # Merge node metadata
    print("Merging node group metadata...")

    df = df.merge(
        node_groups,
        on='node_group',
        how='left'
    )

    # Features
    df, operational_features = (
        engineer_operational_features(df)
    )

    df, hardware_features = (
        engineer_hardware_features(df)
    )

    # Optional lag features
    if INCLUDE_LAG_FEATURES:

        df, lag_features = engineer_lag_features(df)

    else:
        lag_features = None

    # Final selection
    df = select_final_columns(
        df,
        operational_features,
        hardware_features,
        lag_features=lag_features
    )

    # Final cleanup
    df = df.replace(
        [np.inf, -np.inf],
        np.nan
    )

    # Remove corrupted node names
    df = df.dropna(subset=['node_name'])

    # Save
    save_output(df, OUTPUT_PATH)

    print("✓ Feature engineering completed successfully")


if __name__ == '__main__':
    main()