#!/usr/bin/env python3
"""Render the animated SVG cards for the profile README.

Reads config.json, data/contributions.json and data/profile.json, then writes
cards/*.svg and README.md. Standard library only.

    python scripts/render_cards.py            # animated cards
    STATIC=1 python scripts/render_cards.py   # final frame, for screenshots
    python scripts/render_cards.py --sample   # made-up data, for local design work
"""
import base64
import datetime
import json
import math
import os
import pathlib
import random
import sys
import textwrap
from html import escape

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = json.loads((ROOT / "config.json").read_text())
CARDS = ROOT / "cards"
STATIC = os.environ.get("STATIC") == "1"

# ---------------------------------------------------------------- palette --
BG = "#0B1020"
PANEL = "#121A30"
BORDER = "#222C48"
TEXT = "#EEF1F7"
SOFT = "#B4BCCD"
MUTED = "#7F89A0"
MINT = "#3DDC97"
AMBER = "#FFB454"
EMPTY = "#161F38"
LEVELS = [EMPTY, "#14553F", "#1C8A62", "#2BBB82", MINT]

# ------------------------------------------------------------------ fonts --
FONTS = {
    "p4": ("Poppins", 400, "poppins-400.woff"),
    "p5": ("Poppins", 500, "poppins-500.woff"),
    "p7": ("Poppins", 700, "poppins-700.woff"),
    "m4": ("DejaVu Sans Mono", 400, "mono-400.woff"),
}


def font_css(keys):
    """Embed each font as a base64 data URI; an <img> SVG cannot load URLs."""
    out = []
    for key in keys:
        family, weight, filename = FONTS[key]
        b64 = base64.b64encode((ROOT / "fonts" / filename).read_bytes()).decode()
        out.append(
            f"@font-face{{font-family:'{family}';font-weight:{weight};"
            f"src:url(data:font/woff;base64,{b64}) format('woff')}}"
        )
    return "".join(out)


# The resting state of every element is its final frame, and each keyframe
# only describes where it starts from. Turning animation off (STATIC=1 or
# prefers-reduced-motion) therefore leaves the finished card.
BASE_CSS = f"""
text{{font-family:'Poppins',system-ui,sans-serif}}
.mono{{font-family:'DejaVu Sans Mono',ui-monospace,monospace}}
.b{{font-weight:700}}.m{{font-weight:500}}
.box{{transform-box:fill-box}}
.rise{{animation:rise .7s cubic-bezier(.2,.7,.2,1) both}}
.fade{{animation:fade .6s ease-out both}}
.pop{{transform-box:fill-box;transform-origin:center;animation:pop .45s cubic-bezier(.3,1.5,.5,1) both}}
.grow{{transform-box:fill-box;transform-origin:bottom;animation:grow .8s cubic-bezier(.2,.8,.2,1) both}}
.wipe{{transform-box:fill-box;transform-origin:left;animation:wipe .7s cubic-bezier(.2,.8,.2,1) both}}
.swing{{transform-box:fill-box;transform-origin:center;animation:swing .95s cubic-bezier(.2,.8,.2,1) both}}
.pulse{{animation:pulse 2s ease-in-out infinite}}
.blink{{animation:blink 1.1s steps(1) infinite}}
.nudge{{animation:nudge 2.4s ease-in-out infinite}}
.ring{{opacity:0;transform-box:fill-box;transform-origin:center;animation:ring 3s ease-out infinite}}
.sweep{{animation:sweep 6s ease-in-out infinite}}
.frame{{opacity:0;animation:frame .06s linear}}
.final{{animation:fade .01s linear both}}
@keyframes rise{{from{{opacity:0;transform:translateY(16px)}}}}
@keyframes fade{{from{{opacity:0}}}}
@keyframes pop{{from{{opacity:0;transform:scale(.2)}}}}
@keyframes grow{{from{{transform:scaleY(0)}}}}
@keyframes wipe{{from{{transform:scaleX(0)}}}}
@keyframes swing{{0%{{opacity:0;transform:translateY(70px) rotate(5deg)}}65%{{opacity:1;transform:translateY(-7px) rotate(-.8deg)}}100%{{transform:none}}}}
@keyframes pulse{{50%{{opacity:.25}}}}
@keyframes blink{{50%{{opacity:0}}}}
@keyframes nudge{{50%{{transform:translate(4px,-4px)}}}}
@keyframes ring{{0%{{opacity:.7;transform:scale(.5)}}70%,100%{{opacity:0;transform:scale(2.6)}}}}
@keyframes sweep{{0%,65%{{transform:translateX(0)}}100%{{transform:translateX(900px)}}}}
@keyframes frame{{from,to{{opacity:1}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
"""
if STATIC:
    BASE_CSS += "*{animation:none!important}"


