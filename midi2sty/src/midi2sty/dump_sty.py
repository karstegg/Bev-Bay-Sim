"""Dump the structure of a real .sty/.aus/.prs file (markers, setup, CASM tables, trailing chunks).

Use it on styles from the keyboard to compare against what sty_writer produces:
    python -m midi2sty.dump_sty some_style.sty
"""
from __future__ import annotations

import sys

from .smf import META, NOTE_ON, parse_smf


def _chunks(d: bytes, pos: int, end: int):
    while pos + 8 <= end:
        n = int.from_bytes(d[pos + 4:pos + 8], "big")
        yield d[pos:pos + 4], d[pos + 8:pos + 8 + n], pos
        pos += 8 + n


def dump(d: bytes) -> str:
    out = []
    smf = parse_smf(d)
    out.append(f"SMF type {smf.fmt}, ppq {smf.ppq}, tracks {len(smf.tracks)}")
    ev = smf.tracks[0]
    for e in ev:
        if e.kind == META and e.meta_type in (0x01, 0x02, 0x03, 0x06, 0x51, 0x58):
            out.append(f"  t={e.tick:<8} meta {e.meta_type:#04x} {e.data[:40]!r}")
    chans = sorted({e.channel + 1 for e in ev if e.kind == NOTE_ON})
    out.append(f"  note channels (1-based): {chans}; last tick {ev[-1].tick}")
    # first non-SMF chunk follows the real end of the first MTrk (the header length can be off)
    pos = d.find(b"CASM")
    for tag, body, p in _chunks(d, pos, len(d)) if pos >= 0 else []:
        out.append(f"{tag.decode('latin1')} @ {p} len {len(body)}")
        if tag == b"CASM":
            for t2, b2, _ in _chunks(body, 0, len(body)):
                out.append(f"  CSEG len {len(b2)}")
                for t3, b3, _ in _chunks(b2, 0, len(b2)):
                    if t3 == b"Sdec":
                        out.append(f"    Sdec {b3.decode('latin1')}")
                    elif t3 == b"Ctab":
                        out.append(f"    Ctab src={b3[0]} {b3[1:9].decode('latin1')!r} {b3[9:].hex()}")
                    else:
                        out.append(f"    {t3.decode('latin1')} {b3.hex()}")
        if len(body) > 1_000_000:
            break
    return "\n".join(out)


def main() -> None:
    for path in sys.argv[1:]:
        print(f"== {path}")
        print(dump(open(path, "rb").read()))


if __name__ == "__main__":
    main()
