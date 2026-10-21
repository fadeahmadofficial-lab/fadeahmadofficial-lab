#!/usr/bin/env python3
"""Generates the animated SVGs used by the profile README.

Usage:  python scripts/gen_assets.py assets

Everything is plain SVG + SMIL so it animates inside GitHub's <img> sandbox
(no scripts, no web fonts). Colours are the portfolio's dark "control room"
tokens. Edit the data near each function and re-run to update the images.
"""
import math
import random
import sys
from pathlib import Path

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "assets")

BG0, BG1, BG2, BG3 = "#07080b", "#0d0f14", "#13161e", "#1a1e29"
LINE, LINE2 = "#232835", "#5d667c"
INK, MUTED, FAINT = "#eceef3", "#a0a7b8", "#7c8498"
CYAN, VIOLET, AMBER, ROSE = "#22d3ee", "#a78bfa", "#f5b544", "#fb7185"
SANS = "'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "'JetBrains Mono', SFMono-Regular, Consolas, 'Liberation Mono', Menlo, monospace"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def n(x):
    return f"{x:.3f}".rstrip("0").rstrip(".") or "0"


def svg(w, h, title, body, defs=""):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">
<title>{esc(title)}</title>
<defs>
<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="#ffffff" stroke-opacity=".035"/></pattern>
<linearGradient id="accent" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{CYAN}"/><stop offset="1" stop-color="{VIOLET}"/></linearGradient>
<filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<clipPath id="panel"><rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="18"/></clipPath>
{defs}
</defs>
{body}
</svg>
"""


def frame(w, h):
    """Dark rounded panel with a faint grid and HUD corner brackets."""
    s = [
        f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="18" fill="{BG0}" stroke="{LINE}" stroke-width="1.5"/>',
        f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="18" fill="url(#grid)"/>',
    ]
    L, m = 22, 14
    for x, y, dx, dy in ((m, m, 1, 1), (w - m, m, -1, 1), (m, h - m, 1, -1), (w - m, h - m, -1, -1)):
        s.append(f'<path d="M{x} {y + dy * L}V{y}H{x + dx * L}" fill="none" stroke="{CYAN}" stroke-opacity=".5" stroke-width="2"/>')
    return "\n".join(s)


def text(x, y, s, size, fill, font=MONO, weight=None, anchor=None, spacing=None, extra=""):
    attrs = f'x="{n(x)}" y="{n(y)}" font-family="{font}" font-size="{size}" fill="{fill}"'
    if weight:
        attrs += f' font-weight="{weight}"'
    if anchor:
        attrs += f' text-anchor="{anchor}"'
    if spacing:
        attrs += f' letter-spacing="{spacing}"'
    return f"<text {attrs} {extra}>{s}</text>"


def pill(x_right, y, label, color, mono_cw=7.2, spacing=2):
    """Status pill anchored at its right edge, with a pulsing dot."""
    w = 40 + len(label) * (mono_cw + spacing)
    x = x_right - w
    return (
        f'<rect x="{n(x)}" y="{y}" width="{n(w)}" height="28" rx="14" fill="{color}" fill-opacity=".08" stroke="{color}" stroke-opacity=".45"/>'
        f'<circle cx="{n(x + 16)}" cy="{y + 14}" r="4" fill="{color}"><animate attributeName="opacity" values="1;.2;1" dur="1.6s" repeatCount="indefinite"/></circle>'
        + text(x + 28, y + 18.5, label, 12, color, spacing=spacing)
    )


def blink(dur="1.6s", lo=".2"):
    return f'<animate attributeName="opacity" values="1;{lo};1" dur="{dur}" repeatCount="indefinite"/>'


def packet(path, dur, begin, color, r=3.5):
    """A glowing dot that travels along `path` forever (negative begin = already mid-flight on load)."""
    return (
        f'<circle r="{r}" fill="{color}" filter="url(#glow)" opacity="0">'
        f'<animateMotion path="{path}" dur="{dur}s" begin="{n(-begin)}s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.12;.88;1" dur="{dur}s" begin="{n(-begin)}s" repeatCount="indefinite"/>'
        "</circle>"
    )


def flow_line(d, color=LINE2, width=1.4):
    """Dashed connector whose dashes stream along the path."""
    return (
        f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-dasharray="4 6">'
        '<animate attributeName="stroke-dashoffset" values="0;-20" dur="1s" repeatCount="indefinite"/></path>'
    )


def reveal_clip(cid, x, y, h, T, start, end, full, chars=0, cw=0.0, pre=0.0, dt=0.05):
    """clipPath whose width steps open like typing, stays open until `end`, then hides until the loop restarts."""
    times, vals = [0.0, start], [0.0, pre if chars else full]
    for k in range(1, chars + 1):
        times.append(start + k * dt)
        vals.append(pre + k * cw)
    if chars:
        times.append(start + (chars + 1) * dt)
        vals.append(full)
    times += [end, T]
    vals += [0, 0]
    kt = ";".join(n(t / T) for t in times)
    vs = ";".join(n(v) for v in vals)
    return (
        f'<clipPath id="{cid}"><rect x="{n(x)}" y="{n(y)}" width="0" height="{n(h)}">'
        f'<animate attributeName="width" dur="{n(T)}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{kt}" values="{vs}"/>'
        "</rect></clipPath>"
    )


# --------------------------------------------------------------------------- hero

ROLES = [
    "Senior Full Stack AI Engineer",
    "RAG + LangGraph agents in production",
    "Team Lead · 12 engineers · 10 products",
    "PhD scholar · Explainable AI",
]


def hero():
    w, h = 1200, 420
    rnd = random.Random(11)
    cx, cy, R = 962, 210, 168

    nodes = []
    while len(nodes) < 28:
        a = rnd.uniform(0, 2 * math.pi)
        r = R * math.sqrt(rnd.uniform(0.01, 0.88))
        p = (cx + r * math.cos(a), cy + r * math.sin(a))
        if all(math.dist(p, q) > 40 for q in nodes):
            nodes.append(p)
    edges = set()
    for i, p in enumerate(nodes):
        for j in sorted(range(len(nodes)), key=lambda j: math.dist(p, nodes[j]))[1:3]:
            edges.add(tuple(sorted((i, j))))
    edges = sorted(edges)

    defs = [
        f'<radialGradient id="gc"><stop offset="0" stop-color="{CYAN}" stop-opacity=".16"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></radialGradient>',
        f'<radialGradient id="gv"><stop offset="0" stop-color="{VIOLET}" stop-opacity=".16"/><stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></radialGradient>',
        f'<linearGradient id="scan" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{CYAN}" stop-opacity="0"/><stop offset=".5" stop-color="{CYAN}" stop-opacity=".06"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></linearGradient>',
        f'<linearGradient id="bar" x1="64" y1="0" x2="284" y2="0" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{CYAN}"/><stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></linearGradient>',
    ]

    b = [frame(w, h), '<g clip-path="url(#panel)">']
    b.append('<ellipse cx="180" cy="30" rx="460" ry="230" fill="url(#gc)"/>')
    b.append(f'<ellipse cx="{cx}" cy="{cy}" rx="330" ry="260" fill="url(#gv)"/>')
    b.append(f'<rect x="0" y="-90" width="{w}" height="90" fill="url(#scan)"><animate attributeName="y" values="-90;{h}" dur="7s" repeatCount="indefinite"/></rect>')

    # radar rings, crosshair, bearings
    for rr, op in ((R + 14, ".9"), (R * 0.66, ".7"), (R * 0.33, ".6")):
        b.append(f'<circle cx="{cx}" cy="{cy}" r="{n(rr)}" fill="none" stroke="{LINE}" stroke-opacity="{op}"/>')
    b.append(
        f'<circle cx="{cx}" cy="{cy}" r="{R + 26}" fill="none" stroke="{CYAN}" stroke-opacity=".3" stroke-dasharray="2 9">'
        f'<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" dur="60s" repeatCount="indefinite"/></circle>'
    )
    b.append(f'<path d="M{cx - R - 14} {cy}H{cx + R + 14}M{cx} {cy - R - 14}V{cy + R + 14}" stroke="{LINE}"/>')
    for label, x, y, anchor in (("000", cx + 7, cy - R + 14, "start"), ("090", cx + R - 6, cy - 7, "end"),
                                ("180", cx + 7, cy + R - 6, "start"), ("270", cx - R + 6, cy - 7, "start")):
        b.append(text(x, y, label, 10, FAINT, anchor=anchor, spacing="1.5"))

    # sweep: a fan of thin wedges fading behind a bright leading edge
    sweep = ["<g>"]
    for k in range(12):
        a1, a0 = -math.radians(3.5 * k), -math.radians(3.5 * (k + 1))
        x1, y1 = cx + R * math.cos(a1), cy + R * math.sin(a1)
        x0, y0 = cx + R * math.cos(a0), cy + R * math.sin(a0)
        sweep.append(f'<path d="M{cx} {cy}L{n(x1)} {n(y1)}A{R} {R} 0 0 0 {n(x0)} {n(y0)}Z" fill="{CYAN}" fill-opacity="{n(0.2 * (1 - k / 12))}"/>')
    sweep.append(f'<path d="M{cx} {cy}H{cx + R}" stroke="{CYAN}" stroke-opacity=".7" stroke-width="1.5"/>')
    sweep.append(f'<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" dur="6s" repeatCount="indefinite"/></g>')
    b += sweep

    # constellation: edges, signals, nodes
    for i, j in edges:
        (x1, y1), (x2, y2) = nodes[i], nodes[j]
        b.append(f'<line x1="{n(x1)}" y1="{n(y1)}" x2="{n(x2)}" y2="{n(y2)}" stroke="{LINE2}" stroke-opacity=".4"/>')
    for i, j in rnd.sample(edges, 14):
        (x1, y1), (x2, y2) = nodes[i], nodes[j]
        if rnd.random() < 0.5:
            x1, y1, x2, y2 = x2, y2, x1, y1
        color = CYAN if rnd.random() < 0.7 else VIOLET
        b.append(packet(f"M{n(x1)} {n(y1)}L{n(x2)} {n(y2)}", n(rnd.uniform(1.4, 2.6)), rnd.uniform(0, 2.6), color, r=2.4))
    for k, (x, y) in enumerate(nodes):
        hub = k % 6 == 0
        r = 4 if hub else rnd.uniform(1.8, 3)
        dur, beg = rnd.uniform(2, 4), rnd.uniform(0, 4)
        if hub:
            b.append(
                f'<circle cx="{n(x)}" cy="{n(y)}" r="4" fill="none" stroke="{CYAN}">'
                f'<animate attributeName="r" values="4;18" dur="{n(dur)}s" begin="{n(-beg)}s" repeatCount="indefinite"/>'
                f'<animate attributeName="stroke-opacity" values=".8;0" dur="{n(dur)}s" begin="{n(-beg)}s" repeatCount="indefinite"/></circle>'
            )
        b.append(
            f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(r)}" fill="{CYAN if hub else INK}">'
            f'<animate attributeName="opacity" values=".35;1;.35" dur="{n(dur)}s" begin="{n(-beg)}s" repeatCount="indefinite"/></circle>'
        )
    b.append("</g>")

    # left column
    b.append(f'<circle cx="70" cy="87" r="5" fill="{AMBER}">{blink()}</circle>')
    b.append(
        f'<circle cx="70" cy="87" r="5" fill="none" stroke="{AMBER}"><animate attributeName="r" values="5;15" dur="1.6s" repeatCount="indefinite"/>'
        '<animate attributeName="stroke-opacity" values=".8;0" dur="1.6s" repeatCount="indefinite"/></circle>'
    )
    b.append(text(86, 92, "LIVE · SHIPPING AI TO PRODUCTION", 13, AMBER, spacing="2.5"))
    b.append(text(60, 168, "Fade Hafez Ahmad", 64, INK, font=SANS, weight="800", spacing="-1"))
    b.append('<rect x="64" y="188" width="220" height="3" rx="1.5" fill="url(#bar)"/>')
    b.append(f'<circle r="3" fill="{CYAN}" filter="url(#glow)"><animateMotion path="M64 189.5H284" dur="3s" repeatCount="indefinite"/>'
             '<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.1;.7;1" dur="3s" repeatCount="indefinite"/></circle>')

    # rotating role line, typed one character-ish step at a time
    slot, T = 4.0, 4.0 * len(ROLES)
    for i, role in enumerate(ROLES):
        b.append(reveal_clip(f"role{i}", 58, 206, 44, T, i * slot, i * slot + 3.6, 900, chars=len(role) + 1, cw=15, dt=0.045))
        b.append(
            f'<g clip-path="url(#role{i})">'
            + text(64, 238, f'{esc(role)}<tspan fill="{CYAN}"> ▍<animate attributeName="fill-opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></tspan>',
                   28, "url(#accent)", font=SANS, weight="600")
            + "</g>"
        )

    b.append(text(64, 282, "RAG · AI Agents · LangChain · LangGraph · MERN · TypeScript · Python", 15, MUTED))
    b.append(text(64, 312, "Team Lead @ Infinite Cercle  ·  PhD scholar @ SRM IST", 16, FAINT, font=SANS, extra='xml:space="preserve"'))
    b.append(text(64, 378, "CHENNAI, IN  ·  13.08°N 80.27°E  ·  UTC+05:30", 12, FAINT, spacing="2.5", extra='xml:space="preserve"'))

    title = "Fade Hafez Ahmad. Senior Full Stack AI Engineer: RAG, AI agents, LangGraph, MERN, TypeScript, Python."
    return svg(w, h, title, "\n".join(b), "\n".join(defs))


# ----------------------------------------------------------------------- terminal

def kv(key, val, last=False, pad=13):
    segs = [("  ", MUTED), (f'"{key}"', VIOLET), (":" + " " * (pad - len(key)), MUTED)]
    if isinstance(val, list):
        segs.append(("[", MUTED))
        for k, v in enumerate(val):
            segs += [(f'"{v}"', CYAN)] + ([(", ", MUTED)] if k < len(val) - 1 else [])
        segs.append(("]", MUTED))
    else:
        segs.append((f'"{val}"', CYAN))
    if not last:
        segs.append((",", MUTED))
    return segs


TERMINAL = [
    ("cmd", "whoami"),
    ("out", [("Fade Hafez Ahmad", INK), (" — Senior Full Stack AI Engineer · Team Lead", MUTED)]),
    ("cmd", "cat profile.json"),
    ("out", [("{", MUTED)]),
    ("out", kv("base", "Chennai, India")),
    ("out", kv("experience", "5 yrs · 12 production apps shipped")),
    ("out", kv("leading", "12 engineers · 10 products · Infinite Cercle")),
    ("out", kv("ai_in_prod", ["RAG assistant (500+ docs)", "LangGraph agent"])),
    ("out", kv("research", "PhD · Computing Technologies · Explainable AI")),
    ("out", kv("contact", "fadeahmad.official@gmail.com", last=True)),
    ("out", [("}", MUTED)]),
    ("cmd", "./now --focus"),
    ("out", [("▸ ", AMBER), ("grounded LLM features that cite their sources", INK)]),
    ("out", [("▸ ", AMBER), ("faithful-by-construction neuro-symbolic models", INK)]),
    ("end", None),
]


def terminal():
    w = 1200
    fs, lh, cw = 16, 28, 9.6
    x0, y0 = 36, 96
    prompt = [("fade", VIOLET), ("@lab", FAINT), (" ❯ ", CYAN)]
    prompt_w = sum(len(s) for s, _ in prompt) * cw
    h = y0 + (len(TERMINAL) - 1) * lh + 40

    # timeline
    t, starts = 0.8, []
    for kind, payload in TERMINAL:
        if kind == "cmd":
            if starts:
                t += 0.5
            starts.append(t)
            t += 0.25 + (len(payload) + 1) * 0.06 + 0.35
        else:
            starts.append(t)
            t += 0.09
    T = t + 5.0
    end = T - 0.5

    clips, rows = [], []
    for i, ((kind, payload), st) in enumerate(zip(TERMINAL, starts)):
        y = y0 + i * lh
        if kind == "cmd":
            clips.append(reveal_clip(f"l{i}", 0, y - lh + 8, lh, T, st, end, w, chars=len(payload) + 1, cw=cw, pre=x0 + prompt_w, dt=0.06))
            segs = prompt + [(payload, INK)]
        elif kind == "out":
            clips.append(reveal_clip(f"l{i}", 0, y - lh + 8, lh, T, st, end, w))
            segs = [("  ", MUTED)] + payload
        else:
            clips.append(reveal_clip(f"l{i}", 0, y - lh + 8, lh, T, st, end, w))
            segs = prompt
        spans = "".join(f'<tspan fill="{c}">{esc(s)}</tspan>' for s, c in segs)
        if kind == "end":
            spans += f'<tspan fill="{CYAN}">▋<animate attributeName="fill-opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1s" repeatCount="indefinite"/></tspan>'
        rows.append(f'<g clip-path="url(#l{i})">' + text(x0, y, spans, fs, INK, extra='xml:space="preserve" style="white-space:pre"') + "</g>")

    b = [
        f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="16" fill="{BG1}" stroke="{LINE}" stroke-width="1.5"/>',
        f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="16" fill="url(#grid)"/>',
        f'<path d="M1 46V17A16 16 0 0 1 17 1H{w - 17}A16 16 0 0 1 {w - 1} 17V46Z" fill="{BG2}"/>',
        f'<path d="M1 46H{w - 1}" stroke="{LINE}"/>',
        f'<circle cx="26" cy="23.5" r="6.5" fill="{ROSE}"/><circle cx="48" cy="23.5" r="6.5" fill="{AMBER}"/><circle cx="70" cy="23.5" r="6.5" fill="{CYAN}"/>',
        text(w / 2, 28.5, "fade@lab — ~/control-room", 13, FAINT, anchor="middle"),
        text(w - 28, 28.5, "zsh", 12, LINE2, anchor="end"),
    ]
    b += rows
    title = "Animated terminal: whoami, profile.json with experience, AI in production, research and contact, and current focus."
    return svg(w, h, title, "\n".join(b), "\n".join(clips))


# ------------------------------------------------------------------------ metrics

METRICS = [("5", "", "YEARS SHIPPING"), ("12", "", "PRODUCTION APPS"), ("12", "", "ENGINEERS LED"),
           ("100", "K+", "APP DOWNLOADS"), ("500", "+", "DOCS IN PROD RAG")]


def metrics():
    w, h = 1200, 176
    tw, gap = 228, 15
    fs, LH, base, dw = 60, 70, 100, 36
    defs, b = [], []
    for i, (num, suf, label) in enumerate(METRICS):
        tx = i * (tw + gap)
        b.append(f'<rect x="{tx + 1}" y="1" width="{tw - 2}" height="{h - 2}" rx="16" fill="{BG1}" stroke="{LINE}" stroke-width="1.5"/>')
        b.append(f'<rect x="{tx + 1}" y="1" width="{tw - 2}" height="{h - 2}" rx="16" fill="url(#grid)"/>')
        b.append(f'<rect x="{tx + 28}" y="0" width="{tw - 56}" height="2" fill="url(#accent)"/>')
        b.append(f'<circle cx="{tx + tw - 22}" cy="22" r="3.5" fill="{CYAN}">{blink(f"{1.4 + i * 0.2:.1f}s")}</circle>')

        suf_w = len(suf) * 40 * 0.62
        total = len(num) * dw + (2 + suf_w if suf else 0)
        xs = tx + tw / 2 - total / 2
        for j, ch in enumerate(num):
            d = int(ch)
            spins = 1 if j == 0 else 2
            ccx = xs + j * dw + dw / 2
            cid = f"c{i}{j}"
            defs.append(f'<clipPath id="{cid}"><rect x="{n(ccx - dw / 2)}" y="{base - 54}" width="{dw}" height="{LH}"/></clipPath>')
            strip = "".join(
                text(ccx, base + k * LH, str(k % 10), fs, INK, font=SANS, weight="800", anchor="middle")
                for k in range(spins * 10 + d + 1)
            )
            off = (spins * 10 + d) * LH
            b.append(
                f'<g clip-path="url(#{cid})"><g>{strip}'
                f'<animateTransform attributeName="transform" type="translate" values="0 0;0 -{off};0 -{off}" keyTimes="0;.16;1" '
                f'calcMode="spline" keySplines=".2 .7 .2 1;0 0 1 1" dur="14s" begin="{n(0.25 * i + 0.08 * j)}s" repeatCount="indefinite"/></g></g>'
            )
        if suf:
            b.append(text(xs + len(num) * dw + 2, base, suf, 40, CYAN, font=SANS, weight="800"))
        b.append(text(tx + tw / 2, 148, label, 12, FAINT, anchor="middle", spacing="2.4"))
    title = "5 years shipping, 12 production apps, 12 engineers led, 100K+ app downloads, 500+ documents in a production RAG system."
    return svg(w, h, title, "\n".join(b), "\n".join(defs))


# ---------------------------------------------------------------------------- RAG

def box(x, y, w, h, title, sub, stroke=LINE):
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{BG1}" stroke="{stroke}" stroke-width="1.5"/>'
        + text(x + 16, y + 34, esc(title), 17, INK, font=SANS, weight="600")
        + text(x + 16, y + 59, esc(sub), 11.5, MUTED)
    )


def arrow_r(x, y, color=LINE2):
    return f'<path d="M{x - 9} {y - 5}L{x - 1} {y}L{x - 9} {y + 5}Z" fill="{color}"/>'


def rag():
    w, h = 1200, 470
    bw, bh = 190, 80
    cols = [41, 273, 505, 737, 969]
    yI, yQ = 120, 300
    mI, mQ = yI + bh / 2, yQ + bh / 2
    qx = cols[2] + bw / 2

    b = [frame(w, h), '<g clip-path="url(#panel)">']
    b.append(text(41, 62, "// PRODUCTION RAG — WASTEKNOT AI ASSISTANT", 13, FAINT, spacing="2"))
    b.append(pill(w - 41, 42, "IN PRODUCTION", AMBER))
    b.append(text(41, yI - 14, "INGEST", 11, LINE2, spacing="3"))
    b.append(text(41, yQ - 14, "QUERY", 11, LINE2, spacing="3"))

    # connectors + traffic (drawn under the boxes, so packets vanish "into" each stage)
    ingest = f"M{cols[0] + bw} {mI}H{cols[2]}"
    query = f"M{cols[0] + bw} {mQ}H{cols[3]}"
    answer = f"M{cols[3] + bw} {mQ}H{cols[4]}"
    down = f"M{qx} {yI + bh}V{yQ}"
    for d in (ingest, query, answer, down):
        b.append(flow_line(d))
    for k in range(3):
        b.append(packet(ingest, 2.4, k * 0.8, CYAN))
        b.append(packet(query, 3.6, k * 1.2, VIOLET))
    b.append(packet(down, 1.2, 0, CYAN))
    b.append(packet(down, 1.2, 0.6, CYAN))
    b.append(packet(answer, 0.9, 0, AMBER))
    b.append(text(qx + 12, (yI + bh + yQ) / 2 + 4, "vector search", 11, FAINT))

    b.append(box(cols[0], yI, bw, bh, "500+ docs", "platform + compliance"))
    b.append(box(cols[1], yI, bw, bh, "Embedding", "OpenAI embeddings"))
    b.append(box(cols[2], yI, bw, bh, "Qdrant", "vectors + metadata", stroke=CYAN))
    b.append(box(cols[3], yI, cols[4] + bw - cols[3], bh, "AI agent · LangChain + LangGraph", "built and deployed on WasteKnot · in production", stroke=VIOLET))
    b.append(box(cols[0], yQ, bw, bh, "Question", "natural language"))
    b.append(box(cols[1], yQ, bw, bh, "Embed query", "query → vector"))
    b.append(box(cols[2], yQ, bw, bh, "Retrieve", "filter: org + doc type", stroke=CYAN))
    b.append(box(cols[3], yQ, bw, bh, "LLM", "grounded generation", stroke=VIOLET))
    b.append(box(cols[4], yQ, bw, bh, "Answer", "with source citations", stroke=AMBER))
    for x in cols[1:3]:
        b.append(arrow_r(x, mI))
    for x in cols[1:]:
        b.append(arrow_r(x, mQ))
    b.append(f'<path d="M{qx - 5} {yQ - 9}L{qx} {yQ - 1}L{qx + 5} {yQ - 9}Z" fill="{LINE2}"/>')

    b.append(text(41, 432, "python · openai embeddings · qdrant · metadata filtering by org + doc type · answers cite their sources", 12, FAINT))
    b.append("</g>")
    title = "Production RAG pipeline: 500+ documents embedded with OpenAI into Qdrant; questions are embedded, retrieved with org and doc-type filters, and answered by an LLM with source citations. Plus a LangChain/LangGraph agent in production."
    return svg(w, h, title, "\n".join(b))


# ----------------------------------------------------------------------- research

CONCEPTS = [("atypical pigment network", 2), ("blue-whitish veil", 2), ("atypical vascular pattern", 2),
            ("irregular streaks", 1), ("irregular dots/globules", 1), ("irregular blotches", 1), ("regression structures", 1)]


def lesion_path(cx, cy, rnd):
    pts = []
    for k in range(14):
        a = 2 * math.pi * k / 14
        r = 44 + rnd.uniform(-11, 11)
        pts.append((cx + r * math.cos(a), cy + r * 0.86 * math.sin(a)))
    d = f"M{n((pts[-1][0] + pts[0][0]) / 2)} {n((pts[-1][1] + pts[0][1]) / 2)}"
    for k, p in enumerate(pts):
        q = pts[(k + 1) % len(pts)]
        d += f"Q{n(p[0])} {n(p[1])} {n((p[0] + q[0]) / 2)} {n((p[1] + q[1]) / 2)}"
    return d + "Z"


def research():
    w, h = 1200, 440
    rnd = random.Random(3)
    cy = 242
    scx, sr = 132, 86
    defs = [
        f'<radialGradient id="lesion"><stop offset="0" stop-color="{VIOLET}" stop-opacity=".95"/><stop offset=".6" stop-color="#6d3fd6" stop-opacity=".7"/><stop offset="1" stop-color="{CYAN}" stop-opacity=".25"/></radialGradient>',
        f'<radialGradient id="skin"><stop offset="0" stop-color="{BG3}"/><stop offset="1" stop-color="{BG1}"/></radialGradient>',
        f'<clipPath id="scope"><circle cx="{scx}" cy="{cy}" r="{sr}"/></clipPath>',
    ]
    b = [frame(w, h), '<g clip-path="url(#panel)">']
    b.append(text(41, 62, "// PhD RESEARCH — NEURO-SYMBOLIC DERMOSCOPY", 13, FAINT, spacing="2"))
    b.append(pill(w - 41, 42, "EXPLAINABLE AI · SRM IST", VIOLET))

    # dermoscope view
    b.append(f'<circle cx="{scx}" cy="{cy}" r="{sr}" fill="url(#skin)" stroke="{LINE2}" stroke-width="1.5"/>')
    b.append(f'<g clip-path="url(#scope)">')
    b.append(f'<path d="{lesion_path(scx, cy, rnd)}" fill="url(#lesion)"><animate attributeName="opacity" values=".85;1;.85" dur="4s" repeatCount="indefinite"/></path>')
    for _ in range(9):
        a, r = rnd.uniform(0, 2 * math.pi), rnd.uniform(6, 34)
        b.append(f'<circle cx="{n(scx + r * math.cos(a))}" cy="{n(cy + r * math.sin(a))}" r="{n(rnd.uniform(1.5, 3.2))}" fill="{INK}" fill-opacity=".55"/>')
    b.append(f'<rect x="{scx - sr}" y="{cy - sr}" width="{2 * sr}" height="2" fill="{CYAN}" fill-opacity=".8" filter="url(#glow)">'
             f'<animate attributeName="y" values="{cy - sr};{cy + sr};{cy - sr}" dur="3.2s" repeatCount="indefinite"/></rect>')
    b.append("</g>")
    b.append(
        f'<circle cx="{scx}" cy="{cy}" r="{sr + 10}" fill="none" stroke="{CYAN}" stroke-opacity=".4" stroke-dasharray="3 7">'
        f'<animateTransform attributeName="transform" type="rotate" from="0 {scx} {cy}" to="360 {scx} {cy}" dur="20s" repeatCount="indefinite"/></circle>'
    )
    b.append(f'<path d="M{scx - sr - 16} {cy}H{scx - sr + 8}M{scx + sr - 8} {cy}H{scx + sr + 16}M{scx} {cy - sr - 16}V{cy - sr + 8}M{scx} {cy + sr - 8}V{cy + sr + 16}" stroke="{CYAN}" stroke-opacity=".6"/>')
    b.append(text(scx, 370, "DERMOSCOPIC IMAGE", 11, FAINT, anchor="middle", spacing="2"))

    # encoder: a narrowing stack of layers with flickering activations
    ex0, ex1 = 256, 362
    b.append(flow_line(f"M{scx + sr + 18} {cy}H{ex0 - 2}"))
    b.append(f'<path d="M{ex0} {cy - 72}L{ex1} {cy - 36}V{cy + 36}L{ex0} {cy + 72}Z" fill="{BG1}" stroke="{LINE2}" stroke-width="1.5"/>')
    for k in range(5):
        x = ex0 + 14 + k * 20
        half = 72 - (x - ex0) * 36 / (ex1 - ex0) - 10
        b.append(f'<path d="M{x} {n(cy - half)}V{n(cy + half)}" stroke="{CYAN}" stroke-width="3" stroke-linecap="round">'
                 f'<animate attributeName="stroke-opacity" values=".15;.9;.15" dur="1.6s" begin="{n(-k * 0.25)}s" repeatCount="indefinite"/></path>')
    b.append(text((ex0 + ex1) / 2, 370, "CNN ENCODER", 11, FAINT, anchor="middle", spacing="2"))

    # concept bottleneck: the 7-point checklist criteria
    lx, bx, bwid = 398, 590, 110
    ys = [130 + k * 38 for k in range(len(CONCEPTS))]
    ck_x, ck_y, ck_w, ck_h = 788, 182, 212, 120
    for k, ((name, weight), y) in enumerate(zip(CONCEPTS, ys)):
        b.append(f'<path d="M{ex1 + 2} {cy}C{ex1 + 22} {cy} {lx - 26} {y - 4} {lx - 6} {y - 4}" fill="none" stroke="{LINE2}" stroke-opacity=".6"/>')
        b.append(text(lx, y, esc(name), 12.5, MUTED))
        b.append(f'<rect x="{bx}" y="{y - 8}" width="{bwid}" height="8" rx="4" fill="{BG3}"/>')
        vals = ";".join(n(bwid * rnd.uniform(0.15, 0.95)) for _ in range(4))
        first = vals.split(";")[0]
        b.append(f'<rect x="{bx}" y="{y - 8}" width="{first}" height="8" rx="4" fill="{"url(#accent)" if weight == 2 else VIOLET}">'
                 f'<animate attributeName="width" values="{vals};{first}" dur="{n(5 + k * 0.4)}s" calcMode="spline" '
                 f'keySplines=".4 0 .2 1;.4 0 .2 1;.4 0 .2 1;.4 0 .2 1" repeatCount="indefinite"/></rect>')
        b.append(text(bx + bwid + 12, y, f"×{weight}", 12, AMBER if weight == 2 else FAINT))
        fan = f"M{bx + bwid + 40} {y - 4}C{bx + bwid + 70} {y - 4} {ck_x - 30} {cy} {ck_x - 2} {cy}"
        b.append(f'<path d="{fan}" fill="none" stroke="{LINE2}" stroke-opacity=".6"/>')
        b.append(packet(fan, 1.8, k * 0.26, CYAN if weight == 2 else VIOLET, r=2.6))
    b.append(text(lx, 104, "7-POINT CHECKLIST CONCEPTS", 11, LINE2, spacing="2.5"))

    # fixed symbolic layer
    b.append(f'<rect x="{ck_x}" y="{ck_y}" width="{ck_w}" height="{ck_h}" rx="14" fill="{BG1}" stroke="{VIOLET}" stroke-width="1.5"/>')
    b.append(f'<rect x="{ck_x}" y="{ck_y}" width="{ck_w}" height="{ck_h}" rx="14" fill="none" stroke="{VIOLET}" stroke-width="6" stroke-opacity=".12">'
             '<animate attributeName="stroke-opacity" values=".04;.25;.04" dur="2.4s" repeatCount="indefinite"/></rect>')
    b.append(text(ck_x + 18, ck_y + 44, f'<tspan fill="{VIOLET}" font-size="26">Σ</tspan> 7-point checklist', 16, INK, font=SANS, weight="600"))
    b.append(text(ck_x + 18, ck_y + 72, "fixed differentiable layer", 11.5, MUTED))
    b.append(text(ck_x + 18, ck_y + 94, "no free parameters", 11.5, MUTED))
    # padlock badge sitting on the top edge: the clinical relation is frozen
    lx_, ly_ = ck_x + ck_w - 30, ck_y
    b.append(f'<circle cx="{lx_}" cy="{ly_}" r="15" fill="{BG0}" stroke="{AMBER}" stroke-opacity=".6"/>'
             f'<path d="M{lx_ - 5} {ly_ - 1}V{ly_ - 5}A5 5 0 0 1 {lx_ + 5} {ly_ - 5}V{ly_ - 1}" fill="none" stroke="{AMBER}" stroke-width="1.8"/>'
             f'<rect x="{lx_ - 8}" y="{ly_ - 1}" width="16" height="11" rx="2.5" fill="{AMBER}"/>')

    # output
    dx, dy, dw_, dh = 1032, 196, 128, 92
    b.append(flow_line(f"M{ck_x + ck_w} {cy}H{dx}"))
    b.append(packet(f"M{ck_x + ck_w} {cy}H{dx}", 1.0, 0, AMBER))
    b.append(arrow_r(dx, cy))
    b.append(f'<rect x="{dx}" y="{dy}" width="{dw_}" height="{dh}" rx="12" fill="{BG1}" stroke="{AMBER}" stroke-width="1.5"/>')
    b.append(text(dx + 16, dy + 38, "Diagnosis", 16, INK, font=SANS, weight="600"))
    b.append(text(dx + 16, dy + 62, "auditable", 11.5, MUTED))
    b.append(text(dx + 16, dy + 78, "per case", 11.5, MUTED))

    b.append(text(w / 2, 412, "the clinical checklist IS the concept → diagnosis map: leakage is ruled out by construction, not penalised",
                  12.5, FAINT, anchor="middle"))
    b.append("</g>")
    title = "Neuro-symbolic dermoscopy model: a CNN encoder predicts the seven 7-point-checklist concepts, and a fixed differentiable checklist layer with no free parameters maps them to an auditable diagnosis."
    return svg(w, h, title, "\n".join(b), "\n".join(defs))


# ------------------------------------------------------------------------- footer

def footer():
    w, h = 1200, 100
    defs = (f'<linearGradient id="fl" x1="40" y1="0" x2="1160" y2="0" gradientUnits="userSpaceOnUse">'
            f'<stop offset="0" stop-color="{CYAN}" stop-opacity="0"/><stop offset=".3" stop-color="{CYAN}"/>'
            f'<stop offset=".7" stop-color="{VIOLET}"/><stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></linearGradient>')
    line = "M40 50H1160"
    b = [f'<path d="{line}" stroke="url(#fl)" stroke-width="1.5"/>']
    for k in range(4):
        b.append(packet(line, 6, k * 1.5, CYAN if k % 2 else VIOLET, r=3))
    b.append(f'<rect x="360" y="35" width="480" height="30" rx="15" fill="{BG0}" stroke="{LINE}"/>')
    b.append(text(600, 54.5, "END OF TRANSMISSION · THANKS FOR SCROLLING", 12, FAINT, anchor="middle", spacing="3"))
    return svg(w, h, "End of transmission. Thanks for scrolling.", "\n".join(b), defs)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in (("hero", hero), ("terminal", terminal), ("metrics", metrics),
                     ("rag-pipeline", rag), ("research", research), ("footer", footer)):
        (OUT / f"{name}.svg").write_text(fn(), encoding="utf-8")
        print("wrote", OUT / f"{name}.svg")
