import glob
import os

import pytest

from midi2sty import arrange, melody, model, sections
from midi2sty.model import Note, Song, Track
from midi2sty.recipe import Recipe

BAR = 1920
ROOTS = [45, 41, 48, 43]          # A F C G  (Am F C G), one chord per bar
MINOR = [True, False, False, False]


def make_song(bars=16, lead=True, silent_bars=0, drums=True):
    dn, bs, ch, pad, ld = [], [], [], [], []
    for b in range(silent_bars, bars):
        t0 = b * BAR
        r = ROOTS[(b - silent_bars) % 4]
        minor = MINOR[(b - silent_bars) % 4]
        if drums:
            for i in range(8):
                dn.append(Note(t0 + i * 240, 60, 42, 80))
            for beat in (0, 2):
                dn.append(Note(t0 + beat * 480, 100, 36, 100))
            for beat in (1, 3):
                dn.append(Note(t0 + beat * 480, 100, 38, 95))
            dn.append(Note(t0 + 240, 60, 54, 70))
        for i in range(4):
            bs.append(Note(t0 + i * 480, 400, r - 12 + (7 if i == 3 else 0), 90))
        for p in (r + 12, r + 12 + (3 if minor else 4), r + 19):
            ch.append(Note(t0, 1800, p, 70))
            if b - silent_bars >= 8:
                for k in range(1, 8):
                    ch.append(Note(t0 + k * 240, 100, p, 60))
        pad.append(Note(t0, BAR, r + 24, 50))
        if lead and b >= silent_bars + 4:
            for i in range(4):
                ld.append(Note(t0 + i * 480, 300, 79 + (i * 2) % 7, 95))
    tracks = [Track("Drums", 9, 0, dn, True), Track("Bass", 1, 33, bs), Track("Keys", 2, 4, ch),
              Track("Strings", 3, 48, pad)]
    if lead:
        tracks.append(Track("Melody", 4, 65, ld))
    for i, t in enumerate(tracks):
        t.index = i
    return Song(tracks, tempo_bpm=120.0, length_ticks=bars * BAR, key_root=9, key_minor=True)


def roles(recipe):
    return {t.index: t.role for t in recipe.tracks}


def style_of(song, recipe=None):
    recipe = recipe or arrange.suggest_recipe(song)
    return arrange.build_style(song, recipe), recipe


def sec(style, name):
    return next(s for s in style.sections if s.name == name)


def chan(section, role):
    return next((c.notes for c in section.channels if c.role == role), [])


def test_suggest_roles_and_exclusion():
    r = arrange.suggest_recipe(make_song())
    ro = roles(r)
    assert ro[0] == "RHY2" and ro[1] == "BASS" and ro[4] == "exclude"
    assert ro[2] in ("CHD1", "CHD2") and ro[3] == "PAD"
    assert "melody" in next(t.reason for t in r.tracks if t.index == 4).lower()
    assert r.validate() == []
    assert r.tonic == 9 and r.minor


def test_classify_parts_shape():
    rows = melody.classify_parts(make_song())
    assert [x["index"] for x in rows] == [0, 1, 2, 3, 4]
    assert rows[4]["tier"] >= 1 and rows[1]["role"] == "bass" and rows[0]["role"] == "drums"
    assert all({"index", "tier", "score", "reason"} <= set(x) for x in rows)


def test_all_15_sections_in_order_and_lengths():
    style, _ = style_of(make_song())
    assert [s.name for s in style.sections] == model.CANONICAL_ORDER
    for s in style.sections:
        assert s.length_ticks % BAR == 0 and s.length_ticks > 0
        for c in s.channels:
            for n in c.notes:
                assert 0 <= n.start < s.length_ticks and n.start + n.dur <= s.length_ticks, (s.name, c.role, n)
    assert sec(style, "Intro A").length_ticks == BAR
    for f in ("Fill In AA", "Fill In BB", "Fill In CC", "Fill In DD", "Fill In BA"):
        assert sec(style, f).length_ticks == BAR
    assert sec(style, "Main A").length_ticks == 4 * BAR
    assert 2 * BAR <= sec(style, "Intro B").length_ticks <= 4 * BAR
    assert 4 * BAR <= sec(style, "Intro C").length_ticks <= 8 * BAR
    assert BAR <= sec(style, "Ending A").length_ticks <= 2 * BAR
    assert 4 * BAR <= sec(style, "Ending C").length_ticks <= 8 * BAR


def test_tempo_and_override():
    song = make_song()
    style, r = style_of(song)
    assert style.tempo_bpm == pytest.approx(117.0)
    r.tempo_bpm = 100
    assert arrange.build_style(song, r).tempo_bpm == 100


