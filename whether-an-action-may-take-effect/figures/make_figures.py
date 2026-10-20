"""Loomground — figures, authored at print size.

The canvas is the paper's text width in millimetres (166 mm) and type is set in points, so the
page decides what fits: a label that would print below 7 pt cannot be drawn, and one that would
overrun its box is reported. Prose is set in the body face, identifiers in mono. One violet mark
per figure, on the finding. Run: python3 figures/make_figures.py"""
import math
import sys
from html import escape
from pathlib import Path

OUT = Path(__file__).parent
WIDTH = 166.0                                          # mm, the text width of the A4 page
PT = 0.3528                                            # mm per point
INK, META, SURF, V, WHITE = "#111111", "#555555", "#F4F4F4", "#5B5B9A", "#FFFFFF"
SANS, MONO = "Archivo, Arial, sans-serif", "IBM Plex Mono, Courier New, monospace"
ADVANCE = {SANS: 0.42, MONO: 0.52}                     # measured on the rendered faces (0.34 / 0.48) plus headroom
STROKE, HEAVY = 0.3, 0.8                               # mm: every rule ≈ 0.85 pt; the pipe ≈ 2.3 pt
FLOOR_PT = 7.0
PROBLEMS = []


def size(pt):
    if pt < FLOOR_PT:
        raise ValueError(f"{pt} pt is below the {FLOOR_PT} pt floor")
    return pt * PT


def width_of(s, pt, family):
    return len(s) * size(pt) * ADVANCE[family]


def t(x, y, s, pt=8, family=SANS, fill=INK, anchor="start", weight=400, limit=None):
    if limit is not None and width_of(s, pt, family) > limit:
        PROBLEMS.append(f"'{s}' needs {width_of(s, pt, family):.1f} mm, has {limit:.1f} mm")
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-family="{family}" font-size="{size(pt):.3f}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{escape(s)}</text>')


def rect(x, y, w, h, fill=WHITE, stroke=INK, sw=STROKE):
    return (f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"/>')


def box(x, y, w, h, lines, fill=WHITE, stroke=INK, ink=INK, sub=META, pad=2.4):
    """lines: [(text, family, pt, weight)]; the first is the head. Vertically centred."""
    out = [rect(x, y, w, h, fill, stroke)]
    heights = [size(pt) * 1.3 for _, _, pt, _ in lines]
    cy = y + h / 2 - sum(heights) / 2
    for i, ((s, fam, pt, wt), lh) in enumerate(zip(lines, heights)):
        cy += lh
        out.append(t(x + pad, cy - lh * 0.28, s, pt, fam, ink if i == 0 else sub, "start", wt, w - 2 * pad))
    return "".join(out)


def arrow(x1, y1, x2, y2, colour=INK, sw=STROKE, head=1.6):
    a = math.atan2(y2 - y1, x2 - x1)
    h1 = (x2 - head * math.cos(a - 0.45), y2 - head * math.sin(a - 0.45))
    h2 = (x2 - head * math.cos(a + 0.45), y2 - head * math.sin(a + 0.45))
    return (f'<path d="M{x1:.2f} {y1:.2f}L{x2:.2f} {y2:.2f}" stroke="{colour}" stroke-width="{sw}" fill="none"/>'
            f'<path d="M{h1[0]:.2f} {h1[1]:.2f}L{x2:.2f} {y2:.2f}L{h2[0]:.2f} {h2[1]:.2f}Z" fill="{colour}" '
            f'stroke="{colour}" stroke-width="{sw}"/>')


def write(name, h, parts, aria):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}mm" height="{h}mm" '
           f'viewBox="-0.4 -0.4 {WIDTH + 0.8} {h + 0.8}" role="img" aria-label="{escape(aria)}">'
           f'<rect x="-0.4" y="-0.4" width="{WIDTH + 0.8}" height="{h + 0.8}" fill="{WHITE}"/>' + "".join(parts) + "</svg>")
    (OUT / f"{name}.svg").write_text(svg)
    print(f"{name}.svg  {WIDTH:.0f} x {h} mm")


H8, S7, M8, M7 = (lambda s: (s, SANS, 8.5, 600)), (lambda s: (s, SANS, 7.5, 400)), \
                 (lambda s: (s, MONO, 8, 600)), (lambda s: (s, MONO, 7.5, 400))


