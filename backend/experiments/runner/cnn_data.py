"""CNN consumer inputs reuse the accepted one-step data factory."""
from backend.experiments.runner.aapl_factories import make_aapl_loaders


def make_cnn_comparison_loaders(reference_config, seed, *, project_root):
    """Return unchanged CPU float64 (B,30,1) inputs, targets and sample IDs.

    reference_config is the locked LSTM comparison data configuration.
    This function performs no fitting, model selection or training.
    """
    data = reference_config['data']
    if (reference_config['model_type'] != 'lstm_one_step'
            or data['lookback'] != 30 or data['forecast_length'] != 1
            or data.get('common_history') is not True):
        raise ValueError('CNN comparison requires the locked one-step lookback30 common-history reference')
    return make_aapl_loaders(reference_config, seed, project_root=project_root)
