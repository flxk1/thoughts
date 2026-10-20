# Reproduction kit outputs for Loomground Paper I

Everything in this directory is produced by `../reproduce.sh {historical|current} WORKDIR`,
which clones the five `flxk1` repositories fresh, checks out the pinned
full commit hashes below (detached), builds a venv from
`../requirements.lock`, and runs every experiment listed in
`MANIFEST.json`. See `MANIFEST.json` for the exact script/args/output
mapping used for every paper table or claim; this file is a human-readable
summary of the same thing and must not describe anything the manifest
does not.

Timestamps and absolute scratch paths inside the `.out` files differ
between reruns (the standard-root path printed by `verify.py`, and the
`WORKDIR` path embedded in some tool output); everything else is
byte-identical across reruns at the same pins.

## Pins

| State | loomground | loomground-governance | loomground-ref | loomground-solver | loomground-deontic |
| --- | --- | --- | --- | --- | --- |
| historical | `cf221b4` | `408554b` | `586696c` | `f43dfd6` | `ead0ad2` |
| current | `13fc82c` (v0.11.1) | `7f04e1c` (v0.11.2) | `7baee93` | `2eb09a4` | `ead0ad2` |

Full 40-character hashes are in `MANIFEST.json` and are printed by
`reproduce.sh` on every run.

## Layout

- `current/` — outputs at the current (fixed) pins.
- `historical/` — outputs at the historical (audited, pre-fix) pins,
  including the reproduced F1/F2/F3 failures.
- `historical/probes-old-format-pre-rewrite.out` — the pre-2026-09-26
  eleven-probe output in its old condensed-string format, kept for
  reference; it predates the structured-observation rewrite of
  `run_experiments.py` and is not otherwise part of the manifest.
- `MANIFEST.json` — the table/claim -> script/args/pins/output mapping.
- `kit-mock-evaluators.py`, `differential.py` — the two extra probe
  scripts referenced by the manifest (not part of `run_experiments.py`).

## What each file shows

| File (in `current/` and `historical/`) | Command | Current result | Historical result |
| --- | --- | --- | --- |
| `ref-verify.out` | `loomground-ref/tools/verify.py <loomground>` | 69/69 | 65/65 |
| `ref-verify-governance.out` | `loomground-ref/tools/verify.py <loomground-governance>/standard` | 69/69 | 65/65 |
| `ref-machine-readable.out` | `loomground-ref/tests/test_machine_readable.py` | 49/49 | 49/49 |
| `solver-conformance.out` | `loomground-solver/tools/run_loomground_conformance.py` | 69/69 | 65/65 |
| `probes.out` | `run_experiments.py --series H` (Table 3) | 11/11 agree | 11/11 agree |
| `probes-E.out` | `run_experiments.py --series E` (invalid-token / F1) | 7/7 agree | 4/7 agree (F1 reproduced) |
| `probes-P.out` | `run_experiments.py --series P` (composition / F2, F3) | 4/4 agree | 1/4 agree (F2, F3 reproduced) |
| `kit-mock-evaluators.out` | `audit/kit-mock-evaluators.py` | stub scores 4/69, 27/69 | stub scores 4/65, 27/65 |
| `differential.out` | `audit/differential.py 6000 1` | 0/6000 disagree | 1908/6000 disagree |

The eleven Table-3 (H-series) probes agree at both pin sets: none of
them exercises an invalid token or a piped/fan-out gate, so they do not
surface F1-F3. The E-series and P-series probes are the ones that do; at
the historical pins they show the ref and solver actively disagreeing
with each other and with the spec-expected outcome (`ref matches
spec-expected: False`, `solver matches expected: False` in the probe
output), not merely both passing a coverage-only check.

## Known discrepancy against the 2026-09-26 adjudication

Probe `E3c id missing, risk=high` (adjudication id `F1/missing-id`)
reproduces at the historical pins as `ref == solver == reserved/withhold`,
not the solver `auto/act` recorded in
`work/codex-review/adjudication.json`. Both observations still show an
invalid token being evaluated instead of rejected (the defect class F1),
but the specific verdict differs from the adjudicated record. This is
reported here rather than smoothed over; see `MANIFEST.json`'s
`note_on_matching_adjudication`. Every other E-series and P-series
probe reproduces the adjudicated `historical_failures` entries exactly.

## Table-3 selection rule

Stated in `run_experiments.py`'s module docstring: a probe belongs to
Table 3 (the H-series) iff it exercises exactly one of reservation
triggering, grade/risk amplification through on-behalf-of (including its
degenerate cycle/attenuation cases), or a priority/override interaction
among prohibit, an ungranted actor, two activations at one gate, and an
agent acting as its own master. Each H-probe is minimal: removing any
policy line changes which rule fires.
