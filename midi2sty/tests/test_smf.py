import pytest
from midi2sty import smf
from midi2sty.smf import MidiEvent as E, parse_smf, write_smf


def test_vlq_roundtrip():
    for v in (0, 1, 127, 128, 16383, 16384, 0x0FFFFFFF):
        assert smf._read_vlq(smf._vlq(v), 0) == (v, len(smf._vlq(v)))


def test_roundtrip():
    tr0 = [E(0, smf.META, meta_type=0x51, data=(500000).to_bytes(3, "big")),
           E(0, smf.META, meta_type=0x03, data=b"cond")]
    tr1 = [E(0, smf.PROGRAM, 2, 33), E(0, smf.CC, 2, 7, 100),
           E(10, smf.NOTE_ON, 2, 40, 90), E(200, smf.NOTE_OFF, 2, 40, 0),
           E(200, smf.PITCH_BEND, 2, 0, 64), E(300, smf.SYSEX, a=0xF0, data=b"\x7e\xf7")]
    data = write_smf([tr0, tr1], 96, 1)
    f = parse_smf(data)
    assert (f.fmt, f.ppq, len(f.tracks)) == (1, 96, 2)
    assert f.tracks[1][:6] == tr1[:6] and f.tracks[0][:2] == tr0
    assert f.tracks[1][-1].meta_type == 0x2F and f.tracks[1][-1].tick == 300
    assert write_smf(f.tracks, 96, 1) == data


def test_running_status_and_vel0():
    body = bytes([0, 0x90, 60, 100, 10, 62, 100, 20, 60, 0, 0, 62, 0, 0, 0xFF, 0x2F, 0])
    data = b"MThd" + bytes([0, 0, 0, 6, 0, 0, 0, 1, 0, 96]) + b"MTrk" + len(body).to_bytes(4, "big") + body
    ev = parse_smf(data).tracks[0]
    assert [(e.tick, e.kind, e.a) for e in ev[:4]] == [
        (0, "note_on", 60), (10, "note_on", 62), (30, "note_off", 60), (30, "note_off", 62)]


def test_rescale():
    f = smf.SmfFile(0, 96, [[E(48, smf.NOTE_ON, 0, 60, 90)]])
    g = smf.rescale(f)
    assert g.ppq == 480 and g.tracks[0][0].tick == 240


def test_errors():
    with pytest.raises(smf.SmfError):
        parse_smf(b"nope")
    with pytest.raises(smf.SmfError):
        write_smf([[], []], 480, 0)
