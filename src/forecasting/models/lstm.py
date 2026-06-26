import torch.nn as nn

class LSTMNetwork(nn.Module):
    def __init__(self, n_features, hidden=64, n_layers=2, dropout=0.3):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=n_features,
            hidden_size=hidden,
            num_layers=n_layers,
            batch_first=True,
            dropout=dropout if n_layers > 1 else 0.0,
        )
        self.drop = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden, 1)

    def forward(self, x):
        # x: (batch, T, n_features)
        out, _ = self.lstm(x)  
        out = self.drop(out[:, -1, :])
        return self.fc(out).squeeze(-1)
    

