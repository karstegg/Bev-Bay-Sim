import sys
import types

from midi2sty import cli
from midi2sty.recipe import Recipe
from midi2sty.smf import META, NOTE_OFF, NOTE_ON, PROGRAM, MidiEvent, write_smf
from midi2sty.validate import validate_sty

Q = 480


def _midi(bars=16) -> bytes:
    ev = [MidiEvent(0, META, meta_type=0x51, data=(500000).to_bytes(3, "big")),
          MidiEvent(0, META, meta_type=0x03, data=b"Song"),
          MidiEvent(0, META, meta_type=0x58, data=bytes([4, 2, 24, 8]))]
    drums, bass, chords, lead = [], [MidiEvent(0, PROGRAM, 1, 33)], [MidiEvent(0, PROGRAM, 2, 0)], \
        [MidiEvent(0, META, meta_type=0x03, data=b"Melody"), MidiEvent(0, PROGRAM, 3, 65)]
    for b in range(bars):
        t = b * 4 * Q
        for beat in range(4):
            k = 36 if beat % 2 == 0 else 38
            drums += [MidiEvent(t + beat * Q, NOTE_ON, 9, k, 100), MidiEvent(t + beat * Q + 100, NOTE_OFF, 9, k)]
            r = 40 + (b // 4) * 2
            bass += [MidiEvent(t + beat * Q, NOTE_ON, 1, r, 90), MidiEvent(t + beat * Q + Q // 2, NOTE_OFF, 1, r)]
            p = 79 + beat
            lead += [MidiEvent(t + beat * Q, NOTE_ON, 3, p, 90), MidiEvent(t + beat * Q + Q // 2, NOTE_OFF, 3, p)]
        for p in (60, 64, 67):
            chords += [MidiEvent(t, NOTE_ON, 2, p, 70), MidiEvent(t + 4 * Q, NOTE_OFF, 2, p)]
    return write_smf([ev, drums, bass, chords, lead], Q, fmt=1)


def _src(tmp_path):
    p = tmp_path / "in.mid"
    p.write_bytes(_midi())
    return p


def test_convert_default_output_and_validates(tmp_path, capsys):
    src = _src(tmp_path)
    assert cli.main([str(src)]) == 0
    out = tmp_path / "in.sty"
    assert out.exists() and validate_sty(out.read_bytes()) == []
    assert "wrote" in capsys.readouterr().out


def test_list_tracks_prints_and_writes_nothing(tmp_path, capsys):
    src = _src(tmp_path)
    assert cli.main([str(src), "--list-tracks"]) == 0
    txt = capsys.readouterr().out
    assert "exclude" in txt and "BASS" in txt and "RHY2" in txt and "Main A" in txt
    assert not (tmp_path / "in.sty").exists()


def test_write_recipe_edit_and_reuse(tmp_path):
    src, rj = _src(tmp_path), tmp_path / "r.json"
    assert cli.main([str(src), "-o", str(tmp_path / "a.sty"), "--write-recipe", str(rj)]) == 0
    r = Recipe.from_json(rj.read_text())
    assert r.validate() == [] and any(t.role == "exclude" for t in r.tracks)
    r.tempo_bpm = 90
    for t in r.tracks:
        if t.role == "exclude":
            t.role = "PHR1"
    rj.write_text(r.to_json())
    assert cli.main([str(src), "-o", str(tmp_path / "b.sty"), "--recipe", str(rj)]) == 0
    assert (tmp_path / "b.sty").read_bytes() != (tmp_path / "a.sty").read_bytes()
    assert validate_sty((tmp_path / "b.sty").read_bytes()) == []


def test_errors_return_nonzero(tmp_path, capsys):
    assert cli.main([str(tmp_path / "missing.mid")]) == 2
    bad = tmp_path / "bad.mid"
    bad.write_bytes(b"nope")
    assert cli.main([str(bad)]) == 2
    src = _src(tmp_path)
    rj = tmp_path / "r.json"
    rj.write_text('{"tracks": [{"index": 0, "role": "XYZ"}]}')
    assert cli.main([str(src), "--recipe", str(rj)]) == 2
    assert "error" in capsys.readouterr().err


def test_ui_dispatch(monkeypatch):
    seen = {}
    fake = types.ModuleType("midi2sty.ui")
    fake.main = lambda argv: seen.setdefault("argv", argv) and 0
    monkeypatch.setitem(sys.modules, "midi2sty.ui", fake)
    assert cli.main(["ui", "song.mid", "--port", "1"]) == 0
    assert seen["argv"] == ["song.mid", "--port", "1"]


def test_ui_missing(monkeypatch, capsys):
    monkeypatch.setitem(sys.modules, "midi2sty.ui", None)   # makes the import raise ImportError
    assert cli.main(["ui"]) == 2
    assert "ui" in capsys.readouterr().err
