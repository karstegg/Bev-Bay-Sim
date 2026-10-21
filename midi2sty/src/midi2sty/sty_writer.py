"""Write a model.Style as a Yamaha SFF1 style file (.sty) for the DGX-670.

Layout (modelled on 14 real SFF1 styles, see docs/analysis/style_anatomy.md and docs/SFF.md):
SMF type 0 (MThd + one MTrk), then a CASM chunk. Header order: time sig, tempo, `SFF1`
marker, 32-byte track name, 4 fixed Yamaha sysex, `SInt` marker, GM reset, per-channel
mixer setup. Sections follow in the order of ``style.sections``; the first starts one bar
after tick 0 and the track ends exactly at the end of the last section. CASM groups the
sections that share a Ctab/Cntt table set into CSEGs.

``style.sff_version`` is ignored: SFF2 needs Ctb2 tables which this writer does not
produce (real files never mix SFF2 with Ctab), so SFF1 is always written. Optional
chunks (OTSc one-touch settings, FNRc, ...) are not written.
"""
from __future__ import annotations

from . import model
from .smf import (CC, META, NOTE_OFF, NOTE_ON, PROGRAM, SYSEX, MidiEvent,
                  write_smf)

# Ctab lookup values
NTR_ROOT_TRANS, NTR_ROOT_FIXED, NTR_GUITAR, NTR_BYPASS = 0, 1, 2, 3
NTT_BYPASS, NTT_MELODY, NTT_CHORD, NTT_BASS = 0, 1, 2, 3
RTR_STOP, RTR_PITCH_SHIFT, RTR_PITCH_SHIFT_ROOT = 0, 1, 2
CHORD_ROOT_C, CHORD_TYPE_MAJ7 = 0, 2

# role -> (ntr, ntt, high_key, note_low, note_high, rtr, rhythm?)
# Modal values of the 14 real SFF1 files (style_anatomy.md section 5).
_ROLE_RULES = {
    "RHY1": (NTR_ROOT_FIXED, NTT_BYPASS, 0x06, 0x00, 0x7F, RTR_PITCH_SHIFT, True),
    "RHY2": (NTR_ROOT_FIXED, NTT_BYPASS, 0x06, 0x00, 0x7F, RTR_PITCH_SHIFT, True),
    "BASS": (NTR_ROOT_TRANS, NTT_BASS, 0x08, 0x1C, 0x7F, RTR_PITCH_SHIFT_ROOT, False),
    "CHD1": (NTR_ROOT_FIXED, NTT_CHORD, 0x07, 0x00, 0x7F, RTR_PITCH_SHIFT, False),
    "CHD2": (NTR_ROOT_FIXED, NTT_CHORD, 0x07, 0x00, 0x7F, RTR_PITCH_SHIFT, False),
    "PAD": (NTR_ROOT_FIXED, NTT_CHORD, 0x07, 0x00, 0x7F, RTR_PITCH_SHIFT, False),
    "PHR1": (NTR_ROOT_FIXED, NTT_CHORD, 0x07, 0x00, 0x7F, RTR_PITCH_SHIFT, False),
    "PHR2": (NTR_ROOT_FIXED, NTT_CHORD, 0x07, 0x00, 0x7F, RTR_PITCH_SHIFT, False),
}
_DEFAULT_PROGRAM = {"RHY1": 0, "RHY2": 0, "BASS": 33, "CHD1": 0, "CHD2": 25,
                    "PAD": 89, "PHR1": 56, "PHR2": 73}
_RHYTHM_ROLES = ("RHY1", "RHY2")

# Median mixer values of the real files: (volume, pan or None = not sent, reverb, chorus)
_MIX = {
    "RHY1": (67, None, 24, 0), "RHY2": (75, None, 23, 0), "BASS": (65, None, 0, 0),
    "CHD1": (55, 52, 27, 20), "CHD2": (55, 49, 31, 30), "PAD": (44, 76, 36, 23),
    "PHR1": (60, 72, 28, 28), "PHR2": (60, 53, 38, 22),
}

# CSEG grouping of real files: sections that share one table set.
_GROUPS = [
    ["Main A", "Main B", "Main C", "Main D", "Fill In AA", "Fill In BB", "Fill In CC",
     "Fill In DD", "Fill In BA", "Intro A", "Ending A"],
    ["Intro B", "Ending B"],
    ["Intro C", "Ending C"],
]

