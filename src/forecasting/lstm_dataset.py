import numpy as np
import torch
from torch.utils.data import Dataset

class NodeSequenceDataset(Dataset):
    def __init__(self, df, feature_cols, target_col, T):
        self.T        = T
        self.X        = df[feature_cols].values.astype(np.float32)
        self.y        = df[target_col].values.astype(np.float32)
        self.n        = len(df) - T

    def __len__(self):
        return self.n

    def __getitem__(self, idx):
        return (
            torch.tensor(self.X[idx : idx + self.T]),
            torch.tensor(self.y[idx + self.T]),
        )