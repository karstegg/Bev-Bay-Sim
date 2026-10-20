from midi2sty.analyze import load_song
from midi2sty.cli import main
from midi2sty.smf import CC, META, NOTE_OFF, NOTE_ON, PROGRAM, MidiEvent, write_smf
from midi2sty.validate import validate_sty

Q = 480


def _song_bytes(bars=16):
    ev = [MidiEvent(0, META, meta_type=0x51, data=(500000).to_bytes(3, "big")),
          MidiEvent(0, META, meta_type=0x58, data=bytes([4, 2, 24, 8]))]
    drums, bass, chords = [], [MidiEvent(0, PROGRAM, 1, 33)], [MidiEvent(0, PROGRAM, 2, 0)]
    for b in range(bars):
        t = b * 4 * Q
        for beat in range(4):
            drums += [MidiEvent(t + beat * Q, NOTE_ON, 9, 36 if beat % 2 == 0 else 38, 100),
                      MidiEvent(t + beat * Q + 100, NOTE_OFF, 9, 36 if beat % 2 == 0 else 38)]
            bass += [MidiEvent(t + beat * Q, NOTE_ON, 1, 40 + (b // 4) * 2, 90),
                     MidiEvent(t + beat * Q + Q // 2, NOTE_OFF, 1, 40 + (b // 4) * 2)]
        for p in (60, 64, 67):
            chords += [MidiEvent(t, NOTE_ON, 2, p, 70), MidiEvent(t + 4 * Q, NOTE_OFF, 2, p)]
    return write_smf([ev, drums, bass, chords], Q, fmt=1)


def test_cli_end_to_end(tmp_path):
    src, dst = tmp_path / "in.mid", tmp_path / "out.sty"
    src.write_bytes(_song_bytes())
    assert load_song(src.read_bytes()).tracks
    assert main([str(src), "-o", str(dst)]) == 0
    assert validate_sty(dst.read_bytes()) == []
