"""Re-audit stored API results against immutable snapshot; no training."""
import hashlib,json,math,subprocess,sys
from pathlib import Path
import xml.etree.ElementTree as ET
from importlib.metadata import version

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.artifacts.research_release import validate_release
from backend.services.results.release_results import ReleaseResults


def main():
    release=validate_release(ROOT);service=ReleaseResults(ROOT);sidecar=service.validate(release)
    import pandas as pd
    frame=service._cache
    raw=pd.read_csv(ROOT/release['semantic']['snapshot'],float_precision='round_trip')
    prices=raw.set_index('date').adjusted_close
    days=raw.date.tolist();positions={day:i for i,day in enumerate(days)}
    assert not frame.duplicated(['method','seed','forecast_length','sample_id','horizon_step']).any()
    assert (frame.actual_price==frame.target_date.map(prices)).all()
    assert all(math.isclose(r.error_usd,r.predicted_price-r.actual_price,rel_tol=0,abs_tol=1e-12) for r in frame.itertuples())
    assert all(r.target_date==days[positions[r.forecast_origin]+r.horizon_step] for r in frame.itertuples())
    assert frame[['predicted_price','actual_price','error_usd']].map(math.isfinite).all().all()
    metric_groups=0
    for h in (1,5):
        methods=['lstm','cnn','persistence'] if h==1 else ['lstm','persistence']
        for seed in (42,123,456):
            for split in ('val','test'):
                selected=service.select(release,h,seed,methods,split)
                metrics=service.metrics(selected,methods,'release_full_split')
                for m in metrics:
                    p=selected[selected.method==m['method']]
                    if m['horizon_step'] is not None:p=p[p.horizon_step==m['horizon_step']]
                    errors=(p.predicted_price-p.actual_price).tolist()
                    assert math.isclose(m['mae_usd'],math.fsum(map(abs,errors))/len(errors),abs_tol=1e-12)
                    assert math.isclose(m['rmse_usd'],math.sqrt(math.fsum(e*e for e in errors)/len(errors)),abs_tol=1e-12)
                metric_groups+=1
    pip=subprocess.run([sys.executable,'-m','pip','check'],capture_output=True,text=True,check=True)
    environment=json.loads((ROOT/'logs/audit/tv6_api_environment.json').read_text())
    for package in environment['core_packages']:
        assert version(package['package'])==package['version'],package['package']
    pointer=json.loads((ROOT/'logs/audit/tv6_item8_latest.json').read_text())
    folder=(ROOT/pointer['evidence']).parent
    checks=dict(passed=True,rows_checked=len(frame),snapshot_rows=len(raw),metric_groups=metric_groups,
        exact_actual_prices=True,target_session_alignment=True,unique_keys=True,finite_values=True,
        independent_metric_recalculation=True,core_packages_verified=len(environment['core_packages']),pip_check=pip.stdout.strip(),training=False)
    (folder/'data_reaudit.json').write_text(json.dumps(checks,indent=2))
    test_path='logs/audit/tv6_item8_reaudit_tests.xml'
    suites=ET.parse(ROOT/test_path).getroot().findall('testsuite')
    count=sum(int(s.attrib['tests']) for s in suites)
    assert count==51 and all(int(s.attrib['failures'])==0 and int(s.attrib['errors'])==0 for s in suites)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    old=json.loads((ROOT/'logs/audit/tv6_item8_20261127T033804495431Z/acceptance.json').read_text())
    acceptance=dict(old,api_tests_passed=count,tests_file=test_path,tests_sha256=sha(ROOT/test_path),
        source_hashes={p:sha(ROOT/p) for p in ['tests/api/test_tv6_api.py','scripts/requirements-tv6-api-lock.txt','scripts/audit_tv6_api_data.py']},
        evidence_hashes={p:sha(folder/p) for p in ['summary.json','http_responses.json','checks.json','data_reaudit.json']})
    # The HTTP script returns only after its own server has stopped successfully.
    (folder/'acceptance.json').write_text(json.dumps(acceptance,indent=2))
    print(json.dumps(dict(evidence=str(folder),**checks)))


if __name__=='__main__':main()
