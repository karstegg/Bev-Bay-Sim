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


def test_track_override_json_roundtrip_and_unknown_keys():
    r = Recipe(tracks=[TrackPlan(1, "BASS", channel=3, program=40, bank_msb=1, bank_lsb=2,
                                 volume=90, pan=10, reverb=20, chorus=30)])
    r2 = Recipe.from_json(r.to_json())
    assert r2 == r and r2.tracks[0].pan == 10 and TrackPlan(0, "BASS").channel is None
    import json as _j
    d = _j.loads(r.to_json())
    d["future"] = 1
    d["tracks"][0]["colour"] = "red"
    d["sections"] = [{"name": "Main A", "zzz": 5}]
    r3 = Recipe.from_json(_j.dumps(d))
    assert r3.tracks[0].volume == 90 and r3.sections[0].name == "Main A"


def test_override_validation():
    r = Recipe(tracks=[TrackPlan(0, "BASS", channel=16, volume=128)])
    assert len(r.validate()) == 2
    assert Recipe(tracks=[TrackPlan(0, "BASS", channel=15, volume=127, pan=0)]).validate() == []


def test_override_drum_to_pitched_and_back():
    song = make_song()
    r = base_recipe(song)
    r.tracks[0].channel = 3               # drum track no longer drums
    assert song.tracks[0].is_drums and song.tracks[0].channel == 9
    st = arrange.build_style(song, r)
    assert song.tracks[0].is_drums and song.tracks[0].channel == 9   # caller's song untouched
    assert chan(sec(st, "Main B"), "RHY1") == []
    r = base_recipe(song)
    r.tracks[1].channel = 9               # bass becomes drums: split into RHY1/RHY2, no pitched BASS
    st = arrange.build_style(song, r)
    assert chan(sec(st, "Main B"), "BASS") == []
    assert not song.tracks[1].is_drums


def test_override_program_and_mix_reach_style():
    song = make_song()
    r = base_recipe(song)
    r.tracks[1].program = 50
    r.tracks[1].volume = 99
    r.tracks[1].bank_msb = 8
    st = arrange.build_style(song, r)
    bass = next(c for c in sec(st, "Main B").channels if c.role == "BASS")
    assert bass.program == 50 and bass.volume == 99 and bass.bank_msb == 8 and bass.pan is None
    assert song.tracks[1].program == 33


def test_delay_override_reaches_writer():
    from midi2sty import model
    from midi2sty.recipe import Recipe, TrackPlan
    from midi2sty.smf import CC, parse_smf
    from midi2sty.sty_writer import write_sty
    r = Recipe.from_json(Recipe(tracks=[TrackPlan(0, "BASS", delay=77)]).to_json())
    assert r.tracks[0].delay == 77
    notes = [model.Note(0, 240, 36, 90)]
    secs = [model.StyleSection(n, 1920, [model.StyleChannel("BASS", 33, notes, delay=77)])
            for n in ("Main A", "Main B", "Main C", "Main D", "Fill In AA", "Fill In BB", "Fill In CC", "Fill In DD",
                      "Intro A", "Intro B", "Intro C", "Ending A", "Ending B", "Ending C", "Fill In BA")]
    smf = parse_smf(write_sty(model.Style(100.0, (4, 4), secs)))
    cc94 = [e.b for e in smf.tracks[0] if e.kind == CC and e.a == 94 and e.channel == model.STYLE_CHANNELS["BASS"]]
    assert cc94 == [77]
