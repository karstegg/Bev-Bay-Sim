"""Arranger: turn a Song + Recipe into a 15-section model.Style following real Yamaha style anatomy.

Public API
  suggest_recipe(song) -> Recipe     roles for every track, sections, tonic/minor (tempo left to default)
  build_style(song, recipe) -> Style always all 15 sections of model.CANONICAL_ORDER

Key ideas (evidence: docs/analysis/style_anatomy.md)
  * Chord normalisation: per song bar the chord root (duration-weighted pitch class of the BASS role,
    fallback lowest chord note) is shifted to C by the smallest interval and minor-chord bars are
    "majorised" (rel. pc 3->4, 10->11) so all material sits in the CMaj7 source chord. Pitched
    tracks are then octave-placed per role (BASS 24-38, CHD/PAD 48-76, PHR 48-74). Drums never shift.
  * Intro B/C, Ending B/C built literally from song bars (recipe source "song") are only shifted by the
    tonic (key -> C; minor stays minor) and flagged ``bypass_chords``; those derived from Mains stay
    chord-normalised and follow the played chord like Mains.
  * Drums: main kit -> RHY2 (ch10), percussion notes of that kit -> RHY1 (ch9).
  * Mains: song windows; fewer than 4 distinct blocks -> duplicates (D==C) and a thinned Main A.
  * Fills: Main's last bar for pitched channels, drums rebuilt (kick kept, snare+toms, thin hats, crash
    5 ticks before the end). Fill In BA = sparse stop version. Endings: groove + held final hit on the
    last bar start with a silent last beat; Ending B/C get a ritardando.
"""
from __future__ import annotations

import bisect
from collections import defaultdict
from statistics import median

from . import melody, model, sections
from .model import CANONICAL_ORDER, STYLE_CHANNELS, Note, Style, StyleChannel, StyleSection
from .recipe import EXCLUDE, FILL_ONLY, ROLES, Recipe, SectionPlan, TrackPlan

PPQ = model.TICKS_PER_BEAT
PITCHED = ("BASS", "CHD1", "CHD2", "PAD", "PHR1", "PHR2")
MAINS = ("Main A", "Main B", "Main C", "Main D")
WINDOW = {"BASS": (24, 38), "CHD1": (48, 76), "CHD2": (48, 76), "PAD": (48, 76),
          "PHR1": (48, 74), "PHR2": (48, 74)}
TARGET = {"BASS": 29, "CHD1": 60, "CHD2": 62, "PAD": 60, "PHR1": 62, "PHR2": 63}
KICKS = frozenset({35, 36})
SNARES = frozenset({37, 38, 39, 40})
HATS = frozenset({42, 44, 46})
TOMS = frozenset({41, 43, 45, 47, 48, 50})
CRASH = frozenset({49, 52, 55, 57})
CYMBAL = frozenset({51, 53, 59})
PERC = frozenset(range(54, 55)) | {56, 58} | set(range(60, 88))
DEFAULT_BARS = {"Main A": 4, "Main B": 4, "Main C": 4, "Main D": 4,
                "Fill In AA": 1, "Fill In BB": 1, "Fill In CC": 1, "Fill In DD": 1, "Fill In BA": 1,
                "Intro A": 1, "Intro B": 2, "Intro C": 4, "Ending A": 2, "Ending B": 2, "Ending C": 4}
FILL_MIN_DISSIMILARITY = 0.2   # below this the song's transition bar is just the groove: derive a fill instead
FILL_SRC = {"Fill In AA": "Main A", "Fill In BB": "Main B", "Fill In CC": "Main C",
            "Fill In DD": "Main D", "Fill In BA": "Main B"}


# ---------------------------------------------------------------- pattern helpers

class Pat:
    """Notes per style role for a section of n bars (ticks relative to section start)."""
    __slots__ = ("n", "ch")

    def __init__(self, n: int, ch: dict | None = None):
        self.n = n
        self.ch: dict[str, list[Note]] = ch if ch is not None else {}

    def copy(self) -> "Pat":
        return Pat(self.n, {r: list(v) for r, v in self.ch.items()})

    def count(self) -> int:
        return sum(len(v) for v in self.ch.values())


def _cut(notes, a: int, b: int) -> list[Note]:
    """Notes sounding in [a, b) rebased to 0; notes already sounding at a start fresh at 0."""
    out = []
    for x in notes:
        e = x.start + x.dur
        if x.start >= b or e <= a:
            continue
        s, en = max(x.start, a), min(e, b)
        if x.start < a and en - s < 30:
            continue
        out.append(Note(s - a, en - s, x.pitch, x.vel))
    return out


