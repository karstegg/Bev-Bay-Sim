from midi2sty import analyze, arrange, markers
from midi2sty.smf import MidiEvent as E, write_smf
import midi2sty.smf as smf

PPQ = 480
BAR = PPQ * 4


def mk(*pairs):
    return [E(0, smf.META, meta_type=0x03, data=b"markers")] + [E(b * BAR, smf.META, meta_type=0x06, data=n.encode()) for b, n in pairs]


def song_with(pairs, n_bars=40):
    drums = [E(0, smf.META, meta_type=0x03, data=b"Drums")]
    bass = [E(0, smf.META, meta_type=0x03, data=b"Bass"), E(0, smf.PROGRAM, 1, 33)]
    for b in range(n_bars):
        for q in range(4):
            t = b * BAR + q * PPQ
            drums += [E(t, smf.NOTE_ON, 9, 36 if q % 2 == 0 else 38, 90), E(t + 60, smf.NOTE_OFF, 9, 36 if q % 2 == 0 else 38, 0)]
            bass += [E(t, smf.NOTE_ON, 1, 36 + (b % 5), 90), E(t + 200, smf.NOTE_OFF, 1, 36 + (b % 5), 0)]
    return analyze.load_song(write_smf([mk(*pairs), bass, drums], PPQ, 1))


YAMAHA = [(1, "Intro I"), (2, "Fill A"), (3, "Main A"), (5, "Fill B"), (6, "Main B"), (8, "Break"), (9, "Ending I"),
          (10, "Intro II"), (14, "Ending II"), (18, "End of Section")]


def test_markers_loaded_and_mapped():
    s = song_with(YAMAHA)
    assert s.markers[0] == (BAR, "Intro I")
    plans, warns = markers.marker_sections(s)
    by = {p.name: p for p in plans}
    assert not warns
    assert (by["Main A"].start_bar, by["Main A"].n_bars) == (3, 2)
    assert (by["Fill In AA"].start_bar, by["Fill In AA"].n_bars) == (2, 1)
    assert by["Fill In BA"].start_bar == 8          # "Break"
    assert by["Intro A"].n_bars == 1 and by["Intro B"].n_bars == 4
    assert by["Ending B"].n_bars == 4 and by["Ending B"].start_bar == 14


def test_no_main_marker_means_no_plans():
    s = song_with([(1, "Intro I"), (2, "Fill A")])
    assert markers.marker_sections(s)[0] == []


def test_not_on_bar_line_warns_and_duplicates_ignored():
    s = song_with([(0, "Main A"), (4, "Main A")])
    s.markers = [(0, "Main A"), (BAR * 4 + 200, "Main A"), (BAR * 4 + 240, "Main B")]
    plans, warns = markers.marker_sections(s)
    assert [p.name for p in plans] == ["Main A", "Main B"]
    assert any("repeats" in w for w in warns)


def test_suggest_recipe_uses_markers():
    s = song_with(YAMAHA)
    r = arrange.suggest_recipe(s)
    by = {p.name: p for p in r.sections}
    assert by["Main A"].source == "song" and (by["Main A"].start_bar, by["Main A"].n_bars) == (3, 2)
    assert by["Main B"].start_bar == 6 and by["Fill In BA"].start_bar == 8
    assert "marker" in by["Main A"].note
    st = arrange.build_style(s, r)
    assert {x.name for x in st.sections} >= {"Main A", "Main B", "Intro B", "Ending B"}
