#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""A paper's references are all cited and all defined, and every repository quote it grounds is
still in its text. Usage: python3 tools/check_paper.py <paper-directory>"""
import json, re, sys

d = sys.argv[1].rstrip("/")
s = open(f"{d}/paper.md").read()
body, refs = s.split("## References", 1)
defined = set(re.findall(r"^- \[([A-Z0-9-]+)\]", refs, re.M))
cited = set()
for grp in re.findall(r"\[([^\]]+)\]", body):
    for k in re.split(r"[;,]\s*", grp):
        k = k.strip().split()[0] if k.strip() else ""
        if re.fullmatch(r"[A-Z0-9][A-Z0-9-]+", k) and k not in ("README", "SPEC"):
            cited.add(k)
assert not (cited - defined), f"cited but undefined: {sorted(cited - defined)}"
assert not (defined - cited), f"defined but uncited: {sorted(defined - cited)}"
# quotes from standards are not repository quotes, so the record may be shorter than the text's quote list
norm = lambda t: re.sub(r"\s+", " ", t.replace("“", '"').replace("”", '"').replace("’", "'"))
text = norm(body)
listed = json.load(open(f"{d}/quote-grounding.json"))
missing = [q["quote"][:40] for q in listed if norm(q["quote"]) not in text]
assert not missing, f"grounded but no longer quoted: {missing}"
quotes = re.findall(r"\*“([^”]+)”\*", body)
print(f"{d}: {len(defined)} references, {len(quotes)} quotes, {len(listed)} grounded in repositories")