def _bar(p: Pat, i: int, bl: int) -> Pat:
    return Pat(1, {r: _cut(ns, i * bl, (i + 1) * bl) for r, ns in p.ch.items()})


def _fill_bar(p: Pat, bl: int) -> Pat:
    """Last bar of a Main, but a role that plays in the Main and is silent in its last bar
    borrows the nearest earlier bar that has notes (real fills keep chords/bass: only 1/140 is drums-only)."""
    last = _bar(p, p.n - 1, bl)
    for role, notes in p.ch.items():
        if notes and not last.ch.get(role):
            for i in range(p.n - 2, -1, -1):
                prev = _bar(p, i, bl).ch.get(role)
                if prev:
                    last.ch[role] = [Note(n.start, n.dur, n.pitch, n.vel) for n in prev]
                    break
    return last


def _concat(bars: list[Pat], bl: int) -> Pat:
    out = Pat(len(bars))
    for k, b in enumerate(bars):
        for r, ns in b.ch.items():
            out.ch.setdefault(r, []).extend(Note(x.start + k * bl, x.dur, x.pitch, x.vel) for x in ns)
    return out


def _cycle(p: Pat, n: int, bl: int) -> list[Pat]:
    return [_bar(p, k % p.n, bl) for k in range(n)]


def _clean(notes: list[Note], length: int) -> list[Note]:
    notes = sorted((x for x in notes if 0 <= x.start < length), key=lambda x: (x.pitch, x.start, -x.vel))
    out: list[Note] = []
    for x in notes:
        if out and out[-1].pitch == x.pitch:
            p = out[-1]
            if x.start == p.start:
                continue
            if x.start < p.start + p.dur:
                out[-1] = Note(p.start, x.start - p.start, p.pitch, p.vel)
        out.append(Note(x.start, max(1, min(x.dur, length - x.start)), x.pitch, max(1, min(127, x.vel))))
    return sorted(out, key=lambda x: (x.start, x.pitch))


class _Pool:
    def __init__(self, notes: list[Note]):
        self.notes = sorted(notes, key=lambda x: x.start)
        self.starts = [x.start for x in self.notes]
        self.maxdur = max((x.dur for x in self.notes), default=0)

    def cut(self, a: int, b: int) -> list[Note]:
        lo = bisect.bisect_left(self.starts, a - self.maxdur)
        hi = bisect.bisect_left(self.starts, b)
        return _cut(self.notes[lo:hi], a, b)


# ---------------------------------------------------------------- recipe suggestion

def _kind(st: dict) -> str:
    if st["dur_mean"] >= 2.5:
        return "PAD"
    if st["poly"] >= 0.5 or st["triad"] >= 0.3:
        return "CHD"
    return "PHR"


def suggest_recipe(song: model.Song) -> Recipe:
    melody.ensure_index(song)
    rows = melody.classify_parts(song)
    tracks = {t.index: t for t in song.tracks}
    plans: dict[int, TrackPlan] = {}
    cands: list[tuple[dict, str]] = []
    for r in rows:
        tr, i = tracks[r["index"]], r["index"]
        if tr.is_drums:
            core = any(n.pitch in KICKS | SNARES for n in tr.notes)
            plans[i] = TrackPlan(i, "RHY2" if core else "RHY1",
                                 "main drum kit (percussion notes are split to RHY1)" if core
                                 else "percussion only")
        elif not tr.notes:
            plans[i] = TrackPlan(i, EXCLUDE, "no notes")
        elif r["tier"] >= 1:
            plans[i] = TrackPlan(i, EXCLUDE, f"likely melody/vocal lead, excluded by default "
                                             f"({r['reason']}); set PHR1/PHR2 to keep it")
        elif r["role"] == "bass":
            plans[i] = TrackPlan(i, "BASS", r["reason"])
        else:
            cands.append((r, _kind(r["stats"])))
    if not any(p.role == "BASS" for p in plans.values()):
        mono = [(r["stats"]["med"], r) for r, k in cands if r["stats"]["poly"] < 0.3 and k == "PHR"]
        if mono:
            r = min(mono, key=lambda x: x[0])[1]
            plans[r["index"]] = TrackPlan(r["index"], "BASS", "lowest mostly-monophonic part (fallback)")
            cands = [(c, k) for c, k in cands if c is not r]
    groups: dict[str, list[dict]] = {"PAD": [], "CHD": [], "PHR": []}
    for r, k in cands:
        groups[k].append(r)
    for k, rs in groups.items():
        rs.sort(key=lambda r: -r["stats"]["n"])
        for j, r in enumerate(rs):
            role = "PAD" if k == "PAD" else f"{k}{1 if j == 0 else 2}"
            st = r["stats"]
            plans[r["index"]] = TrackPlan(
                r["index"], role, f"{'sustained' if k == 'PAD' else 'comping' if k == 'CHD' else 'riff/arpeggio'}"
                f": polyphony {st['poly']:.2f}, median pitch {st['med']}, mean length {st['dur_mean']:.1f} beats")
    recipe = Recipe(tonic=song.key_root, minor=song.key_minor,
                    tracks=[plans[t.index] for t in song.tracks])
    recipe.sections = _suggest_sections(song, sections.propose_sections(song), plans)
    return recipe


