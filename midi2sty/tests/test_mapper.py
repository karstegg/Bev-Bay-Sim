from midi2sty.mapper import MapOptions, assign_roles, bar_ticks, song_to_style, transpose_shift
from midi2sty.model import Note, Song, Track

BAR = 1920


def drums(bars, hats=True, fill_last=False):
    ns = []
    for b in range(bars):
        for i in range(8):
            t = b * BAR + i * 240
            ns.append(Note(t, 60, 42 if hats else 38, 80))
        ns.append(Note(b * BAR, 100, 36, 100))
        ns.append(Note(b * BAR + 960, 100, 38, 100))
    return Track("drums", 9, 0, ns, True)


def bass(bars, root=45):
    return Track("bass", 0, 33, [Note(b * BAR + i * 480, 400, root + (i % 2) * 7, 90)
                                 for b in range(bars) for i in range(4)])


def chords(bars, root=57, dense_from=None):
    ns = []
    for b in range(bars):
        for p in (0, 4, 7):
            ns.append(Note(b * BAR, 1800, root + p + 12, 70))
        if dense_from is not None and b >= dense_from:
            for i in range(1, 8):
                ns.append(Note(b * BAR + i * 240, 100, root + 24, 70))
    return Track("keys", 1, 4, ns)


def lead(bars):
    return Track("lead", 2, 80, [Note(b * BAR + i * 480, 300, 76 + i, 90)
                                 for b in range(bars) for i in range(4)])


def make_song(bars=16, **kw):
    return Song([drums(bars), bass(bars), chords(bars), lead(bars)], length_ticks=bars * BAR, **kw)


def test_bar_ticks():
    assert bar_ticks((4, 4)) == 1920
    assert bar_ticks((3, 4)) == 1440
    assert bar_ticks((6, 8)) == 1440


def test_role_assignment():
    roles = assign_roles(make_song())
    assert set(roles) == {"RHY1", "RHY2", "BASS", "CHD1", "PHR1"}
    assert all(n.pitch == 42 for n in roles["RHY2"][1])
    assert roles["BASS"][0] == 33


def test_extra_tracks_merge_one_per_channel():
    s = make_song()
    s.tracks.append(lead(16))
    s.tracks.append(lead(16))
    roles = assign_roles(s)
    assert len([r for r in roles if r.startswith("PHR")]) == 2
    assert len(roles["PHR2"][1]) == 2 * len(roles["PHR1"][1])


def test_sections_whole_bars_and_names():
    st = song_to_style(make_song(16))
    names = [s.name for s in st.sections]
    assert "Intro A" in names and "Main A" in names and "Ending A" in names
    for s in st.sections:
        assert s.length_ticks % BAR == 0 and s.length_ticks > 0
        for ch in s.channels:
            assert all(0 <= n.start < s.length_ticks for n in ch.notes)
            assert all(n.start + n.dur <= s.length_ticks for n in ch.notes)
    main = next(s for s in st.sections if s.name == "Main A")
    assert main.length_ticks == 4 * BAR


def test_three_four_time():
    song = make_song(8)
    song.time_sig = (3, 4)
    st = song_to_style(song, MapOptions(bars_per_section=2))
    assert all(s.length_ticks % 1440 == 0 for s in st.sections)


def test_transpose_to_c():
    assert transpose_shift(0, False) == 0
    assert transpose_shift(2, False) == -2
    assert transpose_shift(9, True) == 0       # A minor -> C major
    assert transpose_shift(7, False) == 5
    song = make_song(8, key_root=2)            # D major: everything down 2
    base = song_to_style(make_song(8, key_root=0))
    st = song_to_style(song)
    a = next(c for c in base.sections[0].channels if c.role == "BASS")
    b = next(c for c in st.sections[0].channels if c.role == "BASS")
    assert [n.pitch for n in b.notes] == [n.pitch - 2 for n in a.notes]
    d = next(c for c in st.sections[0].channels if c.role == "RHY1")
    assert {n.pitch for n in d.notes} <= {36, 38}


def test_deterministic():
    assert song_to_style(make_song()) == song_to_style(make_song())


def test_distinct_mains_and_fill_density():
    bars = 16
    song = Song([drums(bars), bass(bars), chords(bars, dense_from=8)], length_ticks=bars * BAR)
    st = song_to_style(song)
    names = [s.name for s in st.sections]
    assert "Main A" in names and "Main B" in names
    dens = {s.name: sum(len(c.notes) for c in s.channels) for s in st.sections}
    assert dens["Main A"] <= dens["Main B"]
    assert next(s for s in st.sections if s.name == "Fill In AA").length_ticks == BAR


def test_sections_option_and_validation():
    st = song_to_style(make_song(), MapOptions(sections=("Main A", "Ending A")))
    assert [s.name for s in st.sections] == ["Main A", "Ending A"]
    try:
        song_to_style(make_song(), MapOptions(sections=("Bogus",)))
    except ValueError:
        pass
    else:
        raise AssertionError


def test_short_song_and_empty():
    st = song_to_style(make_song(2))
    assert st.sections and all(s.length_ticks <= 2 * BAR for s in st.sections)
    assert song_to_style(Song([])).sections == []
