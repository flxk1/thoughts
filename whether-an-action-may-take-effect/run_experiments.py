"""Loomground - Table 3 probes plus the composition/invalid-token probes
that establish the historical failures F1-F3.

Run: PYTHONPATH=loomground-ref:loomground-solver/src python3 run_experiments.py [--series H|E|P|all]

Table 3 selection rule
-----------------------
A probe is included in Table 3 (the H-series) iff it exercises exactly one
of: reservation triggering (H1 family), grade/risk amplification through
on-behalf-of and its degenerate cases - cycles, attenuation (H2 family), or
a priority/override interaction between prohibit, an ungranted actor, two
activations at one gate, and an agent acting as its own master (H3
family). Each H-probe is a *minimal* policy: removing any line changes
which rule fires. The H-probes are unchanged in behaviour from the
original eleven-probe script; only the comparison and reporting below are
new.

The E-series (E3a/E3b, and additional invalid-token shapes noted in the
2026-09-26 adjudication) and the P-series (P-auth, P-fanout, the
fan-out/fan-in diamond, and the P-fanin control) are *not* part of Table 3.
They reproduce the three defects (F1 invalid-token fail-open, F2 skipped
downstream authority, F3 dropped fan-out branch) that were present at the
historical pins (cf221b4/408554b/586696c/f43dfd6/ead0ad2) and fixed in the
current pins (13fc82c/7f04e1c/7baee93/2eb09a4/ead0ad2). Run against the
historical pins they are expected to disagree with SPEC (and, for the
invalid-token probes, with each other); run against the current pins they
are expected to agree with SPEC and with each other.

Comparison is over STRUCTURED observations, not condensed strings: the
per-gate (verdict, master) mapping and the full ordered log entries
(gate id and verdict, not just the verdict sequence). A crash inside an
evaluator is caught and recorded as an observation ("raised
ExceptionType(...)"); it never aborts the run.
"""
import argparse
import json
import sys

import loomground as REF                              # loomground-ref
from loomground_solver import loomground as SOLVER    # loomground-solver


# ---------------------------------------------------------------- helpers

def tok(i, kind, risk, **kw):
    return dict(id=i, kind=kind, risk=risk, party="deployer", provenance=[], **kw)


def A(actor, t, source="decide"):
    return dict(actor=actor, source=source, token=t)


def structured_ref(src, acts):
    """Return a structured observation from loomground-ref, never raising."""
    try:
        p = REF.check(REF.parse(src))
        if isinstance(p, REF.Reject):
            return {"kind": "reject", "stage": p.stage}
    except REF.Reject as e:
        return {"kind": "reject", "stage": e.stage}
    except Exception as e:
        return {"kind": "raised", "error": f"{type(e).__name__}({e})"}
    if not acts:
        return {"kind": "accepted"}
    try:
        res, log = REF.evaluate(p, acts)
    except Exception as e:
        return {"kind": "raised", "error": f"{type(e).__name__}({e})"}
    return {
        "kind": "evaluated",
        "gates": {g: {"verdict": v["verdict"], "master": v.get("master")} for g, v in res.items()},
        "log": [{"gate": e.get("gate"), "verdict": e["verdict"]} for e in log],
    }


def structured_solver(src, acts):
    """Return a structured observation from loomground-solver, never raising."""
    try:
        r = SOLVER.reason(src, {"activations": acts} if acts else None)
    except Exception as e:
        stage = {"ApplyError": "apply", "ParseError": "parse"}.get(type(e).__name__)
        if stage:
            return {"kind": "reject", "stage": stage}
        return {"kind": "raised", "error": f"{type(e).__name__}({e})"}
    if not acts:
        return {"kind": "accepted"}
    t = r["trace"]
    obs = {
        "kind": "evaluated",
        "gates": {g: {"verdict": v["verdict"], "master": v.get("master")} for g, v in t["evaluation"].items()},
        "log": [{"gate": e.get("gate"), "verdict": e["verdict"]} for e in t["log"]],
    }
    obs["accepted"] = r.get("accepted")
    obs["undecided"] = r.get("undecided")
    obs["rejected"] = r.get("rejected")
    return obs


def matches_expected(obs, expected):
    """Compare an observation against a partial spec-expected outcome.

    `expected["gates"]` need only name the gates whose verdict/master the
    probe cares about (e.g. only the gate that pipes into master); other
    gates in the observation are ignored. `expected["log"]` of None means
    the log is not checked (used where only the terminal gate matters)."""
    if expected["kind"] != obs.get("kind"):
        return False
    if expected["kind"] in ("reject", "accepted"):
        return obs_eq(obs, expected)
    for g, want in expected.get("gates", {}).items():
        got = obs.get("gates", {}).get(g)
        if got != want:
            return False
    if expected.get("log") is not None and obs.get("log") != expected["log"]:
        return False
    return True


def obs_eq(a, b):
    """Equality over the parts both evaluators expose (ignore solver-only accepted/undecided/rejected)."""
    if a.get("kind") != b.get("kind"):
        return False
    if a["kind"] == "reject":
        return a.get("stage") == b.get("stage")
    if a["kind"] == "accepted":
        return True
    if a["kind"] == "raised":
        return False  # a crash never counts as agreement with anything, including another crash
    return a.get("gates") == b.get("gates") and a.get("log") == b.get("log")


