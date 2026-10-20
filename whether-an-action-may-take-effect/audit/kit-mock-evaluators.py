import collections, types
from loomground_governance import run_conformance
from loomground_governance.conformance import iter_vectors
print(collections.Counter((v.kind, v.stage) for v in iter_vectors()))
def mk(parse, validate):
    m = types.SimpleNamespace(parse=parse, validate=validate, project=lambda p: None,
        evaluate=lambda p,t: None, evaluate_log=lambda p,t: None, validate_token=lambda t: None)
    return m
def crash(src): raise ZeroDivisionError("bug")
r = run_conformance(mk(crash, lambda p: {"ok": True}))
print("parse always crashes (ZeroDivisionError):", r.passed, "/", r.total)
r = run_conformance(mk(lambda s: s, lambda p: {"ok": False}))
print("parse accepts all, validate always ok=False:", r.passed, "/", r.total)
