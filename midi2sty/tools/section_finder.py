#!/usr/bin/env python3
"""Prototype helpers for the midi2sty mapper (standalone; imports nothing from midi2sty).

Two things live here, both pure python + numpy-free (stdlib only):

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
import sys
from collections import Counter, defaultdict
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

GM_LEAD_FAMILIES = (
    range(56, 80),    # brass (56-63), reed (64-71: sax 64-67, oboe, clarinet), pipe (72-79: flute..)
    range(80, 88),    # synth lead
    range(40, 42),    # violin / viola (solo)
    range(105, 112),  # banjo, shamisen .. ethnic leads (kalimba, fiddle, shanai)
    range(110, 112),  # fiddle, shanai
    range(52, 55),    # choir aahs / voice oohs / synth voice (vocals)
    range(24, 26),    # n/a placeholder, replaced below
)
_NAME_LEAD = ("melod", "lead", "vocal", "vox", "voice", "solo", "sax", "flute", "trumpet",
              "trombone", "violin", "oboe", "clarinet", "harmonica", "whistle", "main",
              "singer", "chorus", "backing", "bv", "mel", "hook", "theme", "flugel", "horn")
_NAME_NOT_LEAD = ("bass", "drum", "perc", "kick", "pad", "string", "chord", "comp", "rhythm",
                  "rhy", "organ", "piano", "pno", "keys", "gtr rhy", "strum", "arp")


def part_stats(m: Midi, p: Part) -> dict:
    ns = p.notes
    nb = m.nbars or 1
    pitches = [n[2] for n in ns]
    # polyphony: share of notes that overlap the next-starting one by > 1/16 note
    sixteenth = m.ppq // 4
    poly = 0
    for i in range(len(ns) - 1):
        a, b = ns[i], ns[i + 1]
        if b[0] < a[0] + a[1] - sixteenth // 2 and b[0] - a[0] > 0:
            poly += 1
        elif b[0] == a[0]:
            poly += 1
    simul = Counter(n[0] // max(1, sixteenth // 2) for n in ns)
    stack = sum(1 for v in simul.values() if v > 1) / max(1, len(simul))
    # melodic line: successive distinct onsets, top voice
    tops = {}
    for n in ns:
        k = n[0] // max(1, sixteenth // 2)
        tops[k] = max(tops.get(k, 0), n[2])
    seq = [tops[k] for k in sorted(tops)]
    iv = [abs(b - a) for a, b in zip(seq, seq[1:])]
    active = len({bar_index(m, n[0]) for n in ns})
    return dict(
        n=len(ns),
        med=sorted(pitches)[len(pitches) // 2],
        hi=sorted(pitches)[int(len(pitches) * .9)],
        poly=max(poly / len(ns), stack),
        stack=stack,
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
    """Return one dict per part: role in {drums, bass, chord, lead} plus the evidence.

    Evidence (all must be evaluated per *part*, i.e. track+channel):
      name keywords, GM family (reed/pipe/brass/synth-lead/choir are lead-ish; guitar/piano/organ
      are ambiguous so only content counts), monophony, register, sparsity, melodic motion.
    score >= 3 => lead.  The thresholds were tuned on the 20 MIDIs in the reference folder.
    """
    rows = []
    for p in m.parts:
        st = part_stats(m, p)
        name = (p.name or "").lower()
        fam = gm_family(p.program)
        row = dict(part=p, stats=st, family=fam, role="chord", score=0.0, why=[])
        if p.is_drums:
            row["role"] = "drums"
            rows.append(row)
            continue
        score, why = 0.0, row["why"]
        if any(k in name for k in _NAME_LEAD) and not any(k in name for k in _NAME_NOT_LEAD):
            score += 3
            why.append("name")
        if fam in ("reed", "pipe", "brass", "synth-lead") or p.program in (40, 41, 52, 53, 54, 110, 111, 12, 109):
            score += 1.5
            why.append(f"GM {fam}")
        mono = st["poly"] < 0.15
        if mono:
            score += 1
            why.append("monophonic")
        if st["med"] >= 66 and st["poly"] < 0.30:
            score += 1
            why.append("high register")
        if st["active_frac"] < 0.6 and mono:
            score += 0.5
            why.append("sparse (not on every bar)")
        if mono and st["leap"] >= 2.0 and st["big_leap_frac"] >= 0.15 and st["repeat_frac"] < 0.5:
            score += 1
            why.append("melodic motion")
        if mono and st["repeat_frac"] >= 0.6:
            score -= 1.5
            why.append("repeated-note ostinato (-)")
        if st["med"] < 52 and mono:
            score -= 2
            why.append("low register (-)")
        if st["poly"] >= 0.45:
            score -= 2
            why.append("chordal (-)")
        if fam == "bass" or "bass" in name:
            score -= 3
        row["score"] = score
        # role without lead: bass / chord
        if fam == "bass" or "bass" in name or (st["med"] < 50 and mono):
            row["role"] = "bass"
        if score >= 3 and row["role"] != "bass":
            row["role"] = "lead"
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
    start: int
    end: int           # exclusive bar
    label: str = ""
    density: float = 0.0
    kind: str = ""

    @property
    def bars(self):
        return self.end - self.start


def _segment_boundaries(m: Midi, feats, S, min_len: int = 4) -> list[int]:
    nb = m.nbars
    # novelty from a checkerboard kernel over the self-similarity matrix (kernel half-width 4)
    k = 4
    nov = [0.0] * (nb + 1)
    for b in range(1, nb):
        v = 0.0
        for i in range(1, k + 1):
            for j in range(1, k + 1):
                if b - i >= 0 and b + j - 1 < nb:
                    v += S[b - i][b - j] + S[b + i - 1][b + j - 1] if False else 0.0
        # simple robust form: within-window similarity minus cross-window similarity
        L = [x for x in range(max(0, b - k), b)]
        R = [x for x in range(b, min(nb, b + k))]
        if len(L) < 2 or len(R) < 2:
            continue
        within = (sum(S[x][y] for x in L for y in L) / len(L) ** 2
                  + sum(S[x][y] for x in R for y in R) / len(R) ** 2) / 2
        cross = sum(S[x][y] for x in L for y in R) / (len(L) * len(R))
        nov[b] = within - cross
    # instrumentation change: parts newly active or dropped between adjacent bars
    for b in range(1, nb):
        a, c = set(feats["active"][b - 1]), set(feats["active"][b])
        nov[b] += 0.08 * len(a ^ c) / max(1, len(a | c)) * 4
    # structural silence / break bars (drum density collapse) mark a boundary on the bar after
    dn = feats["drum_n"]
    med = sorted(x for x in dn if x)[len(dn) // 2] if any(dn) else 0
    for b in range(1, nb):
        if med and dn[b - 1] < 0.35 * med and dn[b] >= 0.6 * med:
            nov[b] += 0.5
    # pick peaks, greedy, enforce min_len
    cand = sorted(range(1, nb), key=lambda b: -nov[b])
    thr = 0.12
    chosen = [0, nb]
    for b in cand:
        if nov[b] < thr:
            break
        if all(abs(b - c) >= min_len for c in chosen):
            chosen.append(b)
    return sorted(chosen)


def find_sections(m: Midi, parts_info=None, verbose=False):
    """Return (segments, info). Segments carry a proposed label and bar range."""
    info = parts_info or classify_parts(m)
    roles = {i: r["role"] for i, r in enumerate(info)}
    parts = [r["part"] for r in info]
    feats = bar_features(m, parts, roles)
    S = similarity_matrix(m, feats, len(parts), roles)
    nb = m.nbars
    # trim leading / trailing empty bars
    first = next((b for b in range(nb) if feats["drum_n"][b] or feats["pitched_n"][b]), 0)
    last = next((b for b in range(nb - 1, -1, -1) if feats["drum_n"][b] or feats["pitched_n"][b]), nb - 1) + 1
    bounds = [b for b in _segment_boundaries(m, feats, S) if first < b < last]
    bounds = [first] + bounds + [last]
    segs = [Segment(a, b) for a, b in zip(bounds, bounds[1:]) if b > a]
    # merge tiny segments (<3 bars) into the neighbour that is more similar
    changed = True
    while changed and len(segs) > 1:
        changed = False
        for i, s in enumerate(segs):
            if s.bars < 3:
                j = i - 1 if i > 0 and (i == len(segs) - 1 or _segsim(S, segs[i - 1], s) >= _segsim(S, s, segs[i + 1])) else i + 1
                lo, hi = sorted((i, j))
                segs[lo] = Segment(segs[lo].start, segs[hi].end)
                del segs[hi]
                changed = True
                break
    for s in segs:
        s.density = sum(feats["drum_n"][b] + feats["pitched_n"][b] for b in range(s.start, s.end)) / s.bars
    _label(segs, S, feats)
    return segs, dict(S=S, feats=feats, info=info)


def _segsim(S, a: Segment, b: Segment) -> float:
    n = min(a.bars, b.bars)
    return sum(S[a.start + i][b.start + i] for i in range(n)) / n if n else 0.0


def _label(segs: list[Segment], S, feats) -> None:
    """Cluster segments by aligned similarity (same-length prefix), then name them."""
    clusters: list[list[int]] = []
    for i, s in enumerate(segs):
        for c in clusters:
            if _segsim(S, segs[c[0]], s) >= 0.80 and abs(segs[c[0]].bars - s.bars) <= max(2, s.bars // 3):
                c.append(i)
                break
        else:
            clusters.append([i])
    tag = {}
    for ci, c in enumerate(clusters):
        for i in c:
            tag[i] = ci
    dn = feats["drum_n"]
    # rank clusters: repeats and density decide Main order (ascending density -> A..D)
    mains = [c for c in clusters if len(c) >= 2 or segs[c[0]].bars >= 4]
    mains.sort(key=lambda c: sum(segs[i].density for i in c) / len(c))
    names = {}
    for rank, c in enumerate(mains[:4]):
        for i in c:
            names[i] = "Main " + "ABCD"[rank]
    for i, s in enumerate(segs):
        drumless = sum(dn[b] for b in range(s.start, s.end)) / s.bars < 3
        if i == 0 and (s.bars <= 8 or drumless or i not in names or segs[0].density < 0.7 * max(x.density for x in segs)):
            if not (len(clusters[tag[i]]) >= 2 and s.bars > 8):
                s.label, s.kind = "Intro", "intro"
                continue
        if i == len(segs) - 1 and (s.bars <= 8 or i not in names or len(clusters[tag[i]]) == 1):
            s.label, s.kind = "Ending", "ending"
            continue
        s.label = names.get(i, "Bridge/other")
        s.kind = "main" if i in names else "other"
    # fills: the last bar of a segment whose drum count is >= 1.25x the segment median
    for s in segs:
        counts = [dn[b] for b in range(s.start, s.end)]
        if len(counts) >= 3:
            med = sorted(counts)[len(counts) // 2]
            if counts[-1] >= 1.25 * med and med > 0:
                s.label += " (+fill bar %d)" % (s.end - 1)


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
    segs, _ = find_sections(m, info)
    for s in segs:
        print(f"  {_fmt_bars(s)}  {s.label:28} density {s.density:6.1f}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    for a in args:
        report(a, show_parts="--no-parts" not in sys.argv)
