from copy import deepcopy
import json
from pathlib import Path

import pytest
from backend.audit.tv6_protocol import digest,validate_protocol,build_protocol,resolve_member,tracked_member,REGISTRY_PATH
import subprocess
import sys
import hashlib

ROOT=Path(__file__).resolve().parents[2]


def read(): return json.loads((ROOT/'experiments/configs/tv6_evaluation_protocol_v1.json').read_text())


def test_current_protocol_accepts(): assert validate_protocol(read(),ROOT)


@pytest.mark.parametrize('section,key,value',[
    ('demo','seed',123),('metrics','std_ddof',0),('metrics','round_before_metric',True),
    ('runtime','dtype','float32'),('evaluation_policy','no_test_tuning',False),
])
def test_policy_drift_rejected_even_after_rehash(section,key,value):
    protocol=read();protocol['semantic'][section][key]=value
    protocol['semantic_sha256']=digest(protocol['semantic'])
    with pytest.raises(ValueError,match='differs'):validate_protocol(protocol,ROOT)


def test_cohort_drift_rejected():
    protocol=read();protocol['semantic']['cohorts'][0]['samples']-=1
    protocol['semantic_sha256']=digest(protocol['semantic'])
    with pytest.raises(ValueError,match='differs'):validate_protocol(protocol,ROOT)


def test_corrupt_fingerprint_rejected():
    protocol=read();protocol['semantic_sha256']='0'*64
    with pytest.raises(ValueError,match='fingerprint'):validate_protocol(protocol,ROOT)


def test_artifact_drift_rejected(tmp_path):
    (tmp_path/'reports/audits').mkdir(parents=True)
    original=json.loads((ROOT/'reports/audits/TV6_Input_Inventory.json').read_text())
    original['files']={'bad.bin':'0'*64}
    (tmp_path/'reports/audits/TV6_Input_Inventory.json').write_text(json.dumps(original))
    (tmp_path/'bad.bin').write_bytes(b'changed')
    with pytest.raises(ValueError,match='artifact changed'):validate_protocol(read(),tmp_path)


@pytest.mark.parametrize('version',[True,1.0,'1'])
def test_wrong_format_types_rejected(version):
    protocol=read();protocol['format_version']=version
    with pytest.raises(ValueError,match='format'):validate_protocol(protocol,ROOT)


@pytest.mark.parametrize('path',['../outside.bin','a/../../outside.bin','C:/outside.bin','a\\outside.bin'])
def test_path_escape_rejected(tmp_path,path):
    with pytest.raises(ValueError):resolve_member(tmp_path,path)


def test_unpinned_reference_rejected(tmp_path):
    with pytest.raises(ValueError,match='not pinned'):tracked_member(tmp_path,{},'missing/weights.pt')


@pytest.mark.parametrize('damage',['duplicate_checkpoint','wrong_model_seed','bad_intake_status'])
def test_bad_inventory_rejected_without_changing_real_artifacts(monkeypatch,damage):
    path=ROOT/'reports/audits/TV6_Input_Inventory.json'
    original=Path.read_text
    inventory=json.loads(original(path))
    if damage=='duplicate_checkpoint':inventory['models'][1]['checkpoint']=inventory['models'][0]['checkpoint']
    if damage=='wrong_model_seed':inventory['models'][0]['seed']=42.0
    if damage=='bad_intake_status':inventory['passed']=False
    def altered(self,*args,**kwargs):
        return json.dumps(inventory) if self==path else original(self,*args,**kwargs)
    monkeypatch.setattr(Path,'read_text',altered)
    with pytest.raises(ValueError):build_protocol(ROOT)


def test_guard_still_runs_under_python_optimized_mode(tmp_path):
    folder=tmp_path/'reports/audits';folder.mkdir(parents=True)
    (folder/'TV6_Input_Inventory.json').write_text(json.dumps(dict(passed=False,test_performance_evaluated=False)))
    code='''import sys
from backend.audit.tv6_protocol import build_protocol
try:
    build_protocol(sys.argv[1])
except ValueError:
    sys.exit(0)
sys.exit(2)
'''
    result=subprocess.run([sys.executable,'-O','-c',code,str(tmp_path)],cwd=ROOT,capture_output=True,text=True)
    assert result.returncode==0,result.stderr


def test_registry_missing_rejected(monkeypatch):
    original=Path.is_file;missing=ROOT/REGISTRY_PATH
    monkeypatch.setattr(Path,'is_file',lambda self:False if self==missing else original(self))
    with pytest.raises(ValueError,match='registry'):validate_protocol(read(),ROOT)


def test_registry_mismatch_rejected(monkeypatch):
    original=Path.read_text;path=ROOT/REGISTRY_PATH
    def altered(self,*args,**kwargs):
        if self==path:
            value=json.loads(original(self,*args,**kwargs));value['protocol_file_sha256']='0'*64
            return json.dumps(value)
        return original(self,*args,**kwargs)
    monkeypatch.setattr(Path,'read_text',altered)
    with pytest.raises(ValueError,match='registered'):validate_protocol(read(),ROOT)


def test_removed_registered_lock_not_silently_recreated(tmp_path):
    script=tmp_path/'scripts/lock_tv6_protocol.py';script.parent.mkdir()
    script.write_bytes((ROOT/'scripts/lock_tv6_protocol.py').read_bytes())
    registry=tmp_path/REGISTRY_PATH;registry.parent.mkdir(parents=True)
    registry.write_bytes((ROOT/REGISTRY_PATH).read_bytes())
    code='import runpy,sys; script=sys.argv[1]; sys.argv=[script]; runpy.run_path(script,run_name="__main__")'
    result=subprocess.run([sys.executable,'-c',code,str(script)],cwd=ROOT,capture_output=True,text=True)
    assert result.returncode!=0 and 'refusing silent recreation' in result.stderr
    assert not (registry.parent/'tv6_evaluation_protocol_v1.json').exists()


@pytest.mark.parametrize('bad',[[],{'format_version':1,'test_performance_evaluated_at_lock':False}])
def test_malformed_protocol_rejected(bad):
    with pytest.raises(ValueError):validate_protocol(bad,ROOT)


def test_missing_lock_and_registry_with_history_rejected(tmp_path):
    script=tmp_path/'scripts/lock_tv6_protocol.py';script.parent.mkdir()
    script.write_bytes((ROOT/'scripts/lock_tv6_protocol.py').read_bytes())
    history=tmp_path/'logs/audit/tv6_item2_fixture';history.mkdir(parents=True)
    (history/'summary.json').write_text(json.dumps(dict(passed=True,protocol='experiments/configs/tv6_evaluation_protocol_v1.json')))
    code='import runpy,sys; script=sys.argv[1]; sys.argv=[script]; runpy.run_path(script,run_name="__main__")'
    result=subprocess.run([sys.executable,'-c',code,str(script)],cwd=ROOT,capture_output=True,text=True)
    assert result.returncode!=0 and 'Historical lock receipt exists' in result.stderr


def test_prior_receipt_corruption_rejected(monkeypatch):
    registry=json.loads((ROOT/REGISTRY_PATH).read_text())
    path=ROOT/registry['prior_receipt']['path'];original=Path.read_bytes
    monkeypatch.setattr(Path,'read_bytes',lambda self:b'changed' if self==path else original(self))
    with pytest.raises(ValueError,match='prior receipt'):validate_protocol(read(),ROOT)
