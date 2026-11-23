"""Build reviewable TV2/TV3 notebooks; backend remains the source of logic."""
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


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--member',choices=['2','3','all'],default='all')
    parser.add_argument('--overwrite',action='store_true',help='Regenerate notebooks, clearing old outputs; execute afterward.')
    args=parser.parse_args()
    for name,cells in [('02_TV2_Preprocessing_and_Audit.ipynb',tv2()),('03_TV3_LSTM_Development_and_Tests.ipynb',tv3())]:
        if args.member != 'all' and not name.startswith('0'+args.member+'_'): continue
        path=ROOT/'notebooks'/name
        if path.exists() and not args.overwrite: raise FileExistsError(f'{path}: use --overwrite only for intended regeneration')
        nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':KERNEL,'display_name':'AAPL Coursework TV2-TV3','language':'python'},'language_info':{'name':'python'}})
        nbf.write(nb,path)
        print(path)


if __name__=='__main__': main()
