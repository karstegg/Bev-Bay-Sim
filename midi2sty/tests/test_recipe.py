import json

import pytest

from midi2sty import arrange
from midi2sty.model import Note
from midi2sty.recipe import Recipe, SectionPlan, TrackPlan

from test_arrange import BAR, chan, make_song, sec


def base_recipe(song, **over):
    r = arrange.suggest_recipe(song)
    r.tracks = [TrackPlan(0, "RHY2"), TrackPlan(1, "BASS"), TrackPlan(2, "CHD1"), TrackPlan(3, "PAD"),
                TrackPlan(4, "exclude")]
    r.sections = [SectionPlan("Main B", "song", 0, 4)]
    for k, v in over.items():
        setattr(r, k, v)
    return r


def painted(song, plan, **kw):
    r = base_recipe(song)
    r.sections.append(plan)
    return arrange.build_style_with_warnings(song, r)


def test_json_roundtrip_track_ranges():
    r = Recipe(sections=[SectionPlan("Main A", track_ranges={1: (8, 4), 2: (0, 2)}, mute_tracks=[3], n_bars=4)])
    text = r.to_json()
    raw = json.loads(text)["sections"][0]
    assert raw["track_ranges"] == {"1": [8, 4], "2": [0, 2]} and raw["mute_tracks"] == [3]
    r2 = Recipe.from_json(text)
    assert r2.sections[0].track_ranges == {1: (8, 4), 2: (0, 2)}
    assert r2.sections[0].mute_tracks == [3] and r2 == r


def test_old_recipe_json_loads_and_builds():
    song = make_song()
    r = arrange.suggest_recipe(song)
    d = json.loads(r.to_json())
    for s in d["sections"]:
        s.pop("track_ranges"), s.pop("mute_tracks")
    r2 = Recipe.from_json(json.dumps(d))
    assert all(s.track_ranges == {} and s.mute_tracks == [] for s in r2.sections)
    a = arrange.build_style(song, r)
    b, w = arrange.build_style_with_warnings(song, r2)
    assert a == b and w == []


def test_main_bass_and_chords_from_different_bars():
    song = make_song()
    song.tracks[1].notes = [n for n in song.tracks[1].notes if not 8 * BAR <= n.start < 12 * BAR] + \
        [Note(b * BAR, 900, 40, 90) for b in range(8, 12)]
    plan = SectionPlan("Main A", track_ranges={1: (8, 4), 2: (0, 4)})
    style, warns = painted(song, plan)
    m = sec(style, "Main A")
    assert warns == [] and m.length_ticks == 4 * BAR
    assert {c.role for c in m.channels} == {"BASS", "CHD1"}
    assert len(chan(m, "BASS")) == 4                      # the sparse bass of bars 8-11 (4 notes), not 16
    assert max(n.start for n in chan(m, "CHD1")) < BAR * 4
    assert not any(n.start % 240 for n in chan(m, "CHD1")) and len(chan(m, "CHD1")) == 12  # bars 0-3: held chords


def test_painted_fill_drums_only_from_bar_7():
    song = make_song()
    song.tracks[0].notes.append(Note(8 * BAR + 5, 100, 49, 100))   # crash on the downbeat after bar 7
    plan = SectionPlan("Fill In AA", track_ranges={0: (7, 1)})
    style, _ = painted(song, plan)
    f = sec(style, "Fill In AA")
    assert f.length_ticks == BAR
    assert {c.role for c in f.channels} <= {"RHY1", "RHY2"} and chan(f, "RHY2")
    assert any(n.pitch == 49 and n.start >= BAR - 120 for n in chan(f, "RHY2"))


def test_section_lengths_and_short_range_not_looped():
    song = make_song()
    plan = SectionPlan("Main C", track_ranges={0: (0, 2), 1: (0, 4)})
    m = sec(painted(song, plan)[0], "Main C")
    assert m.length_ticks == 4 * BAR
    assert max(n.start for n in chan(m, "RHY2")) < 2 * BAR        # drums play once then silent
    assert max(n.start for n in chan(m, "BASS")) >= 3 * BAR
    plan = SectionPlan("Main C", n_bars=2, track_ranges={0: (0, 2), 1: (0, 4)})
    m = sec(painted(song, plan)[0], "Main C")
    assert m.length_ticks == 2 * BAR and max(n.start for n in chan(m, "BASS")) < 2 * BAR


def test_mute_tracks():
    song = make_song()
    plan = SectionPlan("Main C", track_ranges={0: (0, 4), 1: (0, 4), 2: (0, 4)}, mute_tracks=[1])
    m = sec(painted(song, plan)[0], "Main C")
    assert {c.role for c in m.channels} == {"RHY1", "RHY2", "CHD1"}


def test_excluded_track_warns_and_is_skipped():
    song = make_song()
    plan = SectionPlan("Main C", track_ranges={4: (4, 4), 1: (0, 4)})
    style, warns = painted(song, plan)
    assert len(warns) == 1 and "track 4" in warns[0] and "Main C" in warns[0]
    assert {c.role for c in sec(style, "Main C").channels} == {"BASS"}
    # nothing usable -> falls back to the unpainted behaviour
    style, warns = painted(song, SectionPlan("Main C", track_ranges={4: (4, 4)}))
    assert len(warns) == 2 and sec(style, "Main C").channels


def test_ending_painted_gets_final_hit_and_validate():
    song = make_song()
    plan = SectionPlan("Ending A", track_ranges={0: (4, 2), 1: (4, 2)})
    style, _ = painted(song, plan)
    e = sec(style, "Ending A")
    assert e.length_ticks == 2 * BAR
    assert any(n.pitch == 49 and n.start >= BAR for n in chan(e, "RHY2"))
    r = base_recipe(song)
    r.sections.append(SectionPlan("Main C", track_ranges={1: (-1, 4)}))
    assert r.validate()
