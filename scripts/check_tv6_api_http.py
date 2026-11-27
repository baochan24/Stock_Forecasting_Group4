"""Real localhost HTTP acceptance; stops its own server after checks."""
from datetime import datetime,timezone
import hashlib,json,os,socket,subprocess,sys,time
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.artifacts.research_release import validate_release


def main():
    release=validate_release(ROOT)
    folder=ROOT/'logs/audit'/('tv6_item8_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir()
    with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    server_log=(folder/'server.log').open('w',encoding='utf-8')
    process=subprocess.Popen([sys.executable,str(ROOT/'scripts/run_tv6_api.py'),'--port',str(port)],cwd=ROOT,
        stdout=server_log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    responses=[];checks=[];start=time.perf_counter()
    try:
        base=f'http://127.0.0.1:{port}'
        with httpx.Client(base_url=base,timeout=30) as client:
            for attempt in range(180):
                if process.poll() is not None:raise RuntimeError('API server exited; inspect server.log')
                try:
                    if client.get('/api/v1/health',timeout=1).status_code==200:break
                except httpx.HTTPError:pass
                time.sleep(.5)
            else:raise RuntimeError('API startup timeout')
            def call(method,path,expected=200,**kwargs):
                t=time.perf_counter();r=client.request(method,path,**kwargs)
                if r.status_code!=expected:raise AssertionError(f'{path}: {r.status_code} {r.text[:300]}')
                data=r.json()
                if data.get('request_id')!=r.headers.get('X-Request-ID'):raise AssertionError('Request ID mismatch')
                responses.append(dict(method=method,path=path,status=r.status_code,body=data))
                checks.append(dict(method=method,path=path,status=r.status_code,seconds=time.perf_counter()-t))
                return data
            call('GET','/api/v1/health');call('GET','/api/v1/readiness')
            metadata=call('GET','/api/v1/releases/current')
            call('GET','/api/v1/releases/'+metadata['release_id'])
            call('GET','/api/v1/forecast-origins',params={'forecast_length':5,'limit':3})
            call('GET','/api/v1/datasets/'+metadata['dataset_version']+'/prices',params={'limit':3,'start_date':'2023-06-15'})
            for h in (1,5):
                prediction=call('POST','/api/v1/predictions',json=dict(forecast_origin='2025-06-16',forecast_length=h,
                    methods=['lstm','cnn','persistence'] if h==1 else ['lstm','persistence']))
                if prediction['status']!='complete':raise AssertionError('Incomplete prediction')
            call('GET','/api/v1/results',params={'forecast_length':5,'origin_from':'2025-06-01','origin_to':'2025-06-16','limit':3})
            call('GET','/api/v1/metrics',params={'forecast_length':5,'origin_from':'2025-06-01','origin_to':'2025-06-16'})
            run=metadata['experiments'][0]['run_id']
            call('GET','/api/v1/experiments/'+run,params={'limit':2})
            call('GET','/api/v1/experiments/'+run+'/audits')
            trace=call('POST','/api/v1/model-traces',json=dict(forecast_origin='2023-06-15',forecast_length=5))
            if not trace['trace']['verification']['passed']:raise AssertionError('Unverified trace')
            call('GET','/api/v1/releases/unknown',expected=404)
            call('POST','/api/v1/predictions',expected=422,json={'forecast_origin':'2023-06-15','target_values':[99]})
        validate_release(ROOT)
        (folder/'http_responses.json').write_text(json.dumps(responses,indent=2),encoding='utf-8')
        (folder/'checks.json').write_text(json.dumps(checks,indent=2))
        source_paths=['backend/api/app.py','backend/api/schemas.py','backend/services/forecast_service.py',
            'backend/services/results/release_results.py','scripts/build_tv6_api_data.py','scripts/check_tv6_api_http.py','scripts/run_tv6_api.py',
            'experiments/configs/tv6_api_data_v1.registry.json']
        summary=dict(passed=True,release_id=metadata['release_id'],release_sha256=release['semantic_sha256'],http_checks=len(checks),
            real_http=True,bound_host='127.0.0.1',port=port,seconds=time.perf_counter()-start,training=False,
            model_weights_unchanged=True,frontend=False,independent_holdout=False,
            source_hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in source_paths})
        (folder/'summary.json').write_text(json.dumps(summary,indent=2))
        (ROOT/'logs/audit/tv6_item8_latest.json').write_text(json.dumps(dict(evidence=(folder/'summary.json').relative_to(ROOT).as_posix()),indent=2))
        print(json.dumps(dict(**summary,evidence=str(folder/'summary.json'))))
    finally:
        process.terminate()
        try:process.wait(timeout=10)
        except subprocess.TimeoutExpired:process.kill();process.wait(timeout=10)
        server_log.close()


if __name__=='__main__':main()
