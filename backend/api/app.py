"""Historical AAPL API. No training endpoints or arbitrary artifact selection."""
from pathlib import Path
from typing import Annotated
import json,logging,os,time,uuid
from fastapi import FastAPI,Query,Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException
from backend.artifacts.research_release import RELEASE_ID
from backend.services.forecast_service import ResearchService,ServiceError
from backend.services.results.release_results import records
from backend.api.schemas import PredictionRequest,TraceRequest,OriginsQuery,ResultQuery,PriceQuery,PageQuery

ROOT=Path(__file__).resolve().parents[2]


def create_app(root=None):
    root=Path(root or ROOT).resolve();service=ResearchService(root)
    log_dir=root/'logs/api';log_dir.mkdir(parents=True,exist_ok=True)
    logger=logging.getLogger('tv6.api.'+str(root));logger.setLevel(logging.INFO);logger.propagate=False
    if not logger.handlers:
        handler=logging.FileHandler(log_dir/'requests.log',encoding='utf-8');handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'));logger.addHandler(handler)
    app=FastAPI(title='AAPL Forecasting Research API',version='1.0.0',description='Historical research release. No training or live-data endpoints.')
    app.state.service=service

    def envelope(request,**data):return dict(request_id=request.state.request_id,**data)
    def error(request,status,code,message,details=None):
        return JSONResponse(status_code=status,content=envelope(request,status='failed',error=dict(code=code,message=message,details=details or [])))

    @app.middleware('http')
    async def request_context(request,call_next):
        request.state.request_id=uuid.uuid4().hex;start=time.perf_counter()
        try:response=await call_next(request)
        except Exception:
            logger.exception('request_id=%s internal_error',request.state.request_id)
            response=error(request,500,'internal_error','An unexpected server error occurred')
        response.headers['X-Request-ID']=request.state.request_id
        logger.info(json.dumps(dict(request_id=request.state.request_id,method=request.method,path=request.url.path,
            status=response.status_code,duration_ms=round((time.perf_counter()-start)*1000,3))))
        return response

    @app.exception_handler(ServiceError)
    async def service_error(request,exc):
        if exc.status>=500:logger.error('request_id=%s service_error=%s cause=%r',request.state.request_id,exc.code,exc.__cause__)
        return error(request,exc.status,exc.code,exc.message)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request,exc):
        details=[dict(location=list(e['loc']),type=e['type'],message=e['msg']) for e in exc.errors()]
        return error(request,422,'invalid_request','Request parameters are invalid',details)

    @app.exception_handler(HTTPException)
    async def http_error(request,exc):return error(request,exc.status_code,'resource_not_found' if exc.status_code==404 else 'http_error','Resource not found' if exc.status_code==404 else 'Request could not be served')

    def metadata(release):
        s=release['semantic']
        return dict(release_id=s['release_id'],release_sha256=release['semantic_sha256'],dataset_version=s['dataset_version'],
            kind=s['kind'],lookback=s['lookback'],demo_seed=s['demo_seed'],dtype=s['dtype'],methods={'1':['lstm','cnn','persistence'],'5':['lstm','persistence']},
            experiments=[dict(run_id=e['run_id'],method=e['method'],forecast_length=e['forecast_length'],seed=e['seed'],representation=e['representation']) for e in s['models']],
            independent_holdout=False,limitations=s['limitations'])

    @app.get('/api/v1/health')
    async def health(request:Request):return envelope(request,status='ok',service='aapl-research-api')

    @app.get('/api/v1/readiness')
    def readiness(request:Request):
        release=service.ready();return envelope(request,status='ready',release_id=RELEASE_ID,release_sha256=release['semantic_sha256'],models_verified=9,results_verified=True)

    @app.get('/api/v1/releases/current')
    def current(request:Request):return envelope(request,**metadata(service.ready()))

    @app.get('/api/v1/releases/{release_id}')
    def release_info(release_id:str,request:Request):return envelope(request,**metadata(service.ready(release_id)))

    @app.get('/api/v1/forecast-origins')
    def origins(request:Request,q:Annotated[OriginsQuery,Query()]):
        release=service.ready(q.release_id);items=service.origins(release,q.forecast_length,q.origin_from,q.origin_to)
        return envelope(request,release_id=q.release_id,forecast_length=q.forecast_length,total=len(items),offset=q.offset,limit=q.limit,items=items[q.offset:q.offset+q.limit])

    @app.get('/api/v1/datasets/{dataset_version}/prices')
    def prices(dataset_version:str,request:Request,q:Annotated[PriceQuery,Query()]):
        release=service.ready(q.release_id)
        if dataset_version!=release['semantic']['dataset_version']:raise ServiceError(404,'dataset_not_found','Dataset not found')
        f=service.snapshot(release)
        if q.start_date:f=f[f.date>=q.start_date]
        if q.end_date:f=f[f.date<=q.end_date]
        return envelope(request,release_id=q.release_id,dataset_version=dataset_version,currency='USD',feature='adjusted_close',total=len(f),offset=q.offset,limit=q.limit,
            items=records(f.iloc[q.offset:q.offset+q.limit][['date','ticker','adjusted_close']]))

    @app.post('/api/v1/predictions')
    def predictions(body:PredictionRequest,request:Request):
        return envelope(request,**service.predict(body.release_id,body.forecast_origin,body.forecast_length,body.methods,body.seed))

    def selected(q):
        release=service.ready(q.release_id)
        try:frame=service.results.select(release,q.forecast_length,q.seed,q.methods,q.split,q.origin_from,q.origin_to)
        except Exception as exc:raise ServiceError(503,'results_unavailable','Stored results are unavailable') from exc
        return release,frame

    @app.get('/api/v1/results')
    def results(request:Request,q:Annotated[ResultQuery,Query()]):
        release,frame=selected(q)
        return envelope(request,release_id=q.release_id,release_sha256=release['semantic_sha256'],result_source='stored_results',split=q.split,
            total=len(frame),offset=q.offset,limit=q.limit,items=records(frame.iloc[q.offset:q.offset+q.limit]))

    @app.get('/api/v1/metrics')
    def metrics(request:Request,q:Annotated[ResultQuery,Query()]):
        release,frame=selected(q)
        try:scores=service.results.metrics(frame,q.methods,'selected_range' if q.origin_from or q.origin_to else 'release_full_split')
        except ValueError as exc:raise ServiceError(422,'invalid_range','Selected range has no complete comparable results') from exc
        return envelope(request,release_id=q.release_id,release_sha256=release['semantic_sha256'],dataset_version=release['semantic']['dataset_version'],
            result_source='stored_results',split=q.split,origin_from=q.origin_from,origin_to=q.origin_to,seed=q.seed,independent_holdout=False,
            total=len(scores),offset=q.offset,limit=q.limit,items=scores[q.offset:q.offset+q.limit])

    @app.get('/api/v1/experiments/{run_id}')
    def experiment(run_id:str,request:Request,q:Annotated[PageQuery,Query()]):
        release=service.ready()
        try:value=service.results.experiment(release,run_id,q.offset,q.limit)
        except KeyError as exc:raise ServiceError(404,'experiment_not_found','Experiment not found') from exc
        except Exception as exc:raise ServiceError(503,'results_unavailable','Experiment records are unavailable') from exc
        return envelope(request,release_id=RELEASE_ID,**value)

    @app.get('/api/v1/experiments/{run_id}/audits')
    def audits(run_id:str,request:Request):
        release=service.ready()
        if run_id not in [e['run_id'] for e in release['semantic']['models']]:raise ServiceError(404,'experiment_not_found','Experiment not found')
        sidecar=service.results.validate(release)
        return envelope(request,release_id=RELEASE_ID,run_id=run_id,status='accepted_local',evidence_id=sidecar['evidence_id'],
            evidence_sha256=sidecar['acceptance_sha256'],checks=['artifact_hashes','model_scaler_linkage','inference_parity'],verified_on_other_machine=False)

    @app.post('/api/v1/model-traces')
    def trace(body:TraceRequest,request:Request):
        try:value=service.trace(body.release_id,body.forecast_origin,body.forecast_length,body.seed,body.detail)
        except ServiceError:raise
        except Exception as exc:raise ServiceError(503,'trace_unavailable','Model trace could not be verified') from exc
        return envelope(request,**value)

    app.add_middleware(CORSMiddleware,allow_origins=os.environ.get('TV6_CORS_ORIGINS','http://localhost:5173,http://127.0.0.1:5173').split(','),
        allow_credentials=False,allow_methods=['GET','POST'],allow_headers=['Content-Type','X-Request-ID'],expose_headers=['X-Request-ID'])
    return app


app=create_app()
