"""Locate every quoted repository span in the paper at a pinned commit.
Span = [start, end) in Unicode characters of the file at `commit`; urn = sha256 of its bytes.
A match is exact, or `normalised` (whitespace runs, curly quotes, markdown emphasis) and then
mapped back to raw offsets, so the span always indexes the unmodified file.
Run: python3 ground_quotes.py <loomground-repo> <loomground-ref-repo> [paper.md]"""
import hashlib, json, re, subprocess, sys
from pathlib import Path

# Published pins: loomground tag v0.11.2 and loomground-ref main, 2026-10-10.
PIN = {"loomground": "081f1cfccf3724db657428e52d09677c1132e569", "loomground-ref": "2417fee0dd596d31f8a3f1495b8d3282a1878ca7"}
QUOTES = [
    ("loomground", "README.md", 'Every governance tool defines "policy", "gate" and "verdict" its own way; nothing is comparable or checkable.'),
    ("loomground", "spec/SPEC.md", "Expressing a measure in this language does not, by itself, satisfy any legal obligation"),
    ("loomground", "spec/SPEC.md", "MUST reject a token lacking a required field or bearing a risk outside its domain"),
    ("loomground", "spec/SPEC.md", "activates no node and produces no log entry"),
    ("loomground", "spec/SPEC.md", "need not agree"),
    ("loomground", "spec/SPEC.md", "a conforming implementation's log MUST match the one this rule produces"),
    ("loomground", "CONTRIBUTING.md", "the spec, the grammar, the schemas, the vocabulary, `llms.txt`, and a conformance vector agree"),
    ("loomground", "conformance/README.md", "an implementation produced without access to this project's implementations reproduces every vector"),
    ("loomground", "conformance/README.md", "a runner MUST fail the vector if a token so marked in fact validates"),
    ("loomground", "spec/SPEC.md", "A reader MUST NOT assume the reserved action's constraints bind the follow-on activation"),
]
FOLD = {"“": '"', "”": '"', "‘": "'", "’": "'"}


def normalise(text):
    """→ (normalised text, index map from each normalised char to its raw offset)"""
    out, idx, i = [], [], 0
    while i < len(text):
        c = text[i]
        if text.startswith("**", i) or (c in "*_" and (i == 0 or not text[i - 1].isalnum())):
            i += 2 if text.startswith("**", i) else 1
            continue
        if c.isspace():
            j = i
            while j < len(text) and text[j].isspace():
                j += 1
            if out and out[-1] != " ":
                out.append(" "); idx.append(i)
            i = j
            continue
        out.append(FOLD.get(c, c)); idx.append(i)
        i += 1
    return "".join(out), idx


def locate(text, quote):
    hits = [m.start() for m in re.finditer(re.escape(quote), text)]
    if hits:
        return [(h, h + len(quote)) for h in hits], "exact"
    nt, idx = normalise(text)
    nq, _ = normalise(quote)
    hits = [m.start() for m in re.finditer(re.escape(nq), nt)]
    return [(idx[h], idx[h + len(nq) - 1] + 1) for h in hits], "normalised"


def main(core, ref, paper="paper.md"):
    roots = {"loomground": core, "loomground-ref": ref}
    body = Path(paper).read_text() if Path(paper).exists() else ""
    rows, bad = [], 0
    for repo, path, quote in QUOTES:
        raw = subprocess.run(["git", "-C", roots[repo], "show", f"{PIN[repo]}:{path}"],
                             capture_output=True, check=True).stdout
        text = raw.decode()
        spans, how = locate(text, quote)
        row = {"quote": quote, "source": f"{repo}/{path}", "commit": PIN[repo],
               "urn": "urn:kg:sha256:" + hashlib.sha256(raw).hexdigest()}
        if not spans:
            row["span"], bad = None, bad + 1
            row["match"] = "NOT FOUND"
        else:
            row["span"] = list(spans[0])
            row["match"] = how
            if len(spans) > 1:
                row["other_spans"] = [list(s) for s in spans[1:]]
            if how != "exact":
                row["source_text"] = text[spans[0][0]:spans[0][1]]
        nq = normalise(quote)[0]
        row["in_paper"] = nq in normalise(body)[0] if body else None
        rows.append(row)
    (Path(__file__).parent / "quote-grounding.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n")
    for r in rows:
        print(f"{r['match']:<10} {str(r['span']):<14} paper={r['in_paper']!s:<5} {r['source']}: {r['quote'][:50]}")
    return bad


if __name__ == "__main__":
    sys.exit(1 if main(*sys.argv[1:]) else 0)
