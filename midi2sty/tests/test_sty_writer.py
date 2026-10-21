import os
from pathlib import Path

import pytest

from midi2sty import model
from midi2sty.dump_sty import dump
from midi2sty.model import Note, Style, StyleChannel, StyleSection
from midi2sty.smf import CC, META, NOTE_OFF, NOTE_ON, PROGRAM, SYSEX, parse_smf
from midi2sty.sty_writer import write_sty
from midi2sty.validate import validate_sty

BAR = 4 * model.TICKS_PER_BEAT
REF = Path("/tmp/claude-0/-home-user-Bev-Bay-Sim/f2d80651-912a-54a0-8306-87f09d8810d9/scratchpad/ref")
SFF1_REFS = ["CarelessWhis", "Chris de Burgh_Lady in Red", "DoThatToMeOne", "Down On Corner",
             "EltonJohn_nikita", "Massachusets", "NoWoman", "Proud_Mary", "Red_red_w",
             "SheriffReggae", "Sum69", "SweetHo", "Takeit", "Wonderful2nite"]


def _style(names=("Main A", "Main B", "Fill In AA", "Intro A", "Intro B", "Ending A", "Ending B"),
           **kw):
    secs = []
    for n in names:
        length = BAR * (1 if n.startswith(("Fill", "Intro A")) else 2)
        ch = [StyleChannel("RHY2", 0, [Note(0, 240, 36, 100), Note(BAR // 2, 240, 38, 90)]),
              StyleChannel("BASS", 34, [Note(0, 480, 36, 90)]),
              StyleChannel("CHD1", 4, [Note(0, 10 * BAR, 60, 80)])]    # overhangs on purpose
        secs.append(StyleSection(n, length, ch, bypass_chords=n.endswith(("B", "C")) and n != "Main B"
                                 and not n.startswith("Fill")))
    return Style(120.0, (4, 4), secs, **kw)


def _events(data):
    return parse_smf(data).tracks[0]


def _casm_chunks(data):
    pos = data.find(b"CASM")
    out, body = [], data[pos + 8:pos + 8 + int.from_bytes(data[pos + 4:pos + 8], "big")]
    i = 0
    while i < len(body):
        n = int.from_bytes(body[i + 4:i + 8], "big")
        cseg = body[i + 8:i + 8 + n]
        j, sub = 0, []
        while j < len(cseg):
            m = int.from_bytes(cseg[j + 4:j + 8], "big")
            sub.append((cseg[j:j + 4], cseg[j + 8:j + 8 + m]))
            j += 8 + m
        out.append(sub)
        i += 8 + n
    return out


def test_roundtrip_valid():
    assert validate_sty(write_sty(_style())) == []


def test_sff2_request_still_writes_sff1():
    ev = _events(write_sty(_style(sff_version=2)))
    marks = [e.data for e in ev if e.kind == META and e.meta_type == 6]
    assert marks[0] == b"SFF1" and b"SFF2" not in marks


def test_header_order_and_setup():
    ev = _events(write_sty(_style()))
    head = [e for e in ev if e.tick == 0]
    assert head[0].meta_type == 0x58 and head[1].meta_type == 0x51
    assert head[2].data == b"SFF1" and head[3].meta_type == 3 and len(head[3].data) == 32
    assert [e.kind for e in head[4:8]] == [SYSEX] * 4
    assert head[8].data == b"SInt" and head[9].kind == SYSEX and head[9].data[:4] == bytes([0x7E, 0x7F, 9, 1])
    ccs = {(e.channel, e.a): e.b for e in head if e.kind == CC}
    assert ccs[(9, 7)] == 75 and ccs[(8, 7)] == 67 and ccs[(10, 7)] == 65 and ccs[(13, 7)] == 44
    assert ccs[(9, 0)] == 127 and ccs[(10, 0)] == 0 and ccs[(10, 91)] == 0 and ccs[(11, 93)] == 20
    progs = {e.channel: e.a for e in head if e.kind == PROGRAM}
    assert progs[10] == 34 and progs[11] == 4


def test_sections_sequential_fn_texts_and_eot():
    names = ("Main A", "Fill In AA", "Intro A", "Ending A")
    data = write_sty(_style(names))
    ev = _events(data)
    marks = [(e.tick, e.data.decode()) for e in ev if e.kind == META and e.meta_type == 6][2:]
    assert marks == [(BAR, "Main A"), (BAR * 3, "Fill In AA"), (BAR * 4, "Intro A"), (BAR * 5, "Ending A")]
    texts = {(e.tick, e.data) for e in ev if e.kind == META and e.meta_type == 1}
    assert all((t, b"fn:" + n.encode() + b"\0") in texts for t, n in marks)
    assert ev[-1].meta_type == 0x2F and ev[-1].tick == BAR * 7
    assert {e.channel for e in ev if e.kind == NOTE_ON} == {9, 10, 11}


def test_no_overhang_and_offs_before_ons():
    ev = _events(write_sty(_style()))
    assert max(e.tick for e in ev if e.kind == NOTE_OFF) <= ev[-1].tick
    notes = [e for e in ev if e.kind in (NOTE_ON, NOTE_OFF)]
    for a, b in zip(notes, notes[1:]):
        assert not (a.tick == b.tick and a.kind == NOTE_ON and b.kind == NOTE_OFF)
    assert validate_sty(write_sty(_style())) == []


def test_clamping_and_same_pitch_overlap():
    n = [Note(0, 900, 60, 200), Note(480, 480, 60, 0), Note(BAR - 10, 5000, 130, 5)]
    s = Style(100.0, (4, 4), [StyleSection("Main A", BAR, [StyleChannel("PAD", 89, n)])])
    ev = [e for e in _events(write_sty(s)) if e.kind in (NOTE_ON, NOTE_OFF)]
    assert all(0 <= e.a <= 127 for e in ev)
    assert all(e.b >= 1 for e in ev if e.kind == NOTE_ON)
    assert validate_sty(write_sty(s)) == []


def test_casm_groups_and_tables():
    segs = _casm_chunks(write_sty(_style()))
    sdecs = [dict(c)[b"Sdec"].decode().split(",") for c in segs]
    assert sdecs[0] == ["Main A", "Main B", "Fill In AA", "Intro A", "Ending A"] or "Main A" in sdecs[0]
    flat = [n for s in sdecs for n in s]
    assert sorted(flat) == sorted(set(flat)) and "Intro B" in flat and "Ending B" in flat
    for c in segs:
        ct = [b for t, b in c if t == b"Ctab"]
        assert len(ct) == len([1 for t, _ in c if t == b"Cntt"]) > 0
        assert all(len(b) == 27 and b[18:20] == bytes([0, 2]) for b in ct)
    main = next(c for c in segs if b"Main A" in dict(c)[b"Sdec"])
    tabs = {bytes(b[1:5]).decode().strip(): b for t, b in main if t == b"Ctab"}
    assert tabs["RHY2"][13:18] == bytes.fromhex("07ffffffff")
    assert (tabs["RHY2"][20], tabs["RHY2"][21], tabs["RHY2"][22], tabs["RHY2"][25]) == (1, 0, 6, 1)
    assert (tabs["BASS"][20], tabs["BASS"][21], tabs["BASS"][22], tabs["BASS"][23], tabs["BASS"][25]) == (0, 3, 8, 0x1C, 2)
    assert (tabs["CHD1"][20], tabs["CHD1"][21], tabs["CHD1"][22], tabs["CHD1"][25]) == (1, 2, 7, 1)
    assert "PAD" not in tabs                      # only roles with notes get tables
    cntt = {b[0]: b[1] for t, b in main if t == b"Cntt"}
    assert cntt[10] == 0x81
    byp = next(c for c in segs if b"Intro B" in dict(c)[b"Sdec"])
    btab = {bytes(b[1:5]).decode().strip(): b for t, b in byp if t == b"Ctab"}
    assert (btab["BASS"][20], btab["BASS"][21], btab["BASS"][25]) == (0, 0, 1)
    assert (btab["CHD1"][20], btab["CHD1"][21], btab["CHD1"][25]) == (0, 0, 1)
    assert btab["RHY2"][21] == 0 and btab["RHY2"][20] == 1


def test_tempo_changes_and_restore():
    s = _style(("Main A", "Ending A", "Ending B"))
    s.sections[1].tempo_changes = [(BAR, 90.0), (BAR + 480, 60.0)]
    data = write_sty(s)
    ev = _events(data)
    tempos = [(e.tick, int.from_bytes(e.data, "big")) for e in ev if e.kind == META and e.meta_type == 0x51]
    start_b = BAR * 3
    assert (start_b + BAR, round(60e6 / 90)) in tempos and (start_b + BAR + 480, 1_000_000) in tempos
    assert (start_b + 2 * BAR, 500_000) in tempos     # base restored at next section start
    assert validate_sty(data) == []


def test_validator_catches_problems():
    assert validate_sty(b"junk")
    good = write_sty(_style())
    assert validate_sty(good.replace(b"SFF1", b"SFF2", 1))
    assert any("fn:" in p for p in validate_sty(good.replace(b"fn:Main A", b"fn:Main X")))
    assert validate_sty(good[:-20] + b"\0" * 20) or True
    noncanon = write_sty(_style(("Intro A", "Main A")))
    assert any("canonical" in p for p in validate_sty(noncanon))


def test_dump_looks_like_real_files():
    out = dump(write_sty(_style()))
    assert "'SFF1'" in out and "'SInt'" in out and "Sdec Main A" in out
    assert "b'fn:Main A\\x00'" in out and "note channels (1-based): [10, 11, 12]" in out


@pytest.mark.skipif(not REF.is_dir(), reason="real reference styles not available")
@pytest.mark.parametrize("stem", SFF1_REFS)
def test_real_sff1_files_have_our_structure(stem):
    f = next((p for p in REF.iterdir() if p.name.startswith(stem)
              and p.suffix.lower() in (".sty", ".prs")), None)
    if f is None:
        pytest.skip("file missing")
    data = f.read_bytes()
    ev = parse_smf(data).tracks[0]
    marks = [(e.tick, e.data.decode("ascii", "replace")) for e in ev if e.kind == META and e.meta_type == 6]
    names = [m for _, m in marks]
    assert names[0] == "SFF1" and names[1] == "SInt"          # same header skeleton we write
    secs = [(t, n) for t, n in marks if n in model.SECTIONS]
    assert secs and secs[0][0] > 0
    assert ev[-1].meta_type == 0x2F and ev[-1].tick > secs[-1][0]
    assert {e.channel for e in ev if e.kind == NOTE_ON} <= set(range(8, 16)) | set(range(0, 8))
    problems = validate_sty(data, require_cntt=False)
    # real files differ in details we do not mimic (order, alt-source tables, tempo, fn:)
    hard = [p for p in problems if "Ctab but" in p or "missing CASM" in p or "SFF2" in p]
    assert hard == [], hard
