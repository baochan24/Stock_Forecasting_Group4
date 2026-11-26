"""Build reviewable TV2/TV3/TV4 notebooks; backend remains the source of logic."""
import argparse
from pathlib import Path
import textwrap
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
KERNEL = "aapl-coursework-tv2-tv3"


def md(text): return nbf.v4.new_markdown_cell(textwrap.dedent(text).strip())
def code(text): return nbf.v4.new_code_cell(textwrap.dedent(text).strip())


SETUP = '''
from pathlib import Path
import sys, json, os, subprocess, hashlib
from datetime import datetime, timezone
import importlib.metadata as packages
import numpy as np
import pandas as pd
from IPython.display import display, Markdown

ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p/'backend/data/preparation/snapshot.py').is_file())
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
VERSION = 'aapl_2015_2025_acq_20261119T141302002415Z'
SCALER_DIR = ROOT/'artifacts/scalers/aapl_scaler_20261120T124720810874Z'
PREPARED_DIR = ROOT/'data/prepared/tv2_prepared_20261122T145943242978Z'
print('Executed UTC:', datetime.now(timezone.utc).isoformat())
print('Python:', sys.executable)
display(pd.DataFrame([{'package':n, 'version':packages.version(n)} for n in ['numpy','pandas','scikit-learn','torch','pytest']]))

def run_check(script, *args):
    env = dict(os.environ, OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', PYTHONIOENCODING='utf-8')
    run = subprocess.run([sys.executable, '-X', 'utf8', str(ROOT/'scripts'/script), *args], cwd=ROOT, env=env, capture_output=True, text=True, encoding='utf-8')
    print(run.stdout)
    if run.returncode: raise RuntimeError(run.stderr or run.stdout)
    return json.loads(run.stdout)
'''

LOAD = '''
from backend.data.preparation.snapshot import load_tv1_snapshot
from backend.artifacts.scaler import load_scaler
from backend.artifacts.prepared import load_prepared_modes
snapshot = load_tv1_snapshot(ROOT, VERSION)
data = snapshot['data']
scaler, scaler_manifest = load_scaler(SCALER_DIR, expected_dataset_version=VERSION, expected_source_hashes=snapshot['acceptance']['hashes'])
modes, prepared_manifest = load_prepared_modes(PREPARED_DIR, expected_dataset_version=VERSION, expected_source_hashes=snapshot['acceptance']['hashes'], expected_scaler_id=scaler_manifest['scaler_id'])
assert snapshot['acceptance']['passed']
display(data.head())
print('Snapshot rows:', len(data), '| dates:', data.date.iloc[0], '→', data.date.iloc[-1])
'''


def tv2():
    return [
        md('''# TV2 — từ dữ liệu AAPL đến mẫu học có thể kiểm chứng
        Mục tiêu: chuẩn bị 30 phiên lịch sử để dự báo 1 hoặc 5 phiên. Notebook gọi backend thật; không nhân bản pipeline.
        Các cell có dữ liệu thật, kiểm tra/assertions và đường dẫn log. Run All chạy tests/audit lại và tạo evidence ID mới, không fit lại scaler hoặc sửa snapshot.
        **Phạm vi:** preprocessing đã kiểm chứng local; xác nhận máy thành viên khác còn chờ. Không có kết quả huấn luyện/MAE/RMSE.
        Đọc cùng `docs/TV2_Setup_and_Handoff.md`, `reports/audits/TV2_Final_Handoff.md`. Chạy từ workspace có artifacts, kernel Python `.venv/tv3_review_env`.'''),
        md('## Cấu hình và môi trường đang chạy'), code(SETUP),
        md('''## 1. Module nền và hợp đồng đầu vào
        Các helper kiểm tra cột/ngày/ticker/giá hữu hạn và shape, không âm thầm loại dòng. Source trong backend/data/preparation và transforms.
        Cell dưới hiển thị interface thật để liên hệ mã nguồn và bước xử lý.'''),
        code('''import inspect
from backend.data.preparation.preparation import split_data, fit_scaler
from backend.data.transforms.scaling import scale, inverse_scale
display(pd.DataFrame([{'function':fn.__name__, 'signature':str(inspect.signature(fn)), 'source':str(Path(inspect.getfile(fn)).relative_to(ROOT))} for fn in [split_data,fit_scaler,scale,inverse_scale]]))'''),
        md('''## 2. Tiếp nhận snapshot TV1
        Xác minh 5 artifacts/version/hash/provenance/schema/giá và lịch tham chiếu, không tải lại hoặc cleaning. NASDAQ trong thư viện ánh xạ XNYS; giá adjusted là hồi cứu, không coi là backtest point-in-time hoàn hảo.'''),
        code(LOAD),
        code('''display(pd.DataFrame([{'check':name, 'passed':value} for name,value in snapshot['acceptance']['checks'].items()]))
display(pd.DataFrame([{'artifact':name, 'sha256':value} for name,value in snapshot['acceptance']['hashes'].items()]))'''),
        md('''## 3. Chia tập theo ngày target, giữ nguyên lịch sử
        Train2015–2022, validation2023, test2024–2025. Input được dùng lịch sử đã quan sát từ tập trước. Số phiên khác số mẫu do cần đủ lookback/target.'''),
        code('''from backend.data.preparation.preparation import create_split_plan
plan = create_split_plan(data)
display(pd.DataFrame([{'split':s,'sessions':len(idx),'first':data.date.iloc[idx[0]],'last':data.date.iloc[idx[-1]]} for s,idx in plan['target_indices'].items()]))
import matplotlib.pyplot as plt
fig,ax = plt.subplots(figsize=(10,3))
for s,idx in plan['target_indices'].items(): ax.plot(pd.to_datetime(data.date.iloc[idx]),data.adjusted_close.iloc[idx],label=s)
ax.set(ylabel='Adjusted close (USD)',title='Dữ liệu gốc theo split — không phải dự báo'); ax.legend(); plt.show()'''),
        md('''## 4. Scaler chỉ fit train
        Scaler hiện có đã fit2014 giá train và được load lại, không fit trong notebook. Metadata liên kết ngày/version/hashes; không refit với validation/test.'''),
        code('''meta = scaler_manifest['metadata']
display(pd.DataFrame([{'scaler_id':scaler_manifest['scaler_id'],'fit_first':meta['fit_first_date'],'fit_last':meta['fit_last_date'],'fit_rows':meta['fit_row_count'],'mean_USD':scaler.mean_[0],'scale_USD':scaler.scale_[0],'dtype':str(scaler.mean_.dtype)}]))
assert meta['fit_split']=='train' and meta['fit_last_date']<='2022-12-31' ''') ,
        md('''## 5. Scale và inverse về USD
        z=(P−mean_train)/scale_train. Kiểm tra số học không phải sai số dự báo. Không làm tròn trước khi kiểm tra, không clip z âm.'''),
        code('''values = data.adjusted_close.iloc[[0,2014,2264,-1]].to_numpy().reshape(-1,1)
z = scale(values,scaler); restored = inverse_scale(z,scaler)
np.testing.assert_allclose(restored,values,rtol=1e-12,atol=1e-12)
display(pd.DataFrame({'price_USD':values.ravel(),'z':z.ravel(),'inverse_USD':restored.ravel(),'absolute_numeric_error':np.abs(restored-values).ravel()}))'''),
        md('''## 6. Cửa sổ một bước
        X=(B,30,1), y=(B,1). Mỗi input kết thúc ở origin, target là phiên kế tiếp trong snapshot. Chỉ30 phiên đầu train thiếu lịch sử; không bỏ30 target đầu val/test.'''),
        code('''display(pd.DataFrame([{'split':s,'samples':b['num_samples'],'X_shape':str(b['X'].shape),'y_shape':str(b['y'].shape),'excluded_history':b['excluded_insufficient_history']} for s,b in modes[1]['splits'].items()]))
b = modes[1]['splits']['val']; inp,tgt = b['inputs'][0],b['targets'][0]
display(pd.DataFrame({'input_date':inp['input_dates'],'raw_input_USD':inp['input_values'].ravel()}))
display(pd.DataFrame({'target_date':tgt['target_dates'],'raw_target_USD':tgt['target_values']}))
assert inp['forecast_origin'] < tgt['target_dates'][0] ''') ,
        md('''## 7. Direct multi-output5 bước
        X=(B,30,1), y=(B,5);5 target phải cùng split. Loại4 candidate cuối train/val vì cắt ranh giới,4 cuối test vì chưa đủ tương lai. Không recursive.'''),
        code('''display(pd.DataFrame([{'split':s,'samples':b['num_samples'],'X_shape':str(b['X'].shape),'y_shape':str(b['y'].shape),'cross_split':b['excluded_cross_split_targets'],'incomplete':b['excluded_incomplete_targets']} for s,b in modes[5]['splits'].items()]))
tgt = modes[5]['splits']['test']['targets'][-1]
display(pd.DataFrame({'horizon_step':tgt['horizon_step'],'target_date':tgt['target_dates'],'raw_target_USD':tgt['target_values']}))'''),
        md('''## 8. Input/target tách biệt, ID/version/ngày/shape
        Chỉ input được đi vào adapter inference. Các record phải khớp snapshot và scaled arrays. Cell dưới chạy lại kiểm tra cả hai chế độ, không fit model/scaler.'''),
        code('''from backend.data.preparation.contracts import validate_window_result,build_inference_inputs
display(pd.DataFrame([validate_window_result(result,data,scaler) for result in modes.values()]))
b=modes[1]['splits']['val']; only=build_inference_inputs(b['inputs'],scaler)
np.testing.assert_array_equal(only['X'],b['X'])
print('Input-only keys:',list(only), '| Target fields:',list(b['targets'][0]))'''),
        md('''## 9. Tests và audit leakage
        Chạy suite TV2 thật; không skip. Audit độc lập train moments/coverage, thay giá tương lai trong bản sao để kiểm input quá khứ không đổi. Có12 ví dụ đối chiếu ngày/giá trong log; không sửa snapshot.'''),
        code('''tv2_tests = run_check('run_tv2_checks.py')
assert tv2_tests['passed']'''),
        code('''leakage_run = run_check('audit_tv2_leakage.py','--dataset-version',VERSION,'--scaler-dir',str(SCALER_DIR))
leakage = json.loads(Path(leakage_run['evidence']).read_text(encoding='utf-8'))
assert leakage['passed']
display(pd.DataFrame([{'mode':m['forecast_length'],**p} for m in leakage['modes'] for p in m['future_price_perturbations']]))'''),
        md('''## 10. Bàn giao và tái lập
        Gói ZIP hiện có chứa source tại thời điểm đóng gói22/11/2026, không tự cập nhật theo notebook này hoặc code TV3 mới. Cell kiểm hash ZIP và hiển thị evidence venv sạch/gói giải nén đã chạy; chưa có xác nhận máy thành viên khác.'''),
        code('''archive=ROOT/'artifacts/releases/TV2_Handoff_20261122T145943242978Z.zip'
digest=hashlib.sha256(archive.read_bytes()).hexdigest()
assert digest=='2102c638b44cae2b078e1f67fea60735f3273ccd0bc8455812b4a3e35c3b1baa'
receipt=json.loads((ROOT/'logs/audit/tv2_handoff_repro_20261122T150046833893Z/verify_summary.json').read_text(encoding='utf-8'))
display(pd.DataFrame([{'zip':archive.name,'sha256':digest,'clean_local_verify':receipt['passed'],'recipient_machine_verified':receipt['recipient_machine_verified']}]))
display(Markdown('**Kết luận TV2:** kỹ thuật local đã kiểm chứng; chờ xác nhận liên máy. Tests/audit không chứng minh mô hình dự báo tốt.'))'''),
    ]


