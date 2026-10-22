"""Recipe = the user-editable plan for turning one song into one style.

The interactive tool (ui.py) edits a Recipe, `arrange.suggest_recipe(song)` proposes one,
`arrange.build_style(song, recipe)` turns it into a model.Style. Recipes round-trip as JSON
so a conversion can be saved, tweaked and re-run from the CLI (`midi2sty song.mid --recipe r.json`).

Bars are 0-based song bars (bar 0 = first bar of the MIDI at its time signature).
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

from . import model

ROLES = list(model.STYLE_CHANNELS)          # RHY1 RHY2 BASS CHD1 CHD2 PAD PHR1 PHR2
EXCLUDE = "exclude"                          # track not used at all (e.g. vocal/sax melody)
FILL_ONLY = "fill_only"                      # reserved: track material may be used inside fills only


@dataclass
class TrackPlan:
    index: int                               # model.Track.index
    role: str                                # one of ROLES, EXCLUDE or FILL_ONLY
    reason: str = ""                         # why suggested (shown in the UI), e.g. "melody: mono, high, sparse"


@dataclass
class SectionPlan:
    name: str                                # one of model.SECTIONS
    # where the material comes from:
    #   "song"   : song bars [start_bar, start_bar + n_bars) (n_bars may differ from the default length)
    #   "derive" : generated from another section (derive_from), e.g. a Fill from its Main
    #   "auto"   : let the arranger decide (Intro A hats+crash, Ending A final hit, ...)
    source: str = "auto"
    start_bar: int | None = None
    n_bars: int | None = None                # None = canonical default length for the section type
    derive_from: str | None = None
    note: str = ""                           # human-readable why (shown in the UI), e.g. "song bar 34 (best fill candidate, 0.62)"
    # painted material (recipe v2): {track_index: (start_bar, n_bars)}. When non-empty ONLY these tracks feed the
    # section, each playing its own song bar range; source/start_bar/derive_from are ignored. See docs/RECIPE.md.
    track_ranges: dict[int, tuple[int, int]] = field(default_factory=dict)
    mute_tracks: list[int] = field(default_factory=list)   # tracks silent in this section (painted sections)


@dataclass
class Recipe:
    name: str = "midi2sty"
    tonic: int = 0                           # pitch class (0=C) of the song's tonic; bars are normalised relative to chord roots
    minor: bool = False
    tempo_bpm: float | None = None           # None = song tempo minus 3 bpm (real styles are ~3 bpm slower)
    normalise_chords: bool = True            # shift each bar so its chord root becomes C and majorise 3rd/7th
    bar_roots: list[int] | None = None       # per-song-bar chord root pitch class; None = detect from the bass
    tracks: list[TrackPlan] = field(default_factory=list)
    sections: list[SectionPlan] = field(default_factory=list)
    sff_version: int = 1

    def to_json(self) -> str:
        d = asdict(self)
        for s in d["sections"]:
            s["track_ranges"] = {str(k): [int(v[0]), int(v[1])] for k, v in s["track_ranges"].items()}
        return json.dumps(d, indent=2)

    @classmethod
    def from_json(cls, text: str) -> "Recipe":
        d = json.loads(text)
        d["tracks"] = [TrackPlan(**t) for t in d.get("tracks", [])]
        secs = []
        for s in d.get("sections", []):
            s = dict(s)
            s["track_ranges"] = {int(k): (int(v[0]), int(v[1])) for k, v in (s.get("track_ranges") or {}).items()}
            s["mute_tracks"] = [int(x) for x in s.get("mute_tracks") or []]
            secs.append(SectionPlan(**s))
        d["sections"] = secs
        return cls(**d)

    def role_of(self, index: int) -> str | None:
        for t in self.tracks:
            if t.index == index:
                return t.role
        return None

    def validate(self) -> list[str]:
        bad = []
        for t in self.tracks:
            if t.role not in ROLES + [EXCLUDE, FILL_ONLY]:
                bad.append(f"track {t.index}: unknown role {t.role!r}")
        for s in self.sections:
            if s.name not in model.SECTIONS:
                bad.append(f"unknown section {s.name!r}")
            for i, (a, n) in s.track_ranges.items():
                if a < 0 or n < 1:
                    bad.append(f"{s.name}: track {i} range ({a}, {n}) needs start_bar >= 0 and n_bars >= 1")
            if s.track_ranges:
                continue
            if s.source == "song" and s.start_bar is None:
                bad.append(f"{s.name}: source 'song' needs start_bar")
            if s.source == "derive" and not s.derive_from:
                bad.append(f"{s.name}: source 'derive' needs derive_from")
        return bad
