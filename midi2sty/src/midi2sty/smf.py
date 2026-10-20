"""Minimal Standard MIDI File reader/writer (type 0/1). Pure Python, no deps."""
from __future__ import annotations
from dataclasses import dataclass, field

from . import model

# Event kinds
NOTE_ON, NOTE_OFF, POLY_AT, CC, PROGRAM, CHAN_AT, PITCH_BEND = (
    "note_on", "note_off", "poly_at", "cc", "program", "chan_at", "pitch_bend")
META, SYSEX = "meta", "sysex"

_CHAN_KINDS = {0x80: NOTE_OFF, 0x90: NOTE_ON, 0xA0: POLY_AT, 0xB0: CC,
               0xC0: PROGRAM, 0xD0: CHAN_AT, 0xE0: PITCH_BEND}
_KIND_STATUS = {v: k for k, v in _CHAN_KINDS.items()}
_DATA_LEN = {0x80: 2, 0x90: 2, 0xA0: 2, 0xB0: 2, 0xC0: 1, 0xD0: 1, 0xE0: 2}


class SmfError(ValueError):
    pass


@dataclass
class MidiEvent:
    """tick is absolute. Channel events: channel/a/b (a=note|controller|program|lsb,
    b=velocity|value|msb; b=0 when unused). Meta: meta_type + data. Sysex: data
    (bytes after F0/F7) and a = 0xF0 or 0xF7. A note_on with velocity 0 is
    normalised to note_off on read."""
    tick: int
    kind: str
    channel: int = 0
    a: int = 0
    b: int = 0
    meta_type: int = -1
    data: bytes = b""


@dataclass
class SmfFile:
    fmt: int
    ppq: int
    tracks: list[list[MidiEvent]] = field(default_factory=list)


def _read_vlq(d: bytes, i: int) -> tuple[int, int]:
    v = 0
    for _ in range(4):
        if i >= len(d):
            raise SmfError("truncated variable-length quantity")
        c = d[i]
        i += 1
        v = (v << 7) | (c & 0x7F)
        if not c & 0x80:
            return v, i
    raise SmfError("variable-length quantity too long")


def _vlq(v: int) -> bytes:
    if v < 0:
        raise SmfError("negative value")
    out = [v & 0x7F]
    v >>= 7
    while v:
        out.append((v & 0x7F) | 0x80)
        v >>= 7
    return bytes(reversed(out))


def _parse_track(d: bytes) -> list[MidiEvent]:
    ev: list[MidiEvent] = []
    i, tick, running = 0, 0, 0
    n = len(d)
    while i < n:
        delta, i = _read_vlq(d, i)
        tick += delta
        if i >= n:
            break
        st = d[i]
        if st == 0xFF:
            if i + 1 >= n:
                break
            mt = d[i + 1]
            ln, i = _read_vlq(d, i + 2)
            ev.append(MidiEvent(tick, META, meta_type=mt, data=bytes(d[i:i + ln])))
            i += ln
            running = 0
            if mt == 0x2F:
                break
        elif st in (0xF0, 0xF7):
            ln, i = _read_vlq(d, i + 1)
            ev.append(MidiEvent(tick, SYSEX, a=st, data=bytes(d[i:i + ln])))
            i += ln
            running = 0
        else:
            if st & 0x80:
                running = st
                i += 1
            elif not running:
                raise SmfError("data byte without running status")
            hi, ch = running & 0xF0, running & 0x0F
            if hi == 0xF0:
                raise SmfError("unsupported system message in track")
            ln = _DATA_LEN[hi]
            if i + ln > n:
                raise SmfError("truncated channel event")
            a = d[i]
            b = d[i + 1] if ln == 2 else 0
            i += ln
            kind = _CHAN_KINDS[hi]
            if kind == NOTE_ON and b == 0:
                kind = NOTE_OFF
            ev.append(MidiEvent(tick, kind, ch, a, b))
    return ev


def parse_smf(data: bytes) -> SmfFile:
    data = bytes(data)
    if data[:4] != b"MThd" or len(data) < 14:
        raise SmfError("not a Standard MIDI File")
    hlen = int.from_bytes(data[4:8], "big")
    fmt = int.from_bytes(data[8:10], "big")
    ntrk = int.from_bytes(data[10:12], "big")
    div = int.from_bytes(data[12:14], "big")
    if fmt not in (0, 1):
        raise SmfError(f"unsupported SMF format {fmt}")
    if div & 0x8000:
        raise SmfError("SMPTE time division not supported")
    if div == 0:
        raise SmfError("invalid division")
    i = 8 + max(hlen, 6)
    tracks = []
    while i + 8 <= len(data) and len(tracks) < ntrk:
        cid = data[i:i + 4]
        ln = int.from_bytes(data[i + 4:i + 8], "big")
        body = data[i + 8:i + 8 + ln]  # tolerate truncated final chunk
        i += 8 + ln
        if cid == b"MTrk":
            tracks.append(_parse_track(body))
    return SmfFile(fmt, div, tracks)


def _encode_track(events: list[MidiEvent]) -> bytes:
    explicit_end = max((e.tick for e in events if e.kind == META and e.meta_type == 0x2F),
                       default=0)  # an EOT event in the input only sets where the track ends
    evs = [e for e in events if not (e.kind == META and e.meta_type == 0x2F)]
    evs = sorted(evs, key=lambda e: e.tick)  # stable
    out = bytearray()
    last = 0
    for e in evs:
        out += _vlq(e.tick - last)
        last = e.tick
        if e.kind == META:
            out += bytes([0xFF, e.meta_type]) + _vlq(len(e.data)) + e.data
        elif e.kind == SYSEX:
            out += bytes([e.a or 0xF0]) + _vlq(len(e.data)) + e.data
        else:
            st = _KIND_STATUS[e.kind] | (e.channel & 0x0F)
            out.append(st)
            out.append(e.a & 0x7F)
            if _DATA_LEN[st & 0xF0] == 2:
                out.append(e.b & 0x7F)
    end = max(max((e.tick for e in evs), default=0), explicit_end)
    out += _vlq(end - last) + b"\xFF\x2F\x00"
    return bytes(out)


def write_smf(tracks_events: list[list[MidiEvent]], ppq: int = model.TICKS_PER_BEAT,
              fmt: int = 1) -> bytes:
    """Serialise tracks of MidiEvent (absolute ticks) to SMF bytes. An end-of-track
    meta is always appended; type 0 requires exactly one track."""
    if fmt not in (0, 1):
        raise SmfError("fmt must be 0 or 1")
    if fmt == 0 and len(tracks_events) != 1:
        raise SmfError("type 0 file needs exactly one track")
    out = bytearray(b"MThd" + (6).to_bytes(4, "big") + fmt.to_bytes(2, "big")
                    + len(tracks_events).to_bytes(2, "big") + ppq.to_bytes(2, "big"))
    for t in tracks_events:
        body = _encode_track(t)
        out += b"MTrk" + len(body).to_bytes(4, "big") + body
    return bytes(out)


def rescale(smf: SmfFile, target_ppq: int = model.TICKS_PER_BEAT) -> SmfFile:
    """Return a copy with all ticks rescaled to target_ppq (rounded to nearest)."""
    src = smf.ppq

    def conv(t: int) -> int:
        return (t * target_ppq * 2 + src) // (src * 2)

    tracks = [[MidiEvent(conv(e.tick), e.kind, e.channel, e.a, e.b, e.meta_type, e.data)
               for e in t] for t in smf.tracks]
    return SmfFile(smf.fmt, target_ppq, tracks)