def fmt(obs):
    if obs["kind"] == "reject":
        return f"reject@{obs['stage']}"
    if obs["kind"] == "accepted":
        return "accepted"
    if obs["kind"] == "raised":
        return f"raised {obs['error']}"
    gates = " ".join(f"{g}={v['verdict']}/{v['master']}" for g, v in obs["gates"].items())
    log = [e["verdict"] for e in obs["log"]]
    return f"{gates}  log={log}"


# -------------------------------------------------------------- H-series
# (Table 3; byte-for-byte the original eleven probes' policies/activations)

H1 = """actor bot grade L2
human alice role dpo
gate decide risk high grant bot
reserve automated_decision by dpo when risk >= high
cord decide -> master"""
MAX = """actor bot grade L6
actor rogue
human alice role dpo
gate decide risk high grade L2 grant bot
reserve automated_decision by dpo when risk >= high
cord decide -> master"""

H_PROBES = [
 ("H1  DPO reservation, risk high",        H1,  [A("bot", tok("t1","automated_decision","high"))],
  {"gates": {"decide": {"verdict": "reserved", "master": "withhold"}}, "log": [{"gate": "decide", "verdict": "reserved"}]}),
 ("H1' risk low, gate floor high",         H1,  [A("bot", tok("t1","automated_decision","low"))],
  {"gates": {"decide": {"verdict": "reserved", "master": "withhold"}}, "log": [{"gate": "decide", "verdict": "reserved"}]}),
 ("H1'' L6 >= required L2, still reserved", MAX, [A("bot", tok("t1","automated_decision","high"))],
  {"gates": {"decide": {"verdict": "reserved", "master": "withhold"}}, "log": [{"gate": "decide", "verdict": "reserved"}]}),
 ("H3a prohibit beats L6 + reservation",   MAX + "\nprohibit automated_decision", [A("bot", tok("t1","automated_decision","high"))],
  {"gates": {"decide": {"verdict": "prohibited", "master": "withhold"}}, "log": [{"gate": "decide", "verdict": "prohibited"}]}),
 ("H3b ungranted actor",                   MAX, [A("rogue", tok("t2","automated_decision","high"))],
  {"gates": {"decide": {"verdict": "refused", "master": "withhold"}}, "log": [{"gate": "decide", "verdict": "refused"}]}),
 ("H3b' two activations, one gate",        MAX, [A("bot", tok("t1","automated_decision","high")), A("rogue", tok("t2","automated_decision","high"))],
  {"gates": {"decide": {"verdict": "refused", "master": "withhold"}}, "log": [{"gate": "decide", "verdict": "reserved"}, {"gate": "decide", "verdict": "refused"}]}),
 ("H2a grade amplification L3 under L2",   "actor boss grade L2\nactor sub grade L3 on-behalf-of boss\ngate g risk low grant boss sub\ncord g -> master", [],
  {"kind": "reject", "stage": "apply"}),
 ("H2b risk amplification",                "actor boss\nactor sub on-behalf-of boss\ngate g risk low grant boss[pay:low] sub[pay:low,high]\ncord g -> master", [],
  {"kind": "reject", "stage": "apply"}),
 ("H2c on-behalf-of cycle",                "actor a on-behalf-of b\nactor b on-behalf-of a\ngate g risk low grant a b\ncord g -> master", [],
  {"kind": "reject", "stage": "apply"}),
 ("H2d attenuation L2 under L3 (valid)",   "actor boss grade L3\nactor sub grade L2 on-behalf-of boss\ngate g risk low grant boss sub\ncord g -> master", [],
  {"kind": "accepted"}),
 ("H3c agent -> master",                   "actor a\ngate g risk low grant a\ncord a -> master", [],
  {"kind": "reject", "stage": "apply"}),
]
for _row in H_PROBES:
    if "kind" not in _row[3]:
        _row[3]["kind"] = "evaluated"


# -------------------------------------------------------------- E-series
# Invalid-token probes (restores E3a/E3b, dropped from the shipped script
# after the fix; inputs match adjudication.json historical_failures F1/*
# exactly: gate "g", kind "payment", policies "res" (reservation on
# payment when risk >= high) and "none" (no reservation)).

E_POL_RES = "actor a\ngate g risk low grant a\nreserve payment by cfo when risk >= high\ncord g -> master"
E_POL_NONE = "actor a\ngate g risk low grant a\ncord g -> master"


def _tkn(**overrides):
    t = dict(id="t1", kind="payment", risk="low", party="d", provenance=[])
    for k, v in overrides.items():
        if v is ...:
            t.pop(k, None)
        else:
            t[k] = v
    return t


EMPTY = {"kind": "evaluated", "gates": {}, "log": []}

