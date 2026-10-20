"""Command line: midi2sty in.mid -o out.sty [--bars-per-section N] [--sections ...]."""
from __future__ import annotations

import argparse
import sys

from .mapper import DEFAULT_SECTIONS, MapOptions, song_to_style


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="midi2sty", description="Convert a MIDI file to a Yamaha .sty style.")
    p.add_argument("input", help="input .mid file")
    p.add_argument("-o", "--output", help="output .sty (default: input with .sty extension)")
    p.add_argument("--bars-per-section", type=int, default=4, metavar="N",
                   help="bars per Main section (default 4)")
    p.add_argument("--sections", nargs="+", default=list(DEFAULT_SECTIONS), metavar="NAME",
                   help="sections to emit, e.g. 'Intro A' 'Main A' (default: all supported)")
    p.add_argument("--no-transpose", action="store_true", help="do not transpose to CMaj7")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    # Lazy imports: other stages are written by separate modules.
    from .analyze import load_song
    from .sty_writer import write_sty
    from .validate import validate_sty

    out = args.output or (args.input.rsplit(".", 1)[0] + ".sty")
    try:
        opts = MapOptions(bars_per_section=args.bars_per_section,
                          sections=tuple(args.sections), transpose=not args.no_transpose)
        style = song_to_style(load_song(args.input), opts)
    except (ValueError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if not style.sections:
        print("error: no usable material found in input", file=sys.stderr)
        return 1
    data = write_sty(style)
    with open(out, "wb") as f:
        f.write(data)
    warnings = validate_sty(data)
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    print(f"wrote {out} ({len(style.sections)} sections, {len(data)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