def test_chord_normalisation_to_cmaj7_and_register():
    style, _ = style_of(make_song())
    for name in ("Main A", "Main B"):
        s = sec(style, name)
        bass = chan(s, "BASS")
        assert bass and all(24 <= n.pitch <= 38 for n in bass)
        # bass plays root on 3 beats, fifth on beat 4 -> only C and G pitch classes
        assert {n.pitch % 12 for n in bass} <= {0, 7}
        chd = chan(s, "CHD1") + chan(s, "CHD2")
        assert chd and all(48 <= n.pitch <= 76 for n in chd)
        # Am chord bar is majorised: C E G, no Eb/minor third left
        assert {n.pitch % 12 for n in chd} <= {0, 4, 7}


def test_drum_split_and_roles():
    style, _ = style_of(make_song())
    s = sec(style, "Main A")
    assert {n.pitch for n in chan(s, "RHY1")} == {54}
    assert {36, 38, 42} <= {n.pitch for n in chan(s, "RHY2")}
    assert not any(c.role in ("PHR1", "PHR2") for c in s.channels)   # lead excluded


def _derived_fills_recipe(song):
    recipe = arrange.suggest_recipe(song)
    for pl in recipe.sections:
        if pl.name.startswith("Fill In"):
            pl.source, pl.start_bar, pl.n_bars = "derive", None, None
            pl.derive_from = arrange.FILL_SRC[pl.name]
    return recipe


def test_fills_have_crash_toms_and_keep_pitched():
    song = make_song()
    style, _ = style_of(song, _derived_fills_recipe(song))
    for f in ("Fill In AA", "Fill In BB", "Fill In CC", "Fill In DD"):
        s = sec(style, f)
        r2 = chan(s, "RHY2")
        crash = [n for n in r2 if n.pitch == 49]
        assert len(crash) == 1 and crash[0].start == BAR - 5 and crash[0].dur <= 5
        assert 2 <= len([n for n in r2 if n.pitch in (41, 43, 45, 47, 48, 50)]) <= 4
        assert any(n.pitch in (36, 35) for n in r2) and any(n.pitch == 38 for n in r2)
        assert chan(s, "BASS") and (chan(s, "CHD1") or chan(s, "CHD2"))
    ba, bb = sec(style, "Fill In BA"), sec(style, "Fill In BB")
    n_ba = sum(len(c.notes) for c in ba.channels)
    assert n_ba < sum(len(c.notes) for c in bb.channels)


def test_intro_a_rhythm_only_with_crash():
    s = sec(style_of(make_song())[0], "Intro A")
    assert {c.role for c in s.channels} <= {"RHY1", "RHY2"}
    assert any(n.pitch == 49 and n.start == BAR - 5 for n in chan(s, "RHY2"))


@pytest.mark.parametrize("name", ["Intro B", "Intro C"])
def test_intros_end_with_crash(name):
    s = sec(style_of(make_song())[0], name)
    assert any(n.pitch in (49, 57) and n.start >= s.length_ticks - 120 for n in chan(s, "RHY2"))


@pytest.mark.parametrize("name", ["Ending A", "Ending B", "Ending C"])
def test_endings_final_hit_and_silent_last_beat(name):
    s = sec(style_of(make_song())[0], name)
    last_bar = s.length_ticks - BAR
    onsets = [n.start for c in s.channels for n in c.notes]
    assert last_bar in onsets
    assert not any(t >= s.length_ticks - 480 for t in onsets)
    assert any(n.pitch == 49 and n.start == last_bar for n in chan(s, "RHY2"))
    held = [n for c in s.channels if c.role in ("BASS", "CHD1", "CHD2", "PAD") for n in c.notes
            if n.start == last_bar]
    assert held and all(n.start + n.dur >= s.length_ticks - 960 for n in held)


def test_ritardando_only_on_ending_b_c():
    style, _ = style_of(make_song())
    assert sec(style, "Ending A").tempo_changes == []
    for nm in ("Ending B", "Ending C"):
        tc = sec(style, nm).tempo_changes
        assert len(tc) == 8
        bpm = [b for _, b in tc]
        assert bpm == sorted(bpm, reverse=True)
        assert bpm[-1] == pytest.approx(0.6 * style.tempo_bpm, rel=0.02)
        assert all(0 <= t < sec(style, nm).length_ticks for t, _ in tc)


def test_silent_lead_in_bars_do_not_shift_sections():
    song = make_song(bars=24, silent_bars=3)
    props = sections.propose_sections(song)
    assert props and min(a for a, _ in props.values()) >= 3
    style, r = style_of(song)
    assert sum(len(c.notes) for c in sec(style, "Main A").channels) > 0
    assert sum(len(c.notes) for c in sec(style, "Intro A").channels) > 0
    assert sum(len(c.notes) for c in sec(style, "Ending A").channels) > 0


