"""Generate post-training monitoring from frozen validation predictions only."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.error_analysis.validation_monitoring import analyze_validation_errors


def main():
    source=sorted((ROOT/'logs/audit').glob('tv5_item9_*/summary.json'))[-1]
    compare=json.loads(source.read_text())
    assert compare['passed'] and compare['split']=='validation' and not compare['test_performance_evaluated']
    files=[source,source.parent/'predictions_usd.csv',source.parent/'metrics.csv']
    files+=list((ROOT/'backend/error_analysis').glob('*.py'))+[Path(__file__)]
    hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    predictions=pd.read_csv(source.parent/'predictions_usd.csv')
    result=analyze_validation_errors(predictions)
    assert len(result['summary'])==7 and (result['summary'].sample_count==250).all()
    old=pd.read_csv(source.parent/'metrics.csv')
    joined=result['summary'].merge(old,on=['method','seed'],suffixes=('_monitor','_old'),validate='one_to_one')
    for metric in ['mae_usd','rmse_usd']:
        np.testing.assert_allclose(joined[metric+'_monitor'],joined[metric+'_old'],rtol=1e-12,atol=1e-12)
    folder=ROOT/'logs/audit'/('tv5_monitoring_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(parents=True)
    for name,table in result.items(): table.to_csv(folder/(name+'.csv'),index=False)
    colors={'CNN':'#2563eb','LSTM':'#d97706','persistence':'#334155'}
    def label(seed): return 'deterministic' if pd.isna(seed) else 'seed '+str(int(seed))
    fig,axes=plt.subplots(3,1,figsize=(15,11),sharex=True)
    for ax,method in zip(axes,['persistence','LSTM','CNN']):
        for seed,group in predictions[predictions.method==method].groupby('seed',dropna=False):
            ax.plot(pd.to_datetime(group.target_date),group.error_usd,label=label(seed),alpha=.8,linewidth=1)
        ax.axhline(0,color='black',linestyle='--',linewidth=.8)
        ax.set(title=method+' · error = prediction − actual',ylabel='USD');ax.legend();ax.grid(alpha=.2)
    fig.suptitle('Sai số theo ngày · validation2023 · dương = dự báo cao hơn actual')
    fig.tight_layout();fig.savefig(folder/'01_errors_by_date.png',dpi=150);plt.close(fig)
    fig,ax=plt.subplots(figsize=(15,6))
    for (method,seed),group in result['rolling'].groupby(['method','seed'],dropna=False,sort=False):
        ax.plot(pd.to_datetime(group.target_date),group.rolling_mae_usd,
                label=method+' '+label(seed),color=colors[method],alpha=.75,
                linestyle='-' if pd.isna(seed) or seed==42 else '--' if seed==123 else ':')
    ax.set(title='MAE trượt 20 phiên · 19 phiên đầu chưa đủ cửa sổ',ylabel='MAE USD',xlabel='Ngày cuối cửa sổ')
    ax.legend(ncol=3);ax.grid(alpha=.2);fig.tight_layout()
    fig.savefig(folder/'02_rolling_mae.png',dpi=150);plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(16,5),sharex=True)
    bins=np.linspace(predictions.error_usd.min(),predictions.error_usd.max(),35)
    for ax,method in zip(axes,['persistence','LSTM','CNN']):
        for seed,group in predictions[predictions.method==method].groupby('seed',dropna=False):
            ax.hist(group.error_usd,bins=bins,histtype='step',density=True,label=label(seed),linewidth=1.5)
        ax.axvline(0,color='black',linestyle='--',linewidth=.8)
        ax.set(title=method,xlabel='Signed error USD',ylabel='Mật độ');ax.legend();ax.grid(alpha=.2)
    fig.suptitle('Phân phối residual từng seed · không coi các seed là mẫu độc lập')
    fig.tight_layout();fig.savefig(folder/'03_error_distributions.png',dpi=150);plt.close(fig)
    monthly=result['monthly'].groupby(['month','method']).mae_usd.mean().unstack()
    fig,ax=plt.subplots(figsize=(15,5));monthly.plot.bar(ax=ax)
    ax.set(title='MAE theo tháng · trung bình metric từng seed, không phải ensemble',ylabel='USD')
    ax.grid(axis='y',alpha=.2);fig.tight_layout();fig.savefig(folder/'04_monthly_mae.png',dpi=150);plt.close(fig)
    # Inventory distinguishes measured values from unavailable historical telemetry.
    cnn=json.loads((ROOT/compare['cnn_evidence']).read_text())
    inventory=dict(training_loss='recorded per epoch',validation_loss='recorded per epoch',
        nonfinite_checks='trainer guards and smoke gradient probes',checkpoint_reload='six models checked in item9',
        cnn_wall_seconds=cnn['timing']['runner_wall_seconds'],cnn_cpu_seconds=cnn['timing']['process_cpu_seconds'],
        inference_timing='item9 median20 local, includes input/loader overhead',
        historical_peak_ram='not recorded; cannot reconstruct retrospectively',
        gpu_telemetry='not applicable, CPU experiment',production_drift='not implemented; no deployed model')
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
    summary=dict(passed=True,scope='validation2023 post-training monitoring',trained_again=False,
        test_performance_evaluated=False,source_evidence=source.relative_to(ROOT).as_posix(),
        models=7,unique_dates=250,rolling_window_sessions=20,rolling_full_windows_per_run=231,
        top_n_per_run=10,plots=4,source_hashes=hashes,resource_inventory=inventory,
        limitations=['Validation selected checkpoints; descriptive analysis only',
                    'No causal claim about CNN errors or proof of absence of overfitting',
                    'No historical peak RAM, live TensorBoard CNN, alerting or production drift telemetry'])
    (folder/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=True,evidence=str(folder/'summary.json'))))


if __name__=='__main__': main()
