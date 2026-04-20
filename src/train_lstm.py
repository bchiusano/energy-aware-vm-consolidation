import torch
import torch.nn as nn
import pandas as pd
from torch.utils.data import DataLoader
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import root_mean_squared_error, mean_absolute_error

from lstm_dataset import NodeSequenceDataset
from models.lstm import LSTMNetwork
from config import *

# loading data
clean_df = pd.read_parquet(DATAPATH)

# per-node scaling and split
train_dfs, val_dfs, test_dfs = [], [], []

for node, group in clean_df.groupby('node_name'):

    train_group = group[group['timestamp'] <= TRAIN_END_DATE].copy()
    val_group   = group[(group['timestamp'] > TRAIN_END_DATE) & 
                        (group['timestamp'] <= VAL_END_DATE)].copy()
    test_group  = group[group['timestamp'] > VAL_END_DATE].copy()

    # drop NaN rows before building sequences - lstms do not work well with missing data 
    train_group = train_group.dropna(subset=LSTM_FEATURES + [TARGET])
    val_group   = val_group.dropna(subset=LSTM_FEATURES + [TARGET])
    test_group  = test_group.dropna(subset=LSTM_FEATURES + [TARGET])

    # skip if not enough rows to form even one sequence
    if len(train_group) <= T or len(val_group) <= T or len(test_group) <= T:
        print(f"Skipping {node}: insufficient rows in one or more splits")
        continue

    # scale
    print(f"Scaling features for node: {node}")
    scaler = StandardScaler()
    train_group[LSTM_FEATURES] = scaler.fit_transform(train_group[LSTM_FEATURES])
    val_group[LSTM_FEATURES]   = scaler.transform(val_group[LSTM_FEATURES])
    test_group[LSTM_FEATURES]  = scaler.transform(test_group[LSTM_FEATURES])

    train_dfs.append(train_group)
    val_dfs.append(val_group)
    test_dfs.append(test_group)

train_df = pd.concat(train_dfs, ignore_index=True)
val_df = pd.concat(val_dfs, ignore_index=True)
test_df = pd.concat(test_dfs, ignore_index=True)

# build dataloaders
print("Building DataLoaders...")
train_loader = DataLoader(NodeSequenceDataset(train_df, LSTM_FEATURES, TARGET, T), batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(NodeSequenceDataset(val_df, LSTM_FEATURES, TARGET, T), batch_size=BATCH_SIZE)
test_loader = DataLoader(NodeSequenceDataset(test_df, LSTM_FEATURES, TARGET, T), batch_size=BATCH_SIZE)

# train model
print("Training LSTM...")
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

model = LSTMNetwork(len(LSTM_FEATURES)).to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, factor=0.5, patience=5)
criterion = nn.MSELoss()

best_val_loss = float('inf')
patience, patience_counter = 10, 0

train_loss_history, val_loss_history = [], []

for epoch in range(1, 201):
    print(f"Epoch {epoch} starting...")
    model.train()
    train_losses = []
    for X_batch, y_batch in train_loader:
        X_batch, y_batch = X_batch.to(device), y_batch.to(device)
        optimizer.zero_grad()
        preds = model(X_batch)
        loss = criterion(preds, y_batch)
        loss.backward()
        optimizer.step()
        train_losses.append(loss.item())

    train_loss = sum(train_losses) / len(train_losses)
    train_loss_history.append(train_loss)

    model.eval()
    val_losses = []
    with torch.no_grad():
        for X_batch, y_batch in val_loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            preds = model(X_batch)
            val_losses.append(criterion(preds, y_batch).item())

    val_loss = sum(val_losses) / len(val_losses)
    val_loss_history.append(val_loss)
    scheduler.step(val_loss)

    if epoch % 10 == 0:
        print(f"Epoch {epoch} - Train Loss: {train_loss:.4f} - Val Loss: {val_loss:.4f}")

    if val_loss < best_val_loss:
        best_val_loss = val_loss
        patience_counter = 0
        torch.save(model.state_dict(), CHECKPOINT)
    else:
        patience_counter += 1
        if patience_counter >= patience:
            print(f"Early stopping triggered at epoch: {epoch}")
            break


print("Training complete.")
# Plot training and validation loss
plt.figure(figsize=(8, 4))
plt.plot(train_loss_history, label='Train loss')
plt.plot(val_loss_history,   label='Val loss')
plt.xlabel('Epoch')
plt.ylabel('MSE Loss')
plt.title('LSTM Training Curve')
plt.legend()
plt.tight_layout()
plt.savefig('lstm_loss_curve.png', dpi=150, bbox_inches='tight')
plt.close()

print("Evaluating on test set...")
# Test model
model.load_state_dict(torch.load(CHECKPOINT))
model.eval()

all_preds, all_targets = [], []
with torch.no_grad():
    for X_batch, y_batch in test_loader:
        X_batch = X_batch.to(device)
        preds = model(X_batch).cpu().numpy()
        all_preds.extend(preds)
        all_targets.extend(y_batch.numpy())

rmse_lstm = root_mean_squared_error(all_targets, all_preds)
mae_lstm  = mean_absolute_error(all_targets, all_preds)
print(f"LSTM Test RMSE: {rmse_lstm:.2f} W, MAE: {mae_lstm:.2f} W")