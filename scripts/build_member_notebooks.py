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


def tv5():
    return [
        md('''# TV5 — CNN một bước và thực nghiệm so sánh

        ## 1. Tiếp nhận source và kiểm thử baseline

        Nhận model, exports và bảy tests từ PR #9, commit edc2bd953c7644040f4142a545316377cd143e13. Mục này xác minh source trong workspace, unit tests và hình dạng đầu ra. Dữ liệu dùng trong cell kiểm model là tensor tổng hợp.

        Mục 1 đã nhận nguyên source float32 và baseline 7 tests, xem receipt lịch sử. Từ mục 2, CNN dùng CPU float64, một feature và một output. Số tham số vẫn là 17.057.

        **Quyết định phương án A ngày 26/11/2026.** Giữ một cấu hình CNN hiện có để so với LSTM, ba seed 42/123/456, tối đa 100 epoch/run, patience 10, trần 300 epoch.

        ## 2. Kiến trúc và contract

        Chọn float64 để giữ cùng precision với LSTM theo yêu cầu hoàn thành mục 2, không đổi torch global dtype. Model nhận tensor hữu hạn trên CPU (B,30,1) và trả (B,1). Khóa một feature, một output; kiểm config sai kiểu/số không hợp lệ và finite input/output. Giữ Conv 1→16→32, kernel3, pool2, dropout0,1, Linear480→32→1. Dữ liệu thật, Adam/reload và thực nghiệm AAPL sẽ kiểm theo các mục sau.'''),
        code('''from pathlib import Path
import sys, os, json, hashlib, subprocess
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
import pandas as pd
import torch
from IPython.display import display, Markdown
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents]
            if (p / 'rule.md').is_file() and (p / 'backend/models/cnn_one_step/model.py').is_file())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from backend.models.cnn_one_step import CNNOneStep
pointer = json.loads((ROOT / 'logs/audit/tv5_item1_latest.json').read_text(encoding='utf-8'))
intake = json.loads((ROOT / pointer['intake']).read_text(encoding='utf-8'))
display(pd.DataFrame(intake['files']))
print('Commit', intake['commit'])
baseline = json.loads((ROOT / pointer['tests']).read_text(encoding='utf-8'))
print('Baseline mục 1 đã lưu', baseline['tests'], 'tests, dtype', baseline['dtype'])
print('Python', sys.executable)
print('PyTorch', torch.__version__)
assert sys.prefix != sys.base_prefix
assert Path(torch.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())'''),
        code('''folder = ROOT / 'logs/audit' / ('tv5_tests_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
folder.mkdir(parents=True)
env = dict(os.environ, OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', PYTHONIOENCODING='utf-8')
env.pop('PYTHONPATH', None)
command = [sys.executable, '-X', 'utf8', '-m', 'pytest', 'tests/models/test_cnn_one_step.py', 'tests/models/test_cnn_contract.py',
           '-q', '-p', 'no:cacheprovider', '--junitxml=' + str(folder / 'junit.xml')]
run = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, encoding='utf-8')
(folder / 'pytest.log').write_text(run.stdout + run.stderr, encoding='utf-8')
print(run.stdout)
if run.returncode:
    raise RuntimeError(run.stderr or run.stdout)
cases = list(ET.parse(folder / 'junit.xml').getroot().iter('testcase'))
assert len(cases) == 26
assert all(c.find('failure') is None and c.find('error') is None and c.find('skipped') is None for c in cases)
display(pd.DataFrame([{'test': c.get('name'), 'seconds': c.get('time'), 'result': 'PASS'} for c in cases]))'''),
        code('''with torch.random.fork_rng(devices=[]):
    torch.manual_seed(42)
    model = CNNOneStep().eval()
    x = torch.zeros(2, 30, 1, dtype=torch.float64)
    with torch.inference_mode():
        prediction = model(x)
assert prediction.shape == (2, 1) and torch.isfinite(prediction).all()
assert Path(sys.modules[CNNOneStep.__module__].__file__).resolve().is_relative_to(ROOT / 'backend')
print(model)
display(pd.DataFrame([{'input_shape': tuple(x.shape), 'output_shape': tuple(prediction.shape),
                       'dtype': str(prediction.dtype), 'parameters': model.count_parameters(),
                       'data': 'Tensor tổng hợp'}]))'''),
        code('''changed = [name for name, expected in intake['protected_hashes'].items()
           if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected]
allowed5_path = ROOT / 'reports/audits/TV5_Item5_Source_Changes.json'
allowed5 = json.loads(allowed5_path.read_text(encoding='utf-8')) if allowed5_path.is_file() else {}
allowed6_path = ROOT / 'reports/audits/TV5_Item6_Source_Changes.json'
if allowed6_path.is_file():
    allowed5.update(json.loads(allowed6_path.read_text(encoding='utf-8')))
unexpected = [name for name in changed if allowed5.get(name) != hashlib.sha256((ROOT / name).read_bytes()).hexdigest()]
assert not unexpected, unexpected
intentional = [row['path'] for row in intake['files']
               if hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest() != row['sha256']]
assert set(intentional) == {'backend/models/cnn_one_step/model.py', 'tests/models/test_cnn_one_step.py'}
receipt = dict(passed=True, tests=len(cases), commit=intake['commit'], scope='TV5 item2 contract', source_unchanged=False, intentional_source_changes=intentional,
               protected_changes=changed, executable=sys.executable, torch=torch.__version__,
               parameters=model.count_parameters(), dtype=str(prediction.dtype))
(folder / 'summary.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
pointer['item2_tests'] = (folder / 'summary.json').relative_to(ROOT).as_posix()
(ROOT / 'logs/audit/tv5_item1_latest.json').write_text(json.dumps(pointer, indent=2), encoding='utf-8')
display(pd.DataFrame([receipt]))
print('Bằng chứng', folder / 'summary.json')
display(Markdown('**Mục 2 đã kiểm chứng contract và CPU float64. Tiếp theo là mục 3, nối dữ liệu TV2 cho CNN.**'))'''),
        md('''## 3. Dữ liệu TV2 cho CNN

        Consumer CNN dùng lại factory dữ liệu đã kiểm của TV4 và cấu hình lookback30/common60 đã train. Cùng 1.954 mẫu train, 250 validation, scaler và ngày target. Kiểm ID theo thứ tự, đối chiếu từng X/y với prepared artifact và forward toàn bộ batch bằng CNN khởi tạo. Transpose (B,30,1) thành (B,1,30) diễn ra bên trong model.

        Lượt kiểm này chỉ xác minh dữ liệu/forward. Model dùng trọng số khởi tạo, không tính metric chất lượng dự báo.'''),
        code('''data_check = subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'scripts/check_tv5_aapl_data.py')],
                            cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
if data_check.returncode:
    raise RuntimeError(data_check.stderr or data_check.stdout)
path3 = Path(json.loads(data_check.stdout)['evidence'])
item3 = json.loads(path3.read_text(encoding='utf-8'))
assert item3['passed'] and not item3['trained']
display(pd.DataFrame([{key:value for key,value in row.items() if key != 'example'} for row in item3['results']]))
display(pd.DataFrame([dict(split=row['split'], **row['example']) for row in item3['results']]))
display(item3['provenance'])
print('Bằng chứng', path3)
display(Markdown('**Mục 3 kiểm dữ liệu và forward đã đạt. Tiếp theo là mục 4, nghiệm thu sâu model/gradient/dropout/lưu-nạp.**'))'''),
        md('''## 4. Nghiệm thu khả năng học và lưu/nạp CNN

        Kiểm tổng hợp với batch 1 và 32, gradient hữu hạn và khác 0 ở từng tensor tham số, Adam cập nhật trọng số, zero_grad xóa gradient. Kiểm dropout train/eval và output eval ổn định. Sau một Adam step tổng hợp, lưu config/state_dict ra file thật và nạp vào instance mới, yêu cầu output eval bằng chính xác. Từ chối state_dict thiếu key.

        Đây là diagnostic bằng tensors tổng hợp, chưa train AAPL hoặc đánh giá chất lượng. Checkpoint có provenance và tích hợp trainer tiếp tục ở mục 5/6.'''),
        code('''import xml.etree.ElementTree as ET
folder4 = ROOT / 'logs/audit' / ('tv5_item4_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
folder4.mkdir(parents=True)
xml4 = folder4 / 'tests.xml'
command4 = [sys.executable, '-m', 'pytest', 'tests/models/test_cnn_one_step.py',
            'tests/models/test_cnn_contract.py', 'tests/models/test_cnn_learning.py',
            'tests/training', '-q', '-p', 'no:cacheprovider', '--junitxml=' + str(xml4)]
run4 = subprocess.run(command4, cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
(folder4 / 'pytest.txt').write_text(run4.stdout + run4.stderr, encoding='utf-8')
if run4.returncode:
    raise RuntimeError(run4.stdout + run4.stderr)
cases4 = list(ET.parse(xml4).getroot().iter('testcase'))
assert cases4 and all(not any(c.tag in ('failure','error','skipped') for c in case) for case in cases4)
rows4 = [{'test':case.attrib['name'], 'seconds':float(case.attrib['time'])} for case in cases4]
receipt4 = {'passed':True, 'tests':len(cases4), 'scope':'synthetic CNN diagnostics and training regression',
            'aapl_training':False, 'command':command4, 'python':sys.version, 'torch':torch.__version__}
(folder4 / 'summary.json').write_text(json.dumps(receipt4, indent=2), encoding='utf-8')
display(pd.DataFrame([receipt4]))
display(pd.DataFrame([r for r in rows4 if any(k in r['test'] for k in ('adam','dropout','roundtrip'))]))
print('Bằng chứng', folder4 / 'summary.json')
display(Markdown('**Mục 4 đạt kiểm chứng local. Tiếp theo mục 5, nối CNN vào training loop chung TV4.**'))'''),
        md('''## 5. Nối CNN vào training loop chung TV4

        YAML CNN dùng schema kiến trúc CNN và cùng data/scaler/common-history với LSTM đối ứng. Runner chọn factory CNN, còn train_model/_run_epoch vẫn là code TV4. Adam/MSE và early stopping dùng chung; không tạo vòng train riêng.

        Kiểm tổng hợp chạy CNN qua runner một epoch, validation không gradient và không đổi weights, weighted loss giữ batch cuối 1 mẫu, plateau có kiểm soát dừng sau patience và khôi phục best weights. Plateau là tín hiệu kiểm thử, không phải kết quả CNN trên AAPL. Kiểm nối loader thật ở dưới chỉ đọc dữ liệu. Chưa train AAPL hoặc lưu checkpoint CNN có provenance, các mục 6/7 tiếp tục phần đó.'''),
        code('''from backend.experiments.runner.experiment_runner import load_experiment_config
from backend.experiments.runner.cnn_factories import make_cnn_model, make_cnn_loaders
config5 = load_experiment_config(str(ROOT / 'experiments/configs/cnn_one_step_baseline.yaml'))
assert config5['seeds'] == [42,123,456]
train5, val5 = make_cnn_loaders(config5, 42, project_root=ROOT)
assert len(train5.dataset) == 1954 and len(val5.dataset) == 250
assert make_cnn_model(config5).count_parameters() == 17057
runner_cases5 = [case for case in cases4 if 'test_cnn_runner' in case.attrib.get('classname','')]
assert len(runner_cases5) == 9
display(pd.DataFrame([{'test':c.attrib['name'], 'result':'PASS'} for c in runner_cases5]))
display(pd.DataFrame([{'split':name, 'samples':len(dl.dataset), 'batches':len(dl),
    'tail':len(dl.dataset) % dl.batch_size, 'drop_last':dl.drop_last}
    for name,dl in [('train',train5),('validation',val5)]]))
display(config5)
receipt5 = dict(passed=True, integration_tests=len(runner_cases5), regression_tests=len(cases4),
    aapl_training=False, checkpoint_mode='RAM only pending item6', tests_evidence=str(folder4 / 'summary.json'))
folder5 = ROOT / 'logs/audit' / ('tv5_item5_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
folder5.mkdir(parents=True)
(folder5 / 'summary.json').write_text(json.dumps(receipt5,indent=2),encoding='utf-8')
print('Bằng chứng',folder5 / 'summary.json')
display(Markdown('**Mục 5 đã nối loop chung và kiểm chứng local. Tiếp theo mục 6, checkpoint CNN và provenance.**'))'''),
        md('''## Audit lại mục 1–5

        Audit source/config, hash bảo vệ, notebook, bộ tests đầy đủ và forward AAPL. Không train AAPL hoặc đánh giá test. Validator cấu hình chung chưa khóa ngân sách/kiến trúc phương án A; cần khóa và ghi fingerprint trước thực nghiệm chính thức. Script đối chiếu dữ liệu còn cần log TV4 local, cần đóng gói bằng chứng khi bàn giao mục 10. Xem reports/audits/TV5_Items1_5_Audit.md.'''),
        code('''from pathlib import Path
import json
import pandas as pd
from IPython.display import display
audit_root = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'rule.md').is_file())
audit_path = sorted((audit_root / 'logs/audit').glob('tv5_audit_1_5_*/summary.json'))[-1]
audit_result = json.loads(audit_path.read_text(encoding='utf-8'))
assert audit_result['passed'] and audit_result['tests'] == 111
display(pd.DataFrame([{key:audit_result[key] for key in ('passed','tests','aapl_training',
    'test_performance_evaluated','source_unchanged_during_audit','config_matches_lstm_data')}]))
display(pd.DataFrame(audit_result['generic_config_probes']))
display(pd.DataFrame(audit_result['data_results']).drop(columns=['example']))
print('Giới hạn audit', audit_result['limitations'])
print('Bằng chứng', audit_path)'''),
        md('''## 6. Checkpoint CNN và provenance

        Lưu weights.pt cùng manifest chứa kiến trúc, CPU float64, dataset/scaler/prepared IDs và hashes, run/seed, training config/fingerprint, source hashes, best validation epoch/loss và purpose. Bản diagnostic bị từ chối mặc định, kể cả đã chạy train tổng hợp. Loader yêu cầu expected provenance/config fingerprint, kiểm checksum và strict state_dict.

        Tests dùng identities và tensors tổng hợp, gồm runner hai epoch lưu best rồi nạp instance mới để đối chiếu MSE. Chưa train AAPL. Artifact này phục vụ nạp best model/inference, chưa chứa Adam state để resume training. Metadata là thông tin caller cung cấp, không tự chứng minh lịch sử train.'''),
        code('''checkpoint_cases6 = [case for case in cases4 if 'test_cnn_checkpoint' in case.attrib.get('classname','')]
assert checkpoint_cases6
display(pd.DataFrame([{'test':c.attrib['name'],'result':'PASS'} for c in checkpoint_cases6]))
folder6 = ROOT / 'logs/audit' / ('tv5_item6_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
folder6.mkdir(parents=True)
receipt6 = dict(passed=True,checkpoint_tests=len(checkpoint_cases6),regression_tests=len(cases4),
    tests_evidence=str(folder4 / 'summary.json'),aapl_training=False,
    checkpoint_scope='Synthetic persistence/runner diagnostics, not AAPL trained model',
    supports_optimizer_resume=False)
(folder6 / 'summary.json').write_text(json.dumps(receipt6,indent=2),encoding='utf-8')
display(pd.DataFrame([receipt6]))
print('Bằng chứng',folder6 / 'summary.json')
display(Markdown('**Mục 6 kiểm chứng persistence local. Tiếp theo mục 7, smoke train/validation AAPL có giới hạn và purpose diagnostic.**'))'''),
        md('''## Sơ đồ tổng hợp các đường xử lý mục 1–6

        Bốn sơ đồ dưới đây diễn giải source đang triển khai, không phải kết quả train hoặc metric dự báo. Xem lần lượt luồng dữ liệu, các shape bên trong CNN, train/validation/chọn best và checkpoint save/load.

        Loss epoch được tính theo số mẫu, giữ batch cuối. Patience tăng khi validation không cải thiện và được reset khi có best mới. Checkpoint chỉ nạp khi các kiểm tra đều đạt; diagnostic bị từ chối mặc định. Expected identity/config phải đến từ handoff tin cậy. Hash phát hiện hỏng dữ liệu, không xác thực người gửi.'''),
        code('''from pathlib import Path
import sys
from datetime import datetime, timezone
from IPython.display import display
import matplotlib.pyplot as plt
diagram_root = next(p for p in [Path.cwd(),*Path.cwd().parents] if (p / 'rule.md').is_file())
if str(diagram_root / 'scripts') not in sys.path:
    sys.path.insert(0,str(diagram_root / 'scripts'))
from tv5_notebook_diagrams import render_tv5_diagrams
diagram_folder = diagram_root / 'logs/audit' / ('tv5_diagrams_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
diagrams = render_tv5_diagrams(diagram_folder)
for figure, path in diagrams:
    display(figure)
    plt.close(figure)
    print('Ảnh đã lưu',path)
assert len(diagrams) == 4 and all(path.is_file() for _,path in diagrams)'''),
        md('''## 7. Smoke run CNN trên AAPL — 5 epoch, seed 42

        Dùng đủ 1.954 mẫu train và 250 validation với cùng dữ liệu/scaler/LSTM đối ứng. Giữ Adam 0,001, MSE, batch32, float64 và một CPU thread. Run diagnostic giới hạn 5 epoch, không đánh giá test hoặc chọn lại kiến trúc/ngân sách từ kết quả smoke. Patience10 chưa thể kích hoạt trong giới hạn 5 epoch, logic này đã kiểm tổng hợp ở mục 5.

        CLI tái lập `python scripts/run_tv5_smoke.py` tạo run mới. Cell dưới đọc run smoke mới nhất, hiển thị kết quả thật và biểu đồ. Reload best checkpoint vào instance mới phải khớp output và validation MSE. Biểu đồ giá chuẩn hóa chỉ kiểm hành vi forward, không chứng minh chất lượng dự báo hoặc vượt baseline.'''),
        code('''from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display
smoke_root = next(p for p in [Path.cwd(),*Path.cwd().parents] if (p / 'rule.md').is_file())
smoke_path = sorted((smoke_root / 'logs/audit').glob('tv5_item7_*/summary.json'))[-1]
smoke = json.loads(smoke_path.read_text(encoding='utf-8'))
assert smoke['passed'] and smoke['purpose'] == 'diagnostic' and smoke['aapl_training']
assert not smoke['test_performance_evaluated'] and smoke['reload_predictions_exact']
history7 = pd.read_csv(smoke_path.parent / 'history.csv')
predictions7 = pd.read_csv(smoke_path.parent / 'validation_scaled.csv')
display(history7)
display(pd.DataFrame([{key:smoke[key] for key in ('epochs','seed','best_epoch','best_val_loss',
    'reload_val_loss','parameters','dtype','device','weights_changed','finite_weights')}]))
display(pd.DataFrame([smoke['gradient_stats']]))
display(pd.DataFrame([smoke['timing']]))
fig,axes = plt.subplots(2,2,figsize=(15,9))
axes[0,0].plot(history7.epoch,history7.train_loss,'o-',label='Train MSE')
axes[0,0].plot(history7.epoch,history7.val_loss,'o-',label='Validation MSE')
axes[0,0].axvline(smoke['best_epoch'],linestyle='--',color='gray',label='Best epoch')
axes[0,0].set(title='Smoke · loss trên giá chuẩn hóa',xlabel='Epoch',ylabel='MSE',yscale='log')
axes[0,0].legend()
axes[0,1].bar(history7.epoch,history7.train_seconds,label='Train')
axes[0,1].bar(history7.epoch,history7.validation_seconds,bottom=history7.train_seconds,label='Validation')
axes[0,1].set(title='Thời gian mỗi epoch · CPU',xlabel='Epoch',ylabel='Giây')
axes[0,1].legend()
axes[1,0].plot(predictions7.target_scaled,label='Target validation',linewidth=1.5)
axes[1,0].plot(predictions7.prediction_scaled,label='Best smoke CNN',linewidth=1.5)
axes[1,0].set(title='Kiểm hành vi · chưa là so sánh chất lượng',xlabel='Mẫu validation theo thời gian',ylabel='Giá chuẩn hóa')
axes[1,0].legend()
axes[1,1].plot(predictions7.reload_abs_diff)
axes[1,1].set(title='Sai khác prediction trước/sau reload',xlabel='Mẫu validation',ylabel='Sai khác tuyệt đối')
for ax in axes.flat: ax.grid(alpha=.25)
fig.suptitle('TV5 mục 7 · AAPL diagnostic · 5 epoch · seed 42',fontsize=16)
fig.tight_layout()
fig.savefig(smoke_path.parent / 'smoke_overview.png',dpi=150)
display(fig)
plt.close(fig)
print('Checkpoint diagnostic',smoke['checkpoint_path'])
print('Loader mặc định đã từ chối',smoke['default_diagnostic_rejection'])
print('Bằng chứng',smoke_path)'''),
        md('''## 8. Thực nghiệm CNN chính thức — phương án A

        Khóa semantic config gồm model/data/training/seeds/runtime trước chạy, fingerprint ở experiments/configs/cnn_one_step_option_a.lock.json. Ba seed 42/123/456, max100/patience10, cùng data/scaler/lookback30/common-history và CPU float64. Output directory được tạo mới cho mỗi lượt. Không thay kiến trúc/learning rate sau smoke, không đánh giá hiệu năng test hoặc chọn seed thắng.

        Mỗi seed giữ checkpoint có validation MSE thấp nhất. Nạp lại bằng expected provenance/config/run/seed, so toàn bộ prediction với best model RAM và tính lại validation MSE. Báo đủ ba seed, mean và std mẫu ddof=1. CLI tái lập `python scripts/run_tv5_official.py`, cell dưới đọc receipt mới nhất.'''),
        code('''from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display
official_root = next(p for p in [Path.cwd(),*Path.cwd().parents] if (p / 'rule.md').is_file())
official_path = sorted((official_root / 'logs/audit').glob('tv5_item8_*/summary.json'))[-1]
official = json.loads(official_path.read_text(encoding='utf-8'))
assert official['passed'] and not official['test_performance_evaluated']
assert official['seeds'] == [42,123,456] and official['total_epochs'] <= 300
table8 = pd.DataFrame(official['results'])
display(table8.drop(columns=['run_id','checkpoint_path']))
display(pd.DataFrame([{k:official[k] for k in ('validation_mse_mean','validation_mse_std',
    'std_ddof','total_epochs','epoch_cap','parameters','dtype','device','torch_threads')}]))
display(pd.DataFrame([official['timing']]))
fig,axes = plt.subplots(2,2,figsize=(15,10))
for row in official['results']:
    history8 = pd.read_csv(official_path.parent / ('history_seed' + str(row['seed']) + '.csv'))
    axes[0,0].plot(history8.epoch,history8.train_loss,label='Seed '+str(row['seed']))
    axes[0,1].plot(history8.epoch,history8.val_loss,label='Seed '+str(row['seed']))
    axes[0,1].scatter([row['best_epoch']],[row['best_val_loss']],s=50)
axes[0,0].set(title='Train MSE · giá chuẩn hóa',xlabel='Epoch',ylabel='MSE',yscale='log')
axes[0,1].set(title='Validation MSE · điểm đánh dấu best epoch',xlabel='Epoch',ylabel='MSE',yscale='log')
axes[0,0].legend(); axes[0,1].legend()
axes[1,0].bar(table8.seed.astype(str),table8.best_val_loss)
axes[1,0].axhline(official['validation_mse_mean'],linestyle='--',color='black',label='Mean 3 seed')
axes[1,0].set(title='Best validation MSE từng seed',xlabel='Seed',ylabel='MSE')
axes[1,0].legend()
axes[1,1].bar(table8.seed.astype(str),table8.training_seconds)
axes[1,1].set(title='Thời gian training loop · local CPU',xlabel='Seed',ylabel='Giây')
for ax in axes.flat: ax.grid(alpha=.25)
fig.suptitle('TV5 mục 8 · CNN chính thức · chưa đánh giá test',fontsize=16)
fig.tight_layout()
fig.savefig(official_path.parent / 'official_overview.png',dpi=150)
display(fig); plt.close(fig)
print('Semantic fingerprint',official['semantic_sha256'])
print('Cả ba best checkpoint đã reload khớp',table8.reload_predictions_exact.all())
print('Bằng chứng',official_path)'''),
        md('''## 9. So sánh CNN / LSTM / persistence trên validation — USD

        Cùng 250 sample ID/ngày target năm 2023, cùng input30/scaler/dataset. Giữ ba seed42/123/456 của mỗi mạng, không chọn seed thắng. Dùng best validation checkpoint đã có, inverse bằng scaler train đã lưu và persistence lấy giá USD cuối input. MAE/RMSE dùng module evaluation chung, không làm tròn trước tính metric.

        Đây là so sánh validation đã dùng chọn checkpoint, chưa phải kết luận trên test2024–2025; đánh giá test cuối thuộc flow TV6. LSTM đã chọn lookback từ10/30/60, CNN chỉ một cấu hình, ngân sách tìm kiếm khác nhau. Thời gian train lịch sử chỉ mô tả; timing inference đo local cùng một thread/20 lượt, chưa phải benchmark kernel thuần. Lệnh tái lập `python scripts/compare_tv5_validation.py`.'''),
        code('''from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display
compare_root=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'rule.md').is_file())
compare_path=sorted((compare_root/'logs/audit').glob('tv5_item9_*/summary.json'))[-1]
comparison=json.loads(compare_path.read_text(encoding='utf-8'))
assert comparison['passed'] and comparison['samples']==250 and not comparison['test_performance_evaluated']
metrics9=pd.read_csv(compare_path.parent/'metrics.csv')
predictions9=pd.read_csv(compare_path.parent/'predictions_usd.csv')
aggregates9=pd.DataFrame(comparison['aggregates'])
display(metrics9)
display(aggregates9)
base9=metrics9[metrics9.method=='persistence'].iloc[0]
fig,axes=plt.subplots(2,2,figsize=(15,10))
for ax,metric in zip(axes[0],['mae','rmse']):
    names=['persistence']+aggregates9.method.tolist()
    means=[base9[metric+'_usd']]+aggregates9[metric+'_usd_mean'].tolist()
    stds=[0]+aggregates9[metric+'_usd_std'].tolist()
    ax.bar(names,means,yerr=stds,capsize=5)
    ax.set(title=metric.upper()+' USD · mean ± std ba seed',ylabel='USD')
chosen9=predictions9[(predictions9.seed==42)|(predictions9.method=='persistence')]
for method,part in chosen9.groupby('method',sort=False):
    axes[1,0].plot(pd.to_datetime(part.target_date),part.predicted_usd,label=method,alpha=.8)
actual9=chosen9[chosen9.method=='persistence']
axes[1,0].plot(pd.to_datetime(actual9.target_date),actual9.actual_usd,label='Actual',color='black',linewidth=1)
axes[1,0].set(title='Minh họa seed42 · không chọn seed từ kết quả',ylabel='Adjusted close USD')
axes[1,0].legend(); axes[1,0].tick_params(axis='x',rotation=25)
timing9=metrics9.groupby('method').inference_median_seconds.mean()
axes[1,1].bar(timing9.index,timing9.values*1000)
axes[1,1].set(title='Inference local · trung bình median của từng seed',ylabel='ms / 250 mẫu',yscale='log')
for ax in axes.flat: ax.grid(alpha=.25)
fig.suptitle('TV5 mục9 · chỉ validation2023 · chưa đánh giá test',fontsize=16)
fig.tight_layout();fig.savefig(compare_path.parent/'comparison_overview.png',dpi=150)
display(fig);plt.close(fig)
print('Giới hạn',comparison['limitations'])
print('Cùng tập mẫu',comparison['ordered_keys_sha256'])
print('Bằng chứng',compare_path)'''),
        md('''## Bổ sung monitoring chất lượng sau train

        Phân tích lại predictions validation2023 đã đóng băng, không train lại hoặc tuning. Signed error = predicted − actual, dương là dự báo cao. Theo dõi cả ba seed của mỗi mạng và persistence riêng. MAE trượt20 phiên dùng đúng20 mẫu kết thúc tại ngày đang xét; 19 phiên đầu không đủ cửa sổ nên để trống. MAE theo tháng trung bình metric mỗi seed, không tạo ensemble.

        P95/max absolute error và tỷ trọng squared error của5 phiên lớn nhất mô tả tail errors; không coi các seed là mẫu độc lập hoặc suy nguyên nhân chỉ từ biểu đồ. Peak RAM lịch sử chưa đo, không thể tái dựng từ loss log. Chưa có monitoring production/drift hoặc live TensorBoard CNN. CLI tái lập `python scripts/build_tv5_monitoring.py`.'''),
        code('''from pathlib import Path
import json
import pandas as pd
from IPython.display import display, Image
monitor_root=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'rule.md').is_file())
monitor_path=sorted((monitor_root/'logs/audit').glob('tv5_monitoring_*/summary.json'))[-1]
monitor=json.loads(monitor_path.read_text(encoding='utf-8'))
assert monitor['passed'] and not monitor['trained_again'] and not monitor['test_performance_evaluated']
monitor_stats=pd.read_csv(monitor_path.parent/'summary.csv')
monitor_top=pd.read_csv(monitor_path.parent/'largest.csv')
display(monitor_stats)
display(monitor_top.groupby(['method','seed'],dropna=False,sort=False).head(2))
display(pd.DataFrame([{'telemetry':k,'status':v} for k,v in monitor['resource_inventory'].items()]))
for name in ['01_errors_by_date.png','02_rolling_mae.png','03_error_distributions.png','04_monthly_mae.png']:
    display(Image(filename=str(monitor_path.parent/name)))
print('Top10 từng run và bảng tháng/rolling đầy đủ',monitor_path.parent)
print('Giới hạn',monitor['limitations'])
print('Bằng chứng',monitor_path)'''),
        md('''## 10. Audit cuối, tái lập và bàn giao TV5

        Đủ source/config/tests/notebook và artifacts local cho CNN một bước. Gói gồm ba best CNN research, ba LSTM đối ứng, best smoke diagnostic và dependencies TV1/TV2/log TV4. Payload hash từng file, ZIP checksum riêng. Tái lập dùng source tách riêng và venv sạch đã có, chạy tests rồi forward/reload/metrics/monitoring; không train lại AAPL.

        Hướng dẫn docs/TV5_Setup_and_Handoff.md, audit reports/audits/TV5_Final_Handoff.md. Đây là nghiệm thu local, không chứng nhận máy người nhận/fresh install/test2024–2025/API. Peak RAM lịch sử và monitoring production chưa có. Dữ liệu/weights/ZIP không đưa vào Git hoặc tự upload. Kết quả validation vẫn persistence tốt hơn LSTM/CNN; không ép model thắng baseline.'''),
        code('''from pathlib import Path
import json
import pandas as pd
from IPython.display import display
handoff_root=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'rule.md').is_file())
precheck_path=handoff_root/'logs/audit/tv5_item10_precheck.json'
precheck=json.loads(precheck_path.read_text(encoding='utf-8'))
assert precheck['passed'] and precheck['tests']==162 and precheck['relocated_metrics_match']
assert not precheck['recipient_machine_verified'] and not precheck['test_performance_evaluated']
display(pd.DataFrame([precheck]))
display(pd.DataFrame([{'item':i,'status':'Hoàn thành phạm vi local'} for i in range(1,11)]))
print('Bằng chứng kiểm source tách riêng',precheck_path)
pointer_path=handoff_root/'logs/audit/tv5_item10_latest.json'
if pointer_path.is_file():
    print('Gói/receipt ZIP mới nhất',json.loads(pointer_path.read_text(encoding='utf-8')))
else:
    print('Pointer ZIP và checksum được ghi sau bước đóng gói cuối; xem audit/setup.')'''),
    ]