def test_few_distinct_blocks_reuse_and_thin_main_a():
    song = make_song(bars=8)
    style, r = style_of(song)
    a, b = sec(style, "Main A"), sec(style, "Main B")
    cnt = lambda s: sum(len(c.notes) for c in s.channels)
    assert cnt(a) < cnt(b) or cnt(a) == cnt(b) == 0
    assert [(c.role, c.notes) for c in sec(style, "Main C").channels] == \
           [(c.role, c.notes) for c in sec(style, "Main D").channels]


def test_recipe_track_overrides_honoured():
    song = make_song()
    r = arrange.suggest_recipe(song)
    for t in r.tracks:
        if t.index == 4:
            t.role = "PHR1"
    style = arrange.build_style(song, r)
    assert chan(sec(style, "Main B"), "PHR1") or chan(sec(style, "Main C"), "PHR1")
    r2 = arrange.suggest_recipe(song)
    for t in r2.tracks:
        if t.index == 3:
            t.role = "exclude"
    assert not chan(arrange.build_style(song, r2).sections[0], "PAD")


def test_recipe_json_roundtrip_builds_same_style():
    song = make_song()
    r = arrange.suggest_recipe(song)
    r2 = Recipe.from_json(r.to_json())
    s1, s2 = arrange.build_style(song, r), arrange.build_style(song, r2)
    assert [(s.name, [(c.role, c.notes) for c in s.channels]) for s in s1.sections] == \
           [(s.name, [(c.role, c.notes) for c in s.channels]) for s in s2.sections]


def test_section_n_bars_override_and_normalise_off():
    song = make_song()
    r = arrange.suggest_recipe(song)
    for s in r.sections:
        if s.name == "Main A":
            s.n_bars = 2
        if s.name == "Ending B":
            s.n_bars = 3
    r.normalise_chords = False
    style = arrange.build_style(song, r)
    assert sec(style, "Main A").length_ticks == 2 * BAR
    assert sec(style, "Ending B").length_ticks == 3 * BAR


def test_song_without_drums_and_empty():
    style, _ = style_of(make_song(drums=False))
    assert [s.name for s in style.sections] == model.CANONICAL_ORDER
    with pytest.raises(ValueError):
        arrange.build_style(Song([Track("x", 0, 0, [])]), Recipe())


def test_non_four_four():
    song = make_song()
    song.time_sig = (3, 4)
    style, _ = style_of(song)
    assert all(s.length_ticks % 1440 == 0 for s in style.sections)


# ---- smoke test over the user's real files (never copied into the repo)
_SCRATCH = "/tmp/claude-0/-home-user-Bev-Bay-Sim/f2d80651-912a-54a0-8306-87f09d8810d9/scratchpad"
_REAL = sorted(glob.glob(_SCRATCH + "/ref/*.mid") + glob.glob(_SCRATCH + "/midis/*.mid"))


@pytest.mark.skipif(not _REAL, reason="real-world test MIDIs not available")
@pytest.mark.parametrize("path", _REAL, ids=[os.path.basename(p)[:24] for p in _REAL])
def test_real_songs_build_and_validate(path):
    from midi2sty.analyze import load_song
    song = load_song(path)
    r = arrange.suggest_recipe(song)
    style = arrange.build_style(song, r)
    assert [s.name for s in style.sections] == model.CANONICAL_ORDER
    for s in style.sections:
        for c in s.channels:
            assert all(n.start + n.dur <= s.length_ticks for n in c.notes)
    try:
        from midi2sty.sty_writer import write_sty
        from midi2sty.validate import validate_sty
    except ImportError:
        pytest.skip("writer unavailable")
    assert validate_sty(write_sty(style)) == []


def _song_with_real_fill():
    """4-bar groove at bars 4-7 preceded by a distinct tom-fill bar 3 (kick+toms+crash at the end)."""
    song = make_song()
    drums = next(t for t in song.tracks if t.is_drums)
    bl = BAR
    drums.notes = [n for n in drums.notes if not (2 * bl <= n.start < 3 * bl)]
    for i, p in enumerate((45, 43, 41, 41)):
        drums.notes.append(Note(2 * bl + (8 + i * 2) * bl // 16, 60, p, 90))
    drums.notes.append(Note(2 * bl, 60, 36, 100))
    drums.notes.append(Note(3 * bl, 100, 49, 111))      # crash on the downbeat of the next section
    return song


def test_pick_song_fill_prefers_the_songs_own_transition_bar():
    song = _song_with_real_fill()
    plans = {p.index: p for p in arrange.suggest_recipe(song).tracks}
    pick = arrange.pick_song_fill(song, plans, 3, 4)
    assert pick is not None and pick[0] == 2
