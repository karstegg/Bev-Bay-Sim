"""Structural checks for a generated .sty. Returns a list of problems (empty = OK)."""
from __future__ import annotations

from . import model
from .smf import META, NOTE_ON, SmfError, parse_smf


def _split_chunks(data: bytes, pos: int) -> list[tuple[bytes, bytes]]:
    out = []
    while pos + 8 <= len(data):
        tag, size = data[pos:pos + 4], int.from_bytes(data[pos + 4:pos + 8], "big")
        out.append((tag, data[pos + 8:pos + 8 + size]))
        pos += 8 + size
    return out


def validate_sty(data: bytes) -> list[str]:
    problems: list[str] = []
    try:
        smf = parse_smf(data)
    except (SmfError, ValueError, IndexError) as e:
        return [f"not a parseable SMF: {e}"]
    if smf.fmt != 0 or len(smf.tracks) != 1:
        problems.append("expected SMF type 0 with a single track")
    if smf.ppq != model.TICKS_PER_BEAT:
        problems.append(f"ppq is {smf.ppq}, expected {model.TICKS_PER_BEAT}")

    mtrk_end = 14 + 8 + int.from_bytes(data[18:22], "big")
    chunks = _split_chunks(data, mtrk_end)
    casm = [b for t, b in chunks if t == b"CASM"]
    if not casm:
        problems.append("missing CASM chunk")

    events = smf.tracks[0] if smf.tracks else []
    markers = [(e.tick, e.data.decode("ascii", "replace"))
               for e in events if e.kind == META and e.meta_type == 0x06]
    names = [m for _, m in markers]
    if "SInt" not in names:
        problems.append("missing SInt marker")
    sections = [m for m in markers if m[1] in model.SECTIONS]
    if not sections:
        problems.append("no section markers")
    bad_ch = {e.channel for e in events if e.kind == NOTE_ON} - set(model.STYLE_CHANNELS.values())
    if bad_ch:
        problems.append(f"notes outside style channels 9-16: {sorted(c + 1 for c in bad_ch)}")

    if casm:
        csegs = [b for t, b in _split_chunks(casm[0], 0) if t == b"CSEG"]
        sdec = []
        for c in csegs:
            sub = _split_chunks(c, 0)
            sdec += [b.decode("ascii", "replace") for t, b in sub if t == b"Sdec"]
            n_ctab = sum(t == b"Ctab" for t, _ in sub)
            n_cntt = sum(t == b"Cntt" for t, _ in sub)
            if n_ctab == 0 or n_ctab != n_cntt:
                problems.append(f"CSEG has {n_ctab} Ctab but {n_cntt} Cntt chunks")
            if any(t == b"Ctab" and len(b) != 27 for t, b in sub):
                problems.append("Ctab length is not 27")
        missing = {m for _, m in sections} - set(sdec)
        if missing:
            problems.append(f"sections without CASM entry: {sorted(missing)}")
    return problems
