from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import RidgeCV
import numpy as np
import pandas as pd
from sklearn.metrics import root_mean_squared_error, mean_absolute_error
from pathlib import Path

DEBUG = True

BASE = Path.cwd()

LAG_STEPS =[1, 4, 20, 80]

TARGET = 'ipmi_system_power_watts' # then do it for ipmi_system_power_watts_imputed as well
TRAIN_END_DATE = '2025-02-28 23:59:59'
VAL_END_DATE = '2025-03-31 23:59:59'


def evaluate(model, X, y, dataset_name="Dataset"):
    y_pred = model.predict(X)
    rmse = root_mean_squared_error(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    print(f"{dataset_name} RMSE={rmse:.2f} W MAE={mae:.2f} W")
    return y_pred


clean_df = pd.read_parquet(BASE / "datasets/cloud_energy_consumption/full_nodes_features.parquet")

if DEBUG: print(f"Total rows in dataset: {len(clean_df)}")

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

if DEBUG:
    print(f"Training set: {len(train)} rows")
    print(f"Validation set: {len(val)} rows")
    print(f"Test set: {len(test)} rows")

train_clean = train.dropna(subset=ALL_TABULAR_FEATURES + [TARGET])
val_clean = val.dropna(subset=ALL_TABULAR_FEATURES + [TARGET])
test_clean = test.dropna(subset=ALL_TABULAR_FEATURES + [TARGET])

if DEBUG:
    print(f"Training set after cleaning: {len(train_clean)} rows")
    print(f"Validation set after cleaning: {len(val_clean)} rows")
    print(f"Test set after cleaning: {len(test_clean)} rows")


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

if DEBUG: print("Fitting Model: Ridge Regression with Cross-Validation")

alpha_values = [0.01, 0.1, 1.0, 10.0, 100.0, 1000.0]
ridge_model = RidgeCV(alphas=alpha_values, cv=5)
ridge_model.fit(X_train_scaled, y_train)

print(f"Best alpha: {ridge_model.alpha_:.3f}")
# result: 1.00

_ = evaluate(ridge_model, X_val_scaled, y_val, dataset_name="Validation")
_ = evaluate(ridge_model, X_test_scaled, y_test, dataset_name="Test")

coef_df = pd.DataFrame({'feature': ALL_TABULAR_FEATURES , 'coefficient': ridge_model.coef_,
}).sort_values('coefficient', key=abs, ascending=False) 
print(coef_df.head(15).to_string(index=False))

# Naive baseline RMSE=9.42 W MAE=3.39 W
# Validation RMSE=8.51 W MAE=3.00 W
# Test RMSE=7.62 W MAE=3.01 W

# dropped cpu idle because its just the opposite of cpu usage
# also dropped 'cpu_user_percent' because it was highly correlated with cpu_usage_percent 