def tv3():
    return [
        md('''# TV3 — LSTM và bằng chứng kiểm định theo từng hạng mục
        Bài toán:30 phiên adjusted close AAPL →1 hoặc5 giá tiếp theo. Notebook gọi module thật, không xây training loop riêng.
        **Mục1–5 đã nghiệm thu local; mục6 kiểm gói bàn giao trong notebook này. Chưa xác nhận máy người nhận hoặc checkpoint train AAPL.** Cấu hình hiện tại float64; không hạ precision TV2.
        Model trong minh họa là trọng số khởi tạo, không phải checkpoint đã train. Không dùng output dưới đây để tuyên bố độ chính xác hoặc gợi ý giao dịch.
        Tham chiếu `reports/audits/TV3_Progress.md`. Run All chạy lại suite tests và kiểm tra metadata/artifacts.'''),
        md('## Môi trường và nguồn dữ liệu'),code(SETUP),
        md('''## 1. Source đúng module và kiến trúc
        Source tác giả được tiếp nhận vào backend/models và backend/model_trace. Bản GitHub nguyên trạng audit trước lỗi import; workspace này đã sửa bố trí. Sau đó đổi dtype mặc định64 theo lựa chọn người dùng.'''),
        code('''import torch, inspect
from backend.models.lstm_one_step import LSTMOneStep
from backend.models.lstm_multi_step import LSTMMultiStep
torch.set_num_threads(1)
models={1:LSTMOneStep().eval(),5:LSTMMultiStep().eval()}
display(pd.DataFrame([{'model':type(m).__name__,'source':str(Path(inspect.getfile(type(m))).relative_to(ROOT)),'parameters':sum(p.numel() for p in m.parameters()),'weight_dtype':str(next(m.parameters()).dtype),'layers':m.lstm.num_layers,'hidden':m.lstm.hidden_size,'outputs':m.fc.out_features} for m in models.values()]))
print(models[1])'''),
        md('''## 2. Kết nối với TV2 chính thức
        Accept snapshot/scaler/prepared bằng version/hash trước adapter. X/y CPU float64, shape giữ nguyên; model chỉ nhận X. Notebook không refit/scaler hoặc thay dữ liệu nguồn.'''),code(LOAD),
        code('''from backend.data.preparation.tensors import make_lstm_inputs,make_lstm_training_batch
rows=[]
for h,result in modes.items():
    batch=result['splits']['val']
    packed=make_lstm_training_batch(batch,scaler,dataset_version=VERSION,forecast_length=h)
    only=make_lstm_inputs(batch['inputs'],scaler,dataset_version=VERSION,forecast_length=h)
    np.testing.assert_array_equal(packed['X'].numpy(),batch['X'])
    torch.testing.assert_close(only['X'],packed['X'],rtol=0,atol=0)
    with torch.no_grad(): prediction=models[h](only['X'][:2])
    rows.append({'mode':h,'samples':len(packed['X']),'X_shape':str(tuple(packed['X'].shape)),'y_shape':str(tuple(packed['y'].shape)),'dtype':str(packed['X'].dtype),'tensor_copy_max_difference':float(np.max(np.abs(packed['X'].numpy()-batch['X']))),'demo_output_shape':str(tuple(prediction.shape)),'finite':bool(torch.isfinite(prediction).all())})
display(pd.DataFrame(rows))
display(Markdown('Output shape/finite đạt chỉ chứng minh kết nối kỹ thuật; model chưa học từ AAPL.'))'''),
        md('''### Quyết định dtype: giữ float64
        Dữ liệu/scaler/model/tensor đều64. Float64 giảm lỗi làm tròn nhưng không bảo đảm dự báo tốt hơn. Bảng dưới đọc phép đo CPU tổng hợp đã lưu, không phải thời gian train AAPL. Thread1, batch32,5 rounds×10 iterations; không đo lại khi Run All.'''),
        code('''bench=json.loads((ROOT/'logs/audit/tv3_precision_20261123T022251223682Z/summary.json').read_text(encoding='utf-8'))
display(pd.DataFrame([{'model':r['model'],'forward32_ms':1000*r['measurements']['float32']['forward_median_seconds_per_batch'],'forward64_ms':1000*r['measurements']['float64']['forward_median_seconds_per_batch'],'Adam32_ms':1000*r['measurements']['float32']['adam_step_median_seconds_per_batch'],'Adam64_ms':1000*r['measurements']['float64']['adam_step_median_seconds_per_batch'],'weights64_bytes':r['parameter_bytes']['float64']} for r in bench['results']]))
print(bench['scope']); print(bench['limitations'])'''),
        md('''## 3. Nghiệm thu kiến trúc/state/gradient/lưu-nạp
        Chạy toàn bộ tests đang có và hiển thị từng case. Acceptance kiểm forward so LSTM→Linear, gradient sai phân số với mạng nhỏ hidden2/T3, backward mặc định hidden32, h/c zero mới, batch ordering, Adam smoke, file state_dict roundtrip và trọng số hai mode độc lập.
        Tests dùng dữ liệu tổng hợp; state_dict tạm không là checkpoint nghiên cứu. Không chứng minh optimizer hội tụ hoặc model vượt baseline.'''),
        code('''test_run=run_check('run_tv3_checks.py','--require-clean')
assert test_run['passed']
test_summary_path=Path(test_run['evidence'])
test_summary=json.loads(test_summary_path.read_text(encoding='utf-8'))
print('Evidence:',test_summary_path)
display(pd.DataFrame([test_summary['counts']]))
for relative,digest in test_summary['source_hashes'].items():
    assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==digest
print('Source hashes vẫn khớp evidence.')'''),
        code('''import xml.etree.ElementTree as ET
tree=ET.parse(test_summary_path.parent/'junit.xml')
cases=[]
for case in tree.getroot().iter('testcase'):
    status='FAIL' if case.find('failure') is not None or case.find('error') is not None else ('SKIP' if case.find('skipped') is not None else 'PASS')
    cases.append({'module':case.get('classname'),'test':case.get('name'),'status':status,'seconds':float(case.get('time','0'))})
with pd.option_context('display.max_rows',None):
    display(pd.DataFrame(cases))'''),
        md('''## 4. Trace sau cập nhật trọng số và lưu/nạp
        Trace tái dựng các gate i/f/g/o từ chính weights và hai bias của LSTM, đối chiếu hidden/cell từng phiên và output với PyTorch. Đây không phải gate hook trực tiếp từ kernel, không giải thích nguyên nhân thị trường.
        Công thức: c_t=f_t*c_(t−1)+i_t*g_t; h_t=o_t*tanh(c_t). Một cửa sổ, eval/no_grad, không target. Float64 dùng rtol1e-10/atol1e-12; mismatch/nonfinite phải báo lỗi.
        Cell sau chạy kiểm chứng cả hai model qua3 giai đoạn: khởi tạo, sau1 bước Adam **tổng hợp** và sau nạp state_dict. Không huấn luyện AAPL, không checkpoint nghiên cứu hoặc API TV6 đã chốt.'''),
        code('''trace_run=run_check('check_tv3_trace.py','--dataset-version',VERSION,'--scaler-dir',str(SCALER_DIR),'--prepared-dir',str(PREPARED_DIR))
trace_folder=Path(trace_run['evidence']).parent
trace_summary=json.loads((trace_folder/'summary.json').read_text(encoding='utf-8'))
assert trace_summary['passed'] and trace_summary['reload_trace_exact']
display(pd.DataFrame(trace_summary['checks']))
for name,digest in trace_summary['trace_files'].items():
    assert hashlib.sha256((trace_folder/name).read_bytes()).hexdigest()==digest
print('6 trace JSON có checksum khớp; trace sau reload khớp tuyệt đối trace sau cập nhật.')'''),
        code('''envelope=json.loads((trace_folder/'f5_after_reload.json').read_text(encoding='utf-8'))
trace=envelope['trace']
print(envelope['scope'])
print('Sample:',envelope['sample_id'],'| origin:',envelope['forecast_origin'])
gate_rows=[]
for date,scaled,step in zip(envelope['input_dates'],trace['input_scaled'],trace['steps']):
    gate_rows.append({'time_step':step['time_step'],'input_date':date,'input_scaled':scaled[0],
                     'input_gate_0':step['input_gate'][0],'forget_gate_0':step['forget_gate'][0],
                     'candidate_0':step['candidate_state'][0],'output_gate_0':step['output_gate'][0],
                     'hidden_0':step['hidden_state'][0],'cell_0':step['cell_state'][0]})
gate_table=pd.DataFrame(gate_rows)
display(gate_table)
import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(10,3))
for column in ['input_gate_0','forget_gate_0','candidate_0','output_gate_0']:
    ax.plot(gate_table.time_step,gate_table[column],label=column)
ax.set(xlabel='Phiên trong cửa sổ',ylabel='Giá trị gate/candidate',title='Kênh 0 minh họa phép tính — không có diễn giải kinh tế'); ax.legend(); plt.show()'''),
        code('''previous=np.asarray(trace['initial_cell'],dtype=np.float64)
for step in trace['steps']:
    i,f,g,o,c,h=[np.asarray(step[k],dtype=np.float64) for k in ['input_gate','forget_gate','candidate_state','output_gate','cell_state','hidden_state']]
    np.testing.assert_allclose(c,f*previous+i*g,rtol=1e-10,atol=1e-12)
    np.testing.assert_allclose(h,o*np.tanh(c),rtol=1e-10,atol=1e-12)
    previous=c
print('Đối chiếu recurrence đủ 30 phiên × 32 chiều đạt.')
display(Markdown('**Giới hạn:** gate là phép tính tái dựng được đối chiếu; JSON schema nội bộ, chưa là API chính thức. Trọng số sau bước tổng hợp không phải model đã học dự báo AAPL.'))'''),
        md('''## 5. Môi trường CPU sạch và tái lập
        Notebook này phải chạy bằng `.venv/tv3_clean`, không kế thừa system/user packages. Cell tests ở trên dùng --require-clean: kiểm nguồn imports, lock, torch CPU build, pip-check và không skip.
        Lock68 dependencies nằm trong scripts/requirements-tv3-lock.txt, hướng dẫn docs/TV3_Setup_and_Reproduce.md. Phiên bản ghi ở output là phiên thực chạy, không chép số liệu từ môi trường audit cũ.
        **Local sạch không đồng nghĩa máy thành viên khác.** Cần người nhận xác nhận riêng, không tự gắn tên/kết quả thay họ.'''),
        code('''assert test_summary['require_clean'] and test_summary['clean_environment']
assert test_summary['user_site_enabled'] is False
assert test_summary['cpu_torch_build'] and test_summary['pip_check_exit_code']==0
assert not test_summary['lock_mismatches']
display(pd.DataFrame([{'module':n,'import_source':p} for n,p in test_summary['module_origins'].items()]))
display(pd.DataFrame([{'prefix':test_summary['prefix'],'base_prefix':test_summary['base_prefix'],'user_site':test_summary['user_site_enabled'],'torch_CPU_build':test_summary['cpu_torch_build'],'lock_sha256':test_summary['lock_sha256']}]))
print((test_summary_path.parent/'pip-check.log').read_text(encoding='utf-8'))
print((test_summary_path.parent/'requirements-freeze.txt').read_text(encoding='utf-8'))'''),
        md('''## 6. Bàn giao source/contract cho TV4 và TV6
        TV4 nhận hai model và X/y float64 để thực hiện training/validation/early stopping; TV6 nhận loader/input-only/trace để tích hợp sau khi có checkpoint thật. Không có weights AAPL đã train trong gói này.
        Checkpoint loader kiểm identity/hash/dtype/horizon và mặc định từ chối trained=False. Metadata training do TV4 chịu trách nhiệm; JSON không chứng minh đã train. Xem docs/TV3_Handoff_TV4_TV6.md.
        Cell sau kiểm gói cụ thể và receipt verify sau giải nén. Notebook source được bảo vệ bằng hash cells, outputs được phép cập nhật; chưa xác nhận người nhận trên máy khác.'''),
        code('''from scripts.verify_tv3_handoff import verify_members
if (ROOT/'HANDOFF_TV3.json').is_file():
    handoff_root=ROOT
    handoff=json.loads((ROOT/'HANDOFF_TV3.json').read_text(encoding='utf-8'))
    package_info={'handoff_id':handoff['handoff_id'],'archive_sha256':'Xem checksum ZIP riêng do người gửi cung cấp'}
else:
    receipts=sorted((ROOT/'logs/audit').glob('tv3_package_*/summary.json'))
    assert receipts, 'Cần tạo và verify gói TV3 trước khi chạy mục6.'
    package_info=json.loads(receipts[-1].read_text(encoding='utf-8'))
    assert hashlib.sha256(Path(package_info['archive']).read_bytes()).hexdigest()==package_info['archive_sha256']
    handoff_root=Path(package_info['bundle_root'])
    handoff=json.loads((handoff_root/'HANDOFF_TV3.json').read_text(encoding='utf-8'))
verify_members(handoff_root,handoff)
verified=[]
paths=list((ROOT/'logs/audit').glob('tv3_handoff_repro_*/verify_summary.json'))+list((ROOT/'logs/audit').glob('tv3_handoff_verify_*/summary.json'))
for path in paths:
    value=json.loads(path.read_text(encoding='utf-8'))
    if value.get('handoff_id')==handoff['handoff_id'] and value.get('passed'): verified.append((path,value))
assert verified, 'Cần chạy verify_tv3_handoff.py từ bản giải nén trước.'
verify_path,verify_result=sorted(verified,key=lambda pair:str(pair[0]))[-1]
assert handoff['trained_checkpoints']==[]
display(pd.DataFrame(handoff['model_configs']))
display(pd.DataFrame([{'handoff_id':handoff['handoff_id'],'ZIP_SHA256':package_info['archive_sha256'],'local_verify':verify_result['passed'],'trained_checkpoints':len(handoff['trained_checkpoints']),'recipient_machine_verified':verify_result['recipient_machine_verified']}]))
print('Verify evidence:',verify_path)
display(Markdown('**Bàn giao kỹ thuật local đạt. Chưa có checkpoint train AAPL; chưa tự đánh dấu TV4/TV6 đã nhận hoặc máy khác đã chạy.**'))'''),
        code('''display(pd.DataFrame([{'item':i,'work':w,'status':s} for i,w,s in [(1,'Layout/import/model modules','Đạt local'),(2,'TV2 adapter/float64 identity','Đạt local'),(3,'Model acceptance','Đạt local'),(4,'Trace acceptance','Đạt local'),(5,'Clean environment/reproduce','Đạt local'),(6,'Source/contract handoff','Đạt kỹ thuật local; chờ người nhận/checkpoint thật')]]))
display(Markdown('**Giới hạn:** chưa xác nhận máy khác, không train/tuning/metric AAPL trong notebook này.'))'''),
    ]


