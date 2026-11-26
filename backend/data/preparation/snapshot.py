"""Read-only TV1 snapshot acceptance for TV2; never clean or rewrite artifacts."""

from pathlib import Path
import re

import pandas as pd

from backend.data.validation.standard_output import inspect_standard_output
from backend.data.validation.validator import compute_sha256, inspect_raw_dataframe


def load_tv1_snapshot(project_root, dataset_version):
    """Return {data, dataset_version, acceptance, quality, paths} or fail closed.

    Requires raw/metadata/validated/validation report/quality audit for an explicit
    version. Reuses TV1 integrity, provenance, schema and fresh calendar checks.
    `data` retains all four model columns, in source order; no scaling/splitting.
    Integrity is local consistency, not independent Yahoo source authentication.
    """
    if not isinstance(dataset_version, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", dataset_version):
        raise ValueError("An explicit safe dataset_version is required.")
    root = Path(project_root).resolve()
    version = dataset_version
    paths = {
        "raw": root / f"data/raw/aapl_raw_{version}.csv",
        "metadata": root / f"data/metadata/aapl_metadata_{version}.json",
        "validated": root / f"data/validated/aapl_validated_{version}.csv",
        "validation_report": root / f"data/metadata/aapl_validation_report_{version}.json",
        "quality_audit": root / f"data/metadata/aapl_quality_audit_{version}.json",
    }
    for path in paths.values():
        if not path.is_file():
            raise FileNotFoundError(f"Missing TV1 artifact: {path}")
    acceptance = inspect_standard_output(*paths.values(), dataset_version, root)
    if not acceptance["passed"]:
        raise ValueError("TV1 snapshot rejected: " + ", ".join(acceptance["errors"]))
    quality, _ = inspect_raw_dataframe(pd.read_csv(paths["raw"]), dataset_version)
    if not quality["passed"]:
        raise ValueError("TV1 fresh quality check rejected: " + "; ".join(quality["errors"]))
    frame = pd.read_csv(paths["validated"])
    # Detect source changes during acceptance; never use a re-read silently.
    for key, path in paths.items():
        if compute_sha256(path) != acceptance["hashes"][key]:
            raise ValueError(f"TV1 artifact changed during acceptance: {key}")
    return {"data": frame, "dataset_version": version, "acceptance": acceptance,
            "quality": quality, "paths": {k: str(v) for k, v in paths.items()}}
