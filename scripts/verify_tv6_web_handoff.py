"""Verify an extracted TV6 web handoff using its own source; no training."""
import argparse,hashlib,json,sys,subprocess,socket,time,os,platform
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def verify_payload(root,receipt):
    root=Path(root).resolve()
    files=receipt.get('files_sha256')
    if not isinstance(files,dict) or not files:raise ValueError('Empty or invalid payload manifest')
    for name,sha in files.items():
        if not isinstance(name,str) or not name or name.startswith('/') or '\\' in name or ':' in name or Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError('Unsafe manifest member')
        if not isinstance(sha,str) or len(sha)!=64 or any(c not in '0123456789abcdef' for c in sha):raise ValueError('Invalid member checksum')
        path=(root/name).resolve()
        if not path.is_relative_to(root) or not path.is_file():raise ValueError('Missing/unsafe member: '+name)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=sha:raise ValueError('Member checksum mismatch: '+name)


def save_result(output,result):
    path=Path(output);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2)


def main(real_http=False):
    receipt=json.loads((ROOT/'TV6_WEB_HANDOFF.json').read_text(encoding='utf-8'))
    verify_payload(ROOT,receipt)
    from fastapi.testclient import TestClient
    from backend.api.app import create_app
    from backend.artifacts.research_release import validate_release
    from backend.services.results.release_results import ReleaseResults
    release=validate_release(ROOT);ReleaseResults(ROOT).validate(release)
    checks=[]
    with TestClient(create_app(ROOT)) as client:
        for h in (1,5):
            r=client.post('/api/v1/predictions',json={'forecast_origin':'2025-06-16','forecast_length':h,
                'methods':['lstm','cnn','persistence'] if h==1 else ['lstm','persistence'],'seed':42})
            if r.status_code!=200 or len(r.json()['predictions'])!=(3 if h==1 else 10):raise ValueError('Prediction failed')
            checks.append(dict(horizon=h,rows=len(r.json()['predictions']),passed=True))
        for path in ['/api/v1/readiness','/api/v1/metrics?forecast_length=5','/api/v1/releases/current']:
            if client.get(path).status_code!=200:raise ValueError('Endpoint failed: '+path)
        trace=client.post('/api/v1/model-traces',json={'forecast_origin':'2025-06-16','forecast_length':5}).json()
        if not trace['trace']['verification']['passed']:raise ValueError('Trace failed')
    if real_http:
        import httpx
        def port():
            with socket.socket() as sock:sock.bind(('127.0.0.1',0));return sock.getsockname()[1]
        api_port=port();ui_port=port();processes=[]
        try:
            for script,args in [('run_tv6_api.py',['--port',str(api_port)]),('run_tv6_frontend.py',['--port',str(ui_port),'--api-port',str(api_port)])]:
                processes.append(subprocess.Popen([sys.executable,str(ROOT/'scripts'/script),*args],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0))
            with httpx.Client(base_url=f'http://127.0.0.1:{ui_port}',timeout=60) as client:
                for _ in range(180):
                    try:
                        if client.get('/api/v1/health').status_code==200:break
                    except httpx.HTTPError:pass
                    if any(p.poll() is not None for p in processes):raise RuntimeError('Server exited')
                    time.sleep(.5)
                else:raise RuntimeError('Server startup timeout')
                response=client.get('/')
                if response.status_code!=200 or 'AAPL Forecast Lab' not in response.text:raise ValueError('Frontend unavailable')
                for name in ['app.js','styles.css','api_client/client.js']:
                    if client.get('/'+name).status_code!=200:raise ValueError('Frontend asset missing')
                if client.get('/api/v1/readiness').json()['status']!='ready':raise ValueError('Proxy readiness')
                response=client.post('/api/v1/predictions',json={'forecast_origin':'2025-06-16','forecast_length':5})
                if response.status_code!=200 or len(response.json()['predictions'])!=10:raise ValueError('Proxy prediction')
        finally:
            for process in processes:
                if process.poll() is None:process.terminate()
                try:process.wait(timeout=10)
                except subprocess.TimeoutExpired:process.kill();process.wait(timeout=10)
    from importlib.metadata import version
    result=dict(passed=True,root=str(ROOT),payload_files=len(receipt['files_sha256']),checks=checks,
        release_sha256=release['semantic_sha256'],real_http=real_http,owned_servers_stopped=real_http,
        training=False,verified_on_other_machine=False,fresh_environment_verified=False,
        python=sys.version,python_executable=sys.executable,system=platform.system(),system_release=platform.release(),
        packages={p:version(p) for p in ['torch','numpy','pandas','scikit-learn','fastapi','uvicorn']},
        checked_utc=datetime.now(timezone.utc).isoformat())
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--http',action='store_true')
    parser.add_argument('--output',help='Save a new JSON receipt; refuses to overwrite an existing file')
    parser.add_argument('--reviewer',help='Optional member name; recorded as supplied, not proof of another machine')
    args=parser.parse_args()
    if args.output and Path(args.output).exists():parser.error('Output already exists; choose a new receipt filename')
    try:result=main(args.http)
    except Exception as exc:
        result=dict(passed=False,error_type=type(exc).__name__,message=str(exc),training=False,
            checked_utc=datetime.now(timezone.utc).isoformat(),python_executable=sys.executable)
        if args.reviewer:result['reviewer_supplied']=args.reviewer
        if args.output:save_result(args.output,result)
        print(json.dumps(result));raise SystemExit(1)
    if args.reviewer:result['reviewer_supplied']=args.reviewer
    if args.output:save_result(args.output,result)
    print(json.dumps(result))
