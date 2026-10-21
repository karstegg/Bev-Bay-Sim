#!/usr/bin/env python3
"""Prototype helpers for the midi2sty mapper (standalone; imports nothing from midi2sty).

Two things live here (pure python, stdlib only):

1. ``classify_parts`` - decide which song parts are lead/melody/vocal/solo lines
   (NOT usable as accompaniment) vs drums / bass / chordal / pad.
2. ``find_sections`` - propose Intro / Main / Ending bar ranges from a song MIDI using a
   bar-level self-similarity matrix, drum density and instrumentation changes.

It carries its own tolerant SMF reader because ``midi2sty.smf`` currently
  * resets running status after meta events (NIKITA.mid / SACRIFIC.mid then fail to parse), and
  * ignores XG-sysex part programs (nitebirdsShakatak.mid has no Program Change events at
    all - voices are set with ``F0 43 1n 4C 08 pp 03 vv F7``).

Usage:  python tools/section_finder.py song.mid [more.mid ...] [--parts]
"""
from __future__ import annotations

import bisect
import math
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field


# ============================================================ tolerant SMF reader

@dataclass
class Part:
    track: int
    channel: int
    name: str = ""
    program: int | None = None          # program in force at the first note (GM PC or XG sysex)
    prog_events: list = field(default_factory=list)   # (tick, program)
    bank_msb: int | None = None
    notes: list = field(default_factory=list)   # (start_tick, dur_tick, pitch, vel)
    is_drums: bool = False

    @property
    def label(self) -> str:
        return f"t{self.track}/ch{self.channel + 1}"


@dataclass
class Midi:
    ppq: int
    parts: list
    ts_events: list           # (tick, num, den)
    tempo_events: list        # (tick, bpm)
    end_tick: int
    lyric_tracks: set = field(default_factory=set)
    bar_starts: list = field(default_factory=list)   # tick of each bar start (+ end sentinel)

    @property
    def nbars(self) -> int:
        return len(self.bar_starts) - 1


def _vlq(d: bytes, i: int) -> tuple[int, int]:
    v = 0
    while True:
        b = d[i]
        i += 1
        v = (v << 7) | (b & 0x7F)
        if not b & 0x80:
            return v, i