_DRUM_CLASS = {**{p: "K" for p in (35, 36)}, **{p: "S" for p in (37, 38, 39, 40)},
               **{p: "T" for p in TOMS}, **{p: "H" for p in (42, 44, 46)},
               **{p: "C" for p in CRASH}, **{p: "R" for p in CYMBAL}}


def _bar_features(song, plans):
    """Per song bar: set of (16th step, class) onsets over every non-excluded track, plus tom/crash counts."""
    bl, nb = melody.bar_ticks(song), max(melody.n_bars(song), 1)
    sets = [set() for _ in range(nb)]
    toms = [0] * nb
    for t in song.tracks:
        p = plans.get(t.index)
        if p is not None and p.role in (EXCLUDE, FILL_ONLY):
            continue
        for n in t.notes:
            b = n.start // bl
            if b >= nb:
                continue
            c = _DRUM_CLASS.get(n.pitch, "o") if t.is_drums else "p" + str(t.index)
            sets[b].add((n.start % bl * 16 // bl, c))
            toms[b] += t.is_drums and n.pitch in TOMS
    return sets, toms


def _fill_dissimilarity(sets, toms, b, groove):
    if b < 0 or b >= len(sets) or len(sets[b]) < 3:
        return -1.0
    best = max((len(sets[b] & sets[g]) / max(1, len(sets[b] | sets[g])) for g in groove if 0 <= g < len(sets)),
               default=0.0)
    return (1.0 - best) + 0.05 * min(toms[b], 6)


def pick_song_fill(song, plans, a: int, n: int):
    """The song's own transition bar for the Main at song bars [a, a+n): the bar leading into it (a-1) or
    the bar right after the block (a+n). Returns (bar, score) or None when the song has no distinct one."""
    sets, toms = _bar_features(song, plans)
    groove = range(a, a + n)
    cands = [(_fill_dissimilarity(sets, toms, b, groove) + (0.05 if b == a - 1 else 0.0), b)
             for b in (a - 1, a + n) if b >= 0]
    if not cands:
        return None
    score, b = max(cands)
    return (b, score) if score >= FILL_MIN_DISSIMILARITY else None


def _suggest_sections(song, props, plans) -> list[SectionPlan]:
    out: list[SectionPlan] = []

    def add(name, source="auto", a=None, n=None, frm=None, note=""):
        out.append(SectionPlan(name, source, a, n, frm, note))

    found = [(m, props[m]) for m in MAINS if m in props]
    k = len(found)
    if k >= 3:
        for m, (a, n) in found:
            add(m, "song", a, n)
        if k == 3:
            add("Main D", "derive", frm="Main C")
    elif k == 2:
        add("Main B", "song", *found[0][1])
        add("Main C", "song", *found[1][1])
        add("Main A", "derive", frm="Main B")
        add("Main D", "derive", frm="Main C")
    elif k == 1:
        add("Main B", "song", *found[0][1])
        add("Main A", "derive", frm="Main B")
        add("Main C", "derive", frm="Main B")
        add("Main D", "derive", frm="Main B")
    bars_of = {p.name: (p.start_bar, p.n_bars or 4) for p in out if p.source == "song"}
    for f, src in FILL_SRC.items():
        main = src
        if f == "Fill In BA":          # stop/fill into Main A: the song's own bar before Main A when it has one
            main = "Main A"
        pick = None
        if f != "Fill In BA" and main in bars_of:
            pick = pick_song_fill(song, plans, *bars_of[main])
        elif f == "Fill In BA" and "Fill In AA" in {p.name for p in out}:
            pick = None
        if pick:
            add(f, "song", pick[0], 1, note=f"song bar {pick[0] + 1}: the song's own transition bar (change score {pick[1]:.2f})")
        else:
            add(f, "derive", frm=src, note="no distinct fill in the song here: derived from the Main's last bar")
    add("Intro A")
    if "Intro C" in props and props["Intro C"][1] >= 4:
        a, n = props["Intro C"]
        add("Intro B", "song", a + n - 2, 2, note="the last 2 bars of the song's own intro")
    else:
        add("Intro B", "derive", frm="Main A", n=2)
    if "Intro C" in props:
        add("Intro C", "song", *props["Intro C"], note="the song's own intro")
    else:
        add("Intro C", "derive", frm="Main B", n=4)
    add("Ending A")
    if "Ending C" in props and _winds_down(song, props["Ending C"], plans):
        a, n = props["Ending C"]
        add("Ending B", "song", a + n - 2, 2, note="the last 2 bars of the song")
        add("Ending C", "song", a, n, note="the song's own ending")
    else:
        add("Ending B", "derive", frm="Main B", n=2)
        add("Ending C", "derive", frm="Main D", n=4)
    return out


def _winds_down(song, rng, plans) -> bool:
    """True if the song's last bar is clearly thinner than a typical bar (the song really ends)."""
    bl, nb = melody.bar_ticks(song), melody.n_bars(song)
    cnt = [0] * max(nb, 1)
    for t in song.tracks:
        p = plans.get(t.index)
        if p is None or p.role in (EXCLUDE, FILL_ONLY):
            continue
        for n in t.notes:
            cnt[min(nb - 1, n.start // bl)] += 1
    busy = sorted(c for c in cnt if c)
    if not busy:
        return False
    last = rng[0] + rng[1] - 1
    return cnt[min(last, nb - 1)] <= 0.6 * busy[len(busy) // 2]


# ---------------------------------------------------------------- build context

def _tshift(pc: int) -> int:
    pc %= 12
    return -pc if pc <= 6 else 12 - pc


class _Ctx:
    def __init__(self, song: model.Song, recipe: Recipe):
        melody.ensure_index(song)
        self.song, self.recipe = song, recipe
        self.bl, self.nb = melody.bar_ticks(song), melody.n_bars(song)
        self.tracks = {t.index: t for t in song.tracks}
        self.role = {p.index: p.role for p in recipe.tracks if p.index in self.tracks}
        self.tshift = _tshift(recipe.tonic)
        self._bars()
        self._pools: dict[str, dict[str, _Pool]] = {}
        self._tpools: dict[int, dict[str, _Pool]] = {}
        self.warnings: list[str] = []

    def _by_role(self, roles):
        return [t for t in self.song.tracks if self.role.get(t.index) in roles and not t.is_drums]

    def _bars(self):
        nb, bl = self.nb, self.bl
        hist = [defaultdict(float) for _ in range(nb)]
        for t in self._by_role(("BASS",)):
            for n in t.notes:
                for b in range(n.start // bl, min(nb - 1, (n.start + n.dur - 1) // bl) + 1):
                    ov = min(n.start + n.dur, (b + 1) * bl) - max(n.start, b * bl)
                    hist[b][n.pitch % 12] += ov * (1.5 if n.start == b * bl else 1.0)
        roots: list[int | None] = [None] * nb
        for b in range(nb):
            if hist[b]:
                roots[b] = max(hist[b].items(), key=lambda kv: (kv[1], -kv[0]))[0]
        if self.recipe.bar_roots:
            for b, r in enumerate(self.recipe.bar_roots[:nb]):
                if r is not None:
                    roots[b] = r % 12
        if any(r is None for r in roots):
            low: list[int | None] = [None] * nb
            for t in self._by_role(("CHD1", "CHD2", "PAD")):
                for n in t.notes:
                    b = min(nb - 1, n.start // bl)
                    if low[b] is None or n.pitch < low[b]:
                        low[b] = n.pitch
            for b in range(nb):
                if roots[b] is None and low[b] is not None:
                    roots[b] = low[b] % 12
        prev = next((r for r in roots if r is not None), self.recipe.tonic % 12)
        for b in range(nb):
            if roots[b] is None:
                roots[b] = prev
            prev = roots[b]
        self.roots = roots
        # minor-chord bars: more 3rd-below-4th weight (relative to the bar root) than major 3rd
        w3 = [0.0] * nb
        w4 = [0.0] * nb
        src = self._by_role(("BASS", "CHD1", "CHD2", "PAD")) or self._by_role(PITCHED)
        for t in src:
            for n in t.notes:
                for b in range(n.start // bl, min(nb - 1, (n.start + n.dur - 1) // bl) + 1):
                    ov = min(n.start + n.dur, (b + 1) * bl) - max(n.start, b * bl)
                    rel = (n.pitch - roots[b]) % 12
                    if rel == 3:
                        w3[b] += ov
                    elif rel == 4:
                        w4[b] += ov
        self.minor = [w3[b] > w4[b] for b in range(nb)]
        self.shift = [_tshift(r) for r in roots]

    # ---- pools of normalised notes
    def _pieces(self, n: Note, mode: str):
        if mode == "tonic" or not self.recipe.normalise_chords:
            yield n.start, n.dur, n.pitch + self.tshift, n.vel
            return
        bl, nb = self.bl, self.nb
        b0 = min(n.start // bl, nb - 1)
        b1 = max(b0, min((n.start + n.dur - 1) // bl, nb - 1))
        end = n.start + n.dur
        seg_a, key = n.start, None
        for b in range(b0, b1 + 1):
            k = (self.roots[b], self.minor[b])
            if key is not None and k != key:
                yield self._one(seg_a, b * bl, n, key)
                seg_a = b * bl
            key = k
        yield self._one(seg_a, end, n, key)

    def _one(self, a, e, n, key):
        root, minor = key
        p = n.pitch
        if minor and (p - root) % 12 in (3, 10):
            p += 1
        return a, e - a, p + _tshift(root), n.vel

    def _track_raw(self, t, mode: str) -> dict[str, list[Note]]:
        """Normalised notes of one track keyed by style role (drum kits split RHY2/RHY1)."""
        role = self.role.get(t.index)
        out: dict[str, list[Note]] = defaultdict(list)
        if role in ("RHY1", "RHY2"):
            core = t.is_drums and any(n.pitch in KICKS | SNARES for n in t.notes)
            for n in t.notes:
                r = "RHY1" if (role == "RHY1" or (core and n.pitch in PERC)) else "RHY2"
                out[r].append(n)
        elif role in PITCHED and not t.is_drums and t.notes:
            ns = [Note(a, d, p, v) for x in t.notes for a, d, p, v in self._pieces(x, mode)]
            med = median(x.pitch for x in ns)
            off = round((TARGET[role] - med) / 12) * 12
            lo, hi = WINDOW[role]
            for x in ns:
                p = x.pitch + off
                while p < lo:
                    p += 12
                while p > hi:
                    p -= 12
                out[role].append(Note(x.start, x.dur, p, x.vel))
        return out

    def pools(self, mode: str) -> dict[str, _Pool]:
        if mode in self._pools:
            return self._pools[mode]
        raw: dict[str, list[Note]] = defaultdict(list)
        for t in self.song.tracks:
            for r, ns in self._track_raw(t, mode).items():
                raw[r].extend(ns)
        self._pools[mode] = {r: _Pool(v) for r, v in raw.items() if v}
        return self._pools[mode]

    def track_pools(self, index: int) -> dict[str, _Pool]:
        if index not in self._tpools:
            raw = self._track_raw(self.tracks[index], "chord")
            self._tpools[index] = {r: _Pool(v) for r, v in raw.items() if v}
        return self._tpools[index]

    def paint(self, plan: SectionPlan, warn: list[str]) -> Pat | None:
        """Assemble a section from per-track song bar ranges (plan.track_ranges); None if nothing usable."""
        muted = set(plan.mute_tracks)
        parts = []
        for idx, (start, nb) in sorted(plan.track_ranges.items()):
            if idx in muted:
                continue
            role = self.role.get(idx)
            if idx not in self.tracks:
                warn.append(f"{plan.name}: track {idx} does not exist in the song, skipped")
            elif role is None or role in (EXCLUDE, FILL_ONLY):
                warn.append(f"{plan.name}: track {idx} has role {role or 'none'!r} and cannot be painted, skipped")
            elif nb >= 1 and start >= 0:
                parts.append((idx, start, nb))
        if not parts:
            if plan.track_ranges:
                warn.append(f"{plan.name}: no usable painted track, section built without painting")
            return None
        n = plan.n_bars or max(nb for _, _, nb in parts)
        out = Pat(n)
        for idx, start, nb in parts:
            m = min(nb, n)
            for r, pool in self.track_pools(idx).items():
                ns = pool.cut(start * self.bl, (start + m) * self.bl)
                if ns:
                    out.ch.setdefault(r, []).extend(ns)
        return out

    @property
    def has_drums(self) -> bool:
        p = self.pools("chord")
        return "RHY1" in p or "RHY2" in p

    @property
    def present(self) -> set[str]:
        return set(self.pools("chord"))

    def slice(self, mode: str, start_bar: int, n: int) -> Pat:
        a, b = start_bar * self.bl, (start_bar + n) * self.bl
        return Pat(n, {r: pool.cut(a, b) for r, pool in self.pools(mode).items()})

    def program(self, role: str) -> int | None:
        best = None
        for t in self.song.tracks:
            r = self.role.get(t.index)
            if r == role or (role == "RHY1" and r == "RHY2" and t.is_drums):
                if best is None or len(t.notes) > len(best.notes):
                    best = t
        return best.program if best else None


# ---------------------------------------------------------------- musical transforms

def _crash(p: Pat, bl: int, vel: int = 70):
    """Crash pickup 5 ticks (1/96 beat) before the section end, as in real fills/intros."""
    p.ch.setdefault("RHY2", []).append(Note(p.n * bl - 5, 5, 49, vel))


def _thin(main: Pat, bl: int) -> Pat:
    out = Pat(main.n)
    for r, ns in main.ch.items():
        if r in ("PHR1", "PHR2", "CHD2"):
            continue
        if r == "RHY2":
            ns = [x for x in ns if x.pitch not in HATS | CYMBAL or x.start % (PPQ // 2) == 0]
        if r == "RHY1":
            ns = [x for k, x in enumerate(sorted(ns, key=lambda y: y.start)) if k % 2 == 0]
        out.ch[r] = [Note(x.start, x.dur, x.pitch, max(1, int(x.vel * 0.9))) for x in ns]
    return out


def _fill(bar: Pat, bl: int, has_drums: bool, stop: bool = False) -> Pat:
    out = bar.copy()
    if stop:
        half = bl // 2
        for r in list(out.ch):
            if r.startswith("PHR"):
                out.ch[r] = []
            elif r in PITCHED:
                out.ch[r] = _cut(out.ch[r], 0, half)
        if has_drums:
            q = bl // 4
            keep = [x for x in bar.ch.get("RHY2", []) if x.start < half and (
                x.pitch in KICKS or (x.pitch in HATS and x.start % (PPQ // 2) == 0))]
            keep += [Note(bl - q, 100, 38, 80), Note(bl - q // 2 - 20, 100, 45, 76)]
            out.ch["RHY2"] = keep
            out.ch["RHY1"] = [x for x in bar.ch.get("RHY1", []) if x.start < half]
            _crash(out, bl)
        return out
    if has_drums:
        half = min(2 * PPQ, bl // 2)
        cut = bl - half
        keep = []
        for x in bar.ch.get("RHY2", []):
            if x.pitch in KICKS:
                keep.append(x)
            elif x.start < cut and x.pitch not in CRASH:
                if x.pitch in HATS and x.start % (PPQ // 2):
                    continue
                keep.append(x)
        keep.append(Note(cut, 100, 38, 82))
        for off, pitch, vel in ((3, 50, 78), (2, 47, 86), (1, 45, 94)):
            keep.append(Note(bl - half * off // 4, 120, pitch, vel))
        out.ch["RHY2"] = keep
        _crash(out, bl)
    return out


def _hit(src: Pat, bl: int, ctx: _Ctx) -> Pat:
    """Final hit on the bar start, held until the last beat (which stays silent)."""
    hold = max(PPQ // 2, bl - PPQ)
    out = Pat(1)
    for role in ("BASS", "CHD1", "CHD2", "PAD"):
        ns = [x for x in src.ch.get(role, []) if x.start < PPQ]
        if ns:
            t0 = min(x.start for x in ns)
            out.ch[role] = [Note(0, hold, x.pitch, min(127, x.vel + 10)) for x in ns if x.start - t0 <= 60]
    if "BASS" in ctx.present and "BASS" not in out.ch:
        out.ch["BASS"] = [Note(0, hold, 36, 100)]
    if ctx.has_drums:
        out.ch["RHY2"] = [Note(0, 120, 36, 110), Note(0, 120, 38, 100), Note(0, min(hold, PPQ), 49, 100)]
    return out


def _ending(groove: Pat, n: int, fill: Pat | None, bl: int, ctx: _Ctx) -> Pat:
    bars = _cycle(groove, max(1, n - 1), bl) if n > 1 else []
    if fill is not None and n >= 2:
        bars[n - 2] = fill
    bars.append(_hit(_bar(groove, 0, bl), bl, ctx))
    return _concat(bars, bl)


def _ritard(length: int, span_beats: int, base: float) -> list[tuple[int, float]]:
    span = span_beats * PPQ
    return [(length - span + i * span // 8, round(base * (1 - 0.4 * (i + 1) / 8), 2)) for i in range(8)]


def _intro_a(main_a: Pat, bl: int, ctx: _Ctx) -> Pat:
    b = _bar(main_a, 0, bl)
    out = Pat(1)
    if ctx.has_drums:
        r2 = [x for x in b.ch.get("RHY2", []) if x.pitch in HATS | CYMBAL | PERC]
        r2 += [x for x in b.ch.get("RHY2", []) if x.pitch in KICKS and x.start < 120][:1]
        if not r2 and not b.ch.get("RHY1"):
            r2 = [Note(i * PPQ // 2, 60, 42, 70) for i in range(bl // (PPQ // 2))]
        out.ch["RHY2"] = r2
        out.ch["RHY1"] = list(b.ch.get("RHY1", []))
        _crash(out, bl)
    else:
        out = _hit(b, bl, ctx)
    return out


def _has_content(p: Pat) -> bool:
    return sum(len(v) for r, v in p.ch.items() if r != "RHY2") + \
        sum(1 for x in p.ch.get("RHY2", []) if x.pitch not in CRASH) >= 6


def _finish_literal(p: Pat, bl: int, ending: bool, ctx: _Ctx, painted: bool = False):
    end = p.n * bl
    drums = ctx.has_drums and (not painted or any(p.ch.get(r) for r in ('RHY1', 'RHY2')))
    if ending:
        last = end - bl
        for r in list(p.ch):
            keep = []
            for x in p.ch[r]:
                if x.start >= end - PPQ:
                    continue
                if r in PITCHED and x.start + x.dur > end - PPQ:
                    x = Note(x.start, max(30, end - PPQ - x.start), x.pitch, x.vel)
                keep.append(x)
            p.ch[r] = keep
        if drums and not any(x.pitch in CRASH and x.start >= last for x in p.ch.get("RHY2", [])):
            p.ch.setdefault("RHY2", []).append(Note(last, min(PPQ, bl), 49, 100))
    elif drums and not any(x.pitch in CRASH and x.start >= end - 120 for x in p.ch.get("RHY2", [])):
        _crash(p, bl)


# ---------------------------------------------------------------- build_style

def build_style(song: model.Song, recipe: Recipe) -> Style:
    return _build(song, recipe)[0]


def build_style_with_warnings(song: model.Song, recipe: Recipe) -> tuple[Style, list[str]]:
    """Like build_style, plus human-readable warnings (e.g. painted tracks that were skipped)."""
    return _build(song, recipe)


def _build(song: model.Song, recipe: Recipe) -> tuple[Style, list[str]]:
    bad = recipe.validate()
    if bad:
        raise ValueError("invalid recipe: " + "; ".join(bad))
    ctx = _Ctx(song, recipe)
    bl = ctx.bl
    if not ctx.pools("chord") or ctx.nb == 0:
        raise ValueError("the recipe selects no usable notes")
    plans = {s.name: s for s in recipe.sections}
    has_drums = ctx.has_drums
    pats: dict[str, Pat] = {}
    bypass: dict[str, bool] = {}

    def nbars(name, default=None):
        pl = plans.get(name)
        return (pl.n_bars if pl and pl.n_bars else default or DEFAULT_BARS[name])

    painted: dict[str, Pat] = {}
    for pl in recipe.sections:
        if pl.track_ranges:
            p = ctx.paint(pl, ctx.warnings)
            if p is not None:
                painted[pl.name] = p

    # --- Mains
    for m in MAINS:
        pl = plans.get(m)
        if m in painted:
            pats[m] = painted[m]
        elif pl and pl.source == "song" and pl.start_bar is not None:
            pats[m] = ctx.slice("chord", pl.start_bar, nbars(m))
    if not pats:  # nothing declared: first busy 4-bar window becomes Main B
        pools = ctx.pools("chord").values()
        first = min((p.starts[0] for p in pools), default=0) // bl
        pats["Main B"] = ctx.slice("chord", first, max(1, min(4, ctx.nb - first)))
    for m in reversed(MAINS):
        if m in pats:
            continue
        pl = plans.get(m)
        src = pl.derive_from if pl and pl.derive_from in pats else None
        if src is None:
            higher = [x for x in MAINS[MAINS.index(m) + 1:] if x in pats]
            lower = [x for x in reversed(MAINS[:MAINS.index(m)]) if x in pats]
            src = lower[0] if lower else higher[0]
        p = pats[src]
        n = pl.n_bars if pl and pl.n_bars else p.n
        p = _concat(_cycle(p, n, bl), bl)
        pats[m] = _thin(p, bl) if MAINS.index(m) < MAINS.index(src) else p
    # A..D not yet resolved in order D,C,B,A: ensure derived-from-higher sources exist (A from B)
    # --- Fills
    for f, default in FILL_SRC.items():
        pl = plans.get(f)
        n = nbars(f)
        if f in painted:
            p = painted[f]
            if has_drums and any(p.ch.get(r) for r in ("RHY1", "RHY2")) and \
                    not any(x.pitch in CRASH and x.start >= p.n * bl - 120
                            for r in ("RHY1", "RHY2") for x in p.ch.get(r, [])):
                for idx, (st, nb) in sorted(pl.track_ranges.items()):
                    t = ctx.tracks.get(idx)
                    if t is None or not t.is_drums or idx in pl.mute_tracks or ctx.role.get(idx) not in ("RHY1", "RHY2"):
                        continue
                    hit = [x for pool in ctx.track_pools(idx).values() for x in pool.cut((st + min(nb, p.n)) * bl, (st + min(nb, p.n)) * bl + bl // 16)
                           if x.pitch in CRASH]
                    if hit:
                        _crash(p, bl, max(x.vel for x in hit))
                        break
            pats[f] = p
            continue
        if pl and pl.source == "song" and pl.start_bar is not None:
            p = ctx.slice("chord", pl.start_bar, n)
            if has_drums and not any(x.pitch in CRASH and x.start >= p.n * bl - 120
                                     for r in ("RHY1", "RHY2") for x in p.ch.get(r, [])):
                # the song's crash on the downbeat after the fill becomes the pickup crash that ends the fill
                after = ctx.slice("chord", pl.start_bar + n, 1)
                hit = [x for r in ("RHY1", "RHY2") for x in after.ch.get(r, [])
                       if x.pitch in CRASH and x.start < bl // 16]
                if hit:
                    _crash(p, bl, max(x.vel for x in hit))
            pats[f] = p
            continue
        src = pl.derive_from if pl and pl.derive_from in MAINS else default
        main = pats[src]
        fill = _fill(_fill_bar(main, bl), bl, has_drums, stop=(f == "Fill In BA"))
        pats[f] = _concat(_cycle(main, n - 1, bl) + [fill], bl) if n > 1 else fill

    def literal(name, ending):
        pl = plans.get(name)
        if name in painted:
            p = painted[name]
            _finish_literal(p, bl, ending, ctx, painted=True)
            return p
        if pl and pl.source == "song" and pl.start_bar is not None:
            p = ctx.slice("tonic", pl.start_bar, nbars(name))
            if _has_content(p):
                _finish_literal(p, bl, ending, ctx)
                return p
        return None

    def src_main(name, default):
        pl = plans.get(name)
        return pats[pl.derive_from] if pl and pl.derive_from in pats else pats[default if default in pats else "Main B"]

    def src_fill(main_name):
        return pats.get("Fill In " + main_name[-1] * 2)

    def derived_intro(name, default_main):
        pl = plans.get(name)
        mname = pl.derive_from if pl and pl.derive_from in MAINS else default_main
        n = nbars(name)
        groove = pats[mname]
        fill = _fill(_fill_bar(groove, bl), bl, has_drums)
        return _concat(_cycle(groove, n - 1, bl) + [fill], bl) if n > 1 else fill

    def derived_ending(name, default_main):
        pl = plans.get(name)
        mname = pl.derive_from if pl and pl.derive_from in MAINS else default_main
        fill = None if name == "Ending A" else _bar(src_fill(mname), 0, bl)
        return _ending(pats[mname], nbars(name), fill, bl, ctx)

    # --- Intros
    pats["Intro A"] = literal("Intro A", False) or _intro_a(pats["Main A"], bl, ctx)
    for nm, dm in (("Intro B", "Main A"), ("Intro C", "Main B")):
        p = literal(nm, False)
        bypass[nm] = p is not None
        pats[nm] = p or derived_intro(nm, dm)
    # --- Endings
    pats["Ending A"] = literal("Ending A", True) or derived_ending("Ending A", "Main A")
    for nm, dm in (("Ending B", "Main B"), ("Ending C", "Main D")):
        p = literal(nm, True)
        bypass[nm] = p is not None
        pats[nm] = p or derived_ending(nm, dm)

    tempo = recipe.tempo_bpm if recipe.tempo_bpm else max(30.0, song.tempo_bpm - 3)
    programs = {r: ctx.program(r) for r in STYLE_CHANNELS}
    secs = []
    for name in CANONICAL_ORDER:
        p = pats[name]
        length = p.n * bl
        chans = []
        for role in STYLE_CHANNELS:
            ns = _clean(p.ch.get(role, []), length)
            if ns:
                chans.append(StyleChannel(role, programs[role], ns))
        sec = StyleSection(name, length, chans, bypass_chords=bypass.get(name, False))
        if name in ("Ending B", "Ending C"):
            sec.tempo_changes = _ritard(length, 3 if name == "Ending B" else 4, tempo)
        secs.append(sec)
    return Style(tempo_bpm=tempo, time_sig=song.time_sig, sections=secs, sff_version=recipe.sff_version,
                 name=recipe.name), ctx.warnings
