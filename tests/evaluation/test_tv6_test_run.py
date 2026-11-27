import json
import pytest
from backend.audit.tv6_test_run import validate_test_run


def test_execution_lifecycle(tmp_path):
    path=tmp_path/'logs/audit/tv6_item5_fixture/execution.json'
    path.parent.mkdir(parents=True)
    value=dict(status='running',protocol_sha256='abc',authorization='User requested TV6 item5',run_id=path.parent.name)
    path.write_text(json.dumps(value))
    assert validate_test_run(tmp_path,path,'abc')==value
    with pytest.raises(ValueError):validate_test_run(tmp_path,path,'wrong')
    value['status']='completed';path.write_text(json.dumps(value))
    with pytest.raises(ValueError):validate_test_run(tmp_path,path,'abc')


def test_arbitrary_path_rejected(tmp_path):
    with pytest.raises(ValueError):validate_test_run(tmp_path,tmp_path/'execution.json','abc')
