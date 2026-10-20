from midi2sty import analyze
from midi2sty.smf import MidiEvent as E, write_smf
import midi2sty.smf as smf

PPQ = 96


def note(t, d, ch, p, v=90):
    return [E(t, smf.NOTE_ON, ch, p, v), E(t + d, smf.NOTE_OFF, ch, p, 0)]


def build():
    cond = [E(0, smf.META, meta_type=0x03, data=b"Conductor"),
            E(0, smf.META, meta_type=0x51, data=(400000).to_bytes(3, "big")),
            E(0, smf.META, meta_type=0x58, data=bytes([3, 2, 24, 8])),
            E(0, smf.META, meta_type=0x51, data=(1000000).to_bytes(3, "big"))]
    bass = [E(0, smf.META, meta_type=0x03, data=b"Bass"), E(0, smf.PROGRAM, 1, 33)]
    # C major scale-ish / C E G
    for i, p in enumerate([36, 40, 43, 36, 38, 41, 45, 47]):
        bass += note(i * 96, 90, 1, p)
    drums = [E(0, smf.META, meta_type=0x03, data=b"Drums")] + note(0, 48, 9, 36) + note(96, 48, 9, 38)
    return write_smf([cond, bass, drums], PPQ, 1)


def test_load_song():
    s = analyze.load_song(build())
    assert abs(s.tempo_bpm - 150.0) < 1e-6
    assert s.time_sig == (3, 4)
    assert [t.name for t in s.tracks] == ["Bass", "Drums"]
    bass, drums = s.tracks
    assert bass.program == 33 and not bass.is_drums and bass.channel == 1
    assert drums.is_drums and drums.program is None
    assert bass.notes[1].start == 480 and bass.notes[0].dur == 450
    assert s.length_ticks == 7 * 480 + 450
    assert (s.key_root, s.key_minor) == (0, False)


def test_path_and_unterminated(tmp_path):
    tr = [E(0, smf.NOTE_ON, 0, 69, 80), E(96, smf.META, meta_type=0x01, data=b"x")]
    p = tmp_path / "a.mid"
    p.write_bytes(write_smf([tr], 96, 0))
    s = analyze.load_song(p)
    assert s.tracks[0].notes[0].dur == 480 and s.tracks[0].name == "Channel 1"


def test_key_minor():
    w = [0.0] * 12
    for pc, x in ((9, 5), (0, 3), (4, 4), (2, 1), (5, 1), (7, 1)):
        w[pc] = x
    assert analyze.guess_key(w) == (9, True)
    assert analyze.guess_key([0.0] * 12) == (0, False)