def _tv6_before_item5():
    return [
        md('''# TV6 — tích hợp, đánh giá cuối và demo

        **Trạng thái hiện tại: mục1–4 đã hoàn thành local, gồm nghiệm thu đầu vào, khóa protocol, inference và evaluation validation; chưa đánh giá hiệu năng test.**

        ## 1. Nghiệm thu đầu vào TV1–TV5

        Đối chiếu snapshot/hash TV1, scaler/prepared TV2, model contract TV3 và best validation checkpoints TV4/TV5. Danh mục gồm ba LSTM một bước lookback30, ba LSTM năm bước và ba CNN một bước theo seed42/123/456. Không lấy checkpoint mới nhất trên đĩa hoặc chọn seed theo test.

        CLI `python scripts/audit_tv6_inputs.py` chạy lại kiểm dữ liệu/provenance/history/hash và forward hai input validation cho mỗi model. Chỉ kiểm schema/coverage test, không dự đoán hoặc tính metric test. Mục2 sẽ khóa protocol đánh giá cuối; chưa chọn release/demo seed hoặc làm frontend.'''),
        code('''from pathlib import Path
import sys,json,hashlib
import pandas as pd
from IPython.display import display,Markdown
ROOT=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'rule.md').is_file())
pointer=json.loads((ROOT/'logs/audit/tv6_item1_latest.json').read_text(encoding='utf-8'))
inventory=json.loads((ROOT/pointer['evidence']).read_text(encoding='utf-8'))
assert inventory['passed'] and len(inventory['models'])==9
assert not inventory['test_performance_evaluated'] and not inventory['trained_again']
assert not inventory['release_selected']
for name,expected in inventory['files'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,name
display(pd.DataFrame([{'dataset_version':inventory['dataset_version'],'snapshot_rows':inventory['snapshot_rows'],
    'models':len(inventory['models']),'artifact_files':len(inventory['files']),
    'test_evaluated':inventory['test_performance_evaluated']}]))
display(pd.DataFrame(inventory['models']))
display(pd.DataFrame(inventory['coverage']))
display(pd.DataFrame([{'item':i,'status':'Đạt nghiệm thu local' if i==1 else 'Chờ theo flow'} for i in range(1,11)]))
print('Bằng chứng',ROOT/pointer['evidence'])
print('Còn mở',inventory['pending'])
display(Markdown('**Mục1 nghiệm thu artifacts local. Tiếp theo mục2, khóa protocol đánh giá cuối trước test.**'))'''),
        md('''### Kiểm lại bộ dữ liệu bàn giao

        Chạy lại acceptance/calendar/schema/hash TV1, recompute thống kê scaler từ train, audit toàn bộ eligible windows của cả hai mode trong từng prepared bundle. Kiểm float64/finite, inverse X/y khớp raw JSON, thứ tự/ngày/độ phủ/ràng buộc mọi target cùng split. Đối chiếu bytes của dữ liệu local với ZIP đã bàn giao, cùng provenance9 checkpoint.

        raw_window_samples là số windows trong prepared gốc; một bước consumer common-history60 còn lọc các target chưa đủ60 phiên, không đổi input30. Năm bước giữ config TV4 không lọc common-history60. Kiểm test ở đây chỉ kiểm dữ liệu/schema/coverage, không tính prediction/metric hoặc tuning. CLI `python scripts/recheck_tv6_data.py`.'''),
        code('''from pathlib import Path
import json
import pandas as pd
from IPython.display import display
data_root=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'rule.md').is_file())
data_pointer=json.loads((data_root/'logs/audit/tv6_data_recheck_latest.json').read_text(encoding='utf-8'))
data_receipt=json.loads((data_root/data_pointer['evidence']).read_text(encoding='utf-8'))
assert data_receipt['passed'] and not data_receipt['test_performance_evaluated']
display(pd.DataFrame([{k:data_receipt[k] for k in ['snapshot_rows','first_date','last_date',
    'inventory_hashes_verified','zip_data_files_verified','models_provenance_verified',
    'inverse_matches_raw','temporal_coverage_verified','files_unchanged']}]))
display(pd.DataFrame([data_receipt['scaler_train_statistics']]))
display(pd.DataFrame(data_receipt['coverage']))
print('Ví dụ ranh giới', (data_root/data_pointer['evidence']).parent/'boundary_examples.json')
print('Bằng chứng',data_root/data_pointer['evidence'])'''),
        md('''## 2. Khóa protocol đánh giá cuối trước test

        Inventory đã nghiệm thu → protocol v1 + fingerprint → inference/evaluation ở các mục sau. Giữ9 model,3 seed mỗi nhóm; một bước502 samples, năm bước498. Khóa ordered sample/origin/target-date keys và artifacts SHA256, không âm thầm bỏ/trộn mẫu. Rolling input là lịch sử đã quan sát, weights/scaler giữ nguyên.

        Báo MAE/RMSE USD từng seed và mean/std mẫu ddof1, từng horizon1–5; overall h5 là flatten errors, không lấy trung bình RMSE của5 horizon. Baseline deterministic báo một lần. Demo seed42 cố định cho từng neural group, không chọn theo test hoặc tạo ensemble. Numeric tie1e-12USD không phải ngưỡng ý nghĩa thực tiễn/thống kê.

        CLI `python scripts/lock_tv6_protocol.py` chỉ tạo một lần hoặc kiểm lại lock; có drift thì từ chối thay vì ghi đè. Chưa chạy model trên test, chưa triển khai mục3/inference hoặc frontend. Xem docs/TV6_Final_Evaluation_Protocol.md.'''),
        code('''from pathlib import Path
import sys,json
import pandas as pd
from IPython.display import display,Markdown
protocol_root=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'rule.md').is_file())
if str(protocol_root) not in sys.path: sys.path.insert(0,str(protocol_root))
from backend.audit.tv6_protocol import validate_protocol
protocol_path=protocol_root/'experiments/configs/tv6_evaluation_protocol_v1.json'
protocol=json.loads(protocol_path.read_text(encoding='utf-8'))
protocol_sha=validate_protocol(protocol,protocol_root)
assert protocol['test_performance_evaluated_at_lock'] is False
semantic=protocol['semantic']
display(pd.DataFrame(semantic['models']))
display(pd.DataFrame(semantic['cohorts']))
display(pd.DataFrame([semantic['demo']]))
display(semantic['metrics'])
display(semantic['evaluation_policy'])
display(pd.DataFrame([{'item':i,'status':'Đạt local' if i<=2 else 'Chờ theo flow'} for i in range(1,11)]))
print('Protocol fingerprint',protocol_sha)
print('Lock',protocol_path)
print('Tests chống drift',protocol_root/'logs/audit/tv6_item2_tests.xml')
display(Markdown('**Mục2 khóa protocol đã đạt. Tiếp theo mục3, hoàn thiện inference/persistence; chưa đánh giá test.**'))'''),
        md('''### Audit và siết các điểm khóa protocol v1

        Thay assert bằng explicit guards, kiểm kiểu format/schema, path không thoát root và mọi model/data reference phải nằm trong intake hash. Đối chiếu model/run/seed/epoch/provenance với manifest thật, kiểm toàn bộ eligible cohort/history/date order từ snapshot. Registry riêng ghim bytes/fingerprint của lock cũ và receipt trước đó, không tự tái tạo khi mất lock hoặc mất cả lock/registry nhưng còn dấu vết lịch sử.

        Giữ nguyên bytes protocol v1,9 checkpoint,502/498 samples,metric và demo seed42. Không inference/test performance. Registry là bằng chứng consistency local, không phải chữ ký hoặc bằng chứng không ai đã chạy test bằng công cụ khác. Các guard phải được dùng trong các mục inference/evaluation tiếp theo.'''),
        code('''from pathlib import Path
import json,hashlib
import pandas as pd
from IPython.display import display
audit_root=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'rule.md').is_file())
audit_pointer=json.loads((audit_root/'logs/audit/tv6_protocol_audit_latest.json').read_text(encoding='utf-8'))
audit_lock=json.loads((audit_root/audit_pointer['evidence']).read_text(encoding='utf-8'))
assert audit_lock['passed'] and audit_lock['tests']==45
assert audit_lock['original_protocol_bytes_unchanged'] and not audit_lock['test_performance_evaluated']
for name,expected in audit_lock['source_hashes'].items():
    assert hashlib.sha256((audit_root/name).read_bytes()).hexdigest()==expected,name
display(pd.DataFrame([{k:audit_lock[k] for k in ['passed','tests','protocol_tests','models','cohorts',
    'original_protocol_bytes_unchanged','registry_unchanged_on_verify','test_performance_evaluated']}]))
display(pd.DataFrame([{'fix':v,'status':'Đã kiểm chứng'} for v in audit_lock['fixes']]))
print('Fingerprint giữ nguyên',audit_lock['semantic_sha256'])
print('Giới hạn',audit_lock['limitations'])
print('Bằng chứng',audit_root/audit_pointer['evidence'])'''),
        md('''## 3. Inference và persistence một/năm bước

        Forecast Input → protocol/registry guard → kiểm lịch sử snapshot → adapter CPU float64 → model eval/inference_mode hoặc persistence → inverse USD → prediction records. Không nhận target/y/actual hoặc checkpoint/scaler path từ request, không fit/update weights. Một bước LSTM/CNN/persistence; năm bước LSTM direct/persistence. Seed42 demo mặc định, research giữ3 seed.

        Mục3 chỉ cho phép target dates validation2023. Yêu cầu chạm test2024–2025 bị chặn trước forward; bước5 final evaluator mới tích hợp đường test sau bước4. Target dates lấy theo thứ tự phiên snapshot, không cộng ngày lịch. Không phát hành release/API/frontend, release_id hiện null có chủ đích.

        CLI `python scripts/check_tv6_inference.py` đối chiếu toàn bộ validation với inference trực tiếp trên X đã lưu; không tính metric hoặc ghép actual. Bảng/biểu đồ dưới chỉ hiển thị prediction USD, không dùng để kết luận chất lượng.'''),
        code('''from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display
inference_root=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'rule.md').is_file())
inference_pointer=json.loads((inference_root/'logs/audit/tv6_item3_latest.json').read_text(encoding='utf-8'))
inference_path=inference_root/inference_pointer['evidence']
inference=json.loads(inference_path.read_text(encoding='utf-8'))
assert inference['passed'] and inference['models']==9 and inference['output_rows']==6670
assert not inference['test_inference_enabled'] and not inference['metrics_calculated']
checks3=pd.read_csv(inference_path.parent/'checks.csv')
predictions3=pd.read_csv(inference_path.parent/'validation_inference_usd.csv')
display(checks3)
display(pd.DataFrame([{k:inference[k] for k in ['models','output_rows','test_inference_enabled',
    'metrics_calculated','trained_again','source_artifacts_unchanged']}]))
demo3=predictions3[(predictions3.seed==42)|predictions3.seed.isna()]
fig,axes=plt.subplots(1,2,figsize=(14,5))
for ax,h in zip(axes,[1,5]):
    mode=demo3[demo3.forecast_length==h]
    example=mode[mode.sample_id==mode.sample_id.iloc[0]]
    display(example[['method','seed','forecast_origin','target_date','horizon_step','predicted_price','currency','run_id']])
    if h==1:
        ax.bar(example.method,example.predicted_price)
    else:
        for method,group in example.groupby('method'):
            ax.plot(group.horizon_step,group.predicted_price,'o-',label=method)
        ax.set_xticks(range(1,6));ax.set_xlabel('Horizon step theo phiên');ax.legend()
    ax.set_title('Prediction USD · '+str(h)+' bước · origin '+example.forecast_origin.iloc[0])
    ax.set_ylabel('Adjusted close USD');ax.grid(axis='y',alpha=.2)
fig.suptitle('Inference validation · chỉ predictions, không actual/metric',fontsize=14)
fig.tight_layout();fig.savefig(inference_path.parent/'inference_examples.png',dpi=150)
display(fig);plt.close(fig)
display(pd.DataFrame([{'item':i,'status':'Đạt local' if i<=3 else 'Chờ theo flow'} for i in range(1,11)]))
print('Bằng chứng',inference_path)
print('Giới hạn',inference['limitations'])'''),
        md('''## 4. Evaluation USD, alignment và từng horizon

        Prediction input-only của mục3 + actual raw từ target source → kiểm cùng protocol/run/seed/ID/origin/ngày/horizon/units → residual → MAE/RMSE USD từng horizon/overall → mean/std mẫu3 seed. Không inner-join/drop mẫu âm thầm, không ensemble hoặc nhân baseline thành3 runs.

        H5 overall flatten N×5 residuals, RMSE=sqrt(mean squared errors), không mean5 RMSE; horizon_step để trống cho overall, không tạo horizon0. sample_count vẫn là số windows, error_count overall=N×5. Một bước không lặp metric overall vì giống h1. Đây là validation2023, không phải test2024–2025. Cases test-cohort trong unit tests chỉ là fixture tổng hợp.

        CLI `python scripts/check_tv6_evaluation.py` tái tính từ predictions validation đã lưu, không train/inference mới. Kiểm h1 khớp TV5, baseline khớp rawlast. Hàm metric riêng không thay xác minh nguồn actual/protocol: caller phải cung cấp artifacts đã accept và gọi guard.'''),
        code('''from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display
eval_root=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'rule.md').is_file())
eval_pointer=json.loads((eval_root/'logs/audit/tv6_item4_latest.json').read_text(encoding='utf-8'))
eval_path=eval_root/eval_pointer['evidence']
evaluation=json.loads(eval_path.read_text(encoding='utf-8'))
assert evaluation['passed'] and not evaluation['test_performance_evaluated']
metric4=pd.read_csv(eval_path.parent/'metrics.csv')
aggregate4=pd.read_csv(eval_path.parent/'aggregates.csv')
residual4=pd.read_csv(eval_path.parent/'residuals.csv')
display(metric4[['method','seed','forecast_length','horizon_step','metric_scope','sample_count','error_count','mae_usd','rmse_usd']])
display(aggregate4[['method','forecast_length','horizon_step','metric_scope','sample_count','error_count',
    'mae_usd_mean','mae_usd_std','rmse_usd_mean','rmse_usd_std','std_ddof']])
display(residual4.groupby(['method','forecast_length','seed'],dropna=False,sort=False).head(1)[
    ['method','seed','forecast_origin','forecast_length','horizon_step','target_date','predicted_price','actual_price','error_usd']])
fig,axes=plt.subplots(2,2,figsize=(15,10))
base1=metric4[(metric4.method=='persistence')&(metric4.forecast_length==1)].iloc[0]
one=aggregate4[aggregate4.forecast_length==1]
for ax,metric in zip(axes[0],['mae','rmse']):
    ax.bar(['persistence']+one.method.tolist(),[base1[metric+'_usd']]+one[metric+'_usd_mean'].tolist(),
        yerr=[0]+one[metric+'_usd_std'].tolist(),capsize=5)
    ax.set(title='Một bước · '+metric.upper()+' USD · 250 mẫu',ylabel='USD')
five=aggregate4[(aggregate4.forecast_length==5)&(aggregate4.metric_scope=='per_horizon')]
base5=metric4[(metric4.method=='persistence')&(metric4.forecast_length==5)&(metric4.metric_scope=='per_horizon')]
for ax,metric in zip(axes[1],['mae','rmse']):
    ax.errorbar(five.horizon_step,five[metric+'_usd_mean'],yerr=five[metric+'_usd_std'],fmt='o-',capsize=4,label='LSTM mean ± std')
    ax.plot(base5.horizon_step,base5[metric+'_usd'],'o-',label='Persistence')
    ax.set(title='Năm bước · '+metric.upper()+' từng horizon · 246 windows',xlabel='Horizon step',ylabel='USD')
    ax.set_xticks(range(1,6));ax.legend()
for ax in axes.flat:ax.grid(alpha=.2)
fig.suptitle('TV6 mục4 · evaluation validation · chưa chạy final test',fontsize=16)
fig.tight_layout();fig.savefig(eval_path.parent/'evaluation_overview.png',dpi=150)
display(fig);plt.close(fig)
display(pd.DataFrame([{'item':i,'status':'Đạt local' if i<=4 else 'Chờ theo flow'} for i in range(1,11)]))
print('Bằng chứng',eval_path)
print('H1 khớp TV5',evaluation['one_step_matches_tv5'])
print('Giới hạn',evaluation['limitations'])'''),
        md('''### Audit lại quá trình đánh giá và dữ liệu chưa đánh giá

        Phát hiện và sửa guard full validation: nếu prediction và actual cùng bị cắt mẫu, chỉ so chúng với nhau chưa đủ. Nay caller phải cung cấp cohort đầy đủ đọc từ input/target source đã pin hash; module từ chối subset chung bị gắn nhãn toàn tập. Protocol v1/model/data không đổi, scores cũ đã xác nhận không đổi.

        Hồi quy sau sửa đạt104/104 tests, gồm3 regression mới; JUnit logs/audit/tv6_item4_audit_tests.xml.

        Audit độc lập kiểm actual theo raw snapshot, baseline theo giá origin, residual,31 metric bằng math.fsum và8 aggregate bằng statistics mean/stdev. H1 phủ đủ250 phiên2023; H5 có246 windows, loại4 target-start26–29/12/2023 vì5 target sẽ vượt split. Các horizon có ngày đầu/cuối khác nhau có chủ đích, không silently drop mẫu.

        Mục4 đủ nghiệm thu công cụ/validation, chưa hoàn thành đánh giá model cuối. Test2024–2025 vẫn để mục5; phân tích lỗi test ở mục6. Dữ liệu2026/live/intraday/OHLCV không thuộc feature/snapshot đã khóa. Overlapping h5 windows không là các quan sát độc lập để kết luận significance.'''),
        code('''from pathlib import Path
import json
import pandas as pd
from IPython.display import display
audit_eval_root=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'rule.md').is_file())
audit_eval_pointer=json.loads((audit_eval_root/'logs/audit/tv6_evaluation_audit_latest.json').read_text(encoding='utf-8'))
audit_eval=json.loads((audit_eval_root/audit_eval_pointer['evidence']).read_text(encoding='utf-8'))
assert audit_eval['passed'] and not audit_eval['test_performance_evaluated']
display(pd.DataFrame([{k:audit_eval[k] for k in ['metric_rows_verified','aggregate_rows_verified',
    'residual_rows_verified','raw_actual_matches_snapshot','independent_math_matches','seed_std_matches',
    'metrics_unchanged_after_guard_fix']}]))
display(pd.DataFrame(audit_eval['coverage']))
print('H5 target starts loại đúng quy tắc',audit_eval['excluded_h5_validation_target_starts'])
print('Còn chưa đánh giá',audit_eval['remaining'])
print('Bằng chứng',audit_eval_root/audit_eval_pointer['evidence'])'''),
    ]


