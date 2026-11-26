"""Export completed TV4 epoch CSVs as TensorBoard scalar events."""
import csv
import argparse
import json
from pathlib import Path
import time

from tensorboard.compat.proto import event_pb2, summary_pb2
from tensorboard.summary.writer.event_file_writer import EventFileWriter

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, default=ROOT / 'logs/audit/tv4_item8_20261125T122649342552Z/summary.json')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    source = args.summary.resolve()
    receipt = json.loads(source.read_text(encoding='utf-8'))
    assert receipt['passed'] and receipt['status'] == 'completed'
    output = args.output.resolve() if args.output else ROOT / 'logs/tensorboard' / source.parent.name
    if output.exists():
        raise FileExistsError(f'Already exported: {output}')
    for run in receipt['results']:
        name = f"lookback_{run['lookback']}/seed_{run['seed']}"
        writer = EventFileWriter(str(output / name))
        try:
            with (Path(run['run_dir']) / 'epoch_logs.csv').open(encoding='utf-8') as stream:
                rows = list(csv.DictReader(stream))
            assert len(rows) == run['epochs']
            for row in rows:
                fields = {'Loss/train': float(row['train_loss']),
                          'Loss/validation': float(row['val_loss']),
                          'Optimizer/learning_rate': float(row['learning_rate']),
                          'Time/train_seconds': float(row['train_seconds']),
                          'Time/validation_seconds': float(row['validation_seconds'])}
                for index, value in enumerate(json.loads(row.get('val_mse_per_horizon') or '[]'), 1):
                    fields[f'Horizon/validation_mse_{index}'] = value
                summary = summary_pb2.Summary(value=[summary_pb2.Summary.Value(tag=k, simple_value=v)
                                                     for k, v in fields.items()])
                writer.add_event(event_pb2.Event(wall_time=time.time(), step=int(row['epoch']), summary=summary))
        finally:
            writer.close()
    (output / 'export.json').write_text(json.dumps(dict(source=str(source), runs=len(receipt['results']),
        epoch_counts=[r['epochs'] for r in receipt['results']], note='Historical CSV export. Wall time is export time.'), indent=2))
    print(output)


if __name__ == '__main__':
    main()
