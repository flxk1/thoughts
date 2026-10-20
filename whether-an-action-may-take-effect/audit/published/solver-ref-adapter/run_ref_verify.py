#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Run loomground-ref's tools/verify.py against THIS package's evaluator,
via tools/verify_ref_adapter.py (see its docstring for why the adapter is
needed: verify.py is written against ref's own flat module shape, not the
neutral LoomgroundImplementation protocol).

Usage:
    LOOMGROUND_REF=/path/to/loomground-ref \\
    python3 tools/run_ref_verify.py STANDARD_ROOT

STANDARD_ROOT is the directory holding conformance/manifest.json (e.g. the
loomground-governance package's standard/ directory). $LOOMGROUND_REF must
point at a loomground-ref checkout (tools/verify.py); this script never
assumes its location, since loomground-ref is a sibling repo, not a
dependency of this package.
"""
from __future__ import annotations

import importlib.util
import os
import runpy
import sys


def main() -> int:
    ref_root = os.environ.get("LOOMGROUND_REF")
    if not ref_root:
        print("set $LOOMGROUND_REF to a loomground-ref checkout", file=sys.stderr)
        return 2
    verify_path = os.path.join(ref_root, "tools", "verify.py")
    if not os.path.isfile(verify_path):
        print(f"no tools/verify.py under $LOOMGROUND_REF={ref_root!r}", file=sys.stderr)
        return 2
    if len(sys.argv) < 2:
        print("usage: run_ref_verify.py STANDARD_ROOT", file=sys.stderr)
        return 2
    standard_root = sys.argv[1]

    adapter_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "verify_ref_adapter.py")
    spec = importlib.util.spec_from_file_location("loomground", adapter_path)
    adapter = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(adapter)
    # Installed BEFORE verify.py runs, so its `import loomground as L`
    # resolves to this adapter (backed by the solver) instead of re-deriving
    # ref's own flat module from sys.path.
    sys.modules["loomground"] = adapter

    sys.argv = ["verify.py", standard_root]
    try:
        runpy.run_path(verify_path, run_name="__main__")
    except SystemExit as exc:
        return int(exc.code or 0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