def d(seconds):
    """Inline animation delay."""
    return f'style="animation-delay:{seconds:.3f}s"'


def card(width, height, body, fonts, label, radius=18):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" fill="{TEXT}" role="img" aria-label="{escape(label)}">'
        f"<title>{escape(label)}</title>"
        f"<style>{font_css(fonts)}{BASE_CSS}</style>"
        f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="{radius}" '
        f'fill="{BG}" stroke="{BORDER}" stroke-width="2"/>'
        f"{body}</svg>"
    )


def save(name, svg):
    CARDS.mkdir(exist_ok=True)
    (CARDS / f"{name}.svg").write_text(svg)
    print(f"cards/{name}.svg  {len(svg) / 1024:.0f} KB")


def clip(text, limit):
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "..."


# ------------------------------------------------------------------- data --
def sample_data():
    """Deterministic made-up year, only for designing without a token."""
    rng = random.Random(7)
    today = datetime.date.today()
    start = today - datetime.timedelta(days=364 + (today.weekday() + 1) % 7)
    days = []
    day = start
    while day <= today:
        busy = 0.62 + 0.25 * math.sin(day.toordinal() / 37)
        count = 0
        if rng.random() < busy:
            count = min(18, int(rng.expovariate(0.32)) + 1)
        days.append({"date": day.isoformat(), "count": count})
        day += datetime.timedelta(days=1)
    contributions = {"total": sum(x["count"] for x in days), "days": days}
    profile = {
        "public_repos": 73,
        "followers": 36,
        "repos": [
            {"name": "Task-pop", "description": "A small task-list app for Mac and Windows.",
             "url": "", "stars": 0, "forks": 0, "language": "JavaScript", "language_color": "#f1e05a"},
            {"name": "panda-commerce", "description": "", "url": "", "stars": 1, "forks": 0,
             "language": "HTML", "language_color": "#e34c26"},
            {"name": "LU_Covid-Tracker", "description": "All copyrights belong to Team Infinity",
             "url": "", "stars": 1, "forks": 2, "language": "Java", "language_color": "#b07219"},
            {"name": "Smart-Receptionist-System-CSE-Algorithm-Project-", "description": "",
             "url": "", "stars": 1, "forks": 0, "language": "C++", "language_color": "#f34b7d"},
        ],
    }
    return contributions, profile


def load_data():
    if "--sample" in sys.argv:
        return sample_data()
    try:
        contributions = json.loads((ROOT / "data" / "contributions.json").read_text())
        profile = json.loads((ROOT / "data" / "profile.json").read_text())
    except FileNotFoundError:
        sys.exit("No data yet. Run scripts/fetch_data.py first, or pass --sample.")
    return contributions, profile


def stats(days):
    """Streaks, active days, busiest day and the last 12 months."""
    counts = [x["count"] for x in days]
    longest = run = 0
    for count in counts:
        run = run + 1 if count else 0
        longest = max(longest, run)
    # Today may still be empty, so let the current streak end yesterday.
    tail = counts[:-1] if counts and counts[-1] == 0 else counts
    current = 0
    for count in reversed(tail):
        if not count:
            break
        current += 1
    best = max(days, key=lambda x: x["count"]) if days else {"date": "", "count": 0}
    months = {}
    for x in days:
        months[x["date"][:7]] = months.get(x["date"][:7], 0) + x["count"]
    last12 = sorted(months.items())[-12:]
    return {
        "current": current,
        "longest": longest,
        "active": sum(1 for c in counts if c),
        "best_day": best,
        "months": last12,
    }


