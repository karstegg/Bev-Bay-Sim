"""Write a model.Style as a Yamaha SFF2 / SFF GE style file (.sty).

Layout: SMF type 0 (MThd + one MTrk) followed by a CASM chunk. Section markers
delimit sections in the track; CASM holds one CSEG per section with a Sdec
(section names) and a Ctab + Cntt per style channel. See docs/SFF.md for which
details are verified against reverse-engineered sources and which are assumed.
"""
from __future__ import annotations

from . import model
from .smf import (CC, META, NOTE_OFF, NOTE_ON, PROGRAM, SYSEX, MidiEvent,
                  write_smf)

# Ctab lookup values (from the open-source Yamaha-Style-Studio sff2Writer)
NTR_ROOT_TRANS, NTR_ROOT_FIXED, NTR_GUITAR, NTR_BYPASS = 0, 1, 2, 3
NTT_BYPASS, NTT_MELODY, NTT_CHORD, NTT_BASS = 0, 1, 2, 3
RTR_STOP, RTR_PITCH_SHIFT, RTR_PITCH_SHIFT_ROOT = 0, 1, 2
CHORD_ROOT_C, CHORD_TYPE_MAJ7 = 0, 2

# role -> (ntr, ntt, high_key, note_low, note_high, rtr, rhythm?)
# Values copied from real Yamaha-format tables (Audio Phraser demo): rhythm = Root Fixed/Bypass,
# bass = Root Trans/Bass/RTR pitch-shift-to-root, chord parts = Root Fixed/Chord.
_ROLE_RULES = {
    "RHY1": (NTR_ROOT_FIXED, NTT_BYPASS, 0x06, 0x00, 0x7F, RTR_PITCH_SHIFT, True),
    "RHY2": (NTR_ROOT_FIXED, NTT_BYPASS, 0x06, 0x00, 0x7F, RTR_PITCH_SHIFT, True),
    "BASS": (NTR_ROOT_TRANS, NTT_BASS, 0x08, 0x1C, 0x7F, RTR_PITCH_SHIFT_ROOT, False),
    "CHD1": (NTR_ROOT_FIXED, NTT_CHORD, 0x07, 0x00, 0x7F, RTR_PITCH_SHIFT, False),
    "CHD2": (NTR_ROOT_FIXED, NTT_CHORD, 0x07, 0x00, 0x7F, RTR_PITCH_SHIFT, False),
    "PAD": (NTR_ROOT_FIXED, NTT_CHORD, 0x07, 0x00, 0x7F, RTR_PITCH_SHIFT, False),
    "PHR1": (NTR_ROOT_TRANS, NTT_MELODY, 0x07, 0x00, 0x7F, RTR_PITCH_SHIFT, False),
    "PHR2": (NTR_ROOT_TRANS, NTT_MELODY, 0x07, 0x00, 0x7F, RTR_PITCH_SHIFT, False),
}
_DEFAULT_PROGRAM = {"RHY1": 0, "RHY2": 0, "BASS": 33, "CHD1": 0, "CHD2": 25,
                    "PAD": 89, "PHR1": 56, "PHR2": 73}
_RHYTHM_ROLES = ("RHY1", "RHY2")

GM_RESET = bytes([0x7E, 0x7F, 0x09, 0x01, 0xF7])
XG_ON = bytes([0x43, 0x10, 0x4C, 0x00, 0x00, 0x7E, 0x00, 0xF7])


def _meta(tick: int, mtype: int, data: bytes) -> MidiEvent:
    return MidiEvent(tick, META, meta_type=mtype, data=data)


def _marker(tick: int, text: str) -> MidiEvent:
    return _meta(tick, 0x06, text.encode("ascii"))