# ── Figure 2 · §5 · the method: one input, two evaluators, one comparison ─────────────────────
def fig_method():
    p = []
    top, bot, bh = 2.0, 26.0, 16.0
    mid = (top + bot + bh) / 2
    p.append(box(0, mid - 10, 26, 20, [H8("input"), M7(".lg patch"), M7("+ transport")]))
    for y, name in ((top, "loomground-ref"), (bot, "loomground-solver")):
        p.append(box(36, y, 42, bh, [M8(name), S7("emits verdict, master, log")]))
        p.append(arrow(26, mid, 35.6, y + bh / 2))
        p.append(arrow(78, y + bh / 2, 87.6, mid))
    p.append(box(88, mid - 10, 30, 20, [H8("compare"), S7("with each other"), S7("and the spec")]))
    p.append(box(128, top, 38, bh, [H8("agree"), S7("case reproduced")]))
    p.append(box(128, bot - 2, 38, bh + 4, [H8("disagree: a finding"), S7("resolve in the spec, the"),
                                            S7("vector or an evaluator")], fill=V, stroke=V, ink=WHITE, sub=WHITE))
    p.append(arrow(118, mid, 127.6, top + bh / 2))
    p.append(arrow(118, mid, 127.6, bot + bh / 2))
    write("fig2-method", bot + bh + 4, p,
          "Differential testing. One input, a patch plus a transport, goes to loomground-ref and to "
          "loomground-solver. Each emits a verdict per gate, a master decision and a log. The two "
          "observations are compared with each other and with the specification. Agreement "
          "reproduces the case; disagreement is a finding, resolved in the specification, the "
          "vector or an evaluator.")


# ── Figure 1 · §4 · the verdict order, and propagation read off it (vector grade-join) ─────────
def fig_order():
    p = []
    # the worked instance
    gy, gh = 9.0, 13.0
    p.append(t(0, 5, "t1 {kind: act, risk: low} proposed by bot at gate screen",
               7.5, MONO, META, limit=WIDTH))
    nodes = [(0, 22, [M8("actor bot"), S7("grade L2")]), (32, 34, [M8("gate screen"), S7("requires L3")]),
             (86, 34, [M8("gate commit"), S7("terminal, no grade")]), (140, 25, [M8("master")])]
    for x, w, lines in nodes:
        p.append(box(x, gy, w, gh, lines))
    c = gy + gh / 2
    p.append(arrow(22, c, 31.6, c))
    p.append(arrow(66, c, 85.4, c, INK, HEAVY, 2.2))
    p.append(t(76, c - 1.6, "pipe", 7.5, SANS, META, "middle"))
    p.append(arrow(120, c, 139.6, c))
    ry = gy + gh + 5
    p.append(t(32, ry, "own:", 7.5, SANS, META)); p.append(t(40, ry, "human", 8, MONO, INK, weight=600))
    p.append(t(86, ry, "own:", 7.5, SANS, META)); p.append(t(94, ry, "auto", 8, MONO))
    p.append(t(86, ry + 4.2, "effective:", 7.5, SANS, META))
    p.append(t(101, ry + 4.2, "auto ⊔ human = human", 8, MONO, INK, weight=600, limit=WIDTH - 101 - 26))
    p.append(t(140, ry, "withholds", 8, SANS, INK, weight=600))
    # the order the join reads off
    ly, lw, lh, gap = ry + 13, 25.0, 8.0, 9.6       # 5 × 25 + 4 × 9.6 = 163.4 mm: inside the 166 mm text width
    names = ["auto", "human", "refused", "reserved", "prohibited"]
    for i, n in enumerate(names):
        x = i * (lw + gap)
        hot = n == "human"
        p.append(rect(x, ly, lw, lh, V if hot else WHITE, V if hot else INK))
        p.append(t(x + lw / 2, ly + lh / 2 + 1.0, n, 8, MONO, WHITE if hot else INK, "middle", 600, lw - 2))
        if i < 4:
            p.append(t(x + lw + gap / 2, ly + lh / 2 + 1.1, "⊑", 9, MONO, META, "middle"))
    if 5 * lw + 4 * gap > WIDTH - 1:
        PROBLEMS.append("verdict row overruns the text width")
    ay = ly + lh + 5
    p.append(t(lw / 2, ay, "commit's own", 7.5, SANS, META, "middle"))
    p.append(t(1 * (lw + gap) + lw / 2 + 14, ay, "screen's own = commit's effective", 7.5, SANS, INK, "middle", 600))
    p.append(t(WIDTH - 0.5, ay + 4, "more restrictive →", 7.5, SANS, META, "end"))
    p.append(t(0, ay + 4, "auto: the only verdict that releases", 7.5, SANS, META))
    write("fig1-order", round(ay + 6, 1), p,
          "Propagation in the conformance vector grade-join. Actor bot, granted grade L2, proposes a "
          "token at source gate screen, which requires grade L3, so screen's own verdict is human. "
          "screen pipes into terminal gate commit, which declares no grade and no reservation, so its "
          "own verdict is auto. commit's effective verdict is the join, auto joined with human, which "
          "is human, read off the order auto, human, refused, reserved, prohibited. The master "
          "withholds, because only auto releases.")


if __name__ == "__main__":
    fig_method(); fig_order()
    for msg in PROBLEMS:
        print("  overrun:", msg)
    sys.exit(1 if PROBLEMS else 0)