def read_midi(path: str) -> Midi:
    d = open(path, "rb").read()
    if d[:4] != b"MThd":
        raise ValueError("not a MIDI file")
    ppq = int.from_bytes(d[12:14], "big")
    pos = 8 + int.from_bytes(d[4:8], "big")
    parts: dict[tuple[int, int], Part] = {}
    ts, tempo, lyric_tracks = [], [], set()
    end_tick, tno = 0, 0
    while True:
        pos = d.find(b"MTrk", pos)
        if pos < 0:
            break
        i = pos + 8
        end = min(len(d), pos + 8 + int.from_bytes(d[pos + 4:pos + 8], "big"))
        t, running, tname = 0, 0, ""
        on: dict[tuple[int, int], tuple[int, int]] = {}
        pend_bank: dict[int, int] = {}
        while i < len(d):
            try:
                dt, i = _vlq(d, i)
                t += dt
                s = d[i]
                if s == 0xFF:
                    mt = d[i + 1]
                    n, j = _vlq(d, i + 2)
                    body = d[j:j + n]
                    i = j + n
                    if mt == 0x03 and not tname:
                        tname = body.decode("latin-1").strip("\x00 ")
                    elif mt == 0x51 and len(body) == 3:
                        tempo.append((t, 60_000_000 / max(1, int.from_bytes(body, "big"))))
                    elif mt == 0x58 and len(body) >= 2:
                        ts.append((t, body[0], 1 << body[1]))
                    elif mt == 0x05:
                        lyric_tracks.add(tno)
                    if mt == 0x2F:
                        break
                elif s in (0xF0, 0xF7):
                    n, j = _vlq(d, i + 1)
                    body = d[j:j + n]
                    i = j + n
                    running = 0
                    # XG multi-part program: 43 1n 4C 08 pp 03 vv   (bank MSB at 01)
                    if len(body) >= 7 and body[0] == 0x43 and body[2] == 0x4C and body[3] == 0x08:
                        p = parts.setdefault((tno, body[4] & 15), Part(tno, body[4] & 15))
                        if body[5] == 0x03 and body[6] < 128:
                            p.prog_events.append((t, body[6]))
                        elif body[5] == 0x01:
                            p.bank_msb = body[6]
                else:
                    if s & 0x80:
                        running = s
                        i += 1
                    st, ch = running & 0xF0, running & 15
                    if st in (0xC0, 0xD0):
                        a, b = d[i], 0
                        i += 1
                    else:
                        a, b = d[i], d[i + 1]
                        i += 2
                    if st in (0x80, 0x90):
                        key = (ch, a)
                        if st == 0x90 and b > 0:
                            if key in on:
                                _close(parts, tno, ch, a, on.pop(key), t)
                            on[key] = (t, b)
                        elif key in on:
                            _close(parts, tno, ch, a, on.pop(key), t)
                    elif st == 0xC0:
                        parts.setdefault((tno, ch), Part(tno, ch)).prog_events.append((t, a))
                    elif st == 0xB0 and a == 0:
                        parts.setdefault((tno, ch), Part(tno, ch)).bank_msb = b
            except IndexError:
                break
        for (ch, a), st_ in on.items():
            _close(parts, tno, ch, a, st_, t)
        end_tick = max(end_tick, t)
        for (tn, ch), p in parts.items():
            if tn == tno and not p.name:
                p.name = tname
        pos = max(i, end)
        tno += 1
    out = [p for p in parts.values() if p.notes]
    for p in out:
        p.is_drums = p.channel == 9
        p.notes.sort()
    # Program events may live on another track than the notes (XG sysex, conductor track):
    # pool them per channel, then take the last one at/before the part's first note
    # (initial setup values at tick 0 are overridden by later ones, as the synth would).
    pool: dict[int, list] = defaultdict(list)
    bank: dict[int, int] = {}
    for p in parts.values():
        pool[p.channel] += p.prog_events
        if p.bank_msb is not None:
            bank.setdefault(p.channel, p.bank_msb)
    for p in out:
        first = p.notes[0][0]
        evs = sorted(pool[p.channel])
        before = [v for tk, v in evs if tk <= first]
        p.program = before[-1] if before else (evs[0][1] if evs else None)
        if p.bank_msb is None:
            p.bank_msb = bank.get(p.channel)
    m = Midi(ppq, out, sorted(ts) or [(0, 4, 4)], sorted(tempo), end_tick, lyric_tracks)
    _bars(m)
    return m


def _close(parts, tno, ch, pitch, st, t):
    p = parts.setdefault((tno, ch), Part(tno, ch))
    p.notes.append((st[0], max(1, t - st[0]), pitch, st[1]))


def _bars(m: Midi) -> None:
    last = max((n[0] + n[1] for p in m.parts for n in p.notes), default=m.end_tick)
    starts, t = [], 0
    ts = list(m.ts_events)
    if ts[0][0] > 0:
        ts.insert(0, (0, 4, 4))
    k = 0
    while t <= last:
        while k + 1 < len(ts) and ts[k + 1][0] <= t:
            k += 1
        starts.append(t)
        t += m.ppq * 4 * ts[k][1] // ts[k][2]
    starts.append(t)
    m.bar_starts = starts


# ============================================================ per-bar part features

def bar_index(m: Midi, tick: int) -> int:
    return bisect.bisect_right(m.bar_starts, tick) - 1


def part_bar_notes(m: Midi, p: Part) -> dict[int, list]:
    out = defaultdict(list)
    for n in p.notes:
        b = bar_index(m, n[0])
        if 0 <= b < m.nbars:
            out[b].append(n)
    return out


# ============================================================ (1) melody / lead detection

_NAME_LEAD = re.compile(
    r"melod|\blead|vocal|\bvox\b|voice|\bsolo|\bsax|tenor|alto\b|soprano|flute|whistle|trumpet|"
    r"trombone|violin|oboe|clarinet|harmonica|theme|\bhook|singer|\bmel\b|flugel|fiddle|piccolo")
_NAME_NOT_LEAD = re.compile(r"bass|drum|perc|kick|\bpad|string|chord|comp\b|rhythm|rhy\b|organ|"
                            r"piano|keys|choir|strum|arp")
_GM_LEAD = set(range(56, 80)) | set(range(80, 88)) | {40, 41, 110, 111, 109, 21, 22, 23}
# 56-63 brass, 64-71 reeds (sax 64-67), 72-79 pipes, 80-87 synth lead, 40/41 solo violin/viola,
# 21-23 accordion/harmonica/bandoneon.  Choir/voice (52-54) is treated as backing, not lead.