# ------------------------------------------------------------------- hero --
# 5x7 pixel letters for the monogram.
GLYPHS = {
    "A": "01110 10001 10001 11111 10001 10001 10001",
    "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01111 10000 10000 10000 10000 10000 01111",
    "D": "11110 10001 10001 10001 10001 10001 11110",
    "E": "11111 10000 10000 11110 10000 10000 11111",
    "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01111 10000 10000 10011 10001 10001 01111",
    "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "11111 00100 00100 00100 00100 00100 11111",
    "J": "00111 00010 00010 00010 00010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001",
    "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001",
    "N": "10001 11001 10101 10011 10001 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110",
    "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10001 10101 10010 01101",
    "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110",
    "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110",
    "V": "10001 10001 10001 10001 10001 01010 00100",
    "W": "10001 10001 10001 10101 10101 11011 10001",
    "X": "10001 10001 01010 00100 01010 10001 10001",
    "Y": "10001 10001 01010 00100 00100 00100 00100",
    "Z": "11111 00001 00010 00100 01000 10000 11111",
}


def monogram(letters, right, top, height):
    """Pixel letters that assemble square by square, plus a blinking cursor."""
    letters = [c for c in letters.upper() if c in GLYPHS][:2] or ["R"]
    cols = len(letters) * 6          # 5 columns per letter + 1 spare
    pitch = height / 7
    size = pitch * 0.86
    left = right - cols * pitch
    out = []
    for index, letter in enumerate(letters):
        rows = GLYPHS[letter].split()
        for r in range(7):
            for c in range(5):
                x = left + (index * 6 + c) * pitch
                y = top + r * pitch
                lit = rows[r][c] == "1"
                delay = 0.5 + (r * 5 + c + index * 12) * 0.03
                out.append(
                    f'<rect class="pop" {d(delay)} x="{x:.1f}" y="{y:.1f}" width="{size:.1f}" '
                    f'height="{size:.1f}" rx="{size * .2:.1f}" fill="{MINT if lit else EMPTY}"/>'
                )
    cx = left + (cols - 1) * pitch
    cy = top + 6 * pitch
    out.append(
        f'<g class="fade" {d(1.8)}><rect class="blink" x="{cx:.1f}" y="{cy:.1f}" '
        f'width="{size:.1f}" height="{size:.1f}" rx="{size * .2:.1f}" fill="{AMBER}"/></g>'
    )
    return "".join(out)


def render_hero():
    w, h = 840, 300
    lines = "".join(
        f'<text class="rise" {d(0.75 + i * 0.12)} x="42" y="{240 + i * 26}" '
        f'font-size="16.5" fill="{SOFT}">{escape(clip(line, 62))}</text>'
        for i, line in enumerate(CONFIG.get("tagline", [])[:2])
    )
    body = (
        f'<circle class="pulse" cx="47" cy="50" r="5" fill="{MINT}"/>'
        f'<text class="mono fade" {d(0.1)} x="62" y="54.5" font-size="12.5" letter-spacing="2" '
        f'fill="{MINT}">{escape(CONFIG.get("kicker", ""))}</text>'
        f'<text class="rise" {d(0.2)} x="42" y="106" font-size="25" fill="{MUTED}">'
        f'{escape(CONFIG.get("greeting", ""))}</text>'
        f'<text class="b rise" {d(0.35)} x="38" y="184" font-size="84" letter-spacing="-2">'
        f'{escape(CONFIG["name"])}</text>'
        f'<rect class="wipe" {d(0.7)} x="42" y="202" width="72" height="6" rx="3" fill="{MINT}"/>'
        f"{lines}"
        f'{monogram(CONFIG.get("monogram", CONFIG["name"][:1]), 800, 48, 204)}'
    )
    save("hero", card(w, h, body, ["p4", "p7", "m4"], f'{CONFIG["name"]} - {CONFIG.get("kicker", "")}'))


# ------------------------------------------------------------------ tiles --
def count_up(value, x, y, size, start, color):
    """CSS cannot change text, so stack one <text> per frame and flash each."""
    attrs = f'class="b {{cls}}" x="{x}" y="{y}" font-size="{size}" letter-spacing="-2" fill="{color}"'
    frames = 18
    step = 0.05
    out = []
    for i in range(1, frames):
        eased = 1 - (1 - i / frames) ** 3
        shown = f"{round(value * eased):,}"
        out.append(f'<text {attrs.format(cls="frame")} {d(start + (i - 1) * step)}>{shown}</text>')
    out.append(f'<text {attrs.format(cls="final")} {d(start + (frames - 1) * step)}>{value:,}</text>')
    return "".join(out)


