"""Stage 3: map a normalised Song onto a Yamaha-style Style (role assignment + bar slicing).

Approach (all pure and deterministic):

1. Role assignment
   * Drum tracks are merged -> RHY1. Hats/shakers/tambourine/cowbell-type percussion
     (see ``_RHY2_DRUMS``) are split to RHY2 only if the song also has other drums.
   * Pitched tracks are scored for polyphony (fraction of notes sounding with another
     note) and register (median pitch). The lowest mostly-monophonic one (low register
     or GM bass program) becomes BASS.
   * Remaining tracks are "chordal" (polyphony >= 0.3) or "phrase". Chordal tracks, ranked by
     (polyphony, note count), fill CHD1, CHD2, PAD; phrase tracks, ranked by note count,
     fill PHR1, PHR2. Extra tracks are merged into the last role of their group.
     One style channel therefore has at most one source program (that of its main track).

2. Slicing: the song is cut into whole bars (time-signature aware). Bars are grouped into
   blocks of ``bars_per_section``; blocks are clustered by onset-pattern similarity
   (Jaccard). The largest clusters (ties: denser) become Main A..D, ordered by ascending
   density. Intro A = first bars, Ending A = last bars, Fill In XX = the densest last bar
   among blocks of Main X's cluster.

3. Transposition: Yamaha styles are authored in the CMaj7 source chord. Every pitched part
   (bass, chords, phrases; not drums) is shifted by the smallest interval taking the
   song's tonic to C. For minor songs the relative major tonic (key_root + 3) is used, so
   an A-minor song lands in C-major. This assumes the song stays in one key.
"""
from __future__ import annotations

from dataclasses import dataclass
from statistics import median

from .model import (SECTIONS, STYLE_CHANNELS, TICKS_PER_BEAT, Note, Song, Style,
                     StyleChannel, StyleSection, Track)

DEFAULT_SECTIONS = (
    "Intro A", "Main A", "Main B", "Main C", "Main D",
    "Fill In AA", "Fill In BB", "Fill In CC", "Fill In DD", "Ending A",
)
_MAINS = ("Main A", "Main B", "Main C", "Main D")
_FILLS = {"Main A": "Fill In AA", "Main B": "Fill In BB",
          "Main C": "Fill In CC", "Main D": "Fill In DD"}
# GM drum notes routed to RHY2: hats, tambourine, cowbell, shakers, claves, etc.
_RHY2_DRUMS = frozenset({42, 44, 46, 54, 56, 58, 69, 70, 75, 76, 77, 80, 81})
_CHORD_ROLES = ("CHD1", "CHD2", "PAD")
_PHRASE_ROLES = ("PHR1", "PHR2")
_POLY_CHORDAL = 0.3
_POLY_MONO = 0.2


@dataclass(frozen=True)
class MapOptions:
    bars_per_section: int = 4
    sections: tuple[str, ...] = DEFAULT_SECTIONS
    intro_bars: int = 2
    ending_bars: int = 2
    similarity: float = 0.8      # Jaccard threshold for grouping blocks into one Main
    transpose: bool = True


def bar_ticks(time_sig: tuple[int, int]) -> int:
    num, den = time_sig
    return TICKS_PER_BEAT * 4 * num // den


def transpose_shift(key_root: int, key_minor: bool) -> int:
    """Semitone shift (-6..+5) that moves the song's (relative-major) tonic to C."""
    tonic = (key_root + (3 if key_minor else 0)) % 12
    shift = -tonic
    return shift + 12 if shift < -6 else shift


# ---------------------------------------------------------------- role assignment

def _poly_fraction(notes: list[Note]) -> float:
    if not notes:
        return 0.0
    ns = sorted(notes, key=lambda n: (n.start, n.pitch))
    flagged = [False] * len(ns)
    for i, a in enumerate(ns):
        for j in range(i + 1, len(ns)):
            b = ns[j]
            if b.start >= a.start + a.dur - 30 and b.start - a.start > 30:
                break
            flagged[i] = flagged[j] = True
    return sum(flagged) / len(ns)


def _merge(tracks: list[Track]) -> list[Note]:
    return sorted((n for t in tracks for n in t.notes),
                  key=lambda n: (n.start, n.pitch, n.dur, n.vel))


def assign_roles(song: Song) -> dict[str, tuple[int | None, list[Note]]]:
    """Return {role: (program, merged notes)} for roles that received material."""
    roles: dict[str, tuple[int | None, list[Note]]] = {}
    drums = [t for t in song.tracks if t.is_drums and t.notes]
    if drums:
        prog = drums[0].program
        allnotes = _merge(drums)
        rhy2 = [n for n in allnotes if n.pitch in _RHY2_DRUMS]
        rhy1 = [n for n in allnotes if n.pitch not in _RHY2_DRUMS]
        if rhy1 and rhy2:
            roles["RHY1"], roles["RHY2"] = (prog, rhy1), (prog, rhy2)
        else:
            roles["RHY1"] = (prog, allnotes)

    pitched = [t for t in song.tracks if not t.is_drums and t.notes]
    stats = {id(t): (_poly_fraction(t.notes), median(n.pitch for n in t.notes)) for t in pitched}

    bass_c = [t for t in pitched if stats[id(t)][0] <= _POLY_MONO
              and (stats[id(t)][1] < 56 or (t.program is not None and 32 <= t.program <= 39))]
    bass = min(bass_c, key=lambda t: (stats[id(t)][1], -len(t.notes))) if bass_c else None
    if bass:
        roles["BASS"] = (bass.program, _merge([bass]))

    rest = [t for t in pitched if t is not bass]
    chordal = sorted((t for t in rest if stats[id(t)][0] >= _POLY_CHORDAL),
                     key=lambda t: (-stats[id(t)][0], -len(t.notes)))
    phrase = sorted((t for t in rest if stats[id(t)][0] < _POLY_CHORDAL),
                    key=lambda t: (-len(t.notes), -stats[id(t)][1]))
    for names, group in ((_CHORD_ROLES, chordal), (_PHRASE_ROLES, phrase)):
        buckets: dict[str, list[Track]] = {}
        for i, t in enumerate(group):
            buckets.setdefault(names[min(i, len(names) - 1)], []).append(t)
        for role, ts in buckets.items():
            roles[role] = (ts[0].program, _merge(ts))
    return roles


