"""Command line.

    midi2sty in.mid [-o out.sty] [--recipe r.json] [--write-recipe r.json] [--list-tracks]
    midi2sty ui ...          interactive editor (dispatches to midi2sty.ui.main)

Without --recipe the arranger proposes one (``arrange.suggest_recipe``); --write-recipe saves the
recipe that was used so it can be edited and fed back with --recipe. --list-tracks only prints the
track table (role, melody tier, reason) and the proposed sections; it writes no style.
"""
from __future__ import annotations

import argparse
import importlib
import sys


_NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="midi2sty", description="Convert a MIDI file to a Yamaha .sty style "
        "(use 'midi2sty ui ...' for the interactive editor).")
    p.add_argument("input", help="input .mid file")
    p.add_argument("-o", "--output", help="output .sty (default: input with .sty extension)")
    p.add_argument("--recipe", metavar="R.JSON", help="use this recipe instead of the suggested one")
    p.add_argument("--write-recipe", metavar="R.JSON", help="write the recipe used to this file")
    p.add_argument("--list-tracks", action="store_true",
                   help="print tracks with proposed roles / melody detection and exit (no .sty written)")
    return p


def _print_tracks(song, recipe, out=None) -> None:
    out = out or sys.stdout
    from . import melody
    rows = {r["index"]: r for r in melody.classify_parts(song)}
    print(f"tempo {song.tempo_bpm:.1f} bpm, time {song.time_sig[0]}/{song.time_sig[1]}, "
          f"key {_NAMES[song.key_root % 12]} {'minor' if song.key_minor else 'major'} "
          f"(recipe tonic {_NAMES[recipe.tonic % 12]})", file=out)
    print(f"{'#':>2} {'ch':>2} {'name':<18} {'prog':>4} {'notes':>6} {'role':<8} {'tier':>4} {'score':>5}  reason",
          file=out)
    for t in song.tracks:
        r = rows[t.index]
        plan = next((p for p in recipe.tracks if p.index == t.index), None)
        print(f"{t.index:>2} {t.channel + 1:>2} {t.name[:18]:<18} {t.program if t.program is not None else '-':>4} "
              f"{len(t.notes):>6} {(plan.role if plan else '-'):<8} {r['tier']:>4} {r['score']:>5.1f}  "
              f"{(plan.reason if plan else r['reason'])[:90]}", file=out)
    print("sections:", file=out)
    for s in recipe.sections:
        src = (f"song bars {s.start_bar + 1}-{s.start_bar + (s.n_bars or 1)}" if s.source == "song"
               else f"from {s.derive_from}" if s.source == "derive" else "auto")
        print(f"  {s.name:<11} {src}" + (f" ({s.n_bars} bars)" if s.n_bars and s.source != "song" else ""),
              file=out)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "ui":
        try:
            ui = importlib.import_module("midi2sty.ui")
        except ImportError:
            print("error: the 'ui' subcommand is not available (midi2sty.ui missing)", file=sys.stderr)
            return 2
        return ui.main(argv[1:]) or 0
    args = build_parser().parse_args(argv)
    from .analyze import load_song
    from .arrange import build_style, suggest_recipe
    from .recipe import Recipe

    try:
        song = load_song(args.input)
        if args.recipe:
            with open(args.recipe, encoding="utf-8") as f:
                recipe = Recipe.from_json(f.read())
            bad = recipe.validate()
            if bad:
                print("error: invalid recipe: " + "; ".join(bad), file=sys.stderr)
                return 2
        else:
            recipe = suggest_recipe(song)
        if args.write_recipe:
            with open(args.write_recipe, "w", encoding="utf-8") as f:
                f.write(recipe.to_json())
        if args.list_tracks:
            _print_tracks(song, recipe)
            return 0
        style = build_style(song, recipe)
    except (ValueError, OSError, KeyError, TypeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    from .sty_writer import write_sty
    from .validate import validate_sty

    out = args.output or (args.input.rsplit(".", 1)[0] + ".sty")
    data = write_sty(style)
    with open(out, "wb") as f:
        f.write(data)
    for w in validate_sty(data):
        print(f"warning: {w}", file=sys.stderr)
    print(f"wrote {out} ({len(style.sections)} sections, {len(data)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