def render_tile(tile, value, delay):
    w, h = 400, 270
    color = tile["color"]
    body = (
        f'<defs><clipPath id="c"><rect x="2" y="2" width="{w - 4}" height="{h - 4}" rx="20"/></clipPath>'
        f'<linearGradient id="s" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="#fff" stop-opacity=".1"/>'
        f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>'
        f'<g class="swing" {d(delay)}>'
        f'<rect x="2" y="2" width="{w - 4}" height="{h - 4}" rx="20" fill="{PANEL}" stroke="{BORDER}" stroke-width="2"/>'
        f'<rect x="2" y="2" width="{w - 4}" height="8" fill="{color}" clip-path="url(#c)"/>'
        f'<g clip-path="url(#c)"><rect class="sweep" x="-260" y="0" width="180" height="{h}" '
        f'fill="url(#s)" transform="skewX(-18)"/></g>'
        f'<text class="mono" x="32" y="58" font-size="17" letter-spacing="3" fill="{color}">'
        f'{escape(tile["label"])}</text>'
        f'<circle class="ring" cx="{w - 52}" cy="52" r="20" fill="none" stroke="{color}" stroke-width="2"/>'
        f'<circle cx="{w - 52}" cy="52" r="20" fill="{BG}" stroke="{BORDER}" stroke-width="2"/>'
        f'<path class="nudge" d="M{w - 59} 59 L{w - 45} 45 M{w - 56} 45 H{w - 45} V56" fill="none" '
        f'stroke="{color}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>'
        f"{count_up(value, 30, 158, 84, delay + 0.45, TEXT)}"
        f'<text class="m" x="32" y="196" font-size="19" fill="{SOFT}">{escape(tile["caption"])}</text>'
        f'<line x1="32" y1="216" x2="{w - 32}" y2="216" stroke="{BORDER}" stroke-width="2"/>'
        f'<text x="32" y="246" font-size="16.5" fill="{MUTED}">{escape(clip(tile["sub"], 36))}</text>'
        f"</g>"
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'fill="{TEXT}" role="img" aria-label="{escape(tile["label"])}: {value:,} {escape(tile["caption"])}">'
        f'<style>{font_css(["p4", "p5", "p7", "m4"])}{BASE_CSS}</style>{body}</svg>'
    )
    save(tile["file"], svg)


# --------------------------------------------------------------- activity --
def render_activity(total, st):
    w, h = 840, 320
    months = st["months"]
    peak = max((v for _, v in months), default=0) or 1
    best = max(months, key=lambda kv: kv[1])[0] if months else ""
    left, base, top, slot = 44, 252, 108, 41
    bars = []
    for i, (key, value) in enumerate(months):
        height = max(4, (base - top) * value / peak)
        x = left + i * slot
        is_best = key == best
        delay = 1.4 + i * 0.05
        label = datetime.date(int(key[:4]), int(key[5:]), 1).strftime("%b")
        bars.append(
            f'<rect class="grow" {d(delay)} x="{x}" y="{base - height:.1f}" width="27" '
            f'height="{height:.1f}" rx="5" fill="{MINT if is_best else "#2A3556"}"/>'
            f'<text class="mono" x="{x + 13.5}" y="{base + 22}" font-size="11.5" text-anchor="middle" '
            f'fill="{TEXT if is_best else MUTED}">{label}</text>'
        )
        if is_best:
            bars.append(
                f'<text class="b pop" {d(delay + 0.8)} x="{x + 13.5}" y="{base - height - 10:.1f}" '
                f'font-size="15" text-anchor="middle" fill="{MINT}">{value:,}</text>'
            )
    best_day = st["best_day"]
    best_label = ""
    if best_day["date"]:
        when = datetime.date.fromisoformat(best_day["date"])
        best_label = f'{when.day} {when.strftime("%b")}'
    rows = [
        (f'{st["current"]}', "day streak right now"),
        (f'{st["longest"]}', "longest streak, days"),
        (f'{st["active"]}', "active days this year"),
        (f'{best_day["count"]}', f"busiest day, {best_label}"),
    ]
    side = "".join(
        f'<g class="rise" {d(1.7 + i * 0.12)}>'
        f'<text class="b" x="596" y="{104 + i * 52}" font-size="30" fill="{MINT if i == 0 else TEXT}">{value}</text>'
        f'<text x="676" y="{100 + i * 52}" font-size="13.5" fill="{MUTED}">{escape(label)}</text>'
        f"</g>"
        for i, (value, label) in enumerate(rows)
    )
    body = (
        f'<text class="mono fade" {d(1.3)} x="44" y="50" font-size="12.5" letter-spacing="2" '
        f'fill="{MINT}">CONTRIBUTIONS PER MONTH</text>'
        f'<text class="fade" {d(1.35)} x="44" y="78" font-size="15" fill="{MUTED}">'
        f'{total:,} in the last year</text>'
        f'<line x1="44" y1="{base + 1}" x2="{left + 12 * slot - 14}" y2="{base + 1}" stroke="{BORDER}" stroke-width="2"/>'
        f'<line x1="566" y1="44" x2="566" y2="{h - 44}" stroke="{BORDER}" stroke-width="2"/>'
        f'{"".join(bars)}{side}'
    )
    save("activity", card(w, h, body, ["p4", "p7", "m4"], f"{total:,} contributions in the last year"))


