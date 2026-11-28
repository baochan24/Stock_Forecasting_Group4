"""Disposable payloads test handoff integrity and receipt preservation."""
import hashlib,json
import pytest
from scripts.verify_tv6_web_handoff import verify_payload,save_result


def payload(tmp_path):
    path=tmp_path/'frontend/index.html';path.parent.mkdir();path.write_text('<title>AAPL</title>')
    return {'files_sha256':{'frontend/index.html':hashlib.sha256(path.read_bytes()).hexdigest()}}


def test_payload_accepts_correct_files_and_rejects_tampering(tmp_path):
    receipt=payload(tmp_path);verify_payload(tmp_path,receipt)
    (tmp_path/'frontend/index.html').write_text('changed')
    with pytest.raises(ValueError,match='checksum mismatch'):verify_payload(tmp_path,receipt)


def test_payload_requires_every_member(tmp_path):
    receipt=payload(tmp_path);receipt['files_sha256']['missing.bin']='0'*64
    with pytest.raises(ValueError,match='Missing'):verify_payload(tmp_path,receipt)


@pytest.mark.parametrize('name',['../outside','a/../../outside','C:/outside','/absolute','a\\outside'])
def test_payload_rejects_unsafe_paths(tmp_path,name):
    with pytest.raises(ValueError,match='Unsafe'):verify_payload(tmp_path,{'files_sha256':{name:'0'*64}})


@pytest.mark.parametrize('receipt',[{}, {'files_sha256':{}},{'files_sha256':{'x':'bad'}}])
def test_invalid_manifest_is_not_reported_verified(tmp_path,receipt):
    with pytest.raises(ValueError):verify_payload(tmp_path,receipt)


def test_receipt_is_utf8_and_cannot_replace_old_evidence(tmp_path):
    path=tmp_path/'acceptance.json';first={'passed':True,'reviewer_supplied':'Thành viên'}
    save_result(path,first)
    assert json.loads(path.read_text(encoding='utf-8'))==first
    with pytest.raises(FileExistsError):save_result(path,{'passed':False})
    assert json.loads(path.read_text(encoding='utf-8'))==first
