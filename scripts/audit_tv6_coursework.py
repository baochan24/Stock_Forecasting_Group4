"""Final read-only pipeline audit and evidence-backed coursework reports; no training."""
import argparse,hashlib,json,math,statistics,sys
from datetime import datetime,timezone
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.artifacts.research_release import validate_release
from backend.services.results.release_results import ReleaseResults
from backend.data.preparation.snapshot import load_tv1_snapshot
from backend.artifacts.scaler import load_scaler
from backend.artifacts.prepared import load_prepared_modes
from backend.audit.tv2_leakage import audit_train_statistics,audit_temporal_windows


def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(value,message):
    if not value:raise ValueError(message)
def junit(name):
    suites=ET.parse(ROOT/name).getroot().findall('testsuite')
    require(all(int(s.attrib['failures'])==int(s.attrib['errors'])==0 for s in suites),'Regression failures')
    return dict(file=name,cases=sum(int(s.attrib['tests']) for s in suites),skipped=sum(int(s.attrib['skipped']) for s in suites),sha256=sha(ROOT/name))


def main(write_reports=False):
    release=validate_release(ROOT);s=release['semantic'];results=ReleaseResults(ROOT);results.validate(release)
    inventory=read(ROOT/'reports/audits/TV6_Input_Inventory.json')
    for name,digest in inventory['files'].items():require(sha(ROOT/name)==digest,'Intake artifact changed: '+name)
    snapshot=load_tv1_snapshot(ROOT,s['dataset_version']);data=snapshot['data']
    # Match release/API CSV parsing exactly; pandas' default parser may round a last bit.
    raw=pd.read_csv(ROOT/s['snapshot'],float_precision='round_trip').set_index('date').adjusted_close
    original_scaler=inventory['models'][0]['scaler_id']
    scaler,manifest=load_scaler(ROOT/'artifacts/scalers'/original_scaler,expected_dataset_version=s['dataset_version'],expected_source_hashes=s['source_hashes'])
    require(audit_train_statistics(data,scaler,manifest['metadata'])['passed'],'Scaler train statistics')
    coverage=[]
    for prepared_id in sorted({m['prepared_id'] for m in inventory['models']}):
        modes,_=load_prepared_modes(ROOT/'data/prepared'/prepared_id,expected_dataset_version=s['dataset_version'],expected_source_hashes=s['source_hashes'],expected_scaler_id=original_scaler,expected_lookback=30)
        for h,mode in modes.items():
            require(audit_temporal_windows(mode,data,scaler)['passed'],'Temporal leakage audit')
            for split,batch in mode['splits'].items():
                require(batch['X'].dtype==batch['y'].dtype==np.float64,'Dtype mismatch')
                coverage.append(dict(prepared_id=prepared_id,horizon=h,split=split,samples=len(batch['X'])))
    stored=results._cache
    require((stored.actual_price==stored.target_date.map(raw)).all(),'Stored actual mismatch')
    dates=data.date.tolist();position={d:i for i,d in enumerate(dates)}
    require(all(r.target_date==dates[position[r.forecast_origin]+r.horizon_step] for r in stored.itertuples()),'Wrong target session')
    for h in (1,5):
        for seed in (42,123,456):
            for split in ('val','test'):
                methods=['lstm','cnn','persistence'] if h==1 else ['lstm','persistence']
                frame=results.select(release,h,seed,methods,split)
                for metric in results.metrics(frame,methods,'release_full_split'):
                    g=frame[frame.method==metric['method']]
                    if metric['horizon_step'] is not None:g=g[g.horizon_step==metric['horizon_step']]
                    errors=(g.predicted_price-g.actual_price).tolist()
                    require(math.isclose(metric['mae_usd'],math.fsum(map(abs,errors))/len(errors),abs_tol=1e-12),'MAE mismatch')
                    require(math.isclose(metric['rmse_usd'],math.sqrt(math.fsum(e*e for e in errors)/len(errors)),abs_tol=1e-12),'RMSE mismatch')
    old_folder=(ROOT/read(ROOT/'logs/audit/tv6_item5_latest.json')['evidence']).parent
    new_folder=(ROOT/read(ROOT/'logs/audit/tv6_lstm_completion_latest.json')['evidence']).parent
    # Validate accepted evidence hashes rather than mutating old audit receipts.
    for folder in [old_folder,new_folder]:
        receipt=read(folder/'independent_audit.json');require(receipt['passed'],'Prior evaluation rejected')
        for name,digest in receipt['result_hashes'].items():require(sha(folder/name)==digest,'Evaluation evidence changed: '+name)
    old=pd.read_csv(old_folder/'metrics.csv',float_precision='round_trip')
    new=pd.read_csv(new_folder/'metrics.csv',float_precision='round_trip')
    per_horizon=[]
    for frame,phase in [(old,'original_locked_test'),(new[new.scope=='post_development_test_2024_2025'],'post_development_old_test')]:
        for (method,h,scope,step),g in frame.groupby(['method','forecast_length','metric_scope','horizon_step'],dropna=False):
            vals=g.mae_usd.tolist();rms=g.rmse_usd.tolist()
            per_horizon.append(dict(phase=phase,method=method,horizon=int(h),step=None if pd.isna(step) else int(step),scope=scope,
                seeds=0 if method=='persistence' else len(g),samples=int(g.sample_count.iloc[0]),errors=int(g.error_count.iloc[0]),
                mae=statistics.mean(vals),mae_std=statistics.stdev(vals) if len(vals)>1 else None,
                rmse=statistics.mean(rms),rmse_std=statistics.stdev(rms) if len(rms)>1 else None))
    primary=[r for r in per_horizon if r['horizon']==1 or r['scope']=='overall']
    core=junit('logs/audit/tv6_item10_core_verified_20261127.xml');real=junit('logs/audit/tv6_item10_real_tv1_20261128.xml')
    acquisition=read(ROOT/'logs/audit/tv6_item10_acquisition_20261128.json');require(acquisition['passed'],'Acquisition tests')
    ui_path=ROOT/read(ROOT/'logs/audit/tv6_item9_latest.json')['evidence'];ui=read(ui_path)
    require(ui['passed'] and ui['real_api'],'UI not accepted')
    for name,digest in ui['source_hashes'].items():require(sha(ROOT/name)==digest,'UI source changed: '+name)
    folder=ROOT/'logs/audit'/('tv6_item10_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir()
    pd.DataFrame(coverage).to_csv(folder/'data_coverage.csv',index=False)
    pd.DataFrame(per_horizon).to_csv(folder/'per_horizon.csv',index=False)
    pd.DataFrame(primary).to_csv(folder/'comparison.csv',index=False)
    requirements=[
        dict(requirement='Yahoo Finance dataset and past sequences',status='passed_local',evidence='TV1 snapshot/hash and TV2 temporal/scaler audit'),
        dict(requirement='LSTM next-day regression',status='passed_local',evidence='model/checkpoints/inference/API H1'),
        dict(requirement='Multi-step extension',status='passed_local',evidence='direct H5, same target split, per-horizon USD metrics'),
        dict(requirement='CNN vs LSTM extension',status='passed_local',evidence='same cohorts, all3 seeds, original locked test'),
        dict(requirement='Baseline/error analysis/demo/source/setup',status='passed_local',evidence='reports01-07/API/frontend/notebooks'),
        dict(requirement='Fresh install and other member machine',status='pending_external',evidence='relocation on same machine is not independent-machine evidence'),
        dict(requirement='Rights to redistribute Yahoo dataset',status='unverified',evidence='yfinance is not a data redistribution licence; no written permission in project')]
    summary=dict(passed=True,scope='final technical audit local',release_sha256=release['semantic_sha256'],snapshot_rows=len(data),
        inventory_files=len(inventory['files']),stored_rows=len(stored),models=len(s['models']),core_regression=core,
        real_tv1_tests=real,acquisition_tests=acquisition,ui_checks=ui['checks'],ui_unit_tests=ui['unit_tests'],
        training_performed=False,refit_performed=False,independent_holdout=False,
        all_coursework_requirements_fully_signed_off=False,verified_on_other_machine=False,
        open_items=['fresh install/other machine sign-off','data distribution permission/approved alternative source','final submission format and schedule confirmed by team/instructor'],
        requirements=requirements,comparison=primary,
        source_hashes={p:sha(ROOT/p) for p in ['scripts/audit_tv6_coursework.py','docs/đề_yêu_cầu.md','docs/yêu_cầu_mẫu_đề_tài.md']})
    if write_reports:write_final_reports(summary,old_folder,new_folder,folder)
    (folder/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'logs/audit/tv6_item10_latest.json').write_text(json.dumps(dict(evidence=(folder/'summary.json').relative_to(ROOT).as_posix()),indent=2))
    print(json.dumps(dict(passed=True,evidence=str(folder/'summary.json'),core_cases=core['cases'],open_items=summary['open_items'])))


def write_final_reports(summary,old_folder,new_folder,folder):
    header='## Tổng kết hiện hành — audit mục10, 28/11/2026\n\n'
    primary=summary['comparison']
    table='| Giai đoạn | Phương pháp | H | MAE USD | RMSE USD | Mẫu |\n|---|---|---:|---:|---:|---:|\n'
    table+=''.join(f"| {r['phase']} | {r['method']} | {r['horizon']} | {r['mae']:.6f} | {r['rmse']:.6f} | {r['samples']} |\n" for r in primary)
    science='LSTM/CNN gốc thua persistence trên test khóa. Residual cải thiện rõ so với LSTM gốc nhưng chỉ nhỉnh nhẹ persistence trên test cũ đã quan sát; không phải holdout độc lập, chưa chứng minh thắng bền vững/ý nghĩa thống kê hoặc lợi nhuận. Không train/tune/refit thêm trong audit cuối.\n\n'
    contents={
      '01_Problem_and_Scope.md':'''# Vấn đề và phạm vi

Đề Topic4 yêu cầu regression từ Yahoo Finance: dùng chuỗi quá khứ để dự báo giá phiên tiếp theo bằng LSTM; mở rộng multi-step và CNN vs.LSTM. Nhóm cụ thể hóa thành AAPL adjusted close2015–2025,30 phiên,CPUfloat64,H1/H5 và persistence. Các thông số này là lựa chọn nhóm, không phải yêu cầu nguyên văn của đề.

Người dùng chính: giảng viên và nhóm nghiên cứu/người học. Mục tiêu là xây dựng pipeline tái lập, mô hình dự báo có kiểm định và demo giải thích được; không đặt điều kiện LSTM bắt buộc thắng baseline.

Input `(B,30,1)` gồm giá đã quan sát. Output `(B,1)` hoặc `(B,5)`, decode USD, có origin/target date/method/seed/run/release. Actual/error ghép sau inference. Web phục vụ model đã train, không training endpoint hoặc dữ liệu live.

Sản phẩm gồm snapshot/provenance,preprocessing,3 kiến trúc và persistence,checkpoint/scaler/config,metric/error analysis,API/frontend,notebooks và hướng dẫn. Kết quả kỹ thuật đạt local; xác nhận máy khác,quyền phân phối dữ liệu và thủ tục nộp cuối còn mở. Xem [ma trận đầu ra](../docs/TV6_Coursework_Output_and_Defense.md).
''',
      '02_Data_Description.md':f"Snapshot hiện hành `{summary['snapshot_rows']}` phiên,version `aapl_2015_2025_acq_20261119T141302002415Z`,2015-01-02–2025-12-31. Yahoo/yfinance,auto_adjust=False,chọn Adj Close làm adjusted_close. Bảng chuẩn date/ticker/adjusted_close/dataset_version; USD.\n\nTrain target2015–2022,val2023,test2024–2025; scaler chỉfit2014 giá train. H1:train1984/val250/test502 windows; H5:train1980/val246/test498. Giữ lịch sử quan sát từ split trước; cả5 target cùngsplit. Audit toàn bộ prepared/statistics/hash nguồn đạt, không sửa snapshot.\n\nSnapshot điều chỉnh hồi cứu không point-in-time. Nguồn dự phòng vận hành là snapshot/hash đã khóa; đây không phải nguồn thay thế được cấp phép. Chưa có bằng chứng quyền phân phối công khai dataset. Xem docs/TV6_Data_Use_and_Limits.md.\n\n",
      '03_Implementation.md':'''Pipeline: TV1 thu thập/validation → TV2 split/scaler/window/contracts → TV3 LSTM/trace → TV4 shared training/experiments → TV5 CNN → TV6 baseline/inference/evaluation/release/API/UI.

LSTM một lớp hidden32,last readout,Linear1/5,4513/4645 tham số. CNN Conv1d1→16→32,ReLU,MaxPool2,Flatten,Dropout0.1,Linear480→32→1,17057 tham số. CPUfloat64; model không nhận target khi inference. TV4 loop Adam/MSE,validation no_grad,early stopping vàrestore best; CNN dùng chung loop. LSTM chọn lookback30 qua validation từ10/30/60; CNN phương ánA cố định,ngân sách khác nhau nên không gọi so sánh tối ưu toàn cục.

Model gốc dùng StandardScaler absolute; residual LSTM dùng (history−origin)/scale_train vàdecode origin+scale_train×delta,không cộng mean cho delta. H5 direct multi-output,không recursive. Release chọn đúng scaler/representation/checkpoint theo manifest,không lấy file mới nhất.9 models gồm6 residualLSTM và3CNN; persistence không weights.

FastAPI12routes,request input-only,actual ghép sau,error/requestID/CORS/readiness; frontend HTML/CSS/ESmodules gọi API,không tính MAE/RMSE riêng. Source thuộc đúng module hiện có. Các mô tả giai đoạn cũ phía dưới chỉ là lịch sử.

''',
      '04_Setup_and_Run.md':'''Hướng dẫn máy thành viên: [TV6_Member_Setup_and_Run.md](../docs/TV6_Member_Setup_and_Run.md). Windows64/Python3.13.7 tham chiếu,tạo môi trường riêng,pip install theo scripts/requirements-tv6-api-lock.txt,pip check,verify release vàsidecar. Không cầnDocker/GPU/npm install hoặc train lại.

Runtime web cần đủ source+release artifacts+API sidecar/registry+frontend; chỉcloneGit hoặcZIP inference mục7 chưa đủ. Chạy scripts/run_tv6_api.py vàscripts/run_tv6_frontend.py ở2terminal,mở127.0.0.1:5173. Bàn giao mới cómanifest/checksum vàverifier riêng; chỉkết luận tái lập nguồn giải nén cùngmáy khi córeceipt,không gọi làmáy khác.

''',
      '05_System_Demonstration.md':'''# Trình diễn hệ thống

Frontend AAPL Forecast Lab bám concept đã chốt,nốiAPI thật,nền sáng/sidebar/history-forecast/cards/journal. Mở localhost5173 khiAPI8000 sẵn sàng. Chi tiết [kịch bản demo](../docs/TV6_Frontend_Demo.md).

1. Data explorer: snapshot/version/adjusted close USD,bảng/biểu đồ phân trang.
2. Origin2025-06-16,H1,seed42,3methods:3dòng,target2025-06-17,actual/error ghép sau.
3. H5 tựbỏCNN,xóaoutputcũ,chạy10dòng LSTM/persistence theo5phiêndataset.
4. Metrics full-split vàselected-range,từngseed/perhorizon/overall,sample/errorcounts vàevaluationphase.
5. Experiment/config/history/audit; lossscaledkhácbiểu diễnkhôngso trực tiếp.
6. Errors phântrang100dòng,sort|error|trongtrang; khônggọi top-toàntập.
7. TraceLSTM verified30bước; gate trungbìnhhidden32khônggiảithíchkinhtế.
8. Journal20requeststhànhcôngtrongtab,khôngphảidựbáođãpháthànhtạingàylịchsử.

5testsJS/14checksChromeAPI thậtđạtởmục9; códesktop/mobile390px/outage. Screenshot vàreceipt theo logs/audit/tv6_item9_latest.json; khôngdùngảnhconcept làmbằngchứngimplementation. Đổi context khônggiữkếtquảcũ,lỗikhôngthay bằngdata giả. Xem [nghiệmthu](audits/TV6_Item9_Frontend.md).
''',
      '06_Baseline_and_Model_Comparison.md':table+'\nSố model là mean3seeds42/123/456; baseline một quy tắc,không nhân thành3runs. Std mẫu ddof1 vàtừnghorizon nằm trong evidence CSV; bảngtrên chỉH1/H5overall. MeanRMSEcủa3seedkhôngphảiRMSEensemble. Originaltest vàpost-developmentoldtest khôngtrộnthànhmộtphépkiểmđộclập.\n\n'+science+f"Nguồn: `{old_folder.relative_to(ROOT).as_posix()}/metrics.csv`, `{new_folder.relative_to(ROOT).as_posix()}/metrics.csv`; bảngtổng `{folder.relative_to(ROOT).as_posix()}/per_horizon.csv`.\n\n",
      '07_Error_Analysis_and_Limitations.md':science+'''LSTM absolute cóbias âm,lỗi tăng ở mứcgiá cao; điều chỉnhresidual giảmđángkể lỗi so vớibản gốc. Probeshistory/flat vàgradient cho thấy lịch sử cũ ảnhhưởng yếu ởfold2023,hàmhiệuchỉnhgầnhằngsố; chưa đủkếtluậnLSTM họcđượcquyluậtthịtrường mạnh. Coregradient/weights cóđườnghọchoạtđộng,khôngpháthiệnđứtbackprop; mean-readoutablationkhôngđượcchọn.

Giới hạn: một ticker/mộtfeature,adjustedclosehồicứu,validationđãdùngchọnmodel,ngânsáchtuningLSTM/CNNkhácnhau,H5windowschồnglấn,khôngholdoutmớisaupháttriểnresidual,chưathresholdýnghĩathựctiễn/thốngkê,khôngsuyralợinhuận. Trainingtests/đồthịbámgiákhôngthay bằngchứnghiệuquả. Chưaxácnhậnmáykhác/quyềnphânphốicôngkhaidữliệu. KhôngsửacáckếtquảbấtlợiđểđạtđiềukiệnLSTMthắng.

'''}
    for name,content in contents.items():
        path=ROOT/'reports'/name
        if name.startswith(('01_','05_')):path.write_text(content,encoding='utf-8')
        else:
            old_text=path.read_text(encoding='utf-8')
            if header not in old_text:path.write_text(header+content+'---\n\n## Lịch sử các giai đoạn — không dùng làm trạng thái hiện tại\n\n'+old_text,encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--write-reports',action='store_true')
    main(parser.parse_args().write_reports)
