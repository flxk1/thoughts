# Measurement at the published pins (audit/published)

Outputs in this directory were produced on 2026-10-10 against fresh clones of the
published repositories from https://github.com/flxk1 (blob-filtered or shallow
clones under `/Users/rafelixkrone/work/worktrees/paper-pins/`). They supersede
`../next/` (anticipated `session/govfix` commits) for the paper; `../current/`
and `../next/` are left untouched. Every output is identical to `../next/`
apart from the commit line in `vector-counts.out`.

## Pins

Full hashes and notes are in `pins.txt`.

| Repo | Commit | Reference |
| --- | --- | --- |
| loomground | `081f1cf` | tag `v0.11.2` |
| loomground-governance | `648cb89` | tag `loomground-governance-v0.12.0` |
| loomground-ref | `2417fee` | `main` |
| loomground-solver | `fc7f0f4` | `main` |
| loomground-deontic | `319e218` | tag `loomground-deontic-v0.2.1` (solver `pyproject.toml`) |

## Environment

One venv, `~/work/.venvs/paper-pins` (Python 3.14.2), with non-editable installs
of `./loomground-governance` (0.12.0) and `./loomground-deontic` (0.2.1) from the
clones, plus `jsonschema` 4.26.0 and `pytest` 9.1.1. The solver and ref are used
from source via `PYTHONPATH`.

## Commands

```
cd /Users/rafelixkrone/work/worktrees/paper-pins
git clone -q --filter=blob:none https://github.com/flxk1/loomground && git -C loomground checkout -q v0.11.2
git clone -q --filter=blob:none https://github.com/flxk1/loomground-governance && git -C loomground-governance checkout -q loomground-governance-v0.12.0
git clone -q --depth 1 https://github.com/flxk1/loomground-ref        # main = 2417fee
git clone -q --depth 1 https://github.com/flxk1/loomground-solver     # main = fc7f0f4
git clone -q --filter=blob:none https://github.com/flxk1/loomground-deontic && git -C loomground-deontic checkout -q 319e218
python3 -m venv ~/work/.venvs/paper-pins
~/work/.venvs/paper-pins/bin/python -m pip install ./loomground-governance ./loomground-deontic jsonschema pytest

W=/Users/rafelixkrone/work/worktrees/paper-pins
K=/Users/rafelixkrone/work/loomground-paper-I; P=$K/audit/published
V=~/work/.venvs/paper-pins/bin/python

python3 $P/count_vectors.py $W/loomground 081f1cf                         > vector-counts.out
cd $W/loomground && $V tests/lockstep_meta_test.py                        > lockstep-meta.out
cd $W/loomground-ref
$V tools/verify.py $W/loomground                                          > ref-verify.out
$V tools/verify.py $W/loomground-governance/standard                      > ref-verify-governance.out
LOOMGROUND_ROOT=$W/loomground $V tests/test_machine_readable.py           > ref-machine-readable.out
LOOMGROUND_ROOT=$W/loomground $V tests/test_stub_rejection.py             > ref-stub-rejection.out
cd $W/loomground-solver
PYTHONPATH=src $V tools/run_loomground_conformance.py                     > solver-conformance.out
cd $P/solver-ref-adapter
for root in $W/loomground $W/loomground-governance/standard; do
  LOOMGROUND_REF=$W/loomground-ref PYTHONPATH=$P/solver-ref-adapter:$W/loomground-solver/src \
    $V run_ref_verify.py $root; echo "exit $?"
done                                                                      > solver-ref-verify.out
cd $K
$V $P/kit-bundled-engine.py $W/loomground-governance                      > kit-bundled-engine.out
$V audit/kit-mock-evaluators.py                                           > kit-mock-evaluators.out
export PYTHONPATH=$W/loomground-ref:$W/loomground-solver/src
$V run_experiments.py --series H                                          > probes.out
$V run_experiments.py --series E                                          > probes-E.out
$V run_experiments.py --series P                                          > probes-P.out
$V audit/differential.py 6000 1                                           > differential.out
unset PYTHONPATH
python3 ground_quotes.py $W/loomground $W/loomground-ref paper-I.md       > ground-quotes.out
```

Each `.out` ends with its exit status (stderr included). `count_vectors.py`,
`kit-bundled-engine.py` and `solver-ref-adapter/` are copied unchanged from
`../next/`; the adapter translates the solver's API for
`loomground-ref/tools/verify.py` and holds no language logic.

## Results

| What | File | Result |
| --- | --- | --- |
| Vectors (manifest 0.11.2) | `vector-counts.out` | 75: 40 patch (27 with run), 31 negative (27 apply, 4 parse; 20 reason codes), 2 token, 2 determinism |
| lockstep meta test | `lockstep-meta.out` | ALL GREEN |
| ref verify, loomground | `ref-verify.out` | 75/75 |
| ref verify, governance/standard | `ref-verify-governance.out` | 75/75 |
| ref machine-readable | `ref-machine-readable.out` | 49/49 |
| ref stub tests | `ref-stub-rejection.out` | 9 stubs, 5–71 of 75; real implementation 75/75 |
| solver through the kit (governance 0.12.0) | `solver-conformance.out` | 75/75 |
| solver through ref verify.py | `solver-ref-verify.out` | 75/75 on both roots |
| kit bundled engine | `kit-bundled-engine.out` | 75/75 |
| kit stubs (raise always; reject every patch at apply) | `kit-mock-evaluators.out` | 0/75, 0/75 |
| H probes (Table 3) | `probes.out` | 11/11 agree |
| E probes | `probes-E.out` | 7/7 |
| P probes | `probes-P.out` | 4/4 |
| differential fuzz | `differential.out` | 0/6000 disagree |
| quote grounding | `ground-quotes.out` | 9/9 paper=True |
