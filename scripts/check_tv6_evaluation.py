"""TV6 item4 evaluate existing validation outputs only; no test inference."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.audit.tv6_protocol import validate_protocol,PROTOCOL_PATH
from backend.evaluation.forecast_records import evaluate_forecast_records,load_validation_cohorts


def main():
    protocol=json.loads((ROOT/PROTOCOL_PATH).read_text())
    sha=validate_protocol(protocol,ROOT)
    source_pointer=json.loads((ROOT/'logs/audit/tv6_item3_latest.json').read_text())
    source=ROOT/source_pointer['evidence'];receipt=json.loads(source.read_text())
    if not receipt['passed'] or receipt['test_inference_enabled'] or receipt['protocol_sha256']!=sha:
        raise ValueError('Unexpected inference receipt scope/protocol')
    predictions=pd.read_csv(source.parent/'validation_inference_usd.csv',float_precision='round_trip')
    actuals=[];raw_last={}
    for cohort in protocol['semantic']['cohorts']:
        h=cohort['forecast_length'];prepared=ROOT/'data/prepared'/cohort['prepared_id']
        inputs=json.loads((prepared/f'f{h}_val_inputs.json').read_text())
        targets=json.loads((prepared/f'f{h}_val_targets.json').read_text())
        for x,y in zip(inputs,targets):
            if x['sample_id']!=y['sample_id'] or y['split']!='val':raise ValueError('Actual source pairing/split mismatch')
            raw_last[x['sample_id']]=x['input_values'][-1][0]
            for step,(day,value) in enumerate(zip(y['target_dates'],y['target_values']),1):
                actuals.append(dict(sample_id=x['sample_id'],forecast_origin=x['forecast_origin'],
                    forecast_length=h,horizon_step=step,target_date=day,dataset_version=x['dataset_version'],
                    actual_price=value,split='val'))
    baseline=predictions[predictions.method=='persistence']
    np.testing.assert_array_equal(baseline.predicted_price.to_numpy(),[raw_last[i] for i in baseline.sample_id])
    watch=dict(protocol['semantic']['artifacts_sha256'])
    for name in ['backend/evaluation/forecast_records.py','backend/evaluation/one_step.py',
                 'scripts/check_tv6_evaluation.py',source.relative_to(ROOT).as_posix(),
                 (source.parent/'validation_inference_usd.csv').relative_to(ROOT).as_posix()]:
        watch[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    validation_cohorts=load_validation_cohorts(ROOT,protocol)
    result=evaluate_forecast_records(predictions,pd.DataFrame(actuals),protocol=protocol,expected_validation_cohorts=validation_cohorts)
    # Validate h1 outputs against earlier TV5 comparison without using test data.
    previous_path=ROOT/'logs/audit/tv5_item9_20261126T045347179803Z/metrics.csv'
    previous=pd.read_csv(previous_path)
    for row in result['metrics'][result['metrics'].forecast_length==1].itertuples():
        old=previous[previous.method.str.lower()==row.method]
        if row.method!='persistence':old=old[old.seed==row.seed]
        if len(old)!=1:raise ValueError('Previous comparison does not have exactly one matching run')
        np.testing.assert_allclose([row.mae_usd,row.rmse_usd],old[['mae_usd','rmse_usd']].to_numpy()[0],rtol=1e-12,atol=1e-12)
    if len(result['metrics'])!=31 or len(result['aggregates'])!=8 or len(result['residuals'])!=6670:
        raise ValueError('Incomplete evaluation outputs')
    if not all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in watch.items()):
        raise ValueError('Evaluation source/artifacts changed')
    if validate_protocol(protocol,ROOT)!=sha:raise ValueError('Protocol changed')
    folder=ROOT/'logs/audit'/('tv6_item4_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(parents=True)
    for name,frame in result.items():frame.to_csv(folder/(name+'.csv'),index=False)
    summary=dict(passed=True,scope='validation evaluation acceptance',metric_rows=31,aggregate_rows=8,
        residual_rows=6670,protocol_sha256=sha,source_evidence=source.relative_to(ROOT).as_posix(),
        source_hashes=watch,one_step_matches_tv5=True,baseline_matches_raw_last=True,std_ddof=1,
        test_performance_evaluated=False,test_inference_performed=False,trained_again=False,validation_cohorts=validation_cohorts,
        limitations=['Validation used in checkpoint selection; not final held-out evidence',
            'Full-test evaluator math/schema ready, but inference/test run workflow remains item5'])
    (folder/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    (ROOT/'logs/audit/tv6_item4_latest.json').write_text(json.dumps(dict(evidence=(folder/'summary.json').relative_to(ROOT).as_posix()),indent=2))
    print(json.dumps(dict(passed=True,evidence=str(folder/'summary.json'))))


if __name__=='__main__':main()
