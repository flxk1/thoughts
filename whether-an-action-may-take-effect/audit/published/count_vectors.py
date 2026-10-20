"""Count conformance vectors by kind, stage and content at a commit of loomground.
Run: python3 count_vectors.py <loomground-repo> <commit>"""
import collections, json, re, subprocess, sys

repo, commit = sys.argv[1], sys.argv[2]
def show(path):
    r = subprocess.run(["git", "-C", repo, "show", f"{commit}:{path}"], capture_output=True)
    return r.stdout.decode() if r.returncode == 0 else None

m = json.loads(show("conformance/manifest.json"))
print("commit", subprocess.run(["git", "-C", repo, "rev-parse", commit], capture_output=True, text=True).stdout.strip(),
      "manifest version", m["version"])
kinds = collections.Counter(v["kind"] for v in m["vectors"])
print("total", len(m["vectors"]), dict(kinds))
stages, reasons = collections.Counter(), collections.Counter()
runs, deleg_neg, deleg_pos, transfer_neg, transfer_pos = [], [], [], [], []
for v in m["vectors"]:
    d = f"conformance/vectors/{v['name']}/"
    src = show(d + "input.lg") or ""
    if v["kind"] == "negative":
        rj = json.loads(show(d + "reject.json"))
        stages[rj["stage"]] += 1
        reasons[rj.get("reason", "<none>")] += 1
    if v["kind"] == "patch" and "transport.json" in v["files"]:
        runs.append(v["name"])
    has_obo = re.search(r"\bon-behalf-of\b", src) is not None
    has_transfer = re.search(r"^\s*transfer\b", src, re.M) is not None
    if has_obo:
        (deleg_neg if v["kind"] == "negative" else deleg_pos).append(v["name"])
    if has_transfer:
        (transfer_neg if v["kind"] == "negative" else transfer_pos).append(v["name"])
print("negative stages", dict(stages))
print("negative reasons", dict(sorted(reasons.items())))
print("patch vectors with a run", len(runs))
print("on-behalf-of: negative", len(deleg_neg), "non-negative", len(deleg_pos))
print("  negative:", deleg_neg)
print("  non-negative:", deleg_pos)
print("transfer: negative", len(transfer_neg), "non-negative", len(transfer_pos))
print("  negative:", transfer_neg)
print("vector names:", [v["name"] for v in m["vectors"]])
