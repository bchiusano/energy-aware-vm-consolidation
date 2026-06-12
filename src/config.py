from pathlib import Path

BASE = Path.cwd()
DATAPATH = BASE / "datasets/cloud_energy_consumption/features.parquet"
CHECKPOINT   = BASE / "src/checkpoints/best_lstm.pt"

T = 80 # 4 hours at 3-minute resolution
BATCH_SIZE = 512
TARGET = 'ipmi_system_power_watts' # then do it for ipmi_system_power_watts_imputed as well
TRAIN_END_DATE = '2025-02-28 23:59:59'
VAL_END_DATE = '2025-03-31 23:59:59'
LAG_STEPS =[1, 4, 20, 80]

OPERATIONAL_FEATURES = [
    # Percentages
    'cpu_usage_percent', 'cpu_system_percent', 'cpu_wait_percent', 'cpu_nice_percent', 'cpu_interrupt_percent', 
    'load_shortterm_percent', 'load_midterm_percent', 'load_longterm_percent',
    # Ratios
    'memory_util_ratio', 'disk_util_ratio', 'processes_util_ratio', 'processes_blocked_ratio',
    ]

TIME_FEATURES = ['hour', 'day_of_week', 'is_weekend', 'hour_sin', 'hour_cos', 'day_of_week_sin', 'day_of_week_cos']

LAG_FEATURES = ([f'power_lag_{lag}' for lag in LAG_STEPS] + 
                [f'cpu_lag_{lag}' for lag in LAG_STEPS] + 
                ['power_rolling_mean_20', 'power_rolling_mean_80', 'power_rolling_std_20'])

HARDWARE_FEATURES = ['total_threads', 'total_cores', 'rated_power_usable', 'cpu_freq_ghz', 'has_gpu']

ALL_TABULAR_FEATURES = OPERATIONAL_FEATURES + TIME_FEATURES + LAG_FEATURES + HARDWARE_FEATURES
#LSTM_FEATURES = OPERATIONAL_FEATURES + TIME_FEATURES