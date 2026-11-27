"""Official frozen TV6 item5 evaluation. Each invocation preserves its ledger."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import torch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.audit.tv6_protocol import PROTOCOL_PATH,validate_protocol
from backend.inference.frozen_forecaster import FrozenForecaster
from backend.evaluation.forecast_records import evaluate_forecast_records


def main():
    protocol=json.loads((ROOT/PROTOCOL_PATH).read_text(encoding='utf-8'))
    sha=validate_protocol(protocol,ROOT)
    folder=ROOT/'logs/audit'/('tv6_item5_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir()
    watch=dict(protocol['semantic']['artifacts_sha256'])
    for name in (PROTOCOL_PATH,'experiments/configs/tv6_evaluation_protocol_v1.registry.json',
            'backend/inference/frozen_forecaster.py','backend/audit/tv6_test_run.py',
            'backend/evaluation/forecast_records.py','backend/evaluation/one_step.py','scripts/evaluate_tv6_test.py'):
        watch[str(name)]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    ledger=dict(run_id=folder.name,status='running',authorization='User requested TV6 item5',
        started_at_utc=datetime.now(timezone.utc).isoformat(),protocol_sha256=sha,
        source_hashes=watch,trained_again=False,tuned_on_test=False)
    def save():
        (folder/'execution.json').write_text(json.dumps(ledger,indent=2),encoding='utf-8')
    save()  # Written before constructing a test-enabled engine or any test forward.
    try:
        engine=FrozenForecaster(ROOT,test_run=folder/'execution.json')
        output=[];actuals=[];last={};checks=[]
        for cohort in protocol['semantic']['cohorts']:
            h=cohort['forecast_length'];base=ROOT/'data/prepared'/cohort['prepared_id']
            inputs=json.loads((base/f'f{h}_test_inputs.json').read_text())
            for seed in (42,123,456):
                methods=['lstm','cnn'] if h==1 else ['lstm']
                if seed==42:methods.append('persistence')
                rows=engine.predict(inputs,methods=methods,seed=seed)
                output.extend(rows)
                checks.append(dict(forecast_length=h,seed=seed,samples=len(inputs),rows=len(rows)))
            # Target records are loaded only after predictions for this mode exist.
            targets=json.loads((base/f'f{h}_test_targets.json').read_text())
            if len(inputs)!=len(targets):raise ValueError('Source pairing count')
            for x,y in zip(inputs,targets):
                if x['sample_id']!=y['sample_id'] or y['split']!='test':raise ValueError('Source pairing')
                last[x['sample_id']]=x['input_values'][-1][0]
                for k,(day,value) in enumerate(zip(y['target_dates'],y['target_values']),1):
                    actuals.append(dict(sample_id=x['sample_id'],forecast_origin=x['forecast_origin'],
                        forecast_length=h,horizon_step=k,target_date=day,dataset_version=x['dataset_version'],
                        actual_price=value,split='test'))
        pred=pd.DataFrame(output)
        pred.to_csv(folder/'test_predictions_usd.csv',index=False)
        baseline=pred[pred.method=='persistence']
        np.testing.assert_array_equal(baseline.predicted_price,[last[i] for i in baseline.sample_id])
        result=evaluate_forecast_records(pred,pd.DataFrame(actuals),protocol=protocol,split='test')
        if [len(result[n]) for n in ('metrics','aggregates','residuals')]!=[31,8,13474]:
            raise ValueError('Incomplete official results')
        # Independently verify all metric rows with scalar math, including flattened h5.
        for row in result['metrics'].itertuples():
            r=result['residuals'];r=r[(r.method==row.method)&(r.forecast_length==row.forecast_length)]
            if row.method!='persistence':r=r[r.seed==row.seed]
            if row.metric_scope!='overall':r=r[r.horizon_step==row.horizon_step]
            e=(r.predicted_price-r.actual_price).tolist()
            np.testing.assert_allclose([row.mae_usd,row.rmse_usd],
                [math.fsum(abs(v) for v in e)/len(e),math.sqrt(math.fsum(v*v for v in e)/len(e))],rtol=1e-12,atol=1e-12)
        if len(engine._cache)!=9 or any(m.training or any(p.requires_grad or p.grad is not None for p in m.parameters()) for m in engine._cache.values()):
            raise ValueError('Frozen inference contract')
        for n,d in watch.items():
            if hashlib.sha256((ROOT/n).read_bytes()).hexdigest()!=d:raise ValueError('Changed source/artifact: '+n)
        validate_protocol(protocol,ROOT)
        for name,frame in result.items():frame.to_csv(folder/(name+'.csv'),index=False)
        summary=dict(passed=True,scope='official test 2024-2025',protocol_sha256=sha,models=9,
            prediction_rows=len(pred),metric_rows=31,aggregate_rows=8,checks=checks,source_hashes=watch,
            independent_metric_check=True,baseline_raw_last_check=True,test_performance_evaluated=True,
            trained_again=False,tuned_on_test=False,std_ddof=1,
            limitations=['Retrospectively adjusted historical prices; not point-in-time market simulation',
                'Rolling observed inputs, frozen weights; no trading profitability claim',
                'Different search budgets; overlapping multi-step errors are dependent'])
        (folder/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
        ledger.update(status='completed',completed_at_utc=datetime.now(timezone.utc).isoformat())
        save()
        (ROOT/'logs/audit/tv6_item5_latest.json').write_text(json.dumps(dict(evidence=(folder/'summary.json').relative_to(ROOT).as_posix()),indent=2))
        print(result['metrics'].to_string(index=False))
        print(result['aggregates'].to_string(index=False))
        print(str(folder))
    except Exception as exc:
        ledger.update(status='failed',error=repr(exc),test_exposure_possible=True)
        save()
        raise


if __name__=='__main__':main()
