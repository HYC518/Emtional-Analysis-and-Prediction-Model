
import torch
import torch.nn as nn
import matplotlib.pyplot as plt
from datetime import timedelta


class LSTMModel(nn.Module):

    def __init__(self, input_size=1, hidden_size=32, num_layers=2, output_size=1):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers  = num_layers
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc   = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        out, _ = self.lstm(x, (h0, c0))
        return self.fc(out[:, -1, :])


class MoodPredictor:

    def __init__(self, window_size=3, hidden_size=32, num_layers=2,
                 epochs=300, lr=0.01):
        self.window_size = window_size
        self.hidden_size = hidden_size
        self.num_layers  = num_layers
        self.epochs      = epochs
        self.lr          = lr
        self.model       = None
        self.min_val     = None
        self.max_val     = None

    def _normalize(self, data):
        self.min_val = min(data)
        self.max_val = max(data)
        r = self.max_val - self.min_val
        return [0.5] * len(data) if r == 0 else [(x - self.min_val) / r for x in data]

    def _denormalize(self, val):
        r = self.max_val - self.min_val
        return self.min_val if r == 0 else val * r + self.min_val

    def _create_sequences(self, data):
        X, y = [], []
        for i in range(len(data) - self.window_size):
            X.append(data[i:i + self.window_size])
            y.append(data[i + self.window_size])
        return torch.FloatTensor(X).unsqueeze(-1), torch.FloatTensor(y).unsqueeze(-1)

    def train(self, scores: list):
        normed   = self._normalize(scores)
        X, y     = self._create_sequences(normed)
        self.model = LSTMModel(1, self.hidden_size, self.num_layers, 1)
        criterion  = nn.MSELoss()
        optimizer  = torch.optim.Adam(self.model.parameters(), lr=self.lr)
        self.model.train()
        for epoch in range(self.epochs):
            loss = criterion(self.model(X), y)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            if (epoch + 1) % 100 == 0:
                print(f"  Epoch {epoch+1}/{self.epochs}, Loss: {loss.item():.6f}")
        print(f"  Done. Final loss: {loss.item():.6f}")

    def predict(self, scores: list, days: int = 7) -> list:
        self.model.eval()
        normed = self._normalize(scores)
        window = normed[-self.window_size:]
        preds  = []
        with torch.no_grad():
            for _ in range(days):
                x = torch.FloatTensor([window]).unsqueeze(-1)
                p = max(0.0, min(1.0, self.model(x).item()))
                preds.append(p)
                window = window[1:] + [p]
        return [round(max(1, min(5, self._denormalize(p))), 2) for p in preds]

    def plot(self, dates, scores, predicted, title="Mood Trend & Prediction"):
        last   = dates[-1]
        future = [last + timedelta(days=i+1) for i in range(len(predicted))]

        fig, ax = plt.subplots(figsize=(14, 5))
        ax.plot(dates,   scores,    'o-',  color='#1D9E75', lw=2, ms=7, label='Historical')
        ax.plot(future,  predicted, 's--', color='#D85A30', lw=2, ms=7, label='Predicted')
        ax.plot([dates[-1], future[0]], [scores[-1], predicted[0]], '--', color='gray', lw=1, alpha=0.5)
        ax.axvline(x=dates[-1], color='gray', ls=':', alpha=0.5, label='Today')
        ax.axhspan(1, 2, alpha=0.08, color='red')
        ax.axhspan(4, 5, alpha=0.08, color='green')
        for d, s in zip(future, predicted):
            ax.annotate(f'{s}', (d, s), textcoords="offset points",
                        xytext=(0, 12), ha='center', fontsize=9, color='#D85A30')
        ax.set_ylim(0.5, 5.5)
        ax.set_yticks([1, 2, 3, 4, 5])
        ax.set_yticklabels(['1 😞', '2 😔', '3 😐', '4 🙂', '5 😊'])
        ax.set_xlabel('Date')
        ax.set_ylabel('Mood Score')
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
