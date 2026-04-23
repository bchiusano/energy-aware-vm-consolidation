import xgboost as xgb
import shap
from ..config import *
import itertools
from sklearn.metrics import root_mean_squared_error, mean_absolute_error
from xgboost.callback import EarlyStopping
import shap
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# https://mljar.com/blog/visualize-xgboost-tree/

param_grid = {
    'max_depth':        [4, 6],
    'learning_rate':    [0.05, 0.1],
    'subsample':        [0.8, 1.0],
    'colsample_bytree': [0.8, 1.0],
}

def compute_search():

    best_rmse   = float('inf')
    best_params = {}
    best_model  = None

    # all combinations
    keys   = list(param_grid.keys())
    combos = list(itertools.product(*param_grid.values()))

    for i, combo in enumerate(combos):
        params = dict(zip(keys, combo))
        print(f"[{i+1}/{len(combos)}] Testing {params}")

        model = xgb.XGBRegressor(
        **params,
        n_estimators=1000,
        random_state=42,
        n_jobs=-1,
        eval_metric='rmse',
        callbacks=[EarlyStopping(rounds=50, save_best=True)],
        )

        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False,
        )

        val_preds = model.predict(X_val)
        val_rmse  = root_mean_squared_error(y_val, val_preds)
        print(f"val RMSE={val_rmse:.3f}  best_iteration={model.best_iteration}")

        if val_rmse < best_rmse:
            best_rmse   = val_rmse
            best_params = params
            best_model  = model

    print(f"\nBest params: {best_params}")
    print(f"Best val RMSE: {best_rmse:.3f}")

    return best_model


def evaluate(model, X, y, dataset_name="Dataset"):
    y_pred = model.predict(X)
    rmse = root_mean_squared_error(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    print(f"{dataset_name} RMSE={rmse:.2f} W MAE={mae:.2f} W")
    return y_pred

# load data
clean_df = pd.read_parquet(DATAPATH)

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

# for hyperparameter search
#best_model = compute_search()

#Best params: {'max_depth': 6, 'learning_rate': 0.1, 'subsample': 1.0, 'colsample_bytree': 0.8}
#Best val RMSE: 7.013
# After tuning - training final model
model = xgb.XGBRegressor(
        max_depth = 6,
        learning_rate = 0.1,
        subsample=1.0,
        colsample_bytree=0.8,
        n_estimators=2000,
        random_state=42,
        n_jobs=-1,
        eval_metric='rmse',
        callbacks=[EarlyStopping(rounds=50, save_best=True)],
        )

model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    verbose=False,
)

# Evaluation
print(f"best iteration: {model.best_iteration}")
_ = evaluate(model, X_val, y_val, "XGBoost (validation)")
xgboost_test_preds = evaluate(model, X_test, y_test, "XGBoost (test)")

# display predictions vs true values
plt.figure(figsize=(8, 6))
plt.plot(xgboost_test_preds, label='Test predictions')
plt.plot(y_test.values, label='True values')
plt.xlabel('Data Point')
plt.ylabel('Target Value')
plt.title('XGBoost Predictions vs True Values')
plt.legend()
plt.tight_layout()
plt.savefig('xgboost_predictions.png', dpi=150, bbox_inches='tight')
plt.close()

# SHAP
'''
X_test_sample = X_test.sample(n=10_000, replace=False, random_state=42)

explainer = shap.TreeExplainer(model)
shap_values = explainer(X_test_sample) 

# bar plot
shap.plots.bar(shap_values, show=False)
plt.tight_layout()
plt.savefig('shap_bar.png', bbox_inches='tight', dpi=150)
plt.close()

# beeswarm
shap.plots.beeswarm(shap_values, show=False)
plt.tight_layout()
plt.savefig('shap_beeswarm.png', bbox_inches='tight', dpi=150)
plt.close()

# violin
shap.plots.violin(
    shap_values,
    features=X_test_sample,
    feature_names=X_test_sample.columns, # should correspond to all tabular features
    plot_type="layered_violin",
    show=False,
)
plt.tight_layout()
plt.savefig('shap_violin.png', bbox_inches='tight', dpi=150)
plt.close()
'''
#best iteration: 1185
#XGBoost (validation) RMSE=7.00 W MAE=2.70 W
#XGBoost (test) RMSE=6.58 W MAE=2.86 W