# The 4 fixed Yamaha sysex found before SInt in 27-28 of 28 real files.
_FIXED_SYSEX = [
    bytes([0x43, 0x76, 0x1A, 0x10] + [0x01] * 8 + [0xF7]),
    bytes([0x43, 0x73, 0x39, 0x11, 0x00, 0x46, 0x00, 0xF7]),
    bytes([0x43, 0x73, 0x01, 0x51, 0x05, 0x00, 0x01, 0x08] + [0x00] * 7 + [0xF7]),
    bytes([0x43, 0x73, 0x01, 0x51, 0x05, 0x00, 0x02, 0x08] + [0x00] * 7 + [0xF7]),
]
GM_RESET = bytes([0x7E, 0x7F, 0x09, 0x01, 0xF7])


def _meta(tick: int, mtype: int, data: bytes) -> MidiEvent:
    return MidiEvent(tick, META, meta_type=mtype, data=data)


def _marker(tick: int, text: str) -> MidiEvent:
    return _meta(tick, 0x06, text.encode("ascii"))


def _tempo(tick: int, bpm: float) -> MidiEvent:
    usec = max(1, min(0xFFFFFF, int(round(60_000_000 / bpm))))
    return _meta(tick, 0x51, usec.to_bytes(3, "big"))


def _bar_ticks(style: model.Style) -> int:
    num, den = style.time_sig
    return num * model.TICKS_PER_BEAT * 4 // den


def _setup_events(style: model.Style, name: str) -> list[MidiEvent]:
    num, den = style.time_sig
    ev = [_meta(0, 0x58, bytes([num, den.bit_length() - 1, 24, 8])),
          _tempo(0, style.tempo_bpm),
          _marker(0, "SFF1"),
          _meta(0, 0x03, name.encode("ascii", "replace")[:32].ljust(32, b"\0"))]
    ev += [MidiEvent(0, SYSEX, a=0xF0, data=s) for s in _FIXED_SYSEX]
    ev.append(_marker(0, "SInt"))
    ev.append(MidiEvent(0, SYSEX, a=0xF0, data=GM_RESET))
    programs: dict[str, int] = {}
    for sec in style.sections:
        for ch in sec.channels:
            if ch.program is not None:
                programs.setdefault(ch.role, ch.program)
    for role in reversed(list(model.STYLE_CHANNELS)):   # real files list ch16 down to ch9
        midi_ch = model.STYLE_CHANNELS[role]
        vol, pan, rev, cho = _MIX[role]
        rhythm = role in _RHYTHM_ROLES
        ev.append(MidiEvent(0, CC, midi_ch, 7, vol))
        if pan is not None:
            ev.append(MidiEvent(0, CC, midi_ch, 10, pan))
        ev.append(MidiEvent(0, CC, midi_ch, 91, rev))
        ev.append(MidiEvent(0, CC, midi_ch, 93, cho))
        ev.append(MidiEvent(0, CC, midi_ch, 94, 0))
        ev.append(MidiEvent(0, CC, midi_ch, 0, 127 if rhythm else 0))   # XG drum kit bank
        ev.append(MidiEvent(0, CC, midi_ch, 32, 0))
        prog = programs.get(role, _DEFAULT_PROGRAM[role]) & 0x7F
        ev.append(MidiEvent(0, PROGRAM, midi_ch, prog))
    return ev


def _section_events(sec: model.StyleSection, start: int, length: int) -> list[MidiEvent]:
    """Markers + notes of one section. Notes are clamped into [start, start+length]."""
    ev = [_marker(start, sec.name), _meta(start, 0x01, b"fn:" + sec.name.encode("ascii") + b"\0")]
    end_abs = start + length
    for ch in sec.channels:
        midi_ch = model.STYLE_CHANNELS[ch.role]
        # trim same-pitch overlaps so one note-off never cuts a later note of the same key
        by_pitch: dict[int, list[model.Note]] = {}
        for n in ch.notes:
            if n.start < 0 or n.start >= length:
                continue
            by_pitch.setdefault(min(127, max(0, n.pitch)), []).append(n)
        for pitch, notes in by_pitch.items():
            notes.sort(key=lambda n: n.start)
            for i, n in enumerate(notes):
                end = min(n.start + max(n.dur, 1), length)
                if i + 1 < len(notes):
                    end = min(end, notes[i + 1].start)
                if end <= n.start:
                    continue
                vel = min(127, max(1, n.vel))
                ev.append(MidiEvent(start + n.start, NOTE_ON, midi_ch, pitch, vel))
                ev.append(MidiEvent(min(start + end, end_abs), NOTE_OFF, midi_ch, pitch, 0))
    return ev


def _chunk(tag: bytes, body: bytes) -> bytes:
    return tag + len(body).to_bytes(4, "big") + body


