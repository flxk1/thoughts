#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""A thin adapter so loomground-ref's tools/verify.py — written to drive its
own flat `loomground.py` module (Patch objects, a `Reject(stage, reason,
message)` exception, `check()`, and `evaluate(patch, activations) -> (res,
log)`) — can instead drive THIS package's evaluator
(src/loomground_solver/loomground.py), which exposes the neutral
`LoomgroundImplementation` protocol shape instead (`validate()` returning a
report dict, `evaluate(patch, transport)` returning just the result dict).

verify.py never imports this module by name; a runner (see
run_ref_verify.py, same directory) installs it into ``sys.modules["loomground"]``
BEFORE verify.py's own ``import loomground as L`` executes, so that statement
resolves to this adapter instead of re-deriving ref's own module from its
file path. This file is solver-repo tooling, not a conforming Loomground
implementation of its own — it holds no language logic, only API translation.
"""
from __future__ import annotations

from typing import Any

from loomground_solver import loomground as _solver


class Reject(Exception):
    """Mirrors loomground-ref's own `Reject(stage, reason, message)` shape —
    the only exception type verify.py's runners catch and inspect."""

    def __init__(self, stage: str, reason: Any, message: str = "") -> None:
        self.stage = stage
        self.reason = reason
        super().__init__(message)


def parse(text: str) -> dict[str, Any]:
    try:
        return _solver.parse(text)
    except _solver.ParseError as exc:
        raise Reject("parse", getattr(exc, "reason", None), str(exc)) from None


def check(patch: dict[str, Any]) -> dict[str, Any]:
    """Ref's `check()` == this package's `apply()`'s validate half: raise
    Reject("apply", ...) on a well-formedness violation, else return the
    patch unchanged (ref's `check()` returns its argument on success too)."""
    report = _solver.validate(patch)
    if not report["ok"]:
        raise Reject("apply", report.get("reason"), "; ".join(report["errors"]))
    return patch


def project(patch: dict[str, Any]) -> dict[str, Any]:
    return _solver.project(patch)


def validate_token(token: Any) -> bool:
    return _solver.validate_token(token)


def evaluate(patch: dict[str, Any], activations: list) -> tuple[dict, list]:
    """Ref's `evaluate(patch, activations)` takes a bare activations list and
    returns `(result, log)`; this package's `evaluate`/`evaluate_log` take a
    `{"activations": [...]}` transport dict and are two separate calls — both
    differences are bridged here, nowhere else."""
    transport = {"activations": activations}
    result = _solver.evaluate(patch, transport)
    log = _solver.evaluate_log(patch, transport)
    return result, log
