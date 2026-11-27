"""Development ablation: same LSTM parameters, mean sequence readout only."""
import torch
from .model import LSTMOneStep


class LSTMMeanReadout(LSTMOneStep):
    def forward(self,x):
        self._validate_input(x)
        sequence,_=self.lstm(x,self._initial_state(x))
        prediction=self.fc(sequence.mean(dim=1))
        if not torch.isfinite(prediction).all():raise FloatingPointError('Nonfinite mean-readout output')
        return prediction
