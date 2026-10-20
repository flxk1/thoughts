#!/bin/bash
# reproduce.sh — Loomground Paper I reproduction kit.
#
# Runs on macOS default bash 3.2 and on Linux bash (POSIX-ish; no
# bash-4-only associative-array syntax, no process substitution, no
# lower-casing parameter expansion).
#
# Usage:
#   bash reproduce.sh STATE WORKDIR
#     STATE   = historical | current
#     WORKDIR = a directory to clone repos and build a venv in
#               (must live under a scratch tree; never point this at
#               an existing checkout)
#
# What it does:
#   1. Clones the five flxk1 repos fresh into WORKDIR/repos/<state>/.
#   2. Does a detached checkout of the pinned FULL commit hash for each
#      repo (loomground-deontic is pinned to the same commit in both
#      states).
#   3. Prints the five resolved full 40-char hashes.
#   4. Creates a venv at WORKDIR/venv-<state>/ and installs from
#      requirements.lock.
#   5. Runs every experiment for that state, writing outputs into
#      audit/<state>/ under this script's own directory (NOT under
#      WORKDIR).
#
# Never modifies an existing checkout; never pushes or publishes
# anything.

set -eu

STATE="${1:-}"
WORKDIR="${2:-}"

if [ "$STATE" != "historical" ] && [ "$STATE" != "current" ]; then
  echo "usage: bash reproduce.sh historical|current WORKDIR" >&2
  exit 2
fi
if [ -z "$WORKDIR" ]; then
  echo "usage: bash reproduce.sh historical|current WORKDIR" >&2
  exit 2
fi

# Resolve this script's own directory (kit root) in a bash-3.2-safe way.
KIT_ROOT="$(cd "$(dirname "$0")" && pwd)"
AUDIT_DIR="$KIT_ROOT/audit/$STATE"
mkdir -p "$AUDIT_DIR"
mkdir -p "$WORKDIR"
WORKDIR="$(cd "$WORKDIR" && pwd)"

REPO_DIR="$WORKDIR/repos/$STATE"
VENV_DIR="$WORKDIR/venv-$STATE"
mkdir -p "$REPO_DIR"

# Pins — one variable per repo per state (bash-3.2 safe: no assoc arrays).
if [ "$STATE" = "historical" ]; then
  PIN_LOOMGROUND="081f1cfccf3724db657428e52d09677c1132e569"
  PIN_GOVERNANCE="648cb89ea2bc318b3b666525f807c508c4e03a82"
  PIN_REF="2417fee0dd596d31f8a3f1495b8d3282a1878ca7"
  PIN_SOLVER="fc7f0f46e3cad33c1510f28ca98c7c3586ba3553"
  PIN_DEONTIC="319e218500da42dea693830ff790343aa340bd60"
else
  PIN_LOOMGROUND="13fc82c9c48c007e98f3eeaf54df499768c2e75d"
  PIN_GOVERNANCE="7f04e1c67694ef3eca995d51a61eabecec4cba7c"
  PIN_REF="7baee937befa4ff8372b2b5a412b719a1a2efc50"
  PIN_SOLVER="2eb09a4e650668e674e70821b59caa4b1e7dd067"
  PIN_DEONTIC="ead0ad28a133a9d37f3dbec8e890b6e32b3b7048"
fi

clone_and_pin () {
  # $1 = repo name (under github.com/flxk1), $2 = full pinned hash
  name="$1"
  hash="$2"
  dest="$REPO_DIR/$name"
  if [ ! -d "$dest" ]; then
    git clone -q "https://github.com/flxk1/$name.git" "$dest"
  fi
  git -C "$dest" fetch -q origin "$hash" || true
  git -C "$dest" checkout -q --detach "$hash"
  resolved="$(git -C "$dest" rev-parse HEAD)"
  if [ "$resolved" != "$hash" ]; then
    echo "PIN MISMATCH for $name: expected $hash, got $resolved" >&2
    exit 1
  fi
  echo "$name $resolved"
}

echo "== resolved pins ($STATE) =="
clone_and_pin loomground "$PIN_LOOMGROUND"
clone_and_pin loomground-governance "$PIN_GOVERNANCE"
clone_and_pin loomground-ref "$PIN_REF"
clone_and_pin loomground-solver "$PIN_SOLVER"
clone_and_pin loomground-deontic "$PIN_DEONTIC"
echo "============================"

# --- venv ---
if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi
PY="$VENV_DIR/bin/python3"
"$PY" -m pip install -q --upgrade pip
"$PY" -m pip install -q -r "$KIT_ROOT/requirements.lock"
# Install governance and deontic from the pinned local checkouts FIRST,
# then solver with --no-deps: loomground-solver's own pyproject.toml
# pulls governance/deontic from tag-pinned git URLs, which would silently
# fetch a different commit than the one this script just checked out.
"$PY" -m pip install -q -e "$REPO_DIR/loomground-governance"
"$PY" -m pip install -q -e "$REPO_DIR/loomground-deontic"
"$PY" -m pip install -q --no-deps -e "$REPO_DIR/loomground-solver"

REF_PY="$REPO_DIR/loomground-ref"
GOV_STD="$REPO_DIR/loomground-governance/standard"
LG_ROOT="$REPO_DIR/loomground"
PYTHONPATH_ALL="$REF_PY:$REPO_DIR/loomground-solver/src"

run () {
  # $1 = output file (relative to AUDIT_DIR), remaining = command
  out="$AUDIT_DIR/$1"
  shift
  echo "-- running: $* > $out"
  ( PYTHONPATH="$PYTHONPATH_ALL" "$PY" "$@" ) > "$out" 2>&1 || {
    echo "(nonzero exit recorded in $out)" >> "$out"
  }
}

echo "== running experiments into $AUDIT_DIR =="

run ref-verify.out "$REF_PY/tools/verify.py" "$LG_ROOT"
run ref-verify-governance.out "$REF_PY/tools/verify.py" "$GOV_STD"
run ref-machine-readable.out "$REF_PY/tests/test_machine_readable.py"
run ref-stub-rejection.out "$REF_PY/tests/test_stub_rejection.py" "$LG_ROOT"
# the semantic-mutant battery (paper §6.3) lives at a later loomground-ref commit than the
# historical pin; a detached worktree at that commit runs it against the same standard
REF_MUT_COMMIT=0bd1e7e6d5ef1fc5cb3f5e8f187920f0d11bbf9d
REF_MUT="$REPO_DIR/loomground-ref-mutants"
if [ ! -d "$REF_MUT" ]; then
  git -C "$REF_PY" worktree add -q --detach "$REF_MUT" "$REF_MUT_COMMIT"
fi
run ref-semantic-mutants.out "$REF_MUT/tests/test_semantic_mutants.py" "$LG_ROOT"
run solver-conformance.out "$REPO_DIR/loomground-solver/tools/run_loomground_conformance.py"
run probes.out "$KIT_ROOT/run_experiments.py" --series H
run probes-E.out "$KIT_ROOT/run_experiments.py" --series E
run probes-P.out "$KIT_ROOT/run_experiments.py" --series P
run kit-mock-evaluators.out "$KIT_ROOT/audit/kit-mock-evaluators.py"
run differential.out "$KIT_ROOT/audit/differential.py" 6000 1

echo "== done: $STATE =="
