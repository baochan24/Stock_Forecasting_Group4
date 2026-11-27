"""Six h1 runs changing only temporal readout; old paired controls stay immutable."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys,time
import numpy as np
import pandas as pd
import torch
from torch.utils.data import TensorDataset,DataLoader

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
from backend.audit.tv6_protocol import PROTOCOL_PATH,validate_protocol
from backend.artifacts.scaler import load_scaler
from backend.data.transforms.anchored_price import encode_history,encode_targets,decode_prices,REPRESENTATION
from backend.models.lstm_one_step.mean_readout import LSTMMeanReadout
from backend.experiments.management.experiment_manager import set_random_seed
from backend.training.trainer import train_model
from backend.model_trace.gradient_diagnostics import trace_lstm_gradients
from backend.error_analysis.lstm_diagnostics import history_controls,describe
from run_tv6_residual_development import select_records,arrays

PLAN='experiments/configs/tv6_mean_readout_ablation_v1.json'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False),encoding='utf-8')


def main():
    plan=read(ROOT/PLAN);protocol=read(ROOT/PROTOCOL_PATH);protocol_sha=validate_protocol(protocol,ROOT)
    source=(ROOT/read(ROOT/'logs/audit/tv6_residual_development_latest.json')['evidence']).parent
    dev=read(source/'summary.json');audit=read(source/'independent_audit.json')
    if not dev['passed'] or not audit['passed']:raise ValueError('Unaccepted controls')
    watch=dict(dev['source_hashes'])
    for name,expected in audit['result_hashes'].items():
        if sha(source/name)!=expected:raise ValueError('Changed controls')
        watch[(source/name).relative_to(ROOT).as_posix()]=expected
    probe_source=(ROOT/read(ROOT/'logs/audit/tv6_item6_latest.json')['evidence']).parent
    probe_audit=read(probe_source/'independent_audit.json')
    if not probe_audit['passed']:raise ValueError('Unaccepted sensitivity controls')
    for name,expected in probe_audit['result_hashes'].items():
        if sha(probe_source/name)!=expected:raise ValueError('Changed sensitivity control')
        watch[(probe_source/name).relative_to(ROOT).as_posix()]=expected
    for name in [PLAN,'scripts/run_tv6_readout_ablation.py','backend/models/lstm_one_step/mean_readout.py',
                 'backend/model_trace/gradient_diagnostics.py','backend/error_analysis/lstm_diagnostics.py']:
        watch[name]=sha(ROOT/name)
    for name,expected in watch.items():
        if sha(ROOT/name)!=expected:raise ValueError('Changed source '+name)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder=ROOT/'logs/audit'/('tv6_readout_ablation_'+stamp);folder.mkdir()
    artifacts=ROOT/'artifacts/checkpoints'/folder.name;artifacts.mkdir()
    summary=dict(status='running',passed=False,plan=plan,protocol_sha256=protocol_sha,source_hashes=watch,
        control_source=source.relative_to(ROOT).as_posix(),runs=[],test_forward=False,promoted=False)
    write(folder/'summary.json',summary)
    torch.set_num_threads(1);torch.use_deterministic_algorithms(True)
    inventory=read(ROOT/'reports/audits/TV6_Input_Inventory.json');version=inventory['dataset_version']
    cohort=next(c for c in protocol['semantic']['cohorts'] if c['forecast_length']==1)
    base=ROOT/'data/prepared'/cohort['prepared_id']
    xx=read(base/'f1_train_inputs.json')+read(base/'f1_val_inputs.json')
    yy=read(base/'f1_train_targets.json')+read(base/'f1_val_targets.json')
    scores=[];gradient=[];predictions=[];start=time.perf_counter()
    try:
        for year in plan['validation_years']:
            train=select_records(xx,yy,'2015-01-01',f'{year-1}-12-31');val=select_records(xx,yy,f'{year}-01-01',f'{year}-12-31')
            tx,ty=arrays(train);vx,vy=arrays(val)
            for seed in plan['seeds']:
                control=next(r for r in dev['runs'] if r['validation_year']==year and r['task']=='lstm_h1' and r['seed']==seed and r['representation']==REPRESENTATION)
                cm=read(ROOT/control['checkpoint']/'manifest.json')
                sf=ROOT/'artifacts/scalers'/cm['scaler_id']
                for path in [sf/'manifest.json',sf/'scaler.json',ROOT/control['checkpoint']/'manifest.json',ROOT/control['checkpoint']/'state_dict.pt']:
                    watch[path.relative_to(ROOT).as_posix()]=sha(path)
                scaler,sm=load_scaler(sf,expected_dataset_version=version,expected_source_hashes=inventory['source_hashes'])
                if sm['metadata']['fit_last_date']>=f'{year}-01-01':raise ValueError('Scaler leakage')
                x,anchor=encode_history(tx,scaler.scale_[0]);y=encode_targets(ty,anchor,scaler.scale_[0])
                xv,av=encode_history(vx,scaler.scale_[0]);yv=encode_targets(vy,av,scaler.scale_[0])
                set_random_seed(seed);model=LSTMMeanReadout()
                torch.nn.init.zeros_(model.fc.weight);torch.nn.init.zeros_(model.fc.bias)
                run_id=f'{year}_mean_readout_seed{seed}';rf=folder/run_id;rf.mkdir()
                def loader(a,b,shuffle):
                    return DataLoader(TensorDataset(torch.from_numpy(a),torch.from_numpy(b)),batch_size=32,shuffle=shuffle,
                        drop_last=False,generator=torch.Generator().manual_seed(seed))
                def on_epoch(log):
                    pd.DataFrame(log).to_csv(rf/'epoch_logs.csv',index=False)
                    epoch=log[-1]['epoch']
                    if epoch in plan['gradient_log_epochs']:
                        mid=len(x)//2
                        g=trace_lstm_gradients(model,torch.from_numpy(x[mid:mid+32]),torch.from_numpy(y[mid:mid+32]))
                        v=g.pop('input_grad_l2_per_session')
                        gradient.append(dict(validation_year=year,seed=seed,epoch=epoch,**g,oldest_input_grad=v[0],previous_input_grad=v[28]))
                result=train_model(model,loader(x,y,True),loader(xv,yv,False),{'training':dev['plan']['training']},None,run_id,on_epoch=on_epoch)
                model.eval();path=artifacts/run_id;path.mkdir()
                torch.save(model.state_dict(),path/'state_dict.pt')
                restored=LSTMMeanReadout();restored.load_state_dict(torch.load(path/'state_dict.pt',weights_only=True,map_location='cpu'));restored.eval()
                with torch.inference_mode():torch.testing.assert_close(model(torch.from_numpy(xv[:2])),restored(torch.from_numpy(xv[:2])),rtol=0,atol=0)
                for condition,history in history_controls(vx).items():
                    packed,anchors=encode_history(history,scaler.scale_[0])
                    with torch.inference_mode():scaled=torch.cat([restored(torch.from_numpy(packed[i:i+32])) for i in range(0,len(packed),32)]).numpy()
                    price=decode_prices(scaled,anchors,scaler.scale_[0]);rows=[]
                    for i,(inp,target) in enumerate(val):rows.append(dict(validation_year=year,seed=seed,readout='mean',condition=condition,
                        sample_id=inp['sample_id'],target_date=target['target_dates'][0],horizon_step=1,
                        predicted_price=float(price[i,0]),actual_price=float(vy[i,0]),origin_price=float(anchors[i])))
                    predictions.extend(rows)
                    scores.append(dict(validation_year=year,seed=seed,readout='mean',condition=condition,**describe(pd.DataFrame(rows))))
                # Reuse every paired original control/sensitivity, verifying before comparison.
                pp=probe_source/'history_probe_predictions.csv';watch[pp.relative_to(ROOT).as_posix()]=sha(pp)
                old=pd.read_csv(pp,float_precision='round_trip')
                old=old[(old.validation_year==year)&(old.seed==seed)&(old.forecast_length==1)]
                for condition,g in old.groupby('control',sort=False):
                    expected=[(a['sample_id'],b['target_dates'][0]) for a,b in val]
                    if list(zip(g.sample_id,g.target_date))!=expected:raise ValueError('Control keys')
                    copied=g.copy();copied['readout']='last';copied['condition']=condition
                    predictions.extend(copied[['validation_year','seed','readout','condition','sample_id','target_date','horizon_step','predicted_price','actual_price','origin_price']].to_dict('records'))
                    scores.append(dict(validation_year=year,seed=seed,readout='last',condition=condition,**describe(g)))
                manifest=dict(validation_year=year,seed=seed,readout='mean',representation=REPRESENTATION,dataset_version=version,
                    scaler_id=cm['scaler_id'],best_epoch=result['best_epoch'],best_val_loss=result['best_val_loss'],epochs=len(result['epoch_logs']),
                    purpose='post-test-development-not-release',plan_sha256=watch[PLAN],checkpoint_sha256=sha(path/'state_dict.pt'),
                    control_checkpoint=control['checkpoint'],parameter_count=sum(p.numel() for p in model.parameters()),reload_verified=True)
                write(path/'manifest.json',manifest)
                summary['runs'].append(dict(validation_year=year,seed=seed,best_epoch=result['best_epoch'],epochs=len(result['epoch_logs']),checkpoint=path.relative_to(ROOT).as_posix()))
                write(folder/'summary.json',summary)
                for name,rows in [('metrics',scores),('predictions',predictions),('gradient_log',gradient)]:pd.DataFrame(rows).to_csv(folder/(name+'.csv'),index=False)
                score=next(r for r in scores if r['validation_year']==year and r['seed']==seed and r['readout']=='mean' and r['condition']=='real')
                print(f'{run_id}: best={result["best_epoch"]} epochs={len(result["epoch_logs"])} MAE={score["mae_usd"]:.6f} RMSE={score["rmse_usd"]:.6f}',flush=True)
        for name,expected in watch.items():
            if sha(ROOT/name)!=expected:raise ValueError('Source changed '+name)
        validate_protocol(protocol,ROOT)
        if len(summary['runs'])!=6:raise ValueError('Incomplete six-run ablation')
        summary.update(passed=True,status='completed',source_hashes=watch,total_seconds=time.perf_counter()-start,source_artifacts_unchanged=True)
        write(folder/'summary.json',summary)
        write(ROOT/'logs/audit/tv6_readout_ablation_latest.json',dict(evidence=(folder/'summary.json').relative_to(ROOT).as_posix()))
        print(pd.DataFrame(scores).groupby(['validation_year','readout','condition'])[['mae_usd','rmse_usd']].mean().to_string(),flush=True)
        print(str(folder),flush=True)
    except Exception as exc:
        summary.update(status='failed',error=repr(exc));write(folder/'summary.json',summary);raise


if __name__=='__main__':main()
