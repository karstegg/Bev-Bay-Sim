"""Structural checks for a generated SFF1 .sty. Returns a list of problems (empty = OK)."""
from __future__ import annotations

from . import model
from .smf import META, NOTE_OFF, NOTE_ON, SYSEX, SmfError, parse_smf

_CASM_TAGS = (b"CASM", b"OTSc", b"FNRc", b"ASnc", b"Cmbi")


def _split_chunks(data: bytes, pos: int) -> list[tuple[bytes, bytes]]:
    out = []
    while pos + 8 <= len(data):
        tag, size = data[pos:pos + 4], int.from_bytes(data[pos + 4:pos + 8], "big")
        out.append((tag, data[pos + 8:pos + 8 + size]))
        pos += 8 + size
    return out


def _casm_body(data: bytes) -> bytes | None:
    pos = 14 + 8 + int.from_bytes(data[18:22], "big")
    if data[pos:pos + 4] not in _CASM_TAGS:     # header length can be off in odd files
        pos = data.find(b"CASM", 22)
        if pos < 0:
            return None
    for tag, body in _split_chunks(data, pos):
        if tag == b"CASM":
            return body
    return None


def validate_sty(data: bytes, expect_ppq: int | None = None,
                 require_cntt: bool = True) -> list[str]:
    problems: list[str] = []
    try:
        smf = parse_smf(data)
    except (SmfError, ValueError, IndexError) as e:
        return [f"not a parseable SMF: {e}"]
    if smf.fmt != 0 or len(smf.tracks) != 1:
        problems.append("expected SMF type 0 with a single track")
    if not smf.tracks:
        return problems
    if expect_ppq is not None and smf.ppq != expect_ppq:
        problems.append(f"ppq is {smf.ppq}, expected {expect_ppq}")

    events = smf.tracks[0]
    # ---- header: time sig, tempo, SFF1, 32-byte name, 4 fixed sysex, SInt, GM reset
    timesig = next((e for e in events if e.kind == META and e.meta_type == 0x58), None)
    num, den = (timesig.data[0], 1 << timesig.data[1]) if timesig and len(timesig.data) >= 2 else (4, 4)
    if timesig is None:
        problems.append("missing time signature meta")
    if not any(e.kind == META and e.meta_type == 0x51 for e in events):
        problems.append("missing tempo meta")
    markers = [(e.tick, e.data.decode("ascii", "replace")) for e in events
               if e.kind == META and e.meta_type == 0x06]
    mnames = [m for _, m in markers]
    if "SFF1" not in mnames:
        problems.append("missing SFF1 marker")
    if "SFF2" in mnames:
        problems.append("SFF2 marker present (writer produces SFF1 only)")
    sint = next((t for t, m in markers if m == "SInt"), None)
    if sint is None:
        problems.append("missing SInt marker")
    name = next((e for e in events if e.kind == META and e.meta_type == 0x03), None)
    if name is None or len(name.data) != 32:
        problems.append("track name meta must be exactly 32 bytes")
    sysex = [(e.tick, e.data) for e in events if e.kind == SYSEX]
    pre = [d for t, d in sysex if sint is None or t <= sint]
    for needle in (bytes([0x43, 0x76, 0x1A]), bytes([0x43, 0x73, 0x39]), bytes([0x43, 0x73, 0x01, 0x51])):
        if not any(d.startswith(needle) for d in pre):
            problems.append(f"missing Yamaha setup sysex {needle.hex()}")
    if not any(d.startswith(bytes([0x7E, 0x7F, 0x09, 0x01])) for _, d in sysex):
        problems.append("missing GM reset sysex")

    # ---- sections
    sections = [m for m in markers if m[1] in model.SECTIONS]
    if not sections:
        problems.append("no section markers")
        return problems
    eot = next((e.tick for e in reversed(events) if e.kind == META and e.meta_type == 0x2F), None)
    if eot is None:
        problems.append("missing end-of-track")
        eot = max(e.tick for e in events)
    bar = num * smf.ppq * 4 // den
    secnames = [m for _, m in sections]
    if len(set(secnames)) != len(secnames):
        problems.append("duplicate section markers")
    canon = [n for n in model.CANONICAL_ORDER if n in secnames]
    if [n for n in secnames if n in canon] != canon:
        problems.append("sections not in canonical order: " + ", ".join(secnames))
    if sections[0][0] != (sint or 0) + bar:
        problems.append(f"first section starts at tick {sections[0][0]}, expected one bar after SInt ({(sint or 0) + bar})")
    spans: list[tuple[str, int, int]] = []
    for i, (t, n) in enumerate(sections):
        end = sections[i + 1][0] if i + 1 < len(sections) else eot
        spans.append((n, t, end))
        if end <= t:
            problems.append(f"section {n!r} has no length")
        elif (end - t) % bar:
            problems.append(f"section {n!r} is {(end - t) / bar:.2f} bars (not whole bars)")
    if sections[-1][0] >= eot:
        problems.append("end-of-track is not after the last section start")
    # fn: texts
    texts = {(e.tick, e.data) for e in events if e.kind == META and e.meta_type == 0x01}
    for t, n in sections:
        if (t, b"fn:" + n.encode("ascii") + b"\0") not in texts:
            problems.append(f"section {n!r}: missing text meta 'fn:{n}\\0' at its start")

    # ---- tempo restored at every section start
    tempos = sorted((e.tick, e.data) for e in events if e.kind == META and e.meta_type == 0x51)
    if tempos:
        base = tempos[0][1]
        for t, n in sections:
            cur = [d for tt, d in tempos if tt <= t][-1]
            if cur != base:
                problems.append(f"section {n!r} starts with a tempo other than the base tempo")

    # ---- notes
    ons = [e for e in events if e.kind == NOTE_ON]
    bad_ch = {e.channel for e in ons} - set(model.STYLE_CHANNELS.values())
    if bad_ch:
        problems.append(f"notes outside style channels 9-16: {sorted(c + 1 for c in bad_ch)}")
    first = sections[0][0]
    open_notes: dict[tuple[int, int], list[int]] = {}
    sec_of = lambda tick: next((s for s in spans if s[1] <= tick < s[2]), None)  # noqa: E731
    overhang = outside = orphans = misordered = 0
    for e in events:
        key = (e.channel, e.a)
        if e.kind == NOTE_ON:
            if e.tick < first or e.tick >= eot:
                outside += 1
            open_notes.setdefault(key, []).append(e.tick)
        elif e.kind == NOTE_OFF:
            stack = open_notes.get(key)
            if not stack:
                orphans += 1
                continue
            on_tick = stack.pop(0)
            sp = sec_of(on_tick)
            if sp and e.tick > sp[2]:
                overhang += 1
    # an equal-tick note-on that precedes a note-off of the same key
    seen_on: dict[tuple[int, int, int], bool] = {}
    for e in events:
        k = (e.tick, e.channel, e.a)
        if e.kind == NOTE_ON:
            seen_on[k] = True
        elif e.kind == NOTE_OFF and seen_on.get(k):
            misordered += 1
    if outside:
        problems.append(f"{outside} note-on(s) outside the section area")
    if overhang:
        problems.append(f"{overhang} note(s) overhang their section end")
    if orphans:
        problems.append(f"{orphans} note-off(s) without a note-on")
    unclosed = sum(len(v) for v in open_notes.values())
    if unclosed:
        problems.append(f"{unclosed} note(s) never switched off")
    if misordered:
        problems.append(f"{misordered} note-on(s) sorted before a note-off of the same key at the same tick")

    # ---- CASM
    casm = _casm_body(data)
    if casm is None:
        problems.append("missing CASM chunk")
        return problems
    sdec_all: list[str] = []
    cseg_channels: list[tuple[list[str], set[int]]] = []
    for tag, c in _split_chunks(casm, 0):
        if tag != b"CSEG":
            continue
        sub = _split_chunks(c, 0)
        names = []
        for t, b in sub:
            if t == b"Sdec":
                names += [x for x in b.decode("ascii", "replace").split(",") if x]
        sdec_all += names
        ctabs = [b for t, b in sub if t == b"Ctab"]
        cntts = [b for t, b in sub if t == b"Cntt"]
        if not names:
            problems.append("CSEG without Sdec")
        if any(t == b"Ctb2" for t, _ in sub):
            problems.append("CSEG contains Ctb2 (SFF2) tables in an SFF1 file")
        if not ctabs or (cntts or require_cntt) and len(ctabs) != len(cntts):
            problems.append(f"CSEG {names}: {len(ctabs)} Ctab but {len(cntts)} Cntt chunks")
        if any(len(b) not in (27, 31) for b in ctabs):
            problems.append(f"CSEG {names}: Ctab length is not 27")
        tab_dest = {b[9] for b in ctabs if len(b) >= 10}
        tab_src = {b[0] for b in ctabs if b}
        cntt_src = {b[0] for b in cntts if b}
        if cntts and tab_src != cntt_src:
            problems.append(f"CSEG {names}: Ctab and Cntt source channels differ")
        for b in ctabs:
            if len(b) >= 10 and not 8 <= b[9] <= 15:
                problems.append(f"CSEG {names}: Ctab destination channel {b[9] + 1} outside 9-16")
        cseg_channels.append((names, tab_dest))
    dup = {n for n in sdec_all if sdec_all.count(n) > 1}
    if dup:
        problems.append(f"sections listed in more than one Sdec: {sorted(dup)}")
    unknown = set(sdec_all) - set(model.SECTIONS)
    if unknown:
        problems.append(f"Sdec names unknown sections: {sorted(unknown)}")
    missing = set(secnames) - set(sdec_all)
    if missing:
        problems.append(f"sections without CASM entry: {sorted(missing)}")
    extra = set(sdec_all) - set(secnames)
    if extra:
        problems.append(f"Sdec lists sections not in the track: {sorted(extra)}")
    # every channel that plays in a section needs a table in its CSEG
    dest_of = {n: d for names, d in cseg_channels for n in names}
    for n, t, end in spans:
        played = {e.channel for e in ons if t <= e.tick < end}
        lacking = played - dest_of.get(n, set())
        if lacking and n in dest_of:
            problems.append(f"section {n!r}: channel(s) {sorted(c + 1 for c in lacking)} play but have no Ctab")
    return problems