def _setup_events(style: model.Style, name: str) -> list[MidiEvent]:
    num, den = style.time_sig
    usec = int(round(60_000_000 / style.tempo_bpm))
    ev = [_meta(0, 0x58, bytes([num, den.bit_length() - 1, 24, 8])),
          _meta(0, 0x51, usec.to_bytes(3, "big")),
          _marker(0, "SFF2"),
          _meta(0, 0x03, name.encode("ascii", "replace")[:32].ljust(32, b"\0")),
          _marker(0, "SInt")]
    ev.append(MidiEvent(0, SYSEX, a=0xF0, data=GM_RESET))
    ev.append(MidiEvent(0, SYSEX, a=0xF0, data=XG_ON))
    programs = {}
    for sec in style.sections:
        for ch in sec.channels:
            if ch.program is not None:
                programs.setdefault(ch.role, ch.program)
    for role, midi_ch in model.STYLE_CHANNELS.items():
        rhythm = role in _RHYTHM_ROLES
        if rhythm:  # XG drum kit bank
            ev.append(MidiEvent(0, CC, midi_ch, 0, 127))
            ev.append(MidiEvent(0, CC, midi_ch, 32, 0))
        else:
            ev.append(MidiEvent(0, CC, midi_ch, 0, 0))
            ev.append(MidiEvent(0, CC, midi_ch, 32, 0))
        prog = 0 if rhythm else programs.get(role, _DEFAULT_PROGRAM[role]) & 0x7F
        ev.append(MidiEvent(0, PROGRAM, midi_ch, prog))
        ev.append(MidiEvent(0, CC, midi_ch, 7, 100))
        ev.append(MidiEvent(0, CC, midi_ch, 10, 64))
    return ev


def _section_events(sec: model.StyleSection, start: int) -> list[MidiEvent]:
    ev = [_marker(start, sec.name)]
    for ch in sec.channels:
        midi_ch = model.STYLE_CHANNELS[ch.role]
        for n in ch.notes:
            if n.start >= sec.length_ticks:
                continue
            end = min(n.start + max(n.dur, 1), sec.length_ticks)
            ev.append(MidiEvent(start + n.start, NOTE_ON, midi_ch, n.pitch, n.vel))
            ev.append(MidiEvent(start + end, NOTE_OFF, midi_ch, n.pitch, 0))
    return ev


def _chunk(tag: bytes, body: bytes) -> bytes:
    return tag + len(body).to_bytes(4, "big") + body


def _ctab(role: str) -> bytes:
    ntr, ntt, hk, lo, hi, rtr, rhythm = _ROLE_RULES[role]
    ch = model.STYLE_CHANNELS[role]
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


def _cntt(role: str) -> bytes:
    ntt = _ROLE_RULES[role][1]
    # observed: bass parts are 0x81, everything else carries its NTT value
    return _chunk(b"Cntt", bytes([model.STYLE_CHANNELS[role], 0x81 if ntt == NTT_BASS else ntt]))


def _casm(style: model.Style) -> bytes:
    body = b""
    for sec in style.sections:
        roles = [r for r in model.STYLE_CHANNELS]
        cseg = _chunk(b"Sdec", sec.name.encode("ascii"))
        cseg += b"".join(_ctab(r) for r in roles) + b"".join(_cntt(r) for r in roles)
        body += _chunk(b"CSEG", cseg)
    return _chunk(b"CASM", body)


def write_sty(style: model.Style, name: str = "midi2sty") -> bytes:
    """Serialise a Style to .sty bytes."""
    if not style.sections:
        raise ValueError("style has no sections")
    events = _setup_events(style, name)
    num, den = style.time_sig
    pos = num * model.TICKS_PER_BEAT * 4 // den   # real files leave one bar for SInt
    for sec in style.sections:
        events += _section_events(sec, pos)
        pos += sec.length_ticks
    events.append(MidiEvent(pos, META, meta_type=0x2F))  # track ends exactly at last section end
    smf = write_smf([events], model.TICKS_PER_BEAT, fmt=0)
    return smf + _casm(style)
