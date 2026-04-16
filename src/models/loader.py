from pathlib import Path
import pandas as pd
from sklearn.preprocessing import StandardScaler

BASE = Path.cwd()

LAG_STEPS =[1, 4, 20, 80]

TARGET = 'ipmi_system_power_watts' # then do it for ipmi_system_power_watts_imputed as well
TRAIN_END_DATE = '2025-02-28 23:59:59'
VAL_END_DATE = '2025-03-31 23:59:59'

clean_df = pd.read_parquet(BASE / "datasets/cloud_energy_consumption/full_nodes_featurestwo.parquet")

operational_features = [
    # Percentages
    'cpu_usage_percent', 'cpu_system_percent', 'cpu_wait_percent', 'cpu_nice_percent', 'cpu_interrupt_percent', 
    'load_shortterm_percent', 'load_midterm_percent', 'load_longterm_percent',
    # Ratios
    'memory_util_ratio', 'disk_util_ratio', 'processes_util_ratio', 'processes_blocked_ratio',
    ]

time_features = ['hour', 'day_of_week', 'is_weekend', 'hour_sin', 'hour_cos', 'day_of_week_sin', 'day_of_week_cos']

lag_features = ([f'power_lag_{lag}' for lag in LAG_STEPS] + 
                [f'cpu_lag_{lag}' for lag in LAG_STEPS] + 
                ['power_rolling_mean_20', 'power_rolling_mean_80', 'power_rolling_std_20'])

hardware_features = ['total_threads', 'total_cores', 'rated_power_usable', 'cpu_freq_ghz', 'has_gpu']

ALL_TABULAR_FEATURES = operational_features + time_features + lag_features + hardware_features

train = clean_df[clean_df['timestamp'] <= TRAIN_END_DATE]
val = clean_df[(clean_df['timestamp'] > TRAIN_END_DATE) & (clean_df['timestamp'] <= VAL_END_DATE)]
test = clean_df[clean_df['timestamp'] > VAL_END_DATE]

train_clean = train.dropna(subset=ALL_TABULAR_FEATURES + [TARGET])
val_clean = val.dropna(subset=ALL_TABULAR_FEATURES + [TARGET])
test_clean = test.dropna(subset=ALL_TABULAR_FEATURES + [TARGET])


X_train = train_clean[ALL_TABULAR_FEATURES]
y_train = train_clean[TARGET]

X_val = val_clean[ALL_TABULAR_FEATURES]
y_val = val_clean[TARGET]

X_test = test_clean[ALL_TABULAR_FEATURES]
y_test = test_clean[TARGET]

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

