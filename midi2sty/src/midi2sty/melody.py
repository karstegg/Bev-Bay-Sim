"""Melody / vocal / lead detection on a model.Song.

``classify_parts(song)`` returns one dict per track (same order as ``song.tracks``)::

    {index, tier, score, reason, role, family, stats}

``role`` is one of drums / bass / chord / lead (chord = any other accompaniment-capable part).
``tier`` 2 = almost certainly a melody/vocal/solo line (score >= 5), 1 = melody candidate
(3 <= score < 5), 0 = accompaniment. Tier >= 1 tracks are excluded by default by the arranger
(a sax line sent to PHR came out off-key in early conversions). Evidence per track: name keywords,
GM program family, monophony, register, sparsity and melodic motion (docs/analysis/
nightbird_and_melody_detection.md, section 4). Heuristic, tuned on ~20 songs.
"""
from __future__ import annotations

import bisect
import re

from . import model

_NAME_LEAD = re.compile(
    r"melod|\blead|vocal|\bvox\b|voice|\bsolo|\bsax|tenor|alto\b|soprano|flute|whistle|trumpet|"
    r"trombone|violin|oboe|clarinet|harmonica|theme|\bhook|singer|\bmel\b|flugel|fiddle|piccolo")
_NAME_NOT_LEAD = re.compile(r"bass|drum|perc|kick|\bpad|string|chord|comp\b|rhythm|rhy\b|organ|"
                            r"piano|keys|choir|strum|arp")
_GM_LEAD = set(range(56, 88)) | {40, 41, 109, 110, 111, 21, 22, 23}


def ensure_index(song: model.Song) -> None:
    """Give every track a unique index (hand-built tracks default to -1)."""
    if len({t.index for t in song.tracks}) != len(song.tracks) or any(t.index < 0 for t in song.tracks):
        for i, t in enumerate(song.tracks):
            t.index = i


def bar_ticks(song: model.Song) -> int:
    num, den = song.time_sig
    return max(1, model.TICKS_PER_BEAT * 4 * num // den)


def n_bars(song: model.Song) -> int:
    end = max((n.start + n.dur for t in song.tracks for n in t.notes), default=0)
    bl = bar_ticks(song)
    return (end + bl - 1) // bl


def gm_family(prog: int | None) -> str:
    if prog is None:
        return "?"
    names = ["piano", "chrom-perc", "organ", "guitar", "bass", "strings", "ensemble/choir",
             "brass", "reed", "pipe", "synth-lead", "synth-pad", "synth-fx"]
    return names[prog // 8] if prog < 104 else "ethnic/perc/sfx"


def part_stats(song: model.Song, track: model.Track) -> dict:
    ns = sorted(track.notes, key=lambda n: n.start)
    ppq = model.TICKS_PER_BEAT
    bl = bar_ticks(song)
    nb = max(1, n_bars(song))
    if not ns:
        return dict(n=0, med=0, poly=0.0, triad=0.0, per_active_bar=0.0, active_frac=0.0,
                    leap=0.0, repeat_frac=0.0, dur_mean=0.0, pcs=0)
    pitches = sorted(n.pitch for n in ns)
    win = max(1, ppq // 8)
    starts = [n.start for n in ns]
    clusters: list[tuple[int, list[int]]] = []
    for i, n in enumerate(ns):
        if clusters and n.start - clusters[-1][0] <= win:
            clusters[-1][1].append(i)
        else:
            clusters.append((n.start, [i]))
    triad = dyad = 0
    maxdur = max(n.dur for n in ns)
    slack = ppq // 8
    for t, idx in clusters:
        lo = bisect.bisect_left(starts, t - maxdur)
        hi = bisect.bisect_right(starts, t + win)
        pcs = {ns[j].pitch % 12 for j in range(lo, hi) if ns[j].start + ns[j].dur > t + win + slack}
        pcs |= {ns[j].pitch % 12 for j in idx}
        triad += len(pcs) >= 3
        dyad += len(pcs) >= 2
    triad /= len(clusters)
    dyad /= len(clusters)
    tops = [max(ns[j].pitch for j in idx) for _, idx in clusters]
    iv = [abs(b - a) for a, b in zip(tops, tops[1:])]
    active = len({n.start // bl for n in ns})
    return dict(
        n=len(ns), med=pitches[len(pitches) // 2], poly=dyad, triad=triad,
        per_active_bar=len(ns) / max(1, active), active_frac=active / nb,
        leap=sum(iv) / len(iv) if iv else 0.0,
        repeat_frac=sum(1 for x in iv if x == 0) / len(iv) if iv else 0.0,
        dur_mean=sum(n.dur for n in ns) / len(ns) / ppq,
        pcs=len({p % 12 for p in pitches}))


def classify_parts(song: model.Song) -> list[dict]:
    ensure_index(song)
    rows = []
    for tr in song.tracks:
        row = dict(index=tr.index, tier=0, score=0.0, reason="", role="chord",
                   family=gm_family(tr.program), stats={})
        if tr.is_drums:
            row["role"], row["reason"] = "drums", "drum channel"
            rows.append(row)
            continue
        if not tr.notes:
            row["reason"] = "no notes"
            rows.append(row)
            continue
        st = part_stats(song, tr)
        row["stats"] = st
        fam = row["family"]
        name = (tr.name or "").lower()
        named = bool(_NAME_LEAD.search(name)) and not _NAME_NOT_LEAD.search(name)
        gm_lead = tr.program in _GM_LEAD
        mono = st["poly"] < 0.15
        score, why = 0.0, []
        if named:
            score += 3; why.append("name")
        if gm_lead:
            score += 1.5; why.append(f"GM {fam}")
        if mono:
            score += 1; why.append("monophonic")
        if st["med"] >= 66 and st["poly"] < 0.30:
            score += 1; why.append("high register")
        elif 55 <= st["med"] < 66 and mono:
            score += 0.5; why.append("melody register")
        if st["active_frac"] < 0.6 and mono:
            score += 0.5; why.append("sparse")
        if mono and st["leap"] >= 1.8 and st["repeat_frac"] < 0.5:
            score += 1; why.append("melodic motion")
        if mono and st["repeat_frac"] >= 0.6:
            score -= 1.5; why.append("repeated-note ostinato (-)")
        if st["med"] < 52 and mono and not (named or gm_lead):
            score -= 2; why.append("low register (-)")
        if st["dur_mean"] >= 3.0 and not named:
            score -= 1.5; why.append("sustained pad-like (-)")
        if st["triad"] >= 0.45:
            score -= 1 if named else 2; why.append("chordal (-)")
        is_bass = fam == "bass" or "bass" in name
        if is_bass:
            score -= 3
        row["score"] = score
        if is_bass or (st["med"] < 50 and mono and not (named or gm_lead)):
            row["role"] = "bass"
            why = ["bass: " + ("GM/name" if is_bass else "low monophonic")]
        elif score >= 3:
            row["role"] = "lead"
            row["tier"] = 2 if score >= 5 else 1
        row["reason"] = ("melody/lead tier %d (score %.1f): " % (row["tier"], score) if row["tier"]
                         else "") + ", ".join(why)
        rows.append(row)
    return rows