def tv4():
    setup_path = '''from pathlib import Path
import sys
from datetime import datetime, timezone

cwd = Path.cwd().resolve()
ROOT = next((folder for folder in (cwd, *cwd.parents)
             if (folder / 'rule.md').is_file() and (folder / 'backend/training/trainer.py').is_file()), None)
if ROOT is None:
    raise RuntimeError(f'Hãy mở notebook trong thư mục project. Thư mục kernel hiện tại là {cwd}')
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
'''
    return [
        md('''# TV4 — Training và thực nghiệm LSTM
        **Đã hoàn thành 10 hạng mục TV4 tại workspace — training, thực nghiệm và bộ bàn giao local.**

        LSTM năm bước đã hoàn tất ba seed, tổng 300 epoch. Validation MSE tổng trung bình 0,007692942, std mẫu 0,000146946. [Đi tới kết quả năm bước](#tv4-item-9).

        Chín run đã hoàn tất với lookback 10/30/60 và seeds 42/123/456. Mỗi cấu hình dùng cùng 1.954 mẫu train và 250 mẫu validation. Chọn lookback 30 theo validation MSE trung bình thấp nhất.

        | Lookback | Validation MSE trung bình | Độ lệch chuẩn mẫu |
        |---|---:|---:|
        | 10 | 0,012245378 | 0,016262211 |
        | 30 | 0,003265939 | 0,001118952 |
        | 60 | 0,003563105 | 0,000768613 |

        Đi tới [mục 6 — smoke và CPU](#tv4-item-6), [mục 7 — audit và kế hoạch](#tv4-item-7), [mục 8 — chín run và biểu đồ](#tv4-item-8). Tại mục 8 có bảng từng seed và chín biểu đồ train/validation đã lưu output.

        Xem [mục 10 — kiểm chứng và tổng hợp đầu ra](#tv4-item-10). Xác nhận máy người nhận được ghi riêng khi có kết quả thực tế.
        Nguồn PR#10, commit16555929210314b1eb06da9dc84b827ececc1b9e; nhận9 file nguyên nội dung, đặt runner đúng backend/experiments/runner.
        Mục 2 dùng tensors tổng hợp. Mục 3 kiểm tra toàn bộ batch train/validation AAPL bằng hai LSTM TV3.
        Mục tiêu bài: TV4 huấn luyện hai LSTM TV3 trên dữ liệu TV2, chọn checkpoint bằng validation để TV6 đánh giá sau.'''),
        code(setup_path + '''
import json, os, subprocess, hashlib
import xml.etree.ElementTree as ET
import pandas as pd
from IPython.display import display, Markdown
print('Executed UTC:',datetime.now(timezone.utc).isoformat())
print('Python:',sys.executable)
print('TV4 mục 1–4 | Kiểm thử, dữ liệu AAPL và quản lý run')'''),
        md('''## 1. Tiếp nhận source và sửa import
        Đầu vào: source PR#10 đã audit, không nhận toàn nhánh bằng cách ghi đè workspace.
        Đầu ra: trainer, runner, manager, hai YAML và ba file tests đúng module.
        Receipt bên dưới ghi hash của các file lúc tiếp nhận. Mục 3 cập nhật hai YAML để sử dụng đúng snapshot và scaler của TV2.'''),
        code('''from backend.training import trainer
from backend.experiments.runner import experiment_runner
from backend.experiments.management import experiment_manager
modules=[trainer,experiment_runner,experiment_manager]
rows=[]
for module in modules:
    p=Path(module.__file__).resolve()
    assert p.is_relative_to(ROOT/'backend')
    rows.append({'module':module.__name__,'file':p.relative_to(ROOT).as_posix()})
display(pd.DataFrame(rows))
intake_path=ROOT/'logs/audit/tv4_item1_20261125/intake.json'
if intake_path.is_file():
    intake=json.loads(intake_path.read_text(encoding='utf-8'))
    display(pd.DataFrame(intake['files']))
    print('PR:',intake['pr'],'| commit:',intake['head'],'| source content unchanged at intake:',intake['source_content_unchanged'])
else:
    print('Không có receipt tiếp nhận trên máy này; source/lock được kiểm bằng runner bên dưới.')'''),
        md('''### Kiểm thử baseline từ workspace
        Chạy tests trực tiếp, không alias import và không lấy code từ checkout audit.
        Các tests dùng tensor tổng hợp; checkpoint được mock. Một phép thử học hồi quy tuyến tính là bằng chứng loop tổng hợp, không phải training AAPL.
        Môi trường TV4 riêng không kế thừa system/user packages, khớp lock có PyYAML.'''),
        code('''env=dict(os.environ,OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONIOENCODING='utf-8')
env.pop('PYTHONPATH',None)
run=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'scripts/run_tv4_checks.py'),'--require-clean'],cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8')
print(run.stdout)
if run.returncode: raise RuntimeError(run.stderr or run.stdout)
receipt=json.loads(run.stdout)
summary_path=Path(receipt['evidence'])
summary=json.loads(summary_path.read_text(encoding='utf-8'))
assert summary['passed'] and summary['workspace_imports'] and summary['source_unchanged_during_tests']
assert summary['counts']['tests']>0 and all(summary['counts'][k]==0 for k in ['failures','errors','skipped'])
cases=[]
for case in ET.parse(summary_path.parent/'junit.xml').getroot().iter('testcase'):
    cases.append({'suite':case.get('classname'),'test':case.get('name'),'seconds':case.get('time'),'result':'FAIL' if case.find('failure') is not None or case.find('error') is not None else 'SKIP' if case.find('skipped') is not None else 'PASS'})
with pd.option_context('display.max_rows',None,'display.max_colwidth',120): display(pd.DataFrame(cases))
print('Evidence:',summary_path)'''),
        code('''assert summary['require_clean'] and summary['clean_environment']
assert summary['user_site_enabled'] is False and summary['cpu_torch_build']
assert not summary['lock_mismatches'] and summary['pip_check_exit_code']==0
display(pd.DataFrame([{'module':name,'source':path} for name,path in summary['module_origins'].items()]))
display(pd.DataFrame([{'prefix':summary['prefix'],'CPU_torch':summary['cpu_torch_build'],'lock_SHA256':summary['lock_sha256'],'protected_changes':summary['protected_changes_since_intake']}]))
print((summary_path.parent/'pip-check.log').read_text(encoding='utf-8'))
print((summary_path.parent/'requirements-freeze.txt').read_text(encoding='utf-8'))'''),
        md('''## 2. Contract CPU float64 với LSTM TV3
        Giữ dtype input/target, không tự cast hoặc di chuyển model. Hai LSTM yêu cầu CPU float64, một feature, horizon1/5; input(B,30,1), target(B,H).
        Loop chung vẫn hỗ trợ dtype của model tổng hợp khác; đây không phải quyết định dtype CNN. Lookback10/60 chỉ kiểm shape, chưa chạy thí nghiệm.
        Probe sau gọi loop thật với3 mẫu tổng hợp, batch2 nên batch cuối là1; kiểm Adam update, validation không thay weights/gradient, input không đổi và từ chốifloat32.
        Loss ở đây là diagnostic tổng hợp, không phải MAE/RMSE AAPL hoặc bằng chứng model dự báo tốt.'''),
        code('''probe=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'scripts/check_tv4_float64.py')],cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8')
print(probe.stdout)
if probe.returncode: raise RuntimeError(probe.stderr or probe.stdout)
contract_path=Path(json.loads(probe.stdout)['evidence'])
contract=json.loads(contract_path.read_text(encoding='utf-8'))
assert contract['passed'] and contract['default_dtype_unchanged']
display(pd.DataFrame(contract['checks']))
print('Contract evidence:',contract_path)
display(Markdown('**CPU float64 đạt cho hai LSTM trong loop tổng hợp. Không có checkpoint AAPL.**'))'''),
        md('''## 3. Dữ liệu AAPL từ TV2 đến hai LSTM
        Hai cấu hình YAML chỉ định phiên bản snapshot, scaler và bộ cửa sổ đã chuẩn bị. TV4 đối chiếu hash, thống kê scaler trên train và ngày target với lịch phiên. Mỗi batch giữ ID cùng X và y. Bảng bên dưới lấy từ một lượt forward qua toàn bộ train và validation theo thứ tự thời gian. Dòng năm bước có ít mẫu hơn vì cả năm target phải thuộc cùng tập.'''),
        code('''data_check=subprocess.run([sys.executable, str(ROOT/'scripts/check_tv4_aapl_data.py')],cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8')
if data_check.returncode: raise RuntimeError(data_check.stderr or data_check.stdout)
data_path=Path(json.loads(data_check.stdout)['evidence'])
data_report=json.loads(data_path.read_text(encoding='utf-8'))
assert data_report['passed']
display(pd.DataFrame([row for result in data_report['results'] for row in result['checks']])[['horizon','split','samples','batches','final_batch','first_origin','first_target','last_target']])
display(data_report['results'][0]['provenance'])
print('Evidence:', data_path)'''),
        md('''
        ### 3.1. Quan sát LSTM học trên dữ liệu AAPL

        Với kernel TV4 vừa mở, có thể bắt đầu ngay từ cell bên dưới rồi chạy lần lượt các cell còn lại của mục 3.1.

        Phần minh họa dùng LSTM một bước trên CPU float64 và scaler đã fit trên train. Mỗi mẫu gồm 30 giá đóng cửa điều chỉnh để dự báo phiên kế tiếp.

        **Một batch.** Xem dự báo cho cùng một cửa sổ trước và sau khi Adam cập nhật trọng số từ 32 mẫu. Gradient cho biết loss thay đổi theo trọng số như thế nào.

        **Năm epoch.** Mô hình bắt đầu lại từ cùng seed 42. Mỗi epoch đi qua toàn bộ tập train một lần, rồi đo loss trên toàn bộ validation năm 2023 với trọng số vừa học. Hai đường trên biểu đồ đều là MSE trên giá đã chuẩn hóa. Đây là lần chạy minh họa để đọc quá trình học.'''),
        code(setup_path + '''
import torch
import pandas as pd
from IPython.display import display
from backend.experiments.runner.experiment_runner import load_experiment_config
from backend.experiments.runner.aapl_factories import make_aapl_loaders, make_aapl_model
from backend.training.trainer import _run_epoch

demo_config = load_experiment_config(ROOT / 'experiments/configs/lstm_one_step_baseline.yaml')
demo_seed = demo_config['seeds'][0]
demo_train, demo_val = make_aapl_loaders(demo_config, demo_seed, project_root=ROOT)
demo_lr = demo_config['training']['learning_rate']
criterion = torch.nn.MSELoss()
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from backend.artifacts.scaler import load_scaler
from backend.data.transforms.scaling import inverse_scale

provenance = demo_train.dataset.provenance
demo_scaler, _ = load_scaler(ROOT / provenance['scaler_path'],
                             expected_dataset_version=provenance['dataset_version'],
                             expected_source_hashes=provenance['source_hashes'])
demo_stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
demo_dir = ROOT / 'logs' / 'audit' / f'tv4_training_demo_{demo_stamp}'
demo_dir.mkdir(parents=True)

def show_figure(fig, name):
    fig.savefig(demo_dir / name, dpi=155, bbox_inches='tight', facecolor='white')
    plt.show()
    plt.close(fig)

def new_demo_model():
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(demo_seed)
        return make_aapl_model(demo_config)

print(f"LSTM một bước | train {len(demo_train.dataset)} mẫu | validation {len(demo_val.dataset)} mẫu")
print(f"Adam | learning rate {demo_lr} | batch {demo_train.batch_size} | seed {demo_seed}")'''),
        code('''batch_model = new_demo_model()
first_batch = next(iter(demo_train))
x, y, ids = first_batch
weights_before = batch_model.fc.weight.detach().clone()
with torch.no_grad():
    prediction_before = batch_model(x)[0, 0].item()
optimizer = torch.optim.Adam(batch_model.parameters(), lr=demo_lr)
batch_mse = _run_epoch(batch_model, [first_batch], criterion, optimizer)
with torch.no_grad():
    prediction_after = batch_model(x)[0, 0].item()
    step_size = (batch_model.fc.weight - weights_before).norm().item()
assert step_size > 0
print('Mẫu đầu tiên trong batch:', ids[0])
display(pd.DataFrame([{'Target (chuẩn hóa)': y[0, 0].item(),
                       'Dự báo trước Adam': prediction_before, 'Dự báo sau Adam': prediction_after,
                       'MSE cả batch trước Adam': batch_mse, 'Chuẩn L2 gradient lớp cuối': batch_model.fc.weight.grad.norm().item(),
                       'Chuẩn L2 thay đổi trọng số lớp cuối': step_size}]))'''),
        md('''
        #### Một cửa sổ và một lần cập nhật Adam

        Bên trái, đường xanh kết thúc ở phiên gần nhất mô hình đã quan sát. Ba điểm ở phiên kế tiếp là giá thực tế và hai lần dự báo cho cùng một cửa sổ, trước và sau khi học batch đầu tiên. Giá được đổi về USD bằng scaler TV2. Bên phải, mỗi cột là thay đổi của một trọng số nối tầng LSTM với đầu ra. Cột âm cho biết trọng số giảm sau lần cập nhật này.'''),
        code('''window = inverse_scale(x[0, :, 0].numpy(), demo_scaler)
actual, before, after = inverse_scale(np.array([y[0, 0].item(), prediction_before, prediction_after]), demo_scaler)
delta = (batch_model.fc.weight.detach() - weights_before).flatten().numpy()
fig, (ax, weights_ax) = plt.subplots(1, 2, figsize=(11, 4.2), layout='constrained')
ax.plot(range(1 - len(window), 1), window, color='#00796b', label='Giá đã quan sát')
ax.axvline(0, color='0.6', linestyle=':', linewidth=1)
for price, label, marker, color in [(actual, 'Giá thực', 'o', '#00796b'),
                                    (before, 'Trước Adam', 'x', '#b35300'),
                                    (after, 'Sau Adam', '+', '#34599a')]:
    ax.scatter(1, price, marker=marker, color=color, s=75, label=f'{label} · {price:.2f} USD')
ax.set(xlabel='Phiên tương đối (0 = phiên cuối đã biết)', ylabel='Giá điều chỉnh (USD)',
       title=f'Cửa sổ đầu tiên · dự báo phiên {demo_train.dataset.target_dates[0][0]}',
       xticks=[1 - len(window), -20, -10, 0, 1])
ax.legend(fontsize=8)
weights_ax.bar(range(1, len(delta) + 1), delta, color=np.where(delta >= 0, '#00796b', '#b35300'))
weights_ax.axhline(0, color='0.3', linewidth=0.8)
weights_ax.set(xlabel='Chỉ số trọng số ở lớp đầu ra', ylabel='Trọng số sau trừ trọng số trước',
               title=f'Thay đổi sau một batch gồm {len(y)} mẫu')
weights_ax.ticklabel_format(axis='y', style='sci', scilimits=(-3, -3))
show_figure(fig, '01_window_and_weights.png')'''),
        md('''
        #### Từ batch đến epoch

        Trong mỗi epoch, Adam cập nhật mô hình sau từng batch theo thứ tự thời gian. Ta ghi MSE của batch ngay trước lần cập nhật, rồi giữ cố định trọng số cuối epoch để dự báo toàn bộ validation. Các số được lấy trực tiếp khi hàm loss của trainer chạy.'''),
        code('''demo_model = new_demo_model()
optimizer = torch.optim.Adam(demo_model.parameters(), lr=demo_lr)
history = []
batch_rows = []
validation_predictions = {}

def record_train_batch(module, inputs, loss):
    predictions, targets = inputs
    batch_rows.append({'Epoch': epoch, 'Batch': len(batch_rows) % len(demo_train) + 1,
                       'Samples': len(targets), 'MSE': loss.item()})

def record_validation_batch(module, inputs, loss):
    predictions, targets = inputs
    val_outputs.append(predictions.detach().clone())
    val_targets.append(targets.detach().clone())

for epoch in range(1, 6):
    with criterion.register_forward_hook(record_train_batch):
        train_loss = _run_epoch(demo_model, demo_train, criterion, optimizer)
    val_outputs, val_targets = [], []
    with criterion.register_forward_hook(record_validation_batch):
        val_loss = _run_epoch(demo_model, demo_val, criterion)
    predictions = torch.cat(val_outputs)
    targets = torch.cat(val_targets)
    assert torch.equal(targets, demo_val.dataset.y)
    np.testing.assert_allclose((predictions - targets).square().mean().item(), val_loss)
    validation_predictions[epoch] = predictions[:, 0].numpy()
    history.append({'Epoch': epoch, 'Train MSE': train_loss, 'Validation MSE': val_loss})
    print(f'Epoch {epoch}/5   Train MSE {train_loss:.6f}   Validation MSE {val_loss:.6f}', flush=True)
demo_history = pd.DataFrame(history).set_index('Epoch')
batches = pd.DataFrame(batch_rows)
for epoch, group in batches.groupby('Epoch'):
    assert len(group) == len(demo_train) and group['Samples'].sum() == len(demo_train.dataset)
    np.testing.assert_allclose(np.average(group['MSE'], weights=group['Samples']), demo_history.loc[epoch, 'Train MSE'])
batches.to_csv(demo_dir / 'train_batches.csv', index=False)
demo_history.to_csv(demo_dir / 'history.csv')
print('Đã lưu lịch sử epoch tại', (demo_dir / 'history.csv').relative_to(ROOT))
display(demo_history)'''),
        code('''epochs = demo_history.index.to_list()
best = demo_history['Validation MSE'].idxmin()
fig, (curve, heat) = plt.subplots(2, 1, figsize=(10, 7), layout='constrained')
for name, color, marker in [('Train MSE', '#00796b', 'o'), ('Validation MSE', '#b35300', 's')]:
    curve.plot(epochs, demo_history[name], color=color, marker=marker, label=name)
curve.scatter(best, demo_history.loc[best, 'Validation MSE'], s=160, facecolors='none', edgecolors='black')
curve.set(yscale='log', xticks=epochs, xlabel='Epoch', ylabel='MSE chuẩn hóa (thang log)',
          title=f'Loss trung bình · validation thấp nhất ở epoch {best}')
curve.grid(alpha=0.25)
curve.legend()
matrix = batches.pivot(index='Epoch', columns='Batch', values='MSE')
batch_image = heat.imshow(matrix.clip(lower=1e-12), norm=LogNorm(), cmap='viridis',
                          interpolation='nearest', aspect='auto',
                          extent=(0.5, len(demo_train) + 0.5, epochs[-1] + 0.5, 0.5))
heat.set(xlabel='Batch train theo thứ tự thời gian', ylabel='Epoch', yticks=epochs,
         title='Mỗi ô là MSE của một batch trước bước cập nhật Adam')
fig.colorbar(batch_image, ax=heat, label='MSE chuẩn hóa (thang log)')
show_figure(fig, '02_epoch_and_batch_loss.png')
print('Đọc theo hàng để theo dõi từng lần cập nhật trong một epoch. Đọc theo cột để so cùng nhóm cửa sổ qua 5 epoch.')
print('Ô sáng hơn biểu thị sai số lớn hơn. Các batch liên tiếp chứa các phiên khác nhau.')'''),
        md('''
        #### Mô hình dự báo cao hay thấp trên từng phiên validation?

        Hai biểu đồ dùng cùng các ngày target năm 2023. Đường giá đối chiếu thực tế với dự báo của epoch có validation MSE nhỏ nhất trong lần minh họa và epoch cuối. Phía dưới, mỗi ô ứng với một epoch và một phiên. Sai số bằng **dự báo trừ thực tế** theo USD. Xanh là dự báo thấp, đỏ là dự báo cao, trắng là gần đúng. Mỗi cột cho phép theo dõi cùng một phiên khi trọng số thay đổi.'''),
        code('''import matplotlib.dates as mdates
dates = pd.DatetimeIndex(pd.to_datetime([target[0] for target in demo_val.dataset.target_dates]))
assert dates.is_unique and dates.is_monotonic_increasing and (dates.year == 2023).all()
actual_usd = inverse_scale(demo_val.dataset.y[:, 0].numpy(), demo_scaler)
val_prices = pd.DataFrame({epoch: inverse_scale(validation_predictions[epoch], demo_scaler)
                           for epoch in epochs}, index=dates)
val_prices.rename_axis('target_date').add_prefix('epoch_').assign(actual_usd=actual_usd).to_csv(demo_dir / 'validation_usd.csv')
errors = val_prices.sub(actual_usd, axis='index')

fig, (price_ax, error_ax) = plt.subplots(2, 1, figsize=(11, 6.8), sharex=True, layout='constrained')
price_ax.plot(dates, actual_usd, label='Giá thực tế', color='0.16', linewidth=1.6)
for epoch in dict.fromkeys([best, epochs[-1]]):
    label = f'Epoch {epoch}' + (' · validation thấp nhất' if epoch == best else ' · cuối')
    price_ax.plot(dates, val_prices[epoch], label=label, linewidth=1.4,
                  color='#00796b' if epoch == best else '#b35300', linestyle='-' if epoch == best else '--')
price_ax.set(ylabel='Giá điều chỉnh (USD)', title=f'Dự báo trước một phiên · {len(dates)} phiên validation')
price_ax.grid(alpha=0.2)
price_ax.legend()
# Vẽ mỗi phiên rộng một ngày để cuối tuần và ngày nghỉ giữ đúng khoảng trống.
calendar = pd.date_range(dates.min(), dates.max(), freq='D')
values = errors.reindex(calendar).to_numpy().T
limit = np.nanmax(np.abs(values)) or 1.0
image = error_ax.imshow(values, aspect='auto', interpolation='nearest', cmap='RdBu_r', vmin=-limit, vmax=limit,
                        extent=(mdates.date2num(calendar[0])-0.5, mdates.date2num(calendar[-1])+0.5,
                                epochs[-1]+0.5, 0.5))
error_ax.set_facecolor('#dddddd')
error_ax.set(yticks=epochs, ylabel='Epoch', xlabel='Tháng của phiên target (2023)',
             title='Sai số có dấu từng phiên · ngày thị trường đóng cửa hiển thị màu xám')
error_ax.xaxis.set_major_locator(mdates.MonthLocator())
error_ax.xaxis.set_major_formatter(mdates.DateFormatter('%m'))
fig.colorbar(image, ax=error_ax, orientation='horizontal', shrink=0.65, pad=0.12, label='Dự báo − thực tế (USD)')
show_figure(fig, '03_validation_prices_and_errors.png')
print(f'Epoch {best} dự báo thấp hơn thực tế ở {(errors[best] < 0).sum()}/{len(dates)} phiên validation.')
print('Kết quả mô tả một lần chạy 5 epoch với seed', demo_seed)
print('Hình PNG và dữ liệu từng batch, từng phiên được lưu tại', demo_dir.relative_to(ROOT))'''),
        md('''
        ## 4. Nghiệm thu vòng huấn luyện và quản lý run

        Mục 3.1 dùng 5 epoch để quan sát. Ở đây trainer đọc cấu hình tối đa 100 epoch và patience 10. Để kiểm tra cả batch cuối chỉ có một mẫu, dùng 33 cửa sổ đầu của train và 33 cửa sổ đầu của validation từ bộ AAPL một bước. Con số MSE của phép thử chỉ mô tả các cửa sổ này.

        Bảng ghi lại từng epoch từ CSV trên đĩa. Hãy tìm epoch có validation MSE nhỏ nhất, rồi so với epoch dừng. Sau khi trainer khôi phục trọng số tốt nhất trong RAM, script dự báo lại 33 mẫu validation và đối chiếu MSE tính trực tiếp với giá trị đã ghi. Có thể chạy riêng từ cell kế tiếp bằng kernel TV4.'''),
        code(setup_path + '''
import json
import subprocess
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display

probe = subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'scripts/check_tv4_training_run.py')],
                       cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
if probe.returncode:
    raise RuntimeError(probe.stderr or probe.stdout)
evidence = Path(json.loads(probe.stdout)['evidence'])
item4 = json.loads(evidence.read_text(encoding='utf-8'))
assert item4['passed']
run_dir = ROOT / item4['run_dir']
meta = json.loads((run_dir / 'metadata.json').read_text(encoding='utf-8'))
epochs4 = pd.read_csv(run_dir / 'epoch_logs.csv')
display(pd.DataFrame(item4['splits']))
display(epochs4)
display(pd.DataFrame([{'Seed': meta['seed'], 'CPU threads': meta['torch_threads'], 'Trạng thái': meta['status'],
                       'Epoch tốt nhất': item4['best_epoch'], 'Epoch cuối': item4['epochs'],
                       'Dừng sớm': item4['early_stopped'], 'MSE tốt nhất': item4['best_val_loss'],
                       'MSE đo lại từ RAM': item4['restored_val_mse']}]))
print('Log và cấu hình của run:', run_dir)
print('Biên bản kiểm chứng:', evidence)'''),
        code('''ax = epochs4.plot(x='epoch', y=['train_loss', 'val_loss'], marker='.', figsize=(9, 3.8))
ax.set_yscale('log')
ax.axvline(item4['best_epoch'], color='#00796b', linestyle='--', label='Epoch tốt nhất')
ax.axvline(item4['epochs'], color='#933700', linestyle=':', label='Epoch cuối')
ax.set(xlabel='Epoch', ylabel='MSE chuẩn hóa (thang log)', title='LSTM một bước · 33 mẫu mỗi tập')
ax.legend()
plt.tight_layout()
plt.show()'''),
        md('''## 5. Lưu checkpoint và nạp model mới

        Runner lưu một thư mục mới cho mỗi lần validation cải thiện. Manifest ghi seed, cấu hình, epoch, loss, snapshot, scaler và năm hash nguồn. Phép thử dùng 33 cửa sổ mỗi tập của LSTM một bước. Model nạp từ đĩa phải dự báo bằng tuyệt đối model tốt nhất trong RAM trên toàn bộ 33 mẫu validation.'''),
        code(setup_path + '''
import subprocess, json
import pandas as pd
from IPython.display import display
run5 = subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'scripts/check_tv4_training_run.py'), '--checkpoint'],
                      cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
if run5.returncode:
    raise RuntimeError(run5.stderr or run5.stdout)
path5 = Path(json.loads(run5.stdout)['evidence'])
result5 = json.loads(path5.read_text(encoding='utf-8'))
assert result5['passed'] and result5['reload_verified']
display(pd.DataFrame([result5]))
print('Checkpoint:', result5['checkpoint_path'])
print('Bằng chứng:', path5)'''),
        md('''<a id="tv4-item-6"></a>

        ## 6. Smoke training hai horizon và đo CPU

        Chạy ba epoch trên toàn bộ train và validation cho mỗi LSTM, seed 42, một luồng tính toán, CPU float64. Lưu checkpoint theo validation rồi nạp model mới và so toàn bộ dự báo validation bằng dung sai 0. Đo riêng train, validation và 30 lượt inference batch sau 5 lượt làm nóng. Thời gian phụ thuộc máy và tải nền. Các kết quả thuộc lần chạy chẩn đoán giới hạn ba epoch.'''),
        code(setup_path + '''
import subprocess, json
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display
smoke = subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'scripts/check_tv4_smoke.py')],
                       cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
if smoke.returncode:
    raise RuntimeError(smoke.stderr or smoke.stdout)
receipt6 = Path(json.loads(smoke.stdout)['evidence'])
item6 = json.loads(receipt6.read_text(encoding='utf-8'))
assert item6['passed'] and all(row['reload_equal'] for row in item6['results'])
display(pd.DataFrame(item6['results']))
fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), layout='constrained')
for ax, row in zip(axes, item6['results']):
    history6 = pd.read_csv(Path(row['run_dir']) / 'epoch_logs.csv')
    ax.plot(history6.epoch, history6.train_loss, marker='o', label='Train')
    ax.plot(history6.epoch, history6.val_loss, marker='s', label='Validation')
    ax.set(title=row['model'], xlabel='Epoch', ylabel='MSE chuẩn hóa', xticks=history6.epoch, yscale='log')
    ax.legend()
plt.show()
print('Bằng chứng và điều kiện CPU:', receipt6)
print('Threads:', item6['threads'], '| CPU:', item6['cpu'])'''),
        md('''<a id="tv4-item-7"></a>

        ## 7. Audit thiết kế và ngân sách thực nghiệm

        Pipeline đã mở rộng lookback 10/30/60, giữ mặc định 30 cho callers cũ. Kế hoạch gồm 12 run, seeds 42/123/456, tối đa 100 epoch mỗi run. Báo cáo bên dưới ghi bằng chứng và các quy tắc trước training chính thức.'''),
        code(setup_path + '''
from IPython.display import display, Markdown
display(Markdown((ROOT / 'reports/audits/TV4_Item7_Experiment_Plan.md').read_text(encoding='utf-8')))'''),
        md('''<a id="tv4-item-8"></a>

        ## 8. Huấn luyện chính thức LSTM một bước

        Chín run dùng lookback 10/30/60 và seeds 42/123/456, cùng 1.954 mẫu train và 250 mẫu validation. Mỗi run tối đa 100 epoch, patience 10. Chọn lookback theo validation MSE trung bình ba seed, báo độ lệch chuẩn mẫu ddof=1. Cell đọc kết quả đã lưu để xem lại quá trình học.

        **Audit sau training.** Chín trạng thái run, best epoch và hash checkpoint đã đối chiếu đạt. Bốn run chạm 100 epoch, hai run có best ở epoch 100. Đây là giới hạn ngân sách cần ghi trong báo cáo. Dữ liệu thật và cấu hình LSTM năm bước đã kiểm tra lại, đủ điều kiện bước vào mục 9. Xem [báo cáo audit sau training](../reports/audits/TV4_Item8_OneStep_Training.md).

        Xem tương tác tại [TensorBoard local](http://127.0.0.1:6006) khi server đang chạy. Dashboard xuất từ CSV của chín run đã hoàn tất. Trục Step là epoch. Các nhóm Loss, Optimizer và Time hiển thị loss, learning rate và thời gian train/validation. Wall time của event là thời điểm xuất dữ liệu.'''),
        code(setup_path + '''
import json
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display, Markdown
item8_path = ROOT / 'logs/audit/tv4_item8_20261125T122649342552Z/summary.json'
item8 = json.loads(item8_path.read_text(encoding='utf-8'))
assert item8['passed'] and item8['status'] == 'completed'
results8 = pd.DataFrame(item8['results'])
assert len(results8) == 9 and results8.reload_verified.all()
display(results8[['lookback','seed','epochs','best_epoch','validation_mse','seconds','reload_verified']])
display(pd.DataFrame(item8['aggregates']))
print('Lookback được chọn theo validation trung bình:', item8['selected_lookback'])
print('Bằng chứng:', item8_path)'''),
        code('''fig, axes = plt.subplots(3, 3, figsize=(13, 10), layout='constrained')
for ax, row in zip(axes.flat, item8['results']):
    history = pd.read_csv(Path(row['run_dir']) / 'epoch_logs.csv')
    ax.plot(history.epoch, history.train_loss, label='Train', linewidth=1)
    ax.plot(history.epoch, history.val_loss, label='Validation', linewidth=1)
    ax.axvline(row['best_epoch'], linestyle=':', color='black', linewidth=1)
    ax.set(title=f"Lookback {row['lookback']} · seed {row['seed']}",
           xlabel='Epoch', ylabel='MSE chuẩn hóa', yscale='log')
    ax.legend(fontsize=8)
fig.savefig(item8_path.parent / 'learning_curves.png', dpi=150)
plt.show()'''),
        md('''<a id="tv4-item-9"></a>

        ## 9. Huấn luyện chính thức LSTM năm bước

        **Các vấn đề audit đã được xử lý ngày 26/11/2026.** Trainer yêu cầu callback lưu hợp lệ ngay từ đầu, tài liệu đã đồng bộ và có manifest đường dẫn tương đối. Hồi quy strict đạt 69/69, kiểm 323 file và nạp lại 12 model trên bản sao ở thư mục khác đạt. Xem [báo cáo sửa lỗi](../reports/audits/TV4_Audit_Fixes_20261126.md).

        Lookback 30, ba seed 42/123/456, 1.980 mẫu train và 246 mẫu validation. Mỗi mẫu có đủ năm target thuộc cùng tập. Mô hình xuất đồng thời năm giá, được chọn bằng MSE tổng trên năm bước có trọng số bằng nhau. Cấu hình tối đa 100 epoch, patience 10. Các bảng dưới đọc kết quả chính thức đã lưu.'''),
        code(setup_path + '''
import json
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display, Markdown
item9_path = ROOT / 'logs/audit/tv4_item9_20261125T140320407544Z/summary.json'
item9 = json.loads(item9_path.read_text(encoding='utf-8'))
assert item9['passed'] and item9['status'] == 'completed'
results9 = pd.DataFrame(item9['results'])
assert len(results9) == 3 and results9.reload_verified.all()
display(results9[['seed','epochs','best_epoch','validation_mse','seconds','reload_verified']])
display(pd.DataFrame(item9['aggregates']))
horizons9 = pd.DataFrame([row['validation_mse_per_horizon'] for row in item9['results']],
                        index=results9.seed, columns=[f'Bước {i}' for i in range(1,6)])
display(horizons9)
print('Bằng chứng:', item9_path)'''),
        code('''fig, axes = plt.subplots(1, 3, figsize=(13, 3.8), layout='constrained')
for ax, row in zip(axes, item9['results']):
    history = pd.read_csv(Path(row['run_dir']) / 'epoch_logs.csv')
    ax.plot(history.epoch, history.train_loss, label='Train')
    ax.plot(history.epoch, history.val_loss, label='Validation')
    ax.axvline(row['best_epoch'], color='black', linestyle=':', linewidth=1)
    ax.set(title=f"Seed {row['seed']}", xlabel='Epoch', ylabel='MSE tổng chuẩn hóa', yscale='log')
    ax.legend()
fig.savefig(item9_path.parent / 'learning_curves.png', dpi=150)
plt.show()
ax = horizons9.T.plot(marker='o', figsize=(8, 3.8))
ax.set(xlabel='Bước dự báo', ylabel='Validation MSE chuẩn hóa',
       title='Sai số từng bước tại checkpoint tốt nhất của mỗi seed')
plt.tight_layout()
ax.figure.savefig(item9_path.parent / 'horizon_errors.png', dpi=150)
plt.show()'''),
        md('''<a id="tv4-item-10"></a>

        ## 10. Audit cuối và bộ bàn giao

        Bộ source/artifacts được kiểm trên bản sao khác thư mục, cùng máy, bằng môi trường TV4 sạch theo lock. Verifier kiểm checksum và nạp lại 12 model. Bộ được chọn có sáu checkpoint lookback 30, giữ đủ ba seed cho mỗi horizon.

        Tổng 12 run và 1.075 epoch. Đầu ra gồm training loop, cấu hình/seed, dữ liệu có provenance, checkpoint, logs, notebook/biểu đồ, TensorBoard và ZIP có checksum. TV5 nhận pipeline training để làm CNN. TV6 nhận model/scaler và cấu hình để đánh giá test, MAE/RMSE USD, baseline và tích hợp. Xem [hướng dẫn bàn giao](../docs/TV4_Handoff_TV5_TV6.md).'''),
        code(setup_path + '''
import json
import pandas as pd
from IPython.display import display, Markdown
receipt10 = json.loads((ROOT / 'logs/audit/tv4_item10_latest.json').read_text(encoding='utf-8'))
assert receipt10['passed']
display(pd.DataFrame([receipt10]))
print('Kết quả là nghiệm thu local trên bản sao độc lập.')
print('Xác nhận máy người nhận:', receipt10['recipient_machine_verified'])'''),
        code('''display(pd.DataFrame([{'item':i,'work':w,'status':'Đạt local'} for i,w in enumerate(['Tiếp nhận/layout/môi trường','CPU float64 contract','TV2 data/factory/config','Training/validation acceptance','Checkpoint/reload thật','Smoke AAPL/đo CPU','Thiết kế thực nghiệm','LSTM một bước chính thức','LSTM năm bước chính thức','Tái lập/bàn giao local'],1)]))
display(Markdown('**TV4 đã có bộ bàn giao local. Tiếp theo theo flow là hoàn thiện TV5 và đánh giá/tích hợp TV6.**'))'''),
    ]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--member',choices=['2','3','4','all'],default='all')
    parser.add_argument('--overwrite',action='store_true',help='Regenerate notebooks, clearing old outputs; execute afterward.')
    args=parser.parse_args()
    for name,cells in [('02_TV2_Preprocessing_and_Audit.ipynb',tv2()),('03_TV3_LSTM_Development_and_Tests.ipynb',tv3()),('04_TV4_Training_and_Experiments.ipynb',tv4())]:
        if args.member != 'all' and not name.startswith('0'+args.member+'_'): continue
        path=ROOT/'notebooks'/name
        if path.exists() and not args.overwrite: raise FileExistsError(f'{path}: use --overwrite only for intended regeneration')
        kernel='aapl-coursework-tv4' if name.startswith('04_') else KERNEL
        display_name='AAPL Coursework TV4' if name.startswith('04_') else 'AAPL Coursework TV2-TV3'
        nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':kernel,'display_name':display_name,'language':'python'},'language_info':{'name':'python'}})
        nbf.write(nb,path)
        print(path)


if __name__=='__main__': main()