# ---------------------------------------------------------------- heatmap --
def render_heatmap(total, days):
    w, h = 840, 196
    if not days:
        return
    nonzero = sorted(x["count"] for x in days if x["count"])
    cuts = [nonzero[int(len(nonzero) * q)] for q in (0.25, 0.5, 0.75)] if nonzero else [1, 2, 3]

    def level(count):
        return 0 if not count else 1 + sum(count > cut for cut in cuts)

    first = datetime.date.fromisoformat(days[0]["date"])
    origin = first - datetime.timedelta(days=(first.weekday() + 1) % 7)   # back to Sunday
    pitch, size, left, top = 14.6, 11.6, 34, 70
    cells, labels, seen = [], [], set()
    for x in days:
        day = datetime.date.fromisoformat(x["date"])
        col = (day - origin).days // 7
        if col > 52:
            continue
        row = (day.weekday() + 1) % 7
        cells.append(
            f'<rect class="pop" {d(0.8 + col * 0.022 + row * 0.012)} x="{left + col * pitch:.1f}" '
            f'y="{top + row * pitch:.1f}" width="{size}" height="{size}" rx="3" fill="{LEVELS[level(x["count"])]}"/>'
        )
        key = (day.year, day.month)
        if day.day <= 7 and row == 0 and key not in seen and col < 51:
            seen.add(key)
            labels.append(
                f'<text class="mono" x="{left + col * pitch:.1f}" y="{top - 9}" font-size="10.5" '
                f'fill="{MUTED}">{day.strftime("%b")}</text>'
            )
    legend = "".join(
        f'<rect x="{w - 124 + i * 15}" y="35" width="11.6" height="11.6" rx="3" fill="{color}"/>'
        for i, color in enumerate(LEVELS)
    )
    body = (
        f'<text class="mono fade" {d(0.7)} x="34" y="45" font-size="12.5" letter-spacing="2" '
        f'fill="{MINT}">{total:,} CONTRIBUTIONS / LAST 12 MONTHS</text>'
        f'<text class="mono" x="{w - 162}" y="45" font-size="10.5" fill="{MUTED}">less</text>'
        f'{legend}<text class="mono" x="{w - 44}" y="45" font-size="10.5" fill="{MUTED}">more</text>'
        f'{"".join(labels)}{"".join(cells)}'
    )
    save("heatmap", card(w, h, body, ["m4"], f"Contribution graph: {total:,} in the last year"))


