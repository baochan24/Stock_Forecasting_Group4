"""Store/load TV2 batches as separate input/target JSON and non-pickle NPZ."""
import json
from pathlib import Path
import re
import numpy as np
from backend.data.validation.validator import compute_sha256


def _json_value(value):
    if isinstance(value,np.ndarray): return value.tolist()
    if isinstance(value,np.generic): return value.item()
    raise TypeError(f"Unsupported JSON value: {type(value)}")


def _safe_id(value):
    if not isinstance(value,str) or not re.fullmatch(r"[A-Za-z0-9_-]+",value):
        raise ValueError("Unsafe artifact ID")


def save_prepared_modes(results, output_root, prepared_id, scaler_id, source_hashes):
    """Create once, write manifest last; incomplete folders are not loadable.

    Caller validates contracts/coverage before saving. Arrays remain float64;
    no object arrays, executable pickle, fit or model code is persisted.
    """
    _safe_id(prepared_id)
    _safe_id(scaler_id)
    if set(results) != {1,5}: raise ValueError("Both modes are required")
    lookbacks = {r["lookback"] for r in results.values()}
    if len(lookbacks) != 1 or next(iter(lookbacks)) not in (10,30,60): raise ValueError("Invalid lookback")
    lookback = next(iter(lookbacks))
    versions = {result["dataset_version"] for result in results.values()}
    if len(versions) != 1: raise ValueError("Mixed dataset versions")
    folder = Path(output_root)/prepared_id
    folder.mkdir(parents=True,exist_ok=False)
    payloads, modes = {},{}
    for h,result in results.items():
        if result["forecast_length"] != h or result["lookback"] != lookback: raise ValueError("Mode mismatch")
        modes[str(h)] = {}
        for split,batch in result["splits"].items():
            if split not in ("train","val","test"): raise ValueError("Unknown split")
            prefix = f"f{h}_{split}"
            npz = prefix+".npz"
            with (folder/npz).open("xb") as stream:
                np.savez_compressed(stream,X=batch["X"],y=batch["y"],target_indices=batch["target_indices"])
            payloads[npz] = compute_sha256(folder/npz)
            for field in ["inputs","targets"]:
                name = prefix+f"_{field}.json"
                with (folder/name).open("x",encoding="utf-8") as stream:
                    json.dump(batch[field],stream,default=_json_value,allow_nan=False,separators=(",",":"))
                payloads[name] = compute_sha256(folder/name)
            modes[str(h)][split] = {k:batch[k] for k in ["num_samples","excluded_insufficient_history","excluded_cross_split_targets","excluded_incomplete_targets"]}
    manifest = {"format_version":1,"prepared_id":prepared_id,"dataset_version":versions.pop(),
                "scaler_id":scaler_id,"source_hashes":source_hashes,"lookback":lookback,"dtype":"float64",
                "modes":modes,"files":payloads}
    with (folder/"manifest.json").open("x",encoding="utf-8") as stream:
        json.dump(manifest,stream,indent=2,allow_nan=False)
    return folder


def load_prepared_modes(folder, *, expected_dataset_version, expected_source_hashes, expected_scaler_id, expected_lookback=30):
    """Verify payload hashes and exact member names, load arrays without pickle.

    Caller must then run contract/coverage checks against accepted TV1/scaler.
    Checksums guarantee local consistency, not authenticity of a rewritten manifest.
    """
    folder = Path(folder)
    manifest = json.loads((folder/"manifest.json").read_text(encoding="utf-8"))
    if (manifest.get("format_version") != 1 or manifest.get("prepared_id") != folder.name
            or manifest.get("dataset_version") != expected_dataset_version or manifest.get("source_hashes") != expected_source_hashes
            or manifest.get("scaler_id") != expected_scaler_id or manifest.get("lookback") != expected_lookback or manifest.get("dtype") != "float64"):
        raise ValueError("Prepared identity/version/hash mismatch")
    names = {f"f{h}_{s}{suffix}" for h in [1,5] for s in ["train","val","test"] for suffix in [".npz","_inputs.json","_targets.json"]}
    if set(manifest.get("files",{})) != names or set(manifest.get("modes",{})) != {"1","5"}:
        raise ValueError("Wrong prepared file/mode list")
    for name in names:
        if compute_sha256(folder/name) != manifest["files"][name]: raise ValueError(f"Prepared checksum mismatch: {name}")
    lookback = expected_lookback
    results = {}
    for h in [1,5]:
        if set(manifest["modes"][str(h)]) != {"train","val","test"}: raise ValueError("Wrong split list")
        splits = {}
        for split in ["train","val","test"]:
            prefix = f"f{h}_{split}"
            with np.load(folder/(prefix+".npz"),allow_pickle=False) as arrays:
                if set(arrays.files) != {"X","y","target_indices"}: raise ValueError("Wrong NPZ schema")
                batch = {k:arrays[k].copy() for k in arrays.files}
            batch.update(manifest["modes"][str(h)][split])
            for field in ["inputs","targets"]:
                batch[field] = json.loads((folder/(prefix+f"_{field}.json")).read_text(encoding="utf-8"))
                key = "input_values" if field == "inputs" else "target_values"
                for record in batch[field]: record[key] = np.asarray(record[key],dtype=np.float64)
            splits[split] = batch
        results[h] = {"dataset_version":expected_dataset_version,"lookback":lookback,"forecast_length":h,"splits":splits}
    return results,manifest
