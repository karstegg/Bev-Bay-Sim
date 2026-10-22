# Recipe v2

A recipe is the JSON plan that turns one song into one style (`midi2sty song.mid --recipe r.json`).
v2 adds per-track, per-bar-range painting of sections and is backwards compatible: old files load unchanged.
Bars are 0-based song bars.

## Top-level fields
| field | meaning |
|---|---|
| `name` | style name |
| `tonic`, `minor` | key (pitch class 0=C) used for key-to-C shifting |
| `tempo_bpm` | null = song tempo minus 3 |
| `normalise_chords` | shift each source bar so its chord root becomes C, majorise 3rd/7th |
| `bar_roots` | per-song-bar chord root pitch class, null = detect from the bass |
| `tracks` | `[{index, role, reason}]`, role = RHY1 RHY2 BASS CHD1 CHD2 PAD PHR1 PHR2, `exclude` or `fill_only` |
| `sections` | list of section plans (below) |
| `sff_version` | 1 (default) |

## Section plan
`name` is one of: Intro A/B/C, Main A-D, Fill In AA/BB/CC/DD, Fill In BA (the "break"), Ending A/B/C.

Classic fields: `source` (`song` | `derive` | `auto`), `start_bar`, `n_bars`, `derive_from`, `note`.

New in v2:
- `track_ranges`: `{track_index: [start_bar, n_bars]}`. In files the keys are strings and the values 2-lists;
  `Recipe.from_json` converts to `int` keys / tuples.
- `mute_tracks`: `[track_index, ...]`, default `[]`.

### Painted-section semantics (non-empty `track_ranges`)
- ONLY the painted tracks feed the section; every other track is silent, as is anything in `mute_tracks`.
- Each track plays its own song bar range, not the section's `start_bar`. `source`, `start_bar` and `derive_from`
  are ignored.
- Section length = `n_bars` if set, else the maximum `n_bars` over the ranges. A shorter range plays once and is
  silent afterwards (no looping); a longer one is truncated to the section length.
- Roles come from `tracks`. A painted track with role `exclude`/`fill_only`, or an unknown index, is skipped and a
  warning is recorded. If no usable track remains the section falls back to its unpainted behaviour (plus a warning).
- Drum tracks still split into RHY2 (kit) and RHY1 (percussion).
- Chord normalisation is per SOURCE bar (the bar each note comes from), so bass from bar 8 and chords from bar 0
  each follow their own chords. Painted sections use chord-normalised pitches (no NTT-bypass literal tables).
- Finishing: painted Mains are used as is. A painted Fill gets the closing crash (5 ticks before the end) only if
  one is already present or the painted drum track has a crash right after its range. Intros get a closing crash
  if there is none; Endings have their last beat cleared and a held crash on the last bar if missing
  (crash only when the painted material contains drums). Derived sections (e.g. Intro B from Main A) that depend
  on a painted Main use the painted material.
- Sections without `track_ranges` behave exactly as in v1.

## API
`arrange.build_style(song, recipe) -> Style` (unchanged);
`arrange.build_style_with_warnings(song, recipe) -> (Style, list[str])`.
`Recipe.validate()` also checks that painted ranges have `start_bar >= 0`, `n_bars >= 1`.

## Example
```json
{
  "name": "demo", "tonic": 9, "minor": true, "tempo_bpm": null, "normalise_chords": true, "bar_roots": null,
  "tracks": [
    {"index": 0, "role": "RHY2", "reason": "drums"},
    {"index": 1, "role": "BASS", "reason": ""},
    {"index": 2, "role": "CHD1", "reason": ""},
    {"index": 4, "role": "exclude", "reason": "melody"}
  ],
  "sections": [
    {"name": "Main A", "source": "song", "start_bar": 0, "n_bars": 4},
    {"name": "Main B", "source": "auto", "track_ranges": {"1": [8, 4], "2": [0, 4]}, "mute_tracks": []},
    {"name": "Fill In AA", "source": "auto", "track_ranges": {"0": [7, 1]}},
    {"name": "Ending A", "source": "auto", "n_bars": 2, "track_ranges": {"0": [14, 2], "1": [14, 2]}, "mute_tracks": [1]}
  ],
  "sff_version": 1
}
```
