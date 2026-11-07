"""Section markers in the source MIDI -> section plans.

Yamaha's own "MIDI Song to Style" tool ships a marker template (Intro I/II/III, Fill A-D, Main A-D, Break,
Ending I/II/III, End of Section). Files marked that way, or with our own section names, skip the section guessing:
every recognised marker starts a section that runs to the next marker.
"""
from __future__ import annotations
import re

from . import melody, model
from .recipe import SectionPlan

_NAMES: dict[str, str] = {}
for _i, _l in enumerate("ABCD"):
    _NAMES[f"main{_l.lower()}"] = f"Main {_l}"
    _NAMES[f"fill{_l.lower()}"] = f"Fill In {_l}{_l}"
    _NAMES[f"fillin{_l.lower()}{_l.lower()}"] = f"Fill In {_l}{_l}"
for _i, _r in enumerate(("i", "ii", "iii")):
    _a = "ABC"[_i].lower()
    _NAMES[f"intro{_r}"] = _NAMES[f"intro{_a}"] = f"Intro {'ABC'[_i]}"
    _NAMES[f"ending{_r}"] = _NAMES[f"ending{_a}"] = f"Ending {'ABC'[_i]}"
_NAMES["break"] = _NAMES["fillinba"] = "Fill In BA"


def _norm(text: str) -> str:
    return re.sub(r"[\s._-]+", "", text).lower()


def marker_sections(song: model.Song) -> tuple[list[SectionPlan], list[str]]:
    """Section plans from recognised markers (empty list when the song has no usable Main marker)."""
    bl = melody.bar_ticks(song)
    marks = sorted(song.markers)
    plans: list[SectionPlan] = []
    warns: list[str] = []
    seen: set[str] = set()
    for i, (tick, text) in enumerate(marks):
        name = _NAMES.get(_norm(text))
        if name is None:
            continue
        if name in seen:
            warns.append(f"marker '{text}' repeats {name}; the first one is used")
            continue
        end = next((t for t, _ in marks[i + 1:] if t > tick), song.length_ticks)
        start_bar = round(tick / bl)
        n_bars = max(1, round((end - tick) / bl))
        if abs(tick - start_bar * bl) > bl // 8 or abs((end - tick) - n_bars * bl) > bl // 8:
            warns.append(f"marker '{text}' is not on a bar line; rounded to bar {start_bar + 1}, {n_bars} bar(s)")
        seen.add(name)
        plans.append(SectionPlan(name, "song", start_bar, n_bars, note=f"from the marker '{text}'"))
    if not any(p.name.startswith("Main") for p in plans):
        return [], warns
    return plans, warns