# ---------------------------------------------------------------- slicing helpers

def _slice(notes: list[Note], t0: int, t1: int, shift: int) -> list[Note]:
    out = []
    for n in notes:
        if t0 <= n.start < t1:
            dur = max(1, min(n.dur, t1 - n.start))
            out.append(Note(n.start - t0, dur, min(127, max(0, n.pitch + shift)), n.vel))
    return out


def _signature(roles, b0: int, b1: int, bt: int) -> frozenset:
    sig = set()
    for role, (_, notes) in roles.items():
        drum = role.startswith("RHY")
        for n in notes:
            if b0 * bt <= n.start < b1 * bt:
                sig.add((role, (n.start - b0 * bt) // 120, n.pitch if drum else n.pitch % 12))
    return frozenset(sig)


def _density(roles, b0: int, b1: int, bt: int) -> float:
    cnt = sum(1 for _, ns in roles.values() for n in ns if b0 * bt <= n.start < b1 * bt)
    return cnt / max(1, b1 - b0)


def _jaccard(a: frozenset, b: frozenset) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def _num_bars(song: Song, roles, bt: int) -> int:
    end = max(song.length_ticks, max((n.start + n.dur for _, ns in roles.values() for n in ns),
                                     default=0))
    return -(-end // bt) if end else 0


def _pick_mains(roles, nbars: int, bt: int, n: int, thresh: float):
    """Return list of (rep_start_bar, [member start bars]) ordered by ascending density."""
    starts = list(range(0, nbars - n + 1, n)) or [0]
    sigs = {s: _signature(roles, s, s + n, bt) for s in starts}
    # drop silent blocks unless nothing else exists
    live = [s for s in starts if sigs[s]] or starts
    clusters: list[list[int]] = []
    for s in live:
        for c in clusters:
            if _jaccard(sigs[c[0]], sigs[s]) >= thresh:
                c.append(s)
                break
        else:
            clusters.append([s])
    dens = {s: _density(roles, s, s + n, bt) for s in live}
    clusters.sort(key=lambda c: (-len(c), -sum(dens[s] for s in c) / len(c), c[0]))
    top = clusters[:4]
    reps = []
    for c in top:
        rep = max(c, key=lambda s: (sum(_jaccard(sigs[s], sigs[o]) for o in c), -s))
        reps.append((rep, c))
    reps.sort(key=lambda r: (dens[r[0]], r[0]))
    return reps


# ---------------------------------------------------------------- main entry

def song_to_style(song: Song, options: MapOptions | None = None) -> Style:
    opt = options or MapOptions()
    if opt.bars_per_section < 1:
        raise ValueError("bars_per_section must be >= 1")
    for s in opt.sections:
        if s not in SECTIONS:
            raise ValueError(f"unknown section {s!r}")
    bt = bar_ticks(song.time_sig)
    roles = assign_roles(song)
    nbars = _num_bars(song, roles, bt)
    style = Style(song.tempo_bpm, song.time_sig, [])
    if nbars == 0 or not roles:
        return style
    n = min(opt.bars_per_section, nbars)
    shift = transpose_shift(song.key_root, song.key_minor) if opt.transpose else 0

    def build(name: str, b0: int, b1: int) -> StyleSection:
        t0, t1 = b0 * bt, b1 * bt
        chans = []
        for role in STYLE_CHANNELS:
            if role not in roles:
                continue
            prog, notes = roles[role]
            ns = _slice(notes, t0, t1, 0 if role.startswith("RHY") else shift)
            if ns:
                chans.append(StyleChannel(role, prog, ns))
        return StyleSection(name, t1 - t0, chans)

    mains = _pick_mains(roles, nbars, bt, n, opt.similarity)
    main_by_name = {nm: m for nm, m in zip(_MAINS, mains)}
    out: dict[str, StyleSection] = {}
    for nm, (rep, members) in main_by_name.items():
        out[nm] = build(nm, rep, rep + n)
        lasts = [m + n - 1 for m in members]
        best = max(lasts, key=lambda b: (_density(roles, b, b + 1, bt), b == rep + n - 1, -b))
        out[_FILLS[nm]] = build(_FILLS[nm], best, best + 1)
    ib = max(1, min(opt.intro_bars, nbars))
    eb = max(1, min(opt.ending_bars, nbars))
    out["Intro A"] = build("Intro A", 0, ib)
    out["Ending A"] = build("Ending A", nbars - eb, nbars)

    for nm in opt.sections:
        sec = out.get(nm)
        if sec and sec.channels and all(nm != s.name for s in style.sections):
            style.sections.append(sec)
    return style