def part_stats(m: Midi, p: Part) -> dict:
    ns = p.notes                                    # sorted by start
    nb = m.nbars or 1
    pitches = sorted(n[2] for n in ns)
    win = max(1, m.ppq // 8)                        # notes starting within 1/32 note = one onset
    starts = [n[0] for n in ns]
    clusters: list[tuple[int, list[int]]] = []      # (time, indexes)
    for i, n in enumerate(ns):
        if clusters and n[0] - clusters[-1][0] <= win:
            clusters[-1][1].append(i)
        else:
            clusters.append((n[0], [i]))
    # chordness = share of onsets at which >= 3 distinct pitch classes sound together (notes that
    # are still held count; octave doublings do not).  A lead line is ~0, comping/pads are high.
    triad = dyad = 0
    maxdur = max(n[1] for n in ns)
    slack = m.ppq // 8                              # legato overlap shorter than this is ignored
    for t, idx in clusters:
        lo = bisect.bisect_left(starts, t - maxdur)
        hi = bisect.bisect_right(starts, t + win)
        pcs = {ns[j][2] % 12 for j in range(lo, hi) if ns[j][0] + ns[j][1] > t + win + slack}
        pcs |= {ns[j][2] % 12 for j in idx}
        triad += len(pcs) >= 3
        dyad += len(pcs) >= 2
    triad /= len(clusters)
    dyad /= len(clusters)
    tops = [max(ns[j][2] for j in idx) for _, idx in clusters]
    iv = [abs(b - a) for a, b in zip(tops, tops[1:])]
    active = len({bar_index(m, n[0]) for n in ns})
    return dict(
        n=len(ns),
        med=pitches[len(pitches) // 2],
        poly=dyad,                                  # share of onsets with >= 2 pitch classes
        triad=triad,
        per_active_bar=len(ns) / max(1, active),
        active_frac=active / nb,
        leap=sum(iv) / len(iv) if iv else 0.0,
        big_leap_frac=sum(1 for x in iv if x >= 5) / len(iv) if iv else 0.0,
        repeat_frac=sum(1 for x in iv if x == 0) / len(iv) if iv else 0.0,
        dur_mean=sum(n[1] for n in ns) / len(ns) / m.ppq,
        pcs=len({x % 12 for x in pitches}),
    )


def gm_family(prog: int | None) -> str:
    if prog is None:
        return "?"
    if prog < 8: return "piano"
    if prog < 16: return "chrom-perc"
    if prog < 24: return "organ"
    if prog < 32: return "guitar"
    if prog < 40: return "bass"
    if prog < 48: return "strings"
    if prog < 56: return "ensemble/choir"
    if prog < 64: return "brass"
    if prog < 72: return "reed"
    if prog < 80: return "pipe"
    if prog < 88: return "synth-lead"
    if prog < 96: return "synth-pad"
    if prog < 104: return "synth-fx"
    return "ethnic/perc/sfx"


def classify_parts(m: Midi) -> list[dict]:
    """One dict per part: role in {drums, bass, chord, lead}, plus score and evidence.

    role 'lead' = melody / vocal / solo / hook line that must NOT be turned into accompaniment.
    tier 2 = score >= 5 (name or GM lead voice backed by content), tier 1 = 3 <= score < 5
    ('melody candidate': drop by default, but a human may want it as PHR).
    Evidence is evaluated per part (track+channel): name keywords, GM family (programs also
    read from XG sysex), monophony/chordness, register, sparsity, melodic motion.
    """
    rows = []
    for p in m.parts:
        st = part_stats(m, p)
        name = (p.name or "").lower()
        fam = gm_family(p.program)
        row = dict(part=p, stats=st, family=fam, role="chord", score=0.0, tier=0, why=[])
        if p.is_drums:
            row["role"] = "drums"
            rows.append(row)
            continue
        score, why = 0.0, row["why"]
        named = bool(_NAME_LEAD.search(name)) and not _NAME_NOT_LEAD.search(name)
        gm_lead = p.program in _GM_LEAD
        mono = st["poly"] < 0.15
        if named:
            score += 3
            why.append("name")
        if gm_lead:
            score += 1.5
            why.append(f"GM {fam}")
        if mono:
            score += 1
            why.append("monophonic")
        if st["med"] >= 66 and st["poly"] < 0.30:
            score += 1
            why.append("high register")
        elif 55 <= st["med"] < 66 and mono:
            score += 0.5
            why.append("melody register")
        if st["active_frac"] < 0.6 and mono:
            score += 0.5
            why.append("sparse")
        if mono and st["leap"] >= 1.8 and st["repeat_frac"] < 0.5:
            score += 1
            why.append("melodic motion")
        if mono and st["repeat_frac"] >= 0.6:
            score -= 1.5
            why.append("repeated-note ostinato (-)")
        if st["med"] < 52 and mono and not (named or gm_lead):
            score -= 2
            why.append("low register (-)")
        if st["triad"] >= 0.45 and not named:
            score -= 2
            why.append("chordal (-)")
        elif st["triad"] >= 0.45:
            score -= 1
        if fam == "bass" or "bass" in name:
            score -= 3
        row["score"] = score
        if fam == "bass" or "bass" in name or (st["med"] < 50 and mono and not (named or gm_lead)):
            row["role"] = "bass"
        elif score >= 3:
            row["role"] = "lead"
            row["tier"] = 2 if score >= 5 else 1
        rows.append(row)
    return rows


# ============================================================ (2) section finder

def _drum_class(p: int) -> int:
    if p in (35, 36):
        return 0
    if p in (37, 38, 39, 40):
        return 1
    if p in (42, 44, 46, 69, 70, 82, 54, 56, 51, 53, 59, 49, 57):
        return 2
    return 3


def bar_features(m: Midi, parts: list[Part], roles: dict[int, str]):
    """Per-bar feature dict: drum onset grid, per-part activity, chroma, counts."""
    nb = m.nbars
    grid = [[0.0] * 64 for _ in range(nb)]          # 4 drum classes x 16 steps
    pitched_grid = [[0.0] * 16 for _ in range(nb)]  # onsets of all non-lead pitched parts
    chroma = [[0.0] * 12 for _ in range(nb)]
    bass_chroma = [[0.0] * 12 for _ in range(nb)]
    active = [dict() for _ in range(nb)]
    drum_n = [0] * nb
    pitched_n = [0] * nb
    for idx, p in enumerate(parts):
        role = roles[idx]
        for (t, d, pitch, vel) in p.notes:
            b = bar_index(m, t)
            if not 0 <= b < nb:
                continue
            blen = m.bar_starts[b + 1] - m.bar_starts[b]
            step = int(round((t - m.bar_starts[b]) * 16 / blen)) % 16
            active[b][idx] = active[b].get(idx, 0) + 1
            if role == "drums":
                grid[b][_drum_class(pitch) * 16 + step] += 1
                drum_n[b] += 1
            elif role != "lead":
                pitched_n[b] += 1
                pitched_grid[b][step] += 1
                w = min(d, m.ppq * 2) / m.ppq
                (bass_chroma if role == "bass" else chroma)[b][pitch % 12] += w
    return dict(grid=grid, pgrid=pitched_grid, chroma=chroma, bchroma=bass_chroma,
                active=active, drum_n=drum_n, pitched_n=pitched_n)


def _cos(a, b):
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 1.0 if na == nb else 0.0
    return sum(x * y for x, y in zip(a, b)) / (na * nb)


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


def similarity_matrix(m: Midi, feats, nparts: int, roles) -> list[list[float]]:
    nb = m.nbars
    gv = [_smooth16(g) for g in feats["grid"]]
    pv = [_smooth16(g) for g in feats["pgrid"]]
    cv = [[a + b for a, b in zip(feats["chroma"][i], feats["bchroma"][i])] for i in range(nb)]
    av = []
    for i in range(nb):
        av.append([1.0 if j in feats["active"][i] else 0.0 for j in range(nparts)])
    S = [[0.0] * nb for _ in range(nb)]
    for i in range(nb):
        for j in range(i, nb):
            if not feats["drum_n"][i] and not feats["pitched_n"][i] or not feats["drum_n"][j] and not feats["pitched_n"][j]:
                s = 1.0 if i == j else 0.0
            else:
                # harmony (chroma) is the main section discriminator, then instrumentation,
                # then rhythm; drum grid mostly separates fills/breaks.
                s = (0.40 * _cos(cv[i], cv[j]) + 0.25 * _cos(av[i], av[j])
                     + 0.20 * _cos(pv[i], pv[j]) + 0.15 * _cos(gv[i], gv[j]))
            S[i][j] = S[j][i] = s
    return S


@dataclass
class Segment:
    start: int         # 0-based bar index, inclusive
    end: int           # exclusive
    cluster: int = -1  # segments with the same cluster id repeat musically (verse 2 ~ verse 1)
    label: str = ""
    density: float = 0.0
    fill_bar: int | None = None      # bar index of the break/fill that leads INTO this segment

    @property
    def bars(self):
        return self.end - self.start


def _novelty(S, nb, k=4):
    """Within-window minus cross-window similarity around each bar line (checkerboard kernel)."""
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
    """Bars whose drum count collapses (break) or spikes (fill) versus the song median."""
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


def _segment_boundaries(m, feats, S, first, last, min_len=8, thr=0.11):
    nb = m.nbars
    nov = _novelty(S, nb)
    for b in range(1, nb):   # instrumentation change between adjacent bars adds to novelty
        a, c = set(feats["active"][b - 1]), set(feats["active"][b])
        nov[b] += 0.25 * len(a ^ c) / max(1, len(a | c))
    marks = _marker_bars(feats, nb)
    for b in marks:           # a break/fill bar ends a section: boundary is on the next bar line
        if b + 1 < nb:
            nov[b + 1] += 0.06
    cand = sorted((b for b in range(first + 1, last) if nov[b] >= thr), key=lambda b: -nov[b])
    chosen = [first, last]
    for b in cand:
        if all(abs(b - c) >= min_len for c in chosen):
            chosen.append(b)
    return sorted(chosen), marks


def _segsim(S, a: Segment, b: Segment) -> float:
    n = min(a.bars, b.bars, 16)
    return sum(S[a.start + i][b.start + i] for i in range(n)) / n if n else 0.0


def find_sections(m: Midi, parts_info=None, min_len: int = 8):
    """Return (segments, ctx). Each segment has a cluster id and a proposed label."""
    info = parts_info or classify_parts(m)
    roles = {i: r["role"] for i, r in enumerate(info)}
    parts = [r["part"] for r in info]
    feats = bar_features(m, parts, roles)
    S = similarity_matrix(m, feats, len(parts), roles)
    nb = m.nbars
    busy = [feats["drum_n"][b] + feats["pitched_n"][b] >= 4 for b in range(nb)]   # ignore pickups
    first = next((b for b in range(nb) if busy[b]), 0)
    last = next((b for b in range(nb - 1, -1, -1) if busy[b]), nb - 1) + 1
    bounds, marks = _segment_boundaries(m, feats, S, first, last, min_len)
    # A solid lead (tier 2) that enters >= 4 bars after the band starts marks the end of an intro
    # that the self-similarity matrix cannot see (band already at full strength, e.g. NIKITA).
    entries = [min(bar_index(m, n[0]) for n in r["part"].notes)
               for r in info if r.get("tier") == 2]
    if entries:
        e = min(entries)
        if first + 4 <= e < bounds[1] - 2:
            bounds.insert(1, e)
    segs = [Segment(a, b) for a, b in zip(bounds, bounds[1:]) if b > a]
    for s in segs:
        s.density = sum(feats["drum_n"][b] + feats["pitched_n"][b] for b in range(s.start, s.end)) / s.bars
        if s.start - 1 in marks:
            s.fill_bar = s.start - 1
    _cluster(segs, S)
    _label(segs, feats, marks)
    return segs, dict(S=S, feats=feats, info=info, marks=marks)


def _cluster(segs, S, thr=0.78):
    cl = []
    for i, s in enumerate(segs):
        for c in cl:
            ref = segs[c[0]]
            if _segsim(S, ref, s) >= thr and abs(ref.bars - s.bars) <= max(2, ref.bars // 2):
                c.append(i)
                s.cluster = segs[c[0]].cluster if segs[c[0]].cluster >= 0 else len(cl)
                break
        else:
            s.cluster = len(cl)
            cl.append([i])


def _label(segs, feats, marks):
    """Intro = leading segment before the first full-band section; Ending = trailing short/unique
    segment; the rest are ordered by mean density -> Main A..D (clusters beyond 4 -> 'other')."""
    if not segs:
        return
    n = len(segs)
    dn = feats["drum_n"]
    by_cluster: dict[int, list[int]] = defaultdict(list)
    for i, s in enumerate(segs):
        by_cluster[s.cluster].append(i)
    intro = ending = None
    s0 = segs[0]
    if n > 1 and (len(by_cluster[s0.cluster]) == 1 and s0.bars <= 12
                  and s0.density < 0.95 * max(x.density for x in segs)):
        intro = 0
    sl = segs[-1]
    if n > 1 and len(by_cluster[sl.cluster]) == 1 and (sl.bars <= 12 or sl.density >= segs[-2].density):
        ending = n - 1
    pool = [c for c, idx in by_cluster.items() if any(i not in (intro, ending) for i in idx)]
    # most repeated (then densest) clusters become Mains; keep at most 4
    pool.sort(key=lambda c: (-sum(1 for i in by_cluster[c] if i not in (intro, ending)),
                             -sum(segs[i].density for i in by_cluster[c])))
    keep = pool[:4]
    keep.sort(key=lambda c: sum(segs[i].density for i in by_cluster[c]) / len(by_cluster[c]))
    name = {c: "Main " + "ABCD"[r] for r, c in enumerate(keep)}
    for i, s in enumerate(segs):
        if i == intro:
            s.label = "Intro"
        elif i == ending:
            s.label = "Ending"
        else:
            s.label = name.get(s.cluster, "other")


def propose_ranges(segs, feats, marks, loop_bars: int = 4):
    """Turn segments into the ranges a style would use: (name -> (first_bar, last_bar) 1-based,
    inclusive).  Mains: the `loop_bars`-bar window of the cluster closest to its centroid,
    avoiding break/fill bars.  Fill = the break/fill bar that leads into that main (if any)."""
    out = {}
    for s in segs:
        if s.label.startswith("Main") and s.label not in out:
            members = [x for x in segs if x.cluster == s.cluster]
            for x in members:   # prefer a member that starts right after a fill/break bar
                if x.fill_bar is not None:
                    s = x
                    break
            a = s.start
            b = min(s.end, a + loop_bars)
            out[s.label] = (a + 1, b)
            if s.fill_bar is not None:
                out["Fill In " + s.label[-1] + s.label[-1]] = (s.fill_bar + 1, s.fill_bar + 1)
        elif s.label in ("Intro", "Ending") and s.label not in out:
            end = s.end - 1 if (s.end - 1) in marks and s.label == "Intro" else s.end
            a = s.start if s.label == "Intro" else max(s.start, s.end - loop_bars)
            b = min(end, a + (loop_bars * 2 if s.label == "Intro" else loop_bars))
            out[s.label] = (a + 1, b)
    if "Ending" not in out and segs:       # last section repeats a Main: still end on its last bars
        e = segs[-1].end
        out["Ending"] = (max(segs[-1].start, e - loop_bars) + 1, e)
    return out


# ============================================================ CLI

def _fmt_bars(s: Segment) -> str:
    return f"bars {s.start + 1:>3}-{s.end:<3} ({s.bars:>2})"   # 1-based inclusive


def report(path: str, show_parts: bool = True) -> None:
    m = read_midi(path)
    info = classify_parts(m)
    print(f"== {os.path.basename(path)}  ppq={m.ppq} bars={m.nbars} ts={m.ts_events[0][1:]} "
          f"tempo~{m.tempo_events[0][1] if m.tempo_events else 120:.0f}")
    if show_parts:
        for r in info:
            p, st = r["part"], r["stats"]
            print(f"  {p.label:9} {p.name[:16]:16} prog={p.program!s:>4} {r['family']:14} n={st['n']:5d} "
                  f"med={st['med']:3d} poly={st['poly']:.2f} act={st['active_frac']:.2f} "
                  f"leap={st['leap']:4.1f} -> {r['role']:6} {r['score']:+.1f} {','.join(r['why'])}")
    segs, ctx = find_sections(m, info)
    for s in segs:
        fb = f" fill/break bar {s.fill_bar + 1}" if s.fill_bar is not None else ""
        print(f"  {_fmt_bars(s)}  {s.label:8} cluster {chr(65 + s.cluster % 26)} density {s.density:6.1f}{fb}")
    print("  proposed ranges:", ", ".join(f"{k} {a}-{b}" for k, (a, b) in
                                        propose_ranges(segs, ctx["feats"], ctx["marks"]).items()))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    for a in args:
        report(a, show_parts="--no-parts" not in sys.argv)
