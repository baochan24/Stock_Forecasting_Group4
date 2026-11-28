"""Export accepted phase-labelled scores for the seven coursework reports."""
import hashlib,json
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    audit_path=ROOT/read(ROOT/'logs/audit/tv6_item10_latest.json')['evidence']
    audit=read(audit_path)
    if not audit['passed']:raise ValueError('Final audit not accepted')
    folder=audit_path.parent
    output=ROOT/'reports/tables';output.mkdir(exist_ok=True)
    old=(ROOT/read(ROOT/'logs/audit/tv6_item5_latest.json')['evidence']).parent/'metrics.csv'
    new=(ROOT/read(ROOT/'logs/audit/tv6_lstm_completion_latest.json')['evidence']).parent/'metrics.csv'
    original=pd.read_csv(old,float_precision='round_trip');original['evaluation_phase']='original_locked_test'
    residual=pd.read_csv(new,float_precision='round_trip')
    residual=residual[residual.scope=='post_development_test_2024_2025'].copy()
    residual['evaluation_phase']='post_development_old_test'
    columns=['evaluation_phase','method','forecast_length','seed','horizon_step','metric_scope','sample_count','error_count','mae_usd','rmse_usd']
    per_seed=pd.concat([original[columns],residual[columns]],ignore_index=True)
    files={
        'TV6_Final_Comparison.csv':(folder/'comparison.csv').read_bytes(),
        'TV6_Final_Per_Horizon.csv':(folder/'per_horizon.csv').read_bytes(),
        'TV6_Final_Per_Seed.csv':per_seed.to_csv(index=False).encode('utf-8')}
    for name,data in files.items():
        path=output/name
        if path.exists() and path.read_bytes()!=data:raise ValueError('Existing table differs; preserve evidence and choose a new version: '+name)
        if not path.exists():path.write_bytes(data)
    provenance=dict(source_hashes={p.relative_to(ROOT).as_posix():sha(p) for p in [audit_path,old,new]},
        output_hashes={name:sha(output/name) for name in files},per_seed_rows=len(per_seed),
        independent_holdout=False,training=False,note='Mean across predeclared seeds, not an ensemble; phases must remain separate.')
    path=output/'TV6_Final_Tables_Provenance.json';content=json.dumps(provenance,indent=2)+'\n'
    if path.exists() and path.read_text(encoding='utf-8')!=content:raise ValueError('Table provenance differs')
    if not path.exists():path.write_text(content,encoding='utf-8')
    print(json.dumps(dict(passed=True,tables=len(files),per_seed_rows=len(per_seed))))


if __name__=='__main__':main()
