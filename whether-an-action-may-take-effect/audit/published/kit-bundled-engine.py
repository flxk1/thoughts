"""Score the bundled skill engine of loomground-governance through the conformance kit,
using the adapter from that repository's tests/test_bundled_engine_conformance.py.
Run: python3 kit-bundled-engine.py <loomground-governance-repo>"""
import importlib.util, sys
from pathlib import Path
from loomground_governance import run_conformance
t = Path(sys.argv[1]) / "tests" / "test_bundled_engine_conformance.py"
spec = importlib.util.spec_from_file_location("bundled_test", t)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
r = run_conformance(mod._EngineAdapter(mod._load_engine()))
print("bundled engine through the kit:", r.passed, "/", r.total)
