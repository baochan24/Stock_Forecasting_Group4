# Audit TV1 / TV2 — 2026-11-19

## Scope and verdict

Read all five open PRs against team assignment and data flow contract. No PR was merged, modified or commented on GitHub. Review copies and a diagnostic runner are stored alongside this report. Existing staged workspace changes were preserved.

Verdict: TV1 PR5 is substantially implemented but needs fixes and verifiable artifact handoff; TV2 PR2/3 is not integration-ready. This is a review of the data deliverables, not acceptance of the entire project.

Reviewed PR heads:
- #1 c2c0b19ea64e20bc55804c88c80a2f9ba54af3b2
- #2 245dc5c366e3d81d2dfc2f1c2df18f3ce1e9444f
- #3 d52946b85a390d8af8d01c5ad7a7903a16ec8485
- #4 2d0739d741b424f8491ac25897890cb62e76c164
- #5 08675d823bd2499df1508dc4b4cde8722d557629

## Findings

1. P1: PR2 and PR3 add Python text to README.md, not importable modules. PR1 and PR4 have the same packaging issue. PR5 supplies real downloader/validator modules but does not supply TV2 modules. Dependencies and reproducible installation instructions are absent from these changes.
2. P1: PR2 create_windows has an unindented input_scaled assignment followed by an indented statement, causing IndentationError. Confirmed with compile of the added Python text. This fails even if copied into a .py file.
3. P1: PR2 splits prices first and windows each split independently. This drops the first 30 validation/test targets despite available preceding history. Split membership should be determined by target dates; all five targets must share a split, while inputs may use preceding known history. On a synthetic 260-session validation year, current code after an in-memory indentation repair gives 230 one-step / 226 five-step samples, versus 260 / 256 with historical context. Based on the report's unverified 2014/250/502 session counts, intended counts would be 1984/250/502 for one-step and 1980/246/498 for five-step.
4. P1: PR5 inspect_raw_dataframe only bounds dates and counts split rows. It accepts a three-row 2015-only dataset, a Saturday date, and a dataset missing a middle session as passed=True. It cannot substantiate the report claim of complete trading-calendar coverage. Add an agreed exchange-session calendar audit with explicit missing/unexpected sessions and whole-period coverage evidence.
5. P1: Exact raw/validated snapshots and metadata/reports are not in the PR and no actionable shared artifact location is provided. This is compatible with excluding generated data from Git, but incomplete as a handoff. Re-downloading retrospectively adjusted prices is not guaranteed to reproduce the recorded hashes. The report's real-data numbers/hashes remain unverified here.
6. P2: PR2 samples lack dataset_version, per-sample lookback/forecast_length, and explicit horizon_step. Inputs and targets are bundled together rather than exposing a target-free inference contract. sample_id depends only on split and index, causing collisions across dataset versions/horizons. There is no saved scaler, fit provenance, prepared-data manifest, sample-count audit, or reload demonstration.
7. P2: PR5 downloader overwrites raw CSV and metadata when invoked again with the same default dataset_version. This permits different retrospectively adjusted data under the same version. Refuse replacement or use a new immutable snapshot identity.
8. P2: PR5 validator trusts metadata ticker, uses the caller dataset_version without matching metadata identity, and does not bind source/currency/adjustment policy to the validated artifact. A consistent byte hash alone cannot establish these semantic properties. Add explicit AAPL/USD/version/policy checks before accepting a dataset.
9. P2: PR4's older validator accepts positive infinity, removes bad rows without preserving original evidence in a persistent report, and indexes iloc[0]/iloc[-1] after all rows are removed. It should not be merged alongside PR5 as the supported implementation.
10. P2: PR5 tests cover only valid schema, duplicate dates and negative price with synthetic data. The test named missing_or_non_positive does not test NaN. No supplied tests exercise Inf, malformed dates, missing columns, out-of-range dates, calendar completeness, tampered hash rejection, metadata mismatch, or the downloader. Its real-artifact test requires local generated files and fails on this checkout.

## Positive findings

PR5 explicitly requests auto_adjust=False, selects Adj Close, uses an exclusive 2026-01-01 upper bound, records UTC/version/currency/retrospective-price limitation and SHA-256, verifies raw hash, rejects duplicate/order/invalid-price issues without silently repairing them, and creates the contracted four-column validated table. PR2 fits StandardScaler on supplied train values and applies transform to windows; PR3 transforms/inverts without refitting and preserves array shape. These are useful foundations but do not resolve the findings above.

## Validation performed

Python 3.13.7, NumPy 2.4.4, pandas 3.0.6, scikit-learn 1.9.1. Run from repository root:

    python reports/audits/pr_review_2026_11_19/check_review.py

Results: PR2 IndentationError reproduced; three calendar/coverage counterexamples accepted by PR5 reproduced; validation-window loss reproduced after syntax repair in memory; PR5 original tests: 3 passed, 1 failed because raw CSV is absent. The runner prints the unittest outcome; its process exit code does not encode suite failure. No real Yahoo download was performed. The reported 4/4 real-data test success cannot be independently confirmed here. Check-runs endpoint returned zero checks for reviewed PR2/3/5 heads.

## Acceptance checklist

- TV1: calendar/coverage validation; immutable versioned snapshot; semantic metadata checks; artifact download location with exact hashes; reproducible dependency installation and commands; boundary/negative tests and real-data evidence.
- TV2: real .py modules; fix syntax; target-date splitting with previous history; separate input/target contract and stable identifiers; scaler serialization/provenance; prepared manifest and counts; hand-checked 1/5-step examples; leakage, boundary and inverse/reload tests; update implementation/data report and run guide.
- Integration: run TV1 -> TV2 from a clean environment using the handed-off snapshot, verify dates/versions/hashes/sample counts, publish a compact audit result before approving data handoff to TV3-TV6.

PR links: https://github.com/baochan24/Stock_Forecasting_Group4/pull/1 through /pull/5. Prefer PR5 as the TV1 implementation baseline and consolidate/close obsolete PR1/4 only after the owner confirms supersession. This audit does not perform that action.
