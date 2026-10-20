from midi2sty import model
from midi2sty.model import Note, Style, StyleChannel, StyleSection
from midi2sty.smf import META, NOTE_ON, parse_smf
from midi2sty.sty_writer import write_sty
from midi2sty.validate import validate_sty

BAR = 4 * model.TICKS_PER_BEAT


def _style():
    notes = [Note(0, 240, 36, 100), Note(BAR // 2, 240, 38, 90)]
    secs = [StyleSection(n, BAR * 2, [StyleChannel("RHY1", 0, notes),
                                      StyleChannel("BASS", 33, [Note(0, 480, 36, 90)])])
            for n in ("Intro A", "Main A", "Ending A")]
    return Style(120.0, (4, 4), secs)


def test_roundtrip_valid():
    data = write_sty(_style())
    assert validate_sty(data) == []


def test_sections_sequential_and_channels():
    smf = parse_smf(write_sty(_style()))
    ev = smf.tracks[0]
    marks = {e.data.decode(): e.tick for e in ev if e.kind == META and e.meta_type == 6}
    assert marks["Intro A"] == 0 and marks["Main A"] == BAR * 2 and marks["Ending A"] == BAR * 4
    assert {e.channel for e in ev if e.kind == NOTE_ON} == {8, 10}


def test_casm_present_after_track():
    data = write_sty(_style())
    assert b"CASM" in data and data.count(b"Ctab") == 3 * 8


def test_validator_flags_garbage():
    assert validate_sty(b"junk")