def _ctab(role: str, bypass: bool) -> bytes:
    ntr, ntt, hk, lo, hi, rtr, rhythm = _ROLE_RULES[role]
    ch = model.STYLE_CHANNELS[role]
    if bypass and not rhythm:          # literal pitches: do not follow the chord
        ntr, ntt, rtr = NTR_ROOT_TRANS, NTT_BYPASS, RTR_PITCH_SHIFT
    b = bytearray(27)
    b[0] = ch
    b[1:9] = role.ljust(8).encode("ascii")
    b[9] = ch
    b[10] = 1                                  # editable
    b[11], b[12] = 0x0F, 0xFF                  # note mute: none muted
    b[13] = 0x07 if rhythm else 0x03
    b[14:18] = b"\xff\xff\xff\xff"
    b[18], b[19] = CHORD_ROOT_C, CHORD_TYPE_MAJ7
    b[20], b[21] = ntr, ntt
    b[22] = hk
    b[23], b[24] = lo, hi
    b[25] = rtr
    return _chunk(b"Ctab", bytes(b))


def _cntt(role: str, bypass: bool) -> bytes:
    ntt = _ROLE_RULES[role][1]
    if bypass and role not in _RHYTHM_ROLES:
        ntt = NTT_BYPASS
    # observed: bass parts are 0x81, everything else carries its NTT value
    byte = 0x81 if role == "BASS" else ntt
    return _chunk(b"Cntt", bytes([model.STYLE_CHANNELS[role], byte]))


def _casm_groups(style: model.Style) -> list[tuple[list[model.StyleSection], bool]]:
    """Split sections into CSEG groups: (sections, bypass_tables)."""
    layout_of = {n: i for i, g in enumerate(_GROUPS) for n in g}
    buckets: dict[tuple[int, bool], list[model.StyleSection]] = {}
    for sec in style.sections:
        key = (layout_of.get(sec.name, 0), bool(sec.bypass_chords))
        buckets.setdefault(key, []).append(sec)
    return [(secs, key[1]) for key, secs in sorted(buckets.items())]


def _casm(style: model.Style) -> bytes:
    body = b""
    for secs, bypass in _casm_groups(style):
        used = {ch.role for s in secs for ch in s.channels if ch.notes}
        roles = [r for r in model.STYLE_CHANNELS if r in used] or ["RHY2"]
        cseg = _chunk(b"Sdec", ",".join(s.name for s in secs).encode("ascii"))
        cseg += b"".join(_ctab(r, bypass) for r in roles)
        cseg += b"".join(_cntt(r, bypass) for r in roles)
        body += _chunk(b"CSEG", cseg)
    return _chunk(b"CASM", body)


_ORDER = {"off": 0, "meta": 1, "on": 2}


def write_sty(style: model.Style, name: str | None = None) -> bytes:
    """Serialise a Style to SFF1 .sty bytes (``style.sff_version`` is ignored, see module doc)."""
    if not style.sections:
        raise ValueError("style has no sections")
    names = [s.name for s in style.sections]
    if len(set(names)) != len(names):
        raise ValueError("duplicate section names")
    unknown = [n for n in names if n not in model.SECTIONS]
    if unknown:
        raise ValueError(f"unknown section names: {unknown}")
    bar = _bar_ticks(style)
    events = _setup_events(style, name if name is not None else style.name)
    timed: list[tuple[int, int, MidiEvent]] = []   # (tick, order, event) for the song body
    pos = bar                                      # real files leave one bar for SInt
    tempo_dirty = False
    for sec in style.sections:
        length = max(bar, -(-sec.length_ticks // bar) * bar)   # round up to whole bars
        sec_ev = _section_events(sec, pos, length)
        if tempo_dirty:                            # restore the base tempo after a ritardando
            sec_ev.append(_tempo(pos, style.tempo_bpm))
            tempo_dirty = False
        for t, bpm in sorted(sec.tempo_changes):
            if 0 <= t < length and bpm > 0:
                sec_ev.append(_tempo(pos + t, bpm))
                tempo_dirty = True
        for e in sec_ev:
            o = _ORDER["off"] if e.kind == NOTE_OFF else _ORDER["on"] if e.kind == NOTE_ON \
                else _ORDER["meta"]
            timed.append((e.tick, o, e))
        pos += length
    timed.sort(key=lambda x: (x[0], x[1]))   # stable: offs before ons at equal ticks
    events += [e for _, _, e in timed]
    events.append(MidiEvent(pos, META, meta_type=0x2F))  # track ends exactly at last section end
    smf = write_smf([events], model.TICKS_PER_BEAT, fmt=0)
    return smf + _casm(style)
