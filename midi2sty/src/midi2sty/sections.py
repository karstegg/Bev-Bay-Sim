"""Propose song-bar ranges for style sections (port of tools/section_finder.py onto model.Song).

``propose_sections(song)`` -> {name: (start_bar, n_bars)}, bars 0-based. Keys:
  "Main A".."Main D"   4-bar (or 2/1) window of each repeated section cluster, ordered by density
                       (fewer than 4 keys if the song has fewer distinct sections)
  "Fill In AA".. etc   the break/fill bar leading into that Main, when the song has one
  "Intro"              the song's own intro segment, "Intro C" its last <= 8 bars (>= 2 bars)
  "Ending"             trailing segment, "Ending C" its last 4 bars
Method: per-bar features (drum grid, pitched grid, chroma, active parts) -> bar x bar similarity ->
checkerboard novelty + instrumentation change -> boundaries >= 8 bars apart -> clustering of repeated
segments. Constant time signature assumed. Weak on songs with very long sections or tempo/time changes.
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass

from . import model
from .melody import bar_ticks, classify_parts, n_bars


@dataclass
class Segment:
    start: int
    end: int
    cluster: int = -1
    label: str = ""
    density: float = 0.0
    fill_bar: int | None = None

    @property
    def bars(self) -> int:
        return self.end - self.start


def _drum_class(p: int) -> int:
    if p in (35, 36):
        return 0
    if p in (37, 38, 39, 40):
        return 1
    if p in (42, 44, 46, 69, 70, 82, 54, 56, 51, 53, 59, 49, 57):
        return 2
    return 3


def _unit(v):
    n = math.sqrt(sum(x * x for x in v))
    return [x / n for x in v] if n else None


def _cos(a, b):
    if a is None or b is None:
        return 1.0 if a is None and b is None else 0.0
    return sum(x * y for x, y in zip(a, b))


def _smooth16(v):
    out = [0.0] * len(v)
    for i, x in enumerate(v):
        if x:
            base = i - i % 16
            for j in (-1, 0, 1):
                k = i % 16 + j
                if 0 <= k < 16:
                    out[base + k] += x * (1.0 if j == 0 else 0.5)
    return out


def _features(song, info, nb, bl):
    ppq = model.TICKS_PER_BEAT
    grid = [[0.0] * 64 for _ in range(nb)]
    pgrid = [[0.0] * 16 for _ in range(nb)]
    chroma = [[0.0] * 12 for _ in range(nb)]
    active = [dict() for _ in range(nb)]
    drum_n = [0] * nb
    pitched_n = [0] * nb
    for tr, row in zip(song.tracks, info):
        role = row["role"]
        for n in tr.notes:
            b = n.start // bl
            if not 0 <= b < nb:
                continue
            step = int(round((n.start - b * bl) * 16 / bl)) % 16
            active[b][tr.index] = active[b].get(tr.index, 0) + 1
            if role == "drums":
                grid[b][_drum_class(n.pitch) * 16 + step] += 1
                drum_n[b] += 1
            elif role != "lead":
                pitched_n[b] += 1
                pgrid[b][step] += 1
                chroma[b][n.pitch % 12] += min(n.dur, ppq * 2) / ppq
    return dict(grid=grid, pgrid=pgrid, chroma=chroma, active=active, drum_n=drum_n,
                pitched_n=pitched_n)


def _similarity(feats, nb, ntracks):
    gv = [_unit(_smooth16(g)) for g in feats["grid"]]
    pv = [_unit(_smooth16(g)) for g in feats["pgrid"]]
    cv = [_unit(c) for c in feats["chroma"]]
    av = [_unit([1.0 if j in feats["active"][i] else 0.0 for j in range(ntracks)]) for i in range(nb)]
    empty = [not feats["drum_n"][i] and not feats["pitched_n"][i] for i in range(nb)]
    S = [[0.0] * nb for _ in range(nb)]
    for i in range(nb):
        for j in range(i, nb):
            if empty[i] or empty[j]:
                s = 1.0 if i == j else 0.0
            else:
                s = (0.40 * _cos(cv[i], cv[j]) + 0.25 * _cos(av[i], av[j])
                     + 0.20 * _cos(pv[i], pv[j]) + 0.15 * _cos(gv[i], gv[j]))
            S[i][j] = S[j][i] = s
    return S


def _novelty(S, nb, k=4):
    nov = [0.0] * (nb + 1)
    for b in range(1, nb):
        L = range(max(0, b - k), b)
        R = range(b, min(nb, b + k))
        if len(L) < 2 or len(R) < 2:
            continue
        within = (sum(S[x][y] for x in L for y in L) / len(L) ** 2
                  + sum(S[x][y] for x in R for y in R) / len(R) ** 2) / 2
        cross = sum(S[x][y] for x in L for y in R) / (len(L) * len(R))
        nov[b] = within - cross
    return nov


def _marker_bars(feats, nb):
    dn = feats["drum_n"]
    live = sorted(x for x in dn if x)
    med = live[len(live) // 2] if live else 0
    marks = {}
    for b in range(nb):
        if not med or not dn[b]:
            continue
        if dn[b] < 0.35 * med:
            marks[b] = "break"
        elif dn[b] >= 1.25 * med:
            marks[b] = "fill"
    return marks


def _segsim(S, a, b):
    n = min(a.bars, b.bars, 16)
    return sum(S[a.start + i][b.start + i] for i in range(n)) / n if n else 0.0


def _cluster(segs, S, thr=0.78):
    cl: list[list[int]] = []
    for i, s in enumerate(segs):
        for c in cl:
            ref = segs[c[0]]
            if _segsim(S, ref, s) >= thr and abs(ref.bars - s.bars) <= max(2, ref.bars // 2):
                c.append(i)
                s.cluster = ref.cluster
                break
        else:
            s.cluster = len(cl)
            cl.append([i])


def _label(segs):
    n = len(segs)
    by_cluster: dict[int, list[int]] = defaultdict(list)
    for i, s in enumerate(segs):
        by_cluster[s.cluster].append(i)
    intro = ending = None
    if n > 1 and (len(by_cluster[segs[0].cluster]) == 1 and segs[0].bars <= 12
                  and segs[0].density < 0.95 * max(x.density for x in segs)):
        intro = 0
    sl = segs[-1]
    if n > 1 and len(by_cluster[sl.cluster]) == 1 and (sl.bars <= 12 or sl.density >= segs[-2].density):
        ending = n - 1
    pool = [c for c, idx in by_cluster.items() if any(i not in (intro, ending) for i in idx)]
    pool.sort(key=lambda c: (-sum(1 for i in by_cluster[c] if i not in (intro, ending)),
                             -sum(segs[i].density for i in by_cluster[c])))
    keep = pool[:4]
    keep.sort(key=lambda c: sum(segs[i].density for i in by_cluster[c]) / len(by_cluster[c]))
    name = {c: "Main " + "ABCD"[r] for r, c in enumerate(keep)}
    for i, s in enumerate(segs):
        s.label = "Intro" if i == intro else "Ending" if i == ending else name.get(s.cluster, "other")


def analyse(song: model.Song):
    """Return (segments, ctx) with ctx = dict(info, marks, first, last, nb, bl, lead_entry)."""
    nb, bl = n_bars(song), bar_ticks(song)
    info = classify_parts(song)
    if nb == 0:
        return [], dict(info=info, marks={}, first=0, last=0, nb=0, bl=bl, lead_entry=None)
    feats = _features(song, info, nb, bl)
    S = _similarity(feats, nb, len(song.tracks))
    busy = [feats["drum_n"][b] + feats["pitched_n"][b] >= 4 for b in range(nb)]
    first = next((b for b in range(nb) if busy[b]), 0)
    last = next((b for b in range(nb - 1, -1, -1) if busy[b]), nb - 1) + 1
    nov = _novelty(S, nb)
    for b in range(1, nb):
        a, c = set(feats["active"][b - 1]), set(feats["active"][b])
        nov[b] += 0.25 * len(a ^ c) / max(1, len(a | c))
    marks = _marker_bars(feats, nb)
    for b in marks:
        if b + 1 < nb:
            nov[b + 1] += 0.06
    cand = sorted((b for b in range(first + 1, last) if nov[b] >= 0.11), key=lambda b: -nov[b])
    bounds = [first, last]
    for b in cand:
        if all(abs(b - c) >= 8 for c in bounds):
            bounds.append(b)
    bounds.sort()
    tr_by_idx = {t.index: t for t in song.tracks}
    entries = {r["tier"]: [] for r in info}
    for r in info:
        t = tr_by_idx[r["index"]]
        if r["tier"] and t.notes:
            entries[r["tier"]].append(min(n.start for n in t.notes) // bl)
    e2 = min(entries.get(2, []), default=None)
    e1 = min(entries.get(1, []) + entries.get(2, []), default=None)
    if e2 is not None and first + 4 <= e2 < bounds[1] - 2:
        bounds.insert(1, e2)
    segs = [Segment(a, b) for a, b in zip(bounds, bounds[1:]) if b > a]
    for s in segs:
        s.density = sum(feats["drum_n"][b] + feats["pitched_n"][b]
                        for b in range(s.start, s.end)) / s.bars
        if s.start - 1 in marks:
            s.fill_bar = s.start - 1
    if segs:
        _cluster(segs, S)
        _label(segs)
    return segs, dict(info=info, marks=marks, first=first, last=last, nb=nb, bl=bl,
                      lead_entry=e1, feats=feats)


def _window(s: Segment, marks, want=4):
    n = min(want, s.bars)
    if n == 3:
        n = 2
    best = s.start
    for off in range(0, max(0, min(4, s.bars - n)) + 1):
        a = s.start + off
        if not any(b in marks for b in range(a, a + n)):
            best = a
            break
    return best, n


def propose_sections(song: model.Song) -> dict[str, tuple[int, int]]:
    segs, ctx = analyse(song)
    out: dict[str, tuple[int, int]] = {}
    if not segs:
        return out
    marks = ctx["marks"]
    for s in segs:
        if s.label.startswith("Main") and s.label not in out:
            members = [x for x in segs if x.cluster == s.cluster]
            for x in members:
                if x.fill_bar is not None:
                    s = x
                    break
            a, n = _window(s, marks)
            out[s.label] = (a, n)
            if s.fill_bar is not None:
                out["Fill In " + s.label[-1] * 2] = (s.fill_bar, 1)
    intro = next((s for s in segs if s.label == "Intro"), None)
    if intro is not None:
        i_end = intro.end - 1 if (intro.end - 1) in marks else intro.end
        out["Intro"] = (intro.start, max(1, i_end - intro.start))
    elif ctx["lead_entry"] is not None and ctx["lead_entry"] - ctx["first"] >= 4:
        out["Intro"] = (ctx["first"], ctx["lead_entry"] - ctx["first"])
    if "Intro" in out:
        a, n = out["Intro"]
        if n >= 2:
            k = min(8, n)
            out["Intro C"] = (a + n - k, k)
    last = segs[-1]
    out["Ending"] = (last.start, last.bars)
    k = min(4, last.bars) if last.bars >= 2 else min(4, ctx["last"])
    if k >= 2:
        out["Ending C"] = (ctx["last"] - k, k)
    return out
