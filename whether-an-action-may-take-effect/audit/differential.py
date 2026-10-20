"""Randomized differential test: loomground-ref against loomground-solver on generated policies.
Each case is a random acyclic gate graph (grants, grades at source gates, risk floors, reservations, prohibitions,
fan-out and fan-in pipes) with one to three activations, a fifth of whose tokens are invalid.
The two observations (reject stage, or per-gate verdict and master plus the ordered log) must be equal.
Run: PYTHONPATH=loomground-ref:loomground-solver/src python3 audit/differential.py [cases] [seed]"""
import random, sys
import loomground as REF
from loomground_solver import loomground as SOLVER

RISK = ["low", "medium", "high", "critical"]
KINDS = ["payment", "routine", "automated_decision"]
BAD = [("risk", "catastrophic"), ("risk", 5), ("risk", ...), ("kind", ...), ("kind", None),
       ("id", ...), ("party", ...), ("provenance", ...)]


def policy(r):
    actors = [f"a{i}" for i in range(r.randint(1, 3))]
    gates = [f"G{i}" for i in range(r.randint(1, 5))]
    lines = [f"actor {a}" + (f" grade L{r.randint(1, 6)}" if r.random() < .4 else "") for a in actors]
    lines += ["human h1 role cfo", "human h2 role dpo"]
    pipes = [(x, y) for i, x in enumerate(gates) for y in gates[i + 1:] if r.random() < .35]
    grants = {}
    for g in gates:
        grants[g] = [a for a in actors if r.random() < .7]
        line = f"gate {g}"
        if r.random() < .5: line += f" risk {r.choice(RISK)}"
        if r.random() < .3 and not any(y == g for _, y in pipes): line += f" grade L{r.randint(1, 6)}"
        if grants[g]: line += " grant " + " ".join(grants[g])
        lines.append(line)
    for _ in range(r.randint(0, 2)):
        line = f"reserve {r.choice(KINDS)} by {r.choice(['cfo', 'dpo'])}"
        if r.random() < .5: line += f" when risk >= {r.choice(RISK)}"
        lines.append(line)
    if r.random() < .3: lines.append(f"prohibit {r.choice(KINDS)}")
    for g in gates:
        lines += [f"cord {a} -> {g}" for a in grants[g]]
    lines += [f"cord {x} -> {y}" for x, y in pipes]
    lines += [f"cord {g} -> master" for g in gates if not any(x == g for x, _ in pipes)]
    return "\n".join(lines), actors, gates


def token(r, i):
    t = dict(id=f"t{i}", kind=r.choice(KINDS), risk=r.choice(RISK), party="p", provenance=[])
    if r.random() < .2:
        field, value = r.choice(BAD)
        if value is ...: t.pop(field)
        else: t[field] = value
    return t


def ref(src, acts):
    try:
        p = REF.check(REF.parse(src))
        if isinstance(p, REF.Reject): return ("reject", p.stage)
    except REF.Reject as e: return ("reject", e.stage)
    try: res, log = REF.evaluate(p, acts)
    except Exception as e: return ("raised", repr(e))
    return ({g: (v["verdict"], v.get("master")) for g, v in res.items()}, [(e["gate"], e["verdict"]) for e in log])


def solver(src, acts):
    try:
        t = SOLVER.reason(src, {"activations": acts})["trace"]
    except Exception as e:
        return ("reject", {"ApplyError": "apply", "ParseError": "parse"}.get(type(e).__name__, repr(e)))
    return ({g: (v["verdict"], v.get("master")) for g, v in t["evaluation"].items()}, [(e["gate"], e["verdict"]) for e in t["log"]])


def main(n=6000, seed=1):
    r = random.Random(seed)
    stats = dict(cases=0, rejected=0, evaluated=0, invalid_tokens=0, fanout=0, fanin=0, disagree=0)
    for i in range(n):
        src, actors, gates = policy(r)
        acts = [dict(actor=r.choice(actors), source=r.choice(gates), token=token(r, j)) for j in range(r.randint(1, 3))]
        a, b = ref(src, acts), solver(src, acts)
        stats["cases"] += 1
        stats["rejected" if a[0] == "reject" else "evaluated"] += 1
        stats["invalid_tokens"] += sum(not REF.validate_token(x["token"]) for x in acts)
        pipes = [l.split()[1:4:2] for l in src.splitlines() if l.startswith("cord G") and not l.endswith("master")]
        stats["fanout"] += any(sum(x == g for x, _ in pipes) > 1 for g in gates)
        stats["fanin"] += any(sum(y == g for _, y in pipes) > 1 for g in gates)
        if a != b:
            stats["disagree"] += 1
            if stats["disagree"] <= 5: print(f"DISAGREE case {i}\n{src}\n{acts}\n  ref:    {a}\n  solver: {b}")
    print(" ".join(f"{k}={v}" for k, v in stats.items()))
    return stats["disagree"]


if __name__ == "__main__":
    sys.exit(1 if main(*map(int, sys.argv[1:3])) else 0)
