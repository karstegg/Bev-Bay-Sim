"""Shared data contract between the pipeline stages. Do not change without updating PLAN.md."""
from __future__ import annotations
from dataclasses import dataclass, field

TICKS_PER_BEAT = 480  # all internal data is normalised to this PPQ

# Yamaha style channels (0-indexed MIDI channels 8..15 = "channels 9..16")
STYLE_CHANNELS = {
    "RHY1": 8, "RHY2": 9, "BASS": 10, "CHD1": 11,
    "CHD2": 12, "PAD": 13, "PHR1": 14, "PHR2": 15,
}

# Section markers as written in the .sty (SFF1)
SECTIONS = [
    "Intro A", "Intro B", "Intro C",
    "Main A", "Main B", "Main C", "Main D",
    "Fill In AA", "Fill In BB", "Fill In CC", "Fill In DD",
    "Fill In BA", "Ending A", "Ending B", "Ending C",
]
# Canonical marker order seen in 26/28 real DGX/PSR styles (docs/analysis/style_anatomy.md)
CANONICAL_ORDER = [
    "Main A", "Main B", "Main C", "Main D",
    "Fill In AA", "Fill In BB", "Fill In CC", "Fill In DD",
    "Intro A", "Intro B", "Intro C",
    "Ending A", "Ending B", "Ending C", "Fill In BA",
]


@dataclass(frozen=True)
class Note:
    start: int      # ticks, relative to section start
    dur: int        # ticks
    pitch: int      # 0-127
    vel: int        # 1-127


@dataclass
class Track:
    """One source-MIDI track after normalisation."""
    name: str
    channel: int                     # 0-15
    program: int | None
    notes: list[Note] = field(default_factory=list)
    is_drums: bool = False
    index: int = -1                  # position in Song.tracks (stable id used by recipes)


@dataclass
class Song:
    tracks: list[Track]
    tempo_bpm: float = 120.0
    time_sig: tuple[int, int] = (4, 4)
    length_ticks: int = 0
    key_root: int = 0                # 0=C .. 11=B (best guess)
    key_minor: bool = False


@dataclass
class StyleChannel:
    """Notes for one style channel (RHY1..PHR2) inside one section, in the source chord (CMaj7)."""
    role: str                        # key of STYLE_CHANNELS
    program: int | None
    notes: list[Note] = field(default_factory=list)
    # optional mixer overrides from the recipe (None = not sent / role default in the writer)
    bank_msb: int | None = None
    bank_lsb: int | None = None
    volume: int | None = None
    pan: int | None = None
    reverb: int | None = None
    chorus: int | None = None
    delay: int | None = None          # CC94 (variation / delay send)


@dataclass
class StyleSection:
    name: str                        # one of SECTIONS
    length_ticks: int                # whole bars
    channels: list[StyleChannel] = field(default_factory=list)
    # (tick relative to section start, bpm): used for ritardando in endings
    tempo_changes: list[tuple[int, float]] = field(default_factory=list)
    bypass_chords: bool = False      # Intro B/C, Ending B/C: write literal-pitch (NTT bypass) tables


@dataclass
class Style:
    tempo_bpm: float
    time_sig: tuple[int, int]
    sections: list[StyleSection]
    sff_version: int = 1             # 1 = SFF1 + Ctab (default); real files never mix SFF2 with Ctab
    name: str = "midi2sty"