# ------------------------------------------------------------------ repos --
def render_repo(repo, index):
    w, h = 412, 170
    delay = 2.8 + index * 0.12
    description = textwrap.wrap(clip(repo["description"] or "No description yet.", 92), 46)[:2]
    lines = "".join(
        f'<text x="26" y="{84 + i * 22}" font-size="14.5" fill="{SOFT}">{escape(line)}</text>'
        for i, line in enumerate(description)
    )
    name = clip(repo["name"], 27)
    star = "M0 -7 L2 -2.2 L7 -2.2 L3 1 L4.5 6 L0 3 L-4.5 6 L-3 1 L-7 -2.2 L-2 -2.2 Z"
    body = (
        f'<g class="rise" {d(delay)}>'
        f'<path d="M26 28 h9 a2 2 0 0 1 2 2 v13 h-11 a2 2 0 0 1 -2 -2 v-11 a2 2 0 0 1 2 -2 z" '
        f'fill="none" stroke="{MUTED}" stroke-width="1.8"/>'
        f'<text class="b" x="48" y="45" font-size="20" fill="{MINT}">{escape(name)}</text>'
        f"{lines}"
        f'<circle class="pop" {d(delay + 0.5)} cx="32" cy="{h - 30}" r="6" fill="{escape(repo["language_color"])}"/>'
        f'<text class="mono" x="46" y="{h - 25.5}" font-size="12.5" fill="{MUTED}">'
        f'{escape(repo["language"] or "Code")}</text>'
        f'<path d="{star}" transform="translate({w - 122} {h - 30})" fill="{AMBER}"/>'
        f'<text class="mono" x="{w - 110}" y="{h - 25.5}" font-size="12.5" fill="{MUTED}">{repo["stars"]}</text>'
        f'<path d="M0 -6 v5 M-5 -6 v2 a3 3 0 0 0 3 3 h4 a3 3 0 0 0 3 -3 v-2 M0 -1 v6" '
        f'transform="translate({w - 66} {h - 30})" fill="none" stroke="{MUTED}" stroke-width="1.8" stroke-linecap="round"/>'
        f'<text class="mono" x="{w - 54}" y="{h - 25.5}" font-size="12.5" fill="{MUTED}">{repo["forks"]}</text>'
        f"</g>"
    )
    save(f"repo-{index + 1}", card(w, h, body, ["p4", "p7", "m4"], f'Repository {repo["name"]}', radius=16))


# ----------------------------------------------------------------- README --
def write_readme(repos):
    user = CONFIG["username"]
    tiles = "\n".join(
        f'  <a href="{t["link"]}"><img src="./cards/{t["file"]}.svg" width="32.5%" alt="{t["label"]}" /></a>'
        for t in CONFIG["tiles"]
    )
    links = [
        f'  <a href="https://github.com/{user}/{r["name"]}"><img src="./cards/repo-{i + 1}.svg" '
        f'width="48.5%" alt="{r["name"]}" /></a>'
        for i, r in enumerate(repos)
    ]
    # Two cards per paragraph, so rows keep a gap between them.
    repo_cards = "\n</p>\n\n<p align=\"center\">\n".join(
        "\n".join(links[i:i + 2]) for i in range(0, len(links), 2)
    )
    readme = f"""<!-- Generated by scripts/render_cards.py. Edit config.json or the script, not this file. -->
<p align="center">
  <a href="https://github.com/{user}"><img src="./cards/hero.svg" width="100%" alt="{CONFIG['name']}" /></a>
</p>

<p align="center">
  <img src="./cards/heatmap.svg" width="100%" alt="Contribution graph" />
</p>

<p align="center">
  <img src="./cards/activity.svg" width="100%" alt="Contributions per month" />
</p>

<p align="center">
{tiles}
</p>

<p align="center">
{repo_cards}
</p>
"""
    (ROOT / "README.md").write_text(readme)
    print("README.md")


# ------------------------------------------------------------------- main --
def main():
    contributions, profile = load_data()
    days = contributions["days"]
    total = contributions["total"]
    st = stats(days)
    values = {
        "public_repos": profile["public_repos"],
        "followers": profile["followers"],
        "total_contributions": total,
        "current_streak": st["current"],
        "active_days": st["active"],
    }

    for old in CARDS.glob("repo-*.svg"):
        old.unlink()

    render_hero()
    render_heatmap(total, days)
    render_activity(total, st)
    for i, tile in enumerate(CONFIG["tiles"][:3]):
        value = tile["value"]
        render_tile(tile, values[value] if isinstance(value, str) else int(value), 2.0 + i * 0.15)
    repos = profile["repos"][:4]
    for i, repo in enumerate(repos):
        render_repo(repo, i)
    write_readme(repos)


if __name__ == "__main__":
    main()