E_PROBES = [
 ("E3a invalid risk=catastrophic (adjudication F1/E3a)", E_POL_RES,
  [A("a", _tkn(risk="catastrophic"), source="g")], EMPTY),
 ("E3b kind missing, risk=high (adjudication F1/E3b)", E_POL_RES,
  [A("a", _tkn(kind=..., risk="high"), source="g")], EMPTY),
 ("E3c id missing, risk=high (adjudication F1/missing-id)", E_POL_RES,
  [A("a", _tkn(id=..., risk="high"), source="g")], EMPTY),
 ("E3d party missing (adjudication F1/missing-party)", E_POL_NONE,
  [A("a", _tkn(party=...), source="g")], EMPTY),
 ("E3e provenance missing (adjudication F1/missing-provenance)", E_POL_NONE,
  [A("a", _tkn(provenance=...), source="g")], EMPTY),
 ("E3f kind=None (adjudication F1/kind=None)", E_POL_NONE,
  [A("a", _tkn(kind=None), source="g")], EMPTY),
 ("E3g mixed batch: valid t0 high then invalid t1 catastrophic (adjudication F1/mixed-batch)",
  E_POL_RES, [A("a", _tkn(id="t0", risk="high"), source="g"), A("a", _tkn(risk="catastrophic"), source="g")],
  {"kind": "evaluated", "gates": {"g": {"verdict": "reserved", "master": "withhold"}},
   "log": [{"gate": "g", "verdict": "reserved"}]}),
]


# -------------------------------------------------------------- P-series
# Composition probes (F2 downstream authority, F3 fan-out drop, plus a
# fan-in control and the fan-out/fan-in diamond).

P_AUTH = ("P-auth ungranted downstream gate",
          "actor a\ngate A risk low grant a\ngate B risk low\ncord a -> A\ncord A -> B\ncord B -> master",
          [A("a", tok("t1", "op", "low"), source="A")],
          {"kind": "evaluated",
           "gates": {"B": {"verdict": "refused", "master": "withhold"}},
           "log": [{"gate": "A", "verdict": "auto"}, {"gate": "B", "verdict": "refused"}]})

P_FANOUT = ("P-fanout A pipes to B and C",
            "actor a\ngate A risk low grant a\ngate B risk low grant a\ngate C risk low grant a\n"
            "cord a -> A\ncord A -> B\ncord A -> C\ncord B -> master\ncord C -> master",
            [A("a", tok("t1", "op", "low"), source="A")],
            {"kind": "evaluated",
             "gates": {"B": {"verdict": "auto", "master": "act"}, "C": {"verdict": "auto", "master": "act"}},
             "log": [{"gate": "A", "verdict": "auto"}, {"gate": "B", "verdict": "auto"}, {"gate": "C", "verdict": "auto"}]})

P_DIAMOND = ("P-diamond fan-out/fan-in, B floor high, reserve op>=high",
             "actor a\nhuman h role rev\ngate A risk low grant a\ngate B risk high grant a\ngate C risk low grant a\ngate D risk low grant a\n"
             "reserve op by rev when risk >= high\n"
             "cord a -> A\ncord A -> B\ncord A -> C\ncord B -> D\ncord C -> D\ncord D -> master",
             [A("a", tok("t1", "op", "high"), source="A")],
             {"kind": "evaluated", "gates": {"D": {"verdict": "reserved", "master": "withhold"}}, "log": None})

P_FANIN = ("P-fanin control: B and C into D, reserved at C",
           "actor a\nhuman h role rev\ngate B risk low grant a\ngate C risk low grant a\ngate D risk low grant a\n"
           "reserve sens by rev\ncord a -> B\ncord a -> C\ncord B -> D\ncord C -> D\ncord D -> master",
           [A("a", tok("t1", "op", "low"), source="B"), A("a", tok("t2", "sens", "low"), source="C")],
           {"kind": "evaluated", "gates": {"D": {"verdict": "reserved", "master": "withhold"}}, "log": None})

P_PROBES = [P_AUTH, P_FANOUT, P_DIAMOND, P_FANIN]


ALL = [("H", H_PROBES), ("E", E_PROBES), ("P", P_PROBES)]


def run(series_filter):
    total = 0
    agree_count = 0
    for series, probes in ALL:
        if series_filter not in ("all", series):
            continue
        for name, src, acts, expected in probes:
            total += 1
            r = structured_ref(src, acts)
            s = structured_solver(src, acts)
            agree = obs_eq(r, s)
            r_matches_expected = matches_expected(r, expected)
            s_matches_expected = matches_expected(s, expected)
            if agree:
                agree_count += 1
            expected_str = fmt(expected) if expected["kind"] in ("reject", "accepted") or expected.get("log") is not None else "(named gates only) " + json.dumps(expected.get("gates", {}))
            print(f"[{series}] {name}")
            print(f"    ref:      {fmt(r)}")
            print(f"    solver:   {fmt(s)}")
            print(f"    expected: {expected_str}")
            print(f"    agree(ref==solver):        {agree}")
            print(f"    ref matches spec-expected: {r_matches_expected}")
            print(f"    solver matches expected:   {s_matches_expected}")
    print(f"\n{agree_count}/{total} probes agree (ref==solver) in this series selection")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--series", choices=["H", "E", "P", "all"], default="all")
    args = ap.parse_args()
    run(args.series)