def tv6():
    cells=_tv6_before_item5()
    cells[0].source=cells[0].source.replace('**Trạng thái hiện tại: mục1–4 đã hoàn thành local, gồm nghiệm thu đầu vào, khóa protocol, inference và evaluation validation; chưa đánh giá hiệu năng test.**',
        '**Trạng thái hiện tại: mục1–9 hoàn thành local; mục10 đã audit kỹ thuật và tổng hợp đầu ra theo đề. Bàn giao máy khác/quyền phân phối dữ liệu vẫn chờ xác nhận. Residual được đánh giá sau phát triển trên test đã quan sát, không phải test độc lập mới. Các nhận xét ở mục trước phản ánh giai đoạn lịch sử tương ứng.**')
    cells[0].source+='\n\n**Bổ sung sau test:** cuối notebook có chẩn đoán persistence gap và thử nghiệm cải tiến residual trên validation2022/2023; giữ nguyên kết quả test chính thức. Đây là development, không phải test độc lập mới.'
    cells.extend([
        md('''## 5. Đánh giá chính thức test 2024–2025

        Input: 9 checkpoint và scaler đã khóa, ba seed42/123/456, 502 mẫu h1 và498 cửa sổ h5. Không train lại, không chọn seed theo test. Nhật ký execution.json được ghi trước test forward; inference chỉ nhận input, evaluator nhận target riêng sau dự đoán. Output:13.474 dự đoán,31 dòng metric và8 aggregate mean/std ddof1, cùng persistence trên đúng cohort.

        Kết quả: persistence tốt hơn cả LSTM vàCNN trên test này. CNN một bước thấp lỗi hơn LSTM một bước trong cấu hình đã khóa; không suy ra kiến trúcCNN luôn tốt hơn vì ngân sách tìm kiếm khác nhau. H5 overall tính trên toàn bộ498×5 lỗi, không lấy trung bìnhRMSE của5 horizon. Test đã được quan sát; không tiếp tục tuning rồi gọi cùng tập này là test chưa thấy.

        Biểu đồ dưới dùng đủ ba seed, không chọn đường dự đoán đẹp nhất. Phân tích nguyên nhân/lỗi chi tiết thuộc mục6. Dữ liệu adjusted hồi cứu và overlapping windows giới hạn diễn giải; chưa chứng minh lợi nhuận giao dịch.'''),
        code('''from pathlib import Path
import json,hashlib
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display
test_root=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'rule.md').is_file())
test_pointer=json.loads((test_root/'logs/audit/tv6_item5_latest.json').read_text())
test_folder=(test_root/test_pointer['evidence']).parent
test_summary=json.loads((test_folder/'summary.json').read_text())
test_ledger=json.loads((test_folder/'execution.json').read_text())
assert test_summary['passed'] and test_summary['test_performance_evaluated']
assert test_ledger['status']=='completed' and not test_summary['tuned_on_test']
for name,sha in test_summary['source_hashes'].items():
    assert hashlib.sha256((test_root/name).read_bytes()).hexdigest()==sha,name
test_metrics=pd.read_csv(test_folder/'metrics.csv')
test_aggregates=pd.read_csv(test_folder/'aggregates.csv')
assert len(test_metrics)==31 and len(test_aggregates)==8
display(pd.DataFrame([{k:test_summary[k] for k in ['models','prediction_rows','metric_rows','aggregate_rows','independent_metric_check','baseline_raw_last_check']}]))
display(test_metrics)
display(test_aggregates)
fig,axes=plt.subplots(1,2,figsize=(13,4))
one=test_metrics[test_metrics.forecast_length==1].copy()
one['label']=one.method+' '+one.seed.fillna(0).astype(int).astype(str).replace('0','baseline')
axes[0].bar(one.label,one.mae_usd)
axes[0].tick_params(axis='x',rotation=55)
axes[0].set(title='Test one-step: every seed',ylabel='MAE (USD)')
for seed,g in test_metrics[(test_metrics.forecast_length==5)&(test_metrics.method=='lstm')&(test_metrics.metric_scope=='per_horizon')].groupby('seed'):
    axes[1].plot(g.horizon_step,g.mae_usd,marker='o',label=f'LSTM seed{int(seed)}')
base=test_metrics[(test_metrics.forecast_length==5)&(test_metrics.method=='persistence')&(test_metrics.metric_scope=='per_horizon')]
axes[1].plot(base.horizon_step,base.mae_usd,'k--o',label='Persistence')
axes[1].set(title='Test direct five-step',xlabel='Horizon (trading sessions)',ylabel='MAE (USD)',xticks=[1,2,3,4,5])
axes[1].legend()
fig.tight_layout()
fig.savefig(test_folder/'test_metrics.png',dpi=150)
plt.show()
print('Evidence:',test_folder)
print('Next: mục6 phân tích lỗi và giới hạn; giữ nguyên cấu hình đã đánh giá.')''')])
    cells.extend([
        md('''### Kiểm lại nguyên nhân persistence thắng — phân tích sau test

        Không train/tune hoặc chạy forward mới. Đọc prediction đã lưu, đối chiếu raw snapshot và phân nhóm theo giá origin vượt mức tối đa train. Các bảng dưới giữ riêng từng seed, không coi ba seed là ba phiên độc lập.

        Train có giá tối đa177,65USD, test tối đa285,20USD;91,04% giá test vượt mức tối đa train. LSTM/CNN một bước có bias âm rõ: thường dự báo thấp hơn actual. Đây là bằng chứng phù hợp với hạn chế ngoại suy mức giá; không phải chứng minh duy nhất về nguyên nhân, không tự kết luận gate saturation hay overfitting.

        Cơ chế sai số được kiểm bằng đẳng thức: đặt Δ=actual−origin, a=prediction−origin; MSE(model)=E[Δ²]+E[a²]−2E[aΔ]. Persistence có a=0. Trên test này, phần điều chỉnh của mạng làm tăng MSE thay vì cải thiện baseline. Scaler không clip giá; model hiện dự báo mức giá trực tiếp, không có đường cộng lại last price bắt buộc. Các thay đổi mô hình chỉ là giả thuyết nghiên cứu tương lai, chưa triển khai/tuning trên test.'''),
        code('''from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display
gap_root=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'rule.md').is_file())
gap_pointer=json.loads((gap_root/'logs/audit/tv6_item5_latest.json').read_text())
gap_folder=(gap_root/gap_pointer['evidence']).parent/'gap_diagnosis'
gap_receipt=json.loads((gap_folder/'summary.json').read_text())
assert gap_receipt['passed'] and not gap_receipt['new_inference']
display(pd.read_csv(gap_folder/'price_distribution.csv'))
gap_table=pd.read_csv(gap_folder/'diagnosis_by_seed.csv')
gap_one=gap_table[(gap_table.forecast_length==1)&(gap_table.segment=='all')]
display(gap_one[['method','seed','samples','mae','bias','underprediction_fraction','mean_predicted_change','mean_actual_change']])
gap_segments=gap_table[(gap_table.forecast_length==1)&gap_table.segment.str.startswith('origin_')]
display(gap_segments[['method','seed','segment','samples','mae','baseline_mae_same_rows']])
gap_plot=gap_segments.groupby(['segment','method']).mae.mean().unstack('method')
ax=gap_plot.plot.bar(figsize=(10,4),rot=15)
ax.set(ylabel='MAE (USD)',title='Descriptive price-regime association: mean of seed MAEs')
plt.tight_layout()
plt.show()
print('Association is not causal proof. No retraining or test-based selection.')''')])
    cells.extend([
        md('''### Thử nghiệm cải tiến riêng: residual theo giá origin

        Theo yêu cầu thử sửa mô hình sau khi đã xem test: dùng X=(history−origin)/scale_train và target=(future−origin)/scale_train. Decode giá=origin+scale_train*output. LSTM h1, CNN h1 và LSTM direct h5 giữ core architecture/float64; head residual khởi tạo0 để bắt đầu bằng persistence. Đây là gói thay đổi, chưa tách ablation từng yếu tố.

        Hai fold: train2015–2021→validation2022; train2015–2022→validation2023. Scaler fit giá train riêng mỗi fold. Mọi target h5 cùng split.36runs gồm2 biểu diễn×2fold×3task×3seed, cùng Adam/MSE/lr0.001/batch32/max100/patience10. Control được train lại trên cùng mẫu với residual, không phải sao chép điểm test hoặc coi giống hệt run common60 cũ.

        Chỉ đánh giá development; không chạy testforward mới, không tuning/chọn seed theo test, không thay catalog/releasev1. Bảng ghi đủ mọi seed và persistence. Run All chỉ đọc kết quả đã lưu; training ở CLI scripts/run_tv6_residual_development.py.'''),
        code('''from pathlib import Path
import json,hashlib
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display
dev_root=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'rule.md').is_file())
dev_pointer=json.loads((dev_root/'logs/audit/tv6_residual_development_latest.json').read_text())
dev_folder=(dev_root/dev_pointer['evidence']).parent
dev_receipt=json.loads((dev_folder/'summary.json').read_text())
assert dev_receipt['passed'] and dev_receipt['runs_completed']==36
assert dev_receipt['post_test_development'] and not dev_receipt['test_inference_performed']
dev_audit=json.loads((dev_folder/'independent_audit.json').read_text())
assert dev_audit['passed'] and dev_audit['runs_verified']==36
for name,sha in dev_audit['result_hashes'].items():
    assert hashlib.sha256((dev_folder/name).read_bytes()).hexdigest()==sha,name
display(pd.DataFrame([{k:v for k,v in dev_audit.items() if k!='result_hashes'}]))
for name,sha in dev_receipt['source_hashes'].items():
    assert hashlib.sha256((dev_root/name).read_bytes()).hexdigest()==sha,name
dev_metrics=pd.read_csv(dev_folder/'metrics.csv')
dev_aggregate=pd.read_csv(dev_folder/'aggregates.csv')
dev_primary=dev_metrics[((dev_metrics.task!='lstm_h5')|(dev_metrics.scope=='overall'))]
display(dev_primary)
dev_primary_aggregate=dev_aggregate[(dev_aggregate.task!='lstm_h5')|(dev_aggregate.scope=='overall')]
display(dev_primary_aggregate)
dev_compare=[]
for (year,task),g in dev_primary.groupby(['validation_year','task']):
    absolute=g[g.representation=='absolute-price-control'];residual=g[g.representation=='origin-centered-price-delta-v1'];base=g[g.representation=='persistence']
    assert len(absolute)==3 and len(residual)==3 and len(base)==1
    dev_compare.append(dict(validation_year=year,task=task,absolute_mae=absolute.mae_usd.mean(),residual_mae=residual.mae_usd.mean(),
        baseline_mae=base.mae_usd.iloc[0],mae_improvement_pct=100*(1-residual.mae_usd.mean()/absolute.mae_usd.mean()),
        absolute_rmse=absolute.rmse_usd.mean(),residual_rmse=residual.rmse_usd.mean(),baseline_rmse=base.rmse_usd.iloc[0]))
dev_comparison=pd.DataFrame(dev_compare)
display(dev_comparison)
dev_comparison.to_csv(dev_folder/'comparison.csv',index=False)
fig,axes=plt.subplots(1,2,figsize=(14,4))
for ax,(year,g) in zip(axes,dev_comparison.groupby('validation_year')):
    g.set_index('task')[['absolute_mae','residual_mae','baseline_mae']].plot.bar(ax=ax,rot=15)
    ax.set(title=f'Development validation {year}',ylabel='MAE (USD)')
fig.tight_layout();fig.savefig(dev_folder/'development_comparison.png',dpi=140);plt.show()
print('Development only: no new independent held-out claim. Original test results remain unchanged.')'''),
        md('''### Kiểm chứng huấn luyện, checkpoint và chi tiết horizon

        Đồ thị loss dưới là các run thật trên fold2023, hiển thị cả ba seed mỗi nhóm. Train loss được tính online ở chế độ train; validation ở eval, nên không dùng chênh lệch đơn lẻ để kết luận overfitting. Checkpoint best validation được restore và lưu file mới, reload kiểm dự đoán. Không lựa seed tốt nhất để công bố. H5 báo đủ từng horizon và overall trong bảng.'''),
        code('''fig,axes=plt.subplots(3,2,figsize=(14,11))
for i,task in enumerate(['lstm_h1','cnn_h1','lstm_h5']):
    for j,(tag,representation) in enumerate([('absolute','absolute-price-control'),('residual','origin-centered-price-delta-v1')]):
        ax=axes[i,j]
        for seed in [42,123,456]:
            history=pd.read_csv(dev_folder/f'2023_{task}_{tag}_seed{seed}'/'epoch_logs.csv')
            line=ax.plot(history.epoch,history.val_loss,label=f'val seed{seed}')[0]
            ax.plot(history.epoch,history.train_loss,'--',alpha=.4,color=line.get_color())
        ax.set(title=f'{task}: {tag} (solid=val, dashed=train)',xlabel='Epoch',ylabel='Scaled MSE',yscale='log')
        ax.legend(fontsize=8)
fig.tight_layout();fig.savefig(dev_folder/'training_histories.png',dpi=140);plt.show()
display(dev_aggregate[dev_aggregate.task=='lstm_h5'])
display(pd.DataFrame(dev_receipt['runs'])[['validation_year','task','representation','seed','best_epoch','epochs','seconds']])
print('Evidence:',dev_folder)''')])
    cells.extend([
        md('''## 6. Phân tích lỗi và giá trị của lịch sử đối với LSTM

        Nghiệm thu phần phân tích, chưa sửa/train tiếp. Dùng lỗi test v1 đã lưu và12checkpoint residual LSTM hiện có trên development2022/2023. Forward mới chỉ trên validation để kiểm độ nhạy; không forward test mới, không update weights/scaler hoặc chọn seed.

        Các đối chứng giữ nguyên origin: flat (30giá đều bằng giá cuối), đảo/xáo trộn29giá trước với RNG cố định. Chúng là input nhân tạo, có thể ngoài phân phối; dùng để quan sát độ nhạy, không phải bằng chứng nhân quả hoặc phương án chọn model theo điểm tốt nhất.

        Phát hiện trọng tâm: LSTM residual h1 trên validation2023 dự báo gần như một mức điều chỉnh hằng số. Bỏ biến động lịch sử bằng flat chỉ đổi dự báo trung bình0,0037USD; MAE1,6194→1,6196, RMSE flat còn hơi thấp hơn. Đảo/xáo trộn không làm lỗi tăng nhất quán. Đây chưa là bằng chứng học được quy luật30phiên mạnh. Fold2022 h1 nhạy hơn; không khái quát thành mọi LSTM đều bỏ qua lịch sử.

        Những cải thiện trước đó vẫn có thật trên development, nhưng phần lợi thế so persistence cần đối chiếu một tham chiếu drift hằng số và ablation có kiểm soát trước khi quy cho khả năng học chuỗi. Chưa thử sửa các điểm này trong mục6.'''),
        code('''from pathlib import Path
import json,hashlib
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display
item6_root=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'rule.md').is_file())
item6_pointer=json.loads((item6_root/'logs/audit/tv6_item6_latest.json').read_text())
item6_folder=(item6_root/item6_pointer['evidence']).parent
item6_receipt=json.loads((item6_folder/'summary.json').read_text())
item6_audit=json.loads((item6_folder/'independent_audit.json').read_text())
assert item6_receipt['passed'] and item6_audit['passed']
assert not item6_receipt['training_performed'] and not item6_receipt['new_test_inference']
for name,sha in item6_receipt['source_hashes'].items():
    assert hashlib.sha256((item6_root/name).read_bytes()).hexdigest()==sha,name
for name,sha in item6_audit['result_hashes'].items():
    assert hashlib.sha256((item6_folder/name).read_bytes()).hexdigest()==sha,name
display(pd.DataFrame([{k:v for k,v in item6_audit.items() if k!='result_hashes'}]))
item6_probes=pd.read_csv(item6_folder/'history_probes.csv')
item6_primary=item6_probes[(item6_probes.forecast_length==1)|(item6_probes.metric_scope=='overall')]
display(item6_primary[['validation_year','forecast_length','seed','control','mae_usd','rmse_usd','mean_adjustment_usd','std_adjustment_usd','mean_abs_change_from_real_usd']])
display(item6_primary.groupby(['validation_year','forecast_length','control'])[['mae_usd','rmse_usd','mean_abs_change_from_real_usd']].mean())
item6_predictions=pd.read_csv(item6_folder/'history_probe_predictions.csv')
fig,axes=plt.subplots(1,2,figsize=(14,4))
item6_probes[(item6_probes.forecast_length==1)&item6_probes.control.isin(['real','flat'])].groupby(['validation_year','control']).mae_usd.mean().unstack('control').plot.bar(ax=axes[0],rot=0)
axes[0].set(title='LSTM h1: real versus flat history',ylabel='Development MAE (USD)')
scatter=item6_predictions[(item6_predictions.validation_year==2023)&(item6_predictions.forecast_length==1)&(item6_predictions.control=='real')]
for seed,g in scatter.groupby('seed'):
    axes[1].scatter(g.actual_price-g.origin_price,g.predicted_price-g.origin_price,s=12,alpha=.45,label=f'seed{seed}')
lo=(scatter.actual_price-scatter.origin_price).min();hi=(scatter.actual_price-scatter.origin_price).max()
axes[1].plot([lo,hi],[lo,hi],'k--',label='Perfect change prediction')
axes[1].set(title='Development2023: nearly constant correction',xlabel='Actual change (USD)',ylabel='Predicted change (USD)')
axes[1].legend(fontsize=8)
fig.tight_layout();fig.savefig(item6_folder/'history_diagnostics.png',dpi=140);plt.show()
print('All3seeds retained. Each session repeats across seeds; no significance/causal claim.')'''),
        md('''### Lỗi theo thời gian, horizon, stress và các vấn đề cần xử lý

        Test v1: LSTM h1 lỗi lớn tập trung cuối2025, không chỉ ở những phiên biến động lớn. Trên482phiên không vượt ngưỡng95% biến động tương đối của train, MAE LSTM trung bình3seed vẫn10,80USD so persistence2,11USD. Không được loại outlier để cải thiện bảng điểm.

        Residual development: stress dùng actual tương lai để gán nhãn hồi cứu, không phải feature dự báo. Validation2023 h1 chỉ có2phiên stress theo ngưỡngtrain, chưa đủ kết luận về khả năng chống shock. H5 phải xem từnghorizon; windows chồng lấn không là các quan sát độc lập.

        Báo cáo vấn đề: (1)v1 hạn chế ngoại suy/bias âm; (2)residual chủ yếu hiệu chỉnh gần hằng số ởfold2023; (3)lợi thế baseline nhỏ/không đồng đều giữa2fold vàstress; (4)chưa có test độc lập cho sửa sau test; (5)gói cải tiến còn nhiều yếu tố đồng thời, cầnablation để quy nguyên nhân. Không kết luận gate saturation/vanishing gradient hay tăngepoch sẽ sửa được vì chưa có phép đo. Dừng ở báo cáo, chưa train/fix hoặc sangrelease/API.'''),
        code('''item6_summary=pd.read_csv(item6_folder/'summary.csv')
item6_monthly=pd.read_csv(item6_folder/'monthly.csv')
item6_yearly=pd.read_csv(item6_folder/'yearly.csv')
item6_stress=pd.read_csv(item6_folder/'stress.csv')
item6_largest=pd.read_csv(item6_folder/'largest.csv')
display(item6_yearly[(item6_yearly.method=='lstm')&((item6_yearly.forecast_length==1)|(item6_yearly.metric_scope=='overall'))])
display(item6_stress[(item6_stress.method=='lstm')&((item6_stress.forecast_length==1)|(item6_stress.metric_scope=='overall'))])
display(item6_largest[(item6_largest.cohort=='official_test_2024_2025')&(item6_largest.method=='lstm')&(item6_largest.forecast_length==1)])
fig,axes=plt.subplots(2,2,figsize=(15,9))
monthly=item6_monthly[(item6_monthly.cohort=='official_test_2024_2025')&(item6_monthly.forecast_length==1)]
monthly.groupby(['month','method']).mae_usd.mean().unstack('method').plot(ax=axes[0,0])
axes[0,0].set(title='Original test: monthly mean of seed MAEs',ylabel='MAE (USD)')
rolling=pd.read_csv(item6_folder/'rolling.csv')
rolling=rolling[(rolling.cohort=='official_test_2024_2025')&(rolling.forecast_length==1)]
rolling.groupby(['target_date','method']).mae_usd.mean().unstack('method').plot(ax=axes[0,1])
axes[0,1].set(title='Original test: rolling20sessions',ylabel='MAE (USD)')
for ax,cohort,title in [(axes[1,0],'official_test_2024_2025','Original LSTM test2024-2025'),(axes[1,1],'development_2023','Residual LSTM development2023')]:
    h=item6_summary[(item6_summary.cohort==cohort)&(item6_summary.forecast_length==5)&(item6_summary.method=='lstm')&(item6_summary.metric_scope=='per_horizon')]
    h.groupby('horizon_step')[['mae_usd','baseline_mae_usd']].mean().plot(ax=ax,marker='o')
    ax.set(title=title,xlabel='Horizon (sessions)',ylabel='MAE (USD)',xticks=[1,2,3,4,5])
fig.tight_layout();fig.savefig(item6_folder/'time_and_horizon_errors.png',dpi=140);plt.show()
print('Different cohorts in lower panels; no direct test-versus-development performance comparison.')
print('Item6 analysis complete. Model fixes remain for the next user-authorized task.')
print('Evidence:',item6_folder)''')])
    cells.extend([
        md('''### Bước tiếp theo sau mục6: tham chiếu train-only và kiểm đường học

        Xử lý ưu tiên1 bằng phép kiểm có số liệu: tham chiếu origin+meanchange chỉ ước lượng từ các window train của từngfold, không dùngactual validation/test để ước lượng. Đây là diagnostic reference, không đổi persistence/protocol/releasev1.

        Trên cùng mẫu, LSTM residual tốt hơn train-meanchange ở cả hai fold nhưng mức lợi ích nhỏ; chưa chứng minh đó là lợi ích từ lịch sử vì kiểmflat trước đó vẫn gần tương đương. Không nhầm việc thắng một tham chiếu với chứng minh cơ chế học chuỗi.

        Gradient đo bằng MSE delta chuẩn hóa trên3batch train cố định first/middle/last32, đủ12checkpoint và3trạng thái: reconstructed init zerohead/defaulthead vàcheckpoint hiện có. Backward trên bản sao, không optimizerstep, không tạo model đã train mới hoặc chạy testforward. Đây là ảnh chụp gradient, không phải log toàn bộ quá trình train cũ.'''),
        code('''from pathlib import Path
import json,hashlib
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display
learning_root=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'rule.md').is_file())
learning_pointer=json.loads((learning_root/'logs/audit/tv6_lstm_learning_latest.json').read_text())
learning_folder=(learning_root/learning_pointer['evidence']).parent
learning_receipt=json.loads((learning_folder/'summary.json').read_text())
learning_audit=json.loads((learning_folder/'independent_audit.json').read_text())
assert learning_receipt['passed'] and learning_audit['passed']
assert not learning_receipt['weight_updates'] and not learning_receipt['test_inference']
for name,sha in learning_receipt['source_hashes'].items():
    assert hashlib.sha256((learning_root/name).read_bytes()).hexdigest()==sha,name
for name,sha in learning_audit['result_hashes'].items():
    assert hashlib.sha256((learning_folder/name).read_bytes()).hexdigest()==sha,name
learning_metrics=pd.read_csv(learning_folder/'reference_metrics.csv')
learning_primary=learning_metrics[(learning_metrics.forecast_length==1)|(learning_metrics.metric_scope=='overall')]
display(learning_primary[['validation_year','forecast_length','method','seed','samples','mae_usd','rmse_usd','bias_usd']])
learning_compare=learning_primary.groupby(['validation_year','forecast_length','method'])[['mae_usd','rmse_usd']].mean()
display(learning_compare)
display(pd.DataFrame(json.loads((learning_folder/'train_references.json').read_text())))
fig,axes=plt.subplots(1,2,figsize=(14,4))
for ax,year in zip(axes,[2022,2023]):
    learning_compare.loc[year].mae_usd.unstack('method').plot.bar(ax=ax,rot=0)
    ax.set(title=f'Development{year}: all3seed LSTM mean',xlabel='Forecast length (h5=overall)',ylabel='MAE (USD)')
fig.tight_layout();fig.savefig(learning_folder/'drift_comparison.png',dpi=140);plt.show()'''),
        md('''### Kết luận kiểm đường gradient — chưa có lỗi đứt gradient

        Zerohead làm gradient vào core bằng0 ở backward đầu tiên khi headweights còn0, nhưng gradient củahead vẫn có. Đây là hệ quả chainrule tại khởi tạo, không chứng minh core bị chặn mãi hoặc cần bỏzerohead để điểm tốt hơn.

        Tất cả checkpoint hiện có nhận coregradient hữu hạn/nonzero trên cácbatch kiểm; coreweights khác khởi tạo tái dựng theo cùngseed. Kết hợp với độ nhạy thấp ởmục6: vấn đề hiện là giá trị dự báo từ lịch sử chưa rõ, không có bằng chứng pipeline bị đứtbackprop. Không suy norm nhỏ thànhvanishinggradient: loss/thangđo/sốtham số khác nhau.

        Chưa train hoặc chỉnh learningrate/architecture. Bước nghiên cứu sửa tiếp phải làablation một yếu tố với cùngcohort/seeds/budget và log đường học, không mở thêm model. Duy trì mục tiêu LSTM và phân biệt development với kiểm chứng độc lập.'''),
        code('''learning_grad=pd.read_csv(learning_folder/'gradient_norms.csv')
learning_changes=pd.read_csv(learning_folder/'parameter_changes.csv')
display(learning_grad.groupby(['validation_year','forecast_length','state'])[['core_grad_l2','head_weight_grad_l2','head_bias_grad_l2','loss_scaled_mse']].mean())
display(learning_changes)
trained_grad=learning_grad[learning_grad.state=='existing_checkpoint']
assert (trained_grad.core_grad_l2>0).all()
assert (learning_changes.core_l2_change_from_reconstructed_init>0).all()
display(trained_grad.groupby(['validation_year','forecast_length']).core_grad_l2.agg(['min','max','mean']))
learning_input=pd.read_csv(learning_folder/'input_gradient_by_session.csv')
learning_input=learning_input[(learning_input.state=='existing_checkpoint')&(learning_input.session_position<30)]
fig,ax=plt.subplots(figsize=(11,4))
for (year,h),g in learning_input.groupby(['validation_year','forecast_length']):
    g.groupby('session_position').gradient_l2.mean().plot(ax=ax,label=f'fold{year}, h{h}')
ax.set(title='Checkpoint gradient on relative history coordinates (train batches)',xlabel='Position1..29 (oldest to previous session)',ylabel='Gradient L2',yscale='log')
ax.legend();fig.tight_layout();fig.savefig(learning_folder/'input_gradient.png',dpi=140);plt.show()
print('Coordinate gradient, not total raw-price sensitivity; position30 always0 after centering is excluded.')
print('No optimizer step. Core connectivity does not establish useful predictive signal.')
print('Evidence:',learning_folder)''')])
    cells.extend([
        md('''### Ablation một yếu tố: last hidden so với mean30hidden (LSTM h1)

        Giữ4513params, cùngkhởi tạo trướczerohead, relativeinput/deltatarget/scaler/cohort/sampler/3seed/lr/batch/max100/patience10. Chỉ đổi cách đọc sequenceoutput trướcLinear.6run mean mới trêndevelopment2022/2023; lastcontrol dùngrun đãpin, khôngtrain lại hoặcchọnseed. Checkpoint mới làdevelopment, không thayv1/residualcatalog hoặctestforward.

        Chấm bằng MAE/RMSE vàreal-vsflat trêncùngmẫu. Đảo/xáo trộn làsensitivity nhân tạo, khôngchọn làm dữ liệu mới. Chỉtănggradient vềphiêncũ không đủ để giữ thayđổi. Báo đầyđủ kếtquả tốt/xấu, khôngtuning thêmgiữa chừng.'''),
        code('''from pathlib import Path
import json,hashlib
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display
readout_root=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'rule.md').is_file())
readout_pointer=json.loads((readout_root/'logs/audit/tv6_readout_ablation_latest.json').read_text())
readout_folder=(readout_root/readout_pointer['evidence']).parent
readout_receipt=json.loads((readout_folder/'summary.json').read_text())
readout_audit=json.loads((readout_folder/'independent_audit.json').read_text())
assert readout_receipt['passed'] and readout_audit['passed']
assert len(readout_receipt['runs'])==6 and not readout_receipt['test_forward'] and not readout_receipt['promoted']
for name,sha in readout_receipt['source_hashes'].items():
    assert hashlib.sha256((readout_root/name).read_bytes()).hexdigest()==sha,name
for name,sha in readout_audit['result_hashes'].items():
    assert hashlib.sha256((readout_folder/name).read_bytes()).hexdigest()==sha,name
readout_metrics=pd.read_csv(readout_folder/'metrics.csv')
display(readout_metrics[readout_metrics.condition=='real'][['validation_year','seed','readout','mae_usd','rmse_usd','bias_usd','std_adjustment_usd']])
readout_aggregate=readout_metrics.groupby(['validation_year','readout','condition']).agg(mae_mean=('mae_usd','mean'),mae_std=('mae_usd','std'),rmse_mean=('rmse_usd','mean'),rmse_std=('rmse_usd','std')).reset_index()
display(readout_aggregate)
readout_sensitivity=readout_metrics.pivot(index=['validation_year','seed','readout'],columns='condition',values='mae_usd')
readout_sensitivity['flat_minus_real']=readout_sensitivity['flat']-readout_sensitivity['real']
display(readout_sensitivity)
fig,axes=plt.subplots(1,2,figsize=(13,4))
for ax,year in zip(axes,[2022,2023]):
    readout_metrics[(readout_metrics.validation_year==year)&readout_metrics.condition.isin(['real','flat'])].groupby(['readout','condition']).mae_usd.mean().unstack('condition').plot.bar(ax=ax,rot=0)
    ax.set(title=f'Development{year}: temporal readout',ylabel='MAE (USD)')
fig.tight_layout();fig.savefig(readout_folder/'readout_comparison.png',dpi=140);plt.show()
print('No independent held-out claim; evaluate both folds and MAE/RMSE, not a single best seed.')'''),
        md('''### Loghuấn luyện vàgradient củaablation

        Loggradient được đo trêncopy của trạngthái tại cácepoch cốđịnh bằng cùngbatchtrainmiddle32; không thêmoptimizerstep, khôngsửa RNG/modelgốc. Đây làthước đođường học, không làtiêu chí thayMAE/RMSE. Các đườngloss làrunthật, checkpointbest được reload vàđốichiếu.

        Chỉ đưa meanreadout vào ứngviên nếu cóbằngchứng tốt hơn nhấtquán; nếu không thìgiữ lastreadout. Không thửthêm hyperparameter trong lầnablation này hoặc thaymôhình demo tựđộng.'''),
        code('''display(pd.DataFrame(readout_receipt['runs']))
readout_gradient=pd.read_csv(readout_folder/'gradient_log.csv')
display(readout_gradient[['validation_year','seed','epoch','loss_scaled_mse','core_grad_l2','oldest_input_grad','previous_input_grad']])
fig,axes=plt.subplots(1,2,figsize=(14,4))
for ax,year in zip(axes,[2022,2023]):
    for seed in [42,123,456]:
        history=pd.read_csv(readout_folder/f'{year}_mean_readout_seed{seed}'/'epoch_logs.csv')
        line=ax.plot(history.epoch,history.val_loss,label=f'val seed{seed}')[0]
        ax.plot(history.epoch,history.train_loss,'--',color=line.get_color(),alpha=.4)
    ax.set(title=f'Mean readout{year}: solid val, dashed train',xlabel='Epoch',ylabel='Scaled MSE',yscale='log')
    ax.legend(fontsize=8)
fig.tight_layout();fig.savefig(readout_folder/'readout_training.png',dpi=140);plt.show()
print('Detailed decision/report: reports/audits/TV6_Readout_Ablation.md')
print('Evidence:',readout_folder)''')])
    cells.extend([
        md('''### Hoàn thành hạng mục: chốt ứng viên và kiểm chứng đường dự báo

        Theo yêu cầu không train thêm: giữ LSTM residual last, một/năm bước, ba seed42/123/456. Khóa sáu checkpoint/scaler/representation trongconfig tv6_lstm_residual_candidate_v1.json trước testforward. Không tạo kiến trúc/weights mới, không chọnseed theo test, không đổi catalogv1.

        Kiểm lại12validationpipelines của2fold và6testpipelines: rawinput→relativehistory→checkpoint→delta→origin+scale×delta→USD. Scalerfit/partialfit bị chặn, model eval/no-grad, hash/state trước/sau khớp, batchcuối vàbatch1 khớp; actual được ghép sauforward. H5 không cộng dồn recursive hoặc dùnginverse absolute-price nhầm cho delta.

        Protocol riêng ghi rõ test2024–2025 đã được quan sát trước cải tiến: kết quả dưới là **post-development evaluation, không độc lập**. Không tuning sau kết quả. Giữ riêng kết quả v1 đã công bố, không thay bằng điểm development/residual. Hạng mục audit/chốt ứng viên hoàn thành; chưa tự triển khai release/API/demo của mục7–9.'''),
        code('''from pathlib import Path
import json,hashlib
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display
completion_root=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'rule.md').is_file())
completion_pointer=json.loads((completion_root/'logs/audit/tv6_lstm_completion_latest.json').read_text())
completion_folder=(completion_root/completion_pointer['evidence']).parent
completion_receipt=json.loads((completion_folder/'summary.json').read_text())
completion_audit=json.loads((completion_folder/'independent_audit.json').read_text())
assert completion_receipt['passed'] and completion_audit['passed']
assert not completion_receipt['training_performed'] and not completion_receipt['refit_performed']
assert not completion_receipt['weights_changed'] and not completion_receipt['independent_holdout']
for name,sha in completion_receipt['source_hashes'].items():
    assert hashlib.sha256((completion_root/name).read_bytes()).hexdigest()==sha,name
for name,sha in completion_audit['result_hashes'].items():
    assert hashlib.sha256((completion_folder/name).read_bytes()).hexdigest()==sha,name
for name,sha in completion_audit['comparison_source_hashes'].items():
    assert hashlib.sha256((completion_root/name).read_bytes()).hexdigest()==sha,name
candidate_config=json.loads((completion_root/completion_receipt['candidate_config']).read_text())
display(pd.DataFrame(candidate_config['semantic']['models']))
display(pd.DataFrame([{k:completion_receipt[k] for k in ['candidate_models','pipeline_checks','training_performed','refit_performed','weights_changed','independent_holdout','test_label']}]))
completion_comparison=pd.read_csv(completion_folder/'comparison.csv')
display(completion_comparison)
completion_metrics=pd.read_csv(completion_folder/'metrics.csv')
completion_aggregates=pd.read_csv(completion_folder/'aggregates.csv')
post_metrics=completion_metrics[completion_metrics.scope=='post_development_test_2024_2025']
display(post_metrics)
display(completion_aggregates[completion_aggregates.scope=='post_development_test_2024_2025'])
fig,axes=plt.subplots(1,2,figsize=(13,4))
for ax,h in zip(axes,[1,5]):
    p=post_metrics[(post_metrics.forecast_length==h)&((post_metrics.forecast_length==1)|(post_metrics.metric_scope=='overall'))]
    p.groupby('method')[['mae_usd','rmse_usd']].mean().plot.bar(ax=ax,rot=10)
    ax.set(title=f'Post-development old-test evaluation: h{h}',ylabel='USD (lower is better)')
fig.tight_layout();fig.savefig(completion_folder/'candidate_evaluation.png',dpi=140);plt.show()
print('Research candidate only. Old test has informed development; not independent held-out proof.')'''),
        md('''### Nghiệm thu phạm vi và các giới hạn còn lại

        Đã có bảng tổng hợp theo phase, registry sáu ứng viên, protocol riêng trước đánh giá, số liệu đủba seed/horizon và audit độc lập. Không bổ sung train/model trong bước chốt. Meanreadout không được chọn; weights/checkpoint cũ không ghi đè.

        Trên đánh giá sau phát triển testcũ, residual h1MAE2,465892/RMSE3,652078USD so persistence2,476989/3,654583; h5overall4,607636/6,682840 so4,632497/6,707243. Lợi thế nhỏ, chưa có significance/thực tiễn hoặc bằng chứng độc lập. Lịch sử thật đóng góp chưa rõ theo probes trước; không tuyên bố đã tìm ra quy luật giá hoặc lợi nhuận giao dịch.

        Kết luận: hoàn thành hạng mục kiểm chứng và chốt candidate trong giới hạn không train thêm; chưa chứng minh LSTM vượt baseline bền vững và chưa là release tích hợp. Các bước7–10 tiếp tục khi người dùng giao, không tự sửa catalog hoặc tiếp tục tuning theo bảng này.'''),
        code('''display(pd.read_csv(completion_folder/'pipeline_checks.csv'))
display(pd.DataFrame([{k:v for k,v in completion_audit.items() if k not in ['result_hashes','comparison_source_hashes']}]))
post_h5=post_metrics[(post_metrics.forecast_length==5)&(post_metrics.metric_scope=='per_horizon')]
fig,axes=plt.subplots(1,2,figsize=(13,4))
for ax,metric in zip(axes,['mae_usd','rmse_usd']):
    post_h5.groupby(['horizon_step','method'])[metric].mean().unstack('method').plot(ax=ax,marker='o')
    ax.set(title=f'Post-development old-test h5: {metric}',xlabel='Horizon (sessions)',ylabel='USD',xticks=[1,2,3,4,5])
fig.tight_layout();fig.savefig(completion_folder/'candidate_horizons.png',dpi=140);plt.show()
print('Candidate config:',completion_receipt['candidate_config'])
print('Conclusion: item completed; no further training or automatic promotion.')
print('Evidence:',completion_folder)''')])
    cells.extend([
        md('''## 7. Đóng gói release và tích hợp inference

        Release `aapl-research-residual-v1`: sáu LSTM residual last (h1/h5 × ba seed), ba CNN h1 gốc và persistence. Manifest/registry liên kết chính xác weights, scaler, snapshot và sourcehash. Không thay trọng số, train, tuning hoặc source/catalogv1. Default demo seed42 cố định trước, không chọn theo test.

        Inference chỉ nhận bảy trường Forecast Input. Rawhistory→kiểm snapshot/contract→encoder theo model→CPU64model→decoder đúng→predictions USD. LSTM decode origin+scale×delta; CNN inverse absolute scaling; h5 trực tiếp năm output, không recursive. Không có actual/error trong response inference.

        Lịch sử2023–2025, mọi target h5 cùngsplit; không live hoặc ngày tương lai ngoài snapshot. API/frontend còn mục8/9. Source ZIP cục bộ nạp được sau giải nén trong tiến trình Python riêng; không đồng nghĩa đã chạy máy thành viên khác. Giới hạn test sau phát triển và lợi thế baseline nhỏ được giữ trongmanifest/output.'''),
        code('''from pathlib import Path
import sys,json,hashlib
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display
release_root=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'rule.md').is_file())
sys.path.insert(0,str(release_root))
from backend.artifacts.research_release import validate_release
from backend.inference.release_forecaster import ReleaseForecaster
release_document=validate_release(release_root)
release_semantic=release_document['semantic']
release_engine=ReleaseForecaster(release_root)
display(pd.DataFrame(release_semantic['models'])[['method','forecast_length','seed','scaler_id','representation','readout','best_epoch']])
display(pd.DataFrame([release_engine.metadata]))
release_frame=pd.read_csv(release_root/release_semantic['snapshot'],float_precision='round_trip')
release_days=release_frame.date.tolist();origin='2023-06-15';i=release_days.index(origin)
release_demo=[]
for h in [1,5]:
    record=dict(sample_id=f'{release_semantic["dataset_version"]}:lb30:f{h}:{origin}',dataset_version=release_semantic['dataset_version'],
        forecast_origin=origin,input_dates=release_days[i-29:i+1],input_values=[[v] for v in release_frame.adjusted_close.iloc[i-29:i+1]],lookback=30,forecast_length=h)
    release_demo.extend(release_engine.predict([record],methods=['lstm','cnn','persistence'] if h==1 else ['lstm','persistence']))
display(pd.DataFrame(release_demo)[['release_id','method','seed','forecast_origin','forecast_length','horizon_step','target_date','predicted_price','currency','scope']])
fig,ax=plt.subplots(figsize=(12,2.8));ax.axis('off')
labels=['Forecast Input\\nraw USD only','Snapshot + schema\\nhash checks','Residual / absolute\\nencoder','CPU64 LSTM / CNN\\ncheckpoint','Correct USD decode\\n+ persistence']
for j,label in enumerate(labels):
    x=.02+j*.20
    ax.text(x,.5,label,ha='left',va='center',fontsize=9,bbox=dict(boxstyle='round,pad=.55',facecolor='#e9f2fa',edgecolor='#46789a'),transform=ax.transAxes)
    if j<4:ax.annotate('',xy=(x+.195,.5),xytext=(x+.16,.5),xycoords='axes fraction',arrowprops=dict(arrowstyle='->',color='#46789a'))
fig.tight_layout();plt.show()
print('Actual backend inference on validation date, no metric/training. No API endpoint yet.')'''),
        md('''### Nghiệm thu end-to-end và gói release

        14tests tích hợp trên bản chính thức đạt: positiveh1/h5/repeat/no-fit, input cótarget/giá-ngày-version sai/duplicate, seed sai, CNNh5/crosssplit, artifacthash và sai scalerkể cảmanifest được reseal trongfixture. Toàn bộ22nhóm method/mode/seed/split với20.144predictions validation/test khớp bằng0 với evidence được nghiệm thu.

        ZIP chứa manifest/registry, chíncheckpoint, scaler đúng bộ, snapshot, backend source, dependencylock vàverifier. Không là toàn bộ gói log nghiên cứu. Nạp từ nguồn giải nén riêng bằngPython isolatedmode(-I), kiểm đủ9model/3seed, outputdigest khớp workspace. Cùngmáy/cùngdependencyenv, chưa chứng nhận máy khác.

        Mục7 hoàn thành local: đủ bộnạp/inference để nối API ởmục8. Không tự tạoAPI/giao diện, không upload hoặc push. Các metric sau phát triển không được đổi thành independentholdout hoặc lợi nhuận giao dịch.'''),
        code('''release_pointer=json.loads((release_root/'logs/audit/tv6_item7_latest.json').read_text())
release_evidence=(release_root/release_pointer['evidence']).parent
release_acceptance=json.loads((release_evidence/'acceptance.json').read_text())
assert release_acceptance['passed'] and release_acceptance['integration_tests_passed']==14
for name,sha in release_acceptance['evidence_hashes'].items():
    assert hashlib.sha256((release_evidence/name).read_bytes()).hexdigest()==sha,name
assert hashlib.sha256((release_root/release_acceptance['zip_path']).read_bytes()).hexdigest()==release_acceptance['zip_sha256']
assert hashlib.sha256((release_root/release_acceptance['portability_evidence']).read_bytes()).hexdigest()==release_acceptance['portability_evidence_sha256']
display(pd.DataFrame([{k:v for k,v in release_acceptance.items() if k!='evidence_hashes'}]))
display(pd.read_csv(release_evidence/'checks.csv'))
release_portability=json.loads((release_root/release_acceptance['portability_evidence']).read_text())
assert release_portability['workspace']['prediction_sha256']==release_portability['extracted']['prediction_sha256']
print('ZIP:',release_root/release_acceptance['zip_path'])
print('Manifest:',release_root/'artifacts/releases/aapl-research-residual-v1/manifest.json')
print('Isolated source root:',release_portability['extracted']['source_root'])
print('Next: mục8 API, no further training required.')''')])
    cells.extend([
        md('''## 8. API lịch sử theo release — FastAPI/Uvicorn

        API prefix/api/v1, không train hoặc downloadlive. Dùngrelease aapl-research-residual-v1 của mục7, giữ nguyênsource/weights/scaler đãpin. Backend mới chỉ điều phối input theoorigin, inference, đọcresultssidecar vàmetricEvaluation; khôngviết lại côngthức model.

        Endpoint: health/readiness; releasecurrent/detail; forecastorigins; datasetprices; predictions; storedresults/metrics; experiments/history/audits; verifiedLSTMtrace. Health độc lập artifact; readiness kiểm đủ9model vàresults. Client khôngtruyềntarget/scaler/checkpointpath. Seed42default,42/123/456được hỗtrợ. H5 khôngCNN hoặccrosssplit.

        RequestID vàHTTP404/422/503/500 theo contract, traceback/path nội bộ chỉ tronglog. List/ranges có giới hạn/phântrang. Kết quảinference khôngchứaactual; comparison đượcghép sau. Results/metrics đọc dữ liệuđãlưu, táchevaluationphase, không tạo tuyênbốtestđộclập. Frontend cònmục9.'''),
        code('''from pathlib import Path
import sys,json
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display
api_root=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'rule.md').is_file())
sys.path.insert(0,str(api_root))
from fastapi.testclient import TestClient
from backend.api.app import create_app
with TestClient(create_app(api_root)) as api_client:
    api_health=api_client.get('/api/v1/health').json()
    api_ready=api_client.get('/api/v1/readiness').json()
    api_meta=api_client.get('/api/v1/releases/current').json()
    api_pred_response=api_client.post('/api/v1/predictions',json={'forecast_origin':'2023-06-15','forecast_length':5})
    assert api_pred_response.status_code==200,api_pred_response.text
    api_pred=api_pred_response.json()
    api_metrics=api_client.get('/api/v1/metrics',params={'forecast_length':5,'split':'val','origin_from':'2023-06-01','origin_to':'2023-06-15'}).json()
    api_trace=api_client.post('/api/v1/model-traces',json={'forecast_origin':'2023-06-15','forecast_length':5,'detail':'summary'}).json()
assert api_health['status']=='ok' and api_ready['status']=='ready'
assert api_pred['request_id']==api_pred_response.headers['X-Request-ID']
display(pd.DataFrame([api_ready]))
display(pd.DataFrame(api_pred['predictions'])[['release_id','method','seed','forecast_origin','horizon_step','target_date','predicted_price','currency']])
display(pd.DataFrame(api_metrics['items']))
api_chart=pd.DataFrame(api_pred['predictions'])
api_actual=pd.DataFrame(api_pred['comparison']).drop_duplicates('target_date')
fig,axes=plt.subplots(1,2,figsize=(14,4))
for method,g in api_chart.groupby('method'):
    axes[0].plot(g.horizon_step,g.predicted_price,marker='o',label=method)
axes[0].plot(api_actual.horizon_step,api_actual.actual_price,'k--o',label='Actual joined after inference')
axes[0].set(title='API example: validation origin2023-06-15',xlabel='Horizon (sessions)',ylabel='USD',xticks=[1,2,3,4,5]);axes[0].legend(fontsize=8)
api_gate=pd.DataFrame(api_trace['trace']['steps'])
for gate in ['input_gate','forget_gate','output_gate']:
    axes[1].plot(api_gate.time_step,api_gate[gate],label=gate)
axes[1].set(title='Verified gate means from selected LSTM checkpoint',xlabel='Input time step',ylabel='Mean gate activation');axes[1].legend(fontsize=8)
fig.tight_layout();plt.show()
print('Example selected date, not aggregate performance evidence. API does not improve weights.')
print('Trace verified:',api_trace['trace']['verification'])'''),
        md('''### Kiểm chứng API và cách chạy

        51 tests đạt sau tái audit: h1/h5 và 3 seed/2 origin khớp release, invalid input, 404/422/503/500, health/readiness, metric cùng cohort, pagination, trace USD khớp inference, không fit, thiếu output và CORS. Bổ sung mẫu Swagger chạy được và từ chối metric có keys trùng/thiếu hoặc actual khác nhau. 15 HTTP checks qua Uvicorn localhost đạt; server test tự dừng.

        DependenciesAPI được ghim trongscripts/requirements-tv6-api-lock.txt, giữkhớp69package củaTV4core; pipcheck đạt. Haiwarning thưviệntest vềdeprecation vẫnđượcgiữtrongJUnit/log, không làtestfailure; chưađổi dependencycore đểsửa warning.

        Chạy `.venv/tv4_clean/Scripts/python.exe scripts/run_tv6_api.py`, sauđó mở http://127.0.0.1:8000/docs. Scriptchỉbind127.0.0.1,mộtworker,mộttorchthread. Source+artifacts/sidecar cầnđúngbộ; ZIPmục7chỉđónggói inference, chưa gồm API mới. Khôngcótrainendpoint/live/tickerkhác. APIhoạtđộng đúng không nângtínhđộclập hoặc độchínhxácmôhình.'''),
        code('''import hashlib
api_pointer=json.loads((api_root/'logs/audit/tv6_item8_latest.json').read_text())
api_folder=(api_root/api_pointer['evidence']).parent
api_acceptance=json.loads((api_folder/'acceptance.json').read_text())
api_receipt=json.loads((api_folder/'summary.json').read_text())
assert api_acceptance['passed'] and api_acceptance['api_tests_passed']==51
assert api_acceptance['real_http_checks']==15 and api_acceptance['test_server_stopped']
for name,sha in api_receipt['source_hashes'].items():
    assert hashlib.sha256((api_root/name).read_bytes()).hexdigest()==sha,name
for name,sha in api_acceptance['source_hashes'].items():
    assert hashlib.sha256((api_root/name).read_bytes()).hexdigest()==sha,name
for name,sha in api_acceptance['evidence_hashes'].items():
    assert hashlib.sha256((api_folder/name).read_bytes()).hexdigest()==sha,name
display(pd.DataFrame([{k:v for k,v in api_acceptance.items() if k not in ['source_hashes','evidence_hashes']}]))
display(pd.DataFrame(json.loads((api_folder/'checks.json').read_text())))
print('API request logs:',api_root/'logs/api/requests.log')
print('HTTP evidence:',api_folder)
print('Next: mục9 frontend theo concept đã chốt. No new training.')''')])
    cells.extend([
        md('''### Tái audit mục 8 — 27/11/2026

        Đã sửa mẫu Swagger từ ngày `string` sang ngày có thật; bổ sung đối chiếu actual giữa các phương pháp và chống keys trùng khi tính metric. Kiểm toàn bộ 20.144 dòng kết quả với snapshot: giá actual, phiên target, error, finite và keys; tính lại MAE/RMSE độc lập bằng scalar math cho 12 nhóm horizon/seed/split. Không train hoặc thay weights. Đây là nghiệm thu local; chưa kiểm tải, triển khai Internet hoặc máy khác. ZIP inference mục 7 chưa bao gồm API/sidecar mới.'''),
        code('''api_reaudit=json.loads((api_folder/'data_reaudit.json').read_text())
assert api_reaudit['passed'] and api_reaudit['metric_groups']==12
assert hashlib.sha256((api_root/api_acceptance['tests_file']).read_bytes()).hexdigest()==api_acceptance['tests_sha256']
display(pd.DataFrame([api_reaudit]))
with TestClient(create_app(api_root)) as swagger_client:
    swagger_schemas=swagger_client.get('/openapi.json').json()['components']['schemas']
    swagger_examples=[]
    for schema_name,route in [('PredictionRequest','predictions'),('TraceRequest','model-traces')]:
        example=swagger_schemas[schema_name]['examples'][0]
        response=swagger_client.post('/api/v1/'+route,json=example)
        assert response.status_code==200,response.text
        swagger_examples.append(dict(schema=schema_name,origin=example['forecast_origin'],horizon=example['forecast_length'],http_status=response.status_code))
display(pd.DataFrame(swagger_examples))
print('Sau khi sửa source, dừng server cũ và chạy lại scripts/run_tv6_api.py để Swagger nạp mẫu mới.')''')])
    cells.extend([
        md('''## 9. Frontend — AAPL Forecast Lab

        Bám concept đã chốt: nền sáng/sidebar, biểu đồ 30 input và vùng dự báo, thẻ mô hình, nhật ký. Dữ liệu và số liệu đến từ API mục8. HTML/CSS/ES modules, không cài npm; proxy localhost5173 gọi API8000, không train, fit scaler hoặc tự tính MAE/RMSE. Năm phiên bỏ CNN; một phiên chỉ T+1. Các màn Dữ liệu, So sánh, Phân tích lỗi, Nhật ký và Khám phá LSTM có phạm vi/nguồn rõ ràng.

        Chạy API rồi `python scripts/run_tv6_frontend.py`; mở http://127.0.0.1:5173. Nhật ký chỉ tồn tại trong tab; không phải dự báo phát hành tại ngày lịch sử. Metric từng seed/full-split tách khỏi selected-range. Residual đánh giá trên test cũ sau phát triển, không phải holdout độc lập. Kiểm Chrome thật và responsive390px được lưu cùng receipt.'''),
        code('''from IPython.display import Image
ui_pointer=json.loads((api_root/'logs/audit/tv6_item9_latest.json').read_text())
ui_receipt_path=api_root/ui_pointer['evidence']
ui_folder=ui_receipt_path.parent
ui_receipt=json.loads(ui_receipt_path.read_text())
assert ui_receipt['passed'] and ui_receipt['real_api'] and not ui_receipt['training']
for name,sha in ui_receipt['source_hashes'].items():
    assert hashlib.sha256((api_root/name).read_bytes()).hexdigest()==sha,name
ui_requests=json.loads((ui_folder/'prediction_requests.json').read_text())
assert [r['forecast_length'] for r in ui_requests]==[1,5]
assert all('target_values' not in r and 'input_values' not in r for r in ui_requests)
with TestClient(create_app(api_root)) as ui_api:
    replay=ui_api.post('/api/v1/predictions',json=ui_requests[1])
    assert replay.status_code==200,replay.text
    ui_replay=replay.json()
assert len(ui_replay['predictions'])==10 and ui_replay['status']=='complete'
display(pd.DataFrame(ui_replay['predictions'])[['forecast_origin','target_date','method','horizon_step','predicted_price']])
display(Image(filename=str(ui_folder/'forecast_h1_desktop.png'),width=1100))'''),
        md('''### Nghiệm thu giao diện và giới hạn

        Kiểm browser thực: h1/h5, CNN disabled khi h5, xóa kết quả cũ, metric full/range, run/history, dữ liệu phân trang, stored errors, nhật ký, trace verified, responsive390px và lỗi mất backend. Test JavaScript kiểm request input-only, ghép comparison đúng key, escape dữ liệu và lỗi HTTP. Screenshot là kết quả API thật; chưa triển khai Internet, load test hoặc xác nhận máy khác. Mục10 còn audit cuối/tái lập/bàn giao.'''),
        code('''ui_checks=json.loads((ui_folder/'checks.json').read_text())
assert len(ui_checks)==ui_receipt['checks'] and all(c['passed'] for c in ui_checks)
display(pd.DataFrame(ui_checks))
display(pd.DataFrame([{k:v for k,v in ui_receipt.items() if k!='source_hashes'}]))
display(Image(filename=str(ui_folder/'forecast_mobile.png'),width=300))
print('Bằng chứng:',ui_folder)
print('Tiếp theo mục10: audit cuối, tái lập và bàn giao; chưa push hoặc upload.')''')])
    cells.extend([
        md('''## 10. Audit toàn bài toán và chốt đầu ra theo đề

        Đề Topic4: Yahoo Finance, LSTM regression dự báo phiên tiếp theo; mở rộng multi-step và CNN vs.LSTM. Sản phẩm hiện có snapshot/preprocessing, H1/H5/CNN/persistence, checkpoint/scaler/config/seed, metric USD, phân tích lỗi, API/frontend và hướng dẫn. Bảy báo cáo được tổng hợp lại theo bằng chứng hiện hành; không dùng trạng thái khung báo cáo cũ làm kết luận.

        Audit kiểm lại hash dữ liệu/model, scaler train, prepared windows/split/float64, actual/target dates, metric scalar math, kết quả test gốc và residual theo giai đoạn. Không train/tune/refit mô hình. Tests acquisition dùng môi trường TV1 riêng, core/model/API dùng TV4; fixture tổng hợp không thay bằng chứng artifacts thật. Máy khác và quyền phân phối dữ liệu vẫn cần xác nhận, không ghi đã nghiệm thu toàn bộ.'''),
        code('''final_pointer=json.loads((api_root/'logs/audit/tv6_item10_latest.json').read_text(encoding='utf-8'))
final_path=api_root/final_pointer['evidence']
final_audit=json.loads(final_path.read_text(encoding='utf-8'))
assert final_audit['passed'] and not final_audit['training_performed'] and not final_audit['refit_performed']
from backend.artifacts.research_release import validate_release
assert validate_release(api_root)['semantic_sha256']==final_audit['release_sha256']
for name,sha in final_audit['source_hashes'].items():
    assert hashlib.sha256((api_root/name).read_bytes()).hexdigest()==sha,name
display(pd.DataFrame(final_audit['requirements']))
final_scores=pd.read_csv(final_path.parent/'comparison.csv')
display(final_scores[['phase','method','horizon','seeds','samples','errors','mae','mae_std','rmse','rmse_std']])
print('Core JUnit (có subtests):',final_audit['core_regression'])
print('Real TV1 tests:',final_audit['real_tv1_tests'])
print('Acquisition offline:',final_audit['acquisition_tests'])'''),
        md('''### Đầu ra và kết luận để trình bày giảng viên

        Một request trả giá dự báo USD kèm release/dataset/origin/target/method/seed/run/horizon. Actual/error ghép sau inference. H1 một giá/phương pháp; H5 năm giá/phương pháp, không CNN. Metric chính thức và khoảng chọn tách biệt, model gốc và residual post-development không gộp thành test độc lập.

        Kết luận: đã triển khai được bài toán và hai extension local. Model gốc thua persistence; residual giảm sai số so với bản gốc nhưng lợi thế baseline nhỏ trên test cũ đã quan sát, chưa chứng minh bền vững hoặc lợi nhuận. Đóng góp là pipeline/kiểm chứng/thực nghiệm minh bạch/demo tái lập. Đọc docs/TV6_Coursework_Output_and_Defense.md và reports/audits/TV6_Item10_Final_Audit.md. Gói web local mới dùng verifier riêng, không ghi đè release v1. Không tự upload/push hoặc nhận đã xác minh máy khác.'''),
        code('''fig,axes=plt.subplots(1,2,figsize=(13,4.8))
for ax,h in zip(axes,[1,5]):
    selected=final_scores[final_scores.horizon==h].copy()
    labels=[r.method+' / '+('original' if r.phase=='original_locked_test' else 'post-dev old test') for r in selected.itertuples()]
    ax.barh(labels,selected.mae,color=['#597caa' if p=='original_locked_test' else '#2b9d8f' for p in selected.phase])
    ax.set(title=f'H{h}: MAE USD; phases must remain separate',xlabel='MAE USD')
fig.tight_layout();plt.show()
display(pd.DataFrame({'Còn cần xác nhận':final_audit['open_items']}))
print('Technical audit local:',final_audit['passed'])
print('Whole coursework fully signed off:',final_audit['all_coursework_requirements_fully_signed_off'])
print('No new independent holdout:',not final_audit['independent_holdout'])''')])
    cells.extend([
        md('''### Hoàn thiện phần bàn giao còn mở — cài môi trường mới

        Sau audit mục10 đã tạo venv riêng, cài dependencies từ lock thay vì sao chép môi trường cũ, kiểm85 phiên bản và đường dẫn import. API/handoff và browser thực được chạy bằng interpreter mới. Có verifier xuất biên bản JSON không ghi đè, checker chọn Python/Chrome/Edge và các bảng CSV riêng cho báo cáo.

        Đây vẫn là cùng máy vật lý; không thay xác nhận thành viên khác. Quyền phân phối dữ liệu và thủ tục nộp cần bằng chứng bên ngoài. Kết luận model không đổi, không train/refit/tuning. Gói mới phải được đối chiếu checksum và biên bản kiểm nguồn giải nén riêng; không ghi đè ZIP cũ.'''),
        code('''closure_pointer=json.loads((api_root/'logs/audit/tv6_closure_latest.json').read_text(encoding='utf-8'))
closure_folder=api_root/closure_pointer['folder']
closure_checks=json.loads((closure_folder/'local_checks.json').read_text(encoding='utf-8'))
assert closure_checks['passed'] and closure_checks['fresh_install_verified'] and not closure_checks['training']
for name,sha in closure_checks['evidence_hashes'].items():
    assert hashlib.sha256((closure_folder/name).read_bytes()).hexdigest()==sha,name
assert validate_release(api_root)['semantic_sha256']==closure_checks['release_sha256']
display(pd.DataFrame([{k:closure_checks[k] for k in ['packages_verified','pip_check_passed','pytest_passed','pytest_failures','pytest_skipped','browser_checks','javascript_tests','same_machine','verified_on_other_machine']}]))
display(pd.read_csv(api_root/'reports/tables/TV6_Final_Comparison.csv'))
display(pd.DataFrame({'Cần xác nhận bên ngoài':closure_checks['remaining_external']}))
print('Fresh Python:',closure_checks['fresh_python'])
print('Biên bản cho người nhận: docs/TV6_Member_Acceptance.md')
print('Không train thêm; không có holdout độc lập mới.')''')])
    return cells


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--member',choices=['2','3','4','5','6','all'],default='all')
    parser.add_argument('--overwrite',action='store_true',help='Regenerate notebooks, clearing old outputs; execute afterward.')
    args=parser.parse_args()
    for name,cells in [('02_TV2_Preprocessing_and_Audit.ipynb',tv2()),('03_TV3_LSTM_Development_and_Tests.ipynb',tv3()),('04_TV4_Training_and_Experiments.ipynb',tv4()),('05_TV5_CNN_Development_and_Experiments.ipynb',tv5()),('06_TV6_Integration_Evaluation_and_Demo.ipynb',tv6())]:
        if args.member != 'all' and not name.startswith('0'+args.member+'_'): continue
        path=ROOT/'notebooks'/name
        if path.exists() and not args.overwrite: raise FileExistsError(f'{path}: use --overwrite only for intended regeneration')
        kernel='aapl-coursework-tv4' if name.startswith('04_') else KERNEL
        display_name='AAPL Coursework TV4' if name.startswith('04_') else 'AAPL Coursework TV2-TV3'
        if name.startswith('05_'):
            kernel, display_name = 'aapl-coursework-tv5', 'AAPL Coursework TV5'
        if name.startswith('06_'):
            kernel, display_name = 'aapl-coursework-tv6', 'AAPL Coursework TV6'
        nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':kernel,'display_name':display_name,'language':'python'},'language_info':{'name':'python'}})
        nbf.write(nb,path)
        print(path)


if __name__=='__main__': main()
