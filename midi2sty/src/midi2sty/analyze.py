"""Analyse a MIDI file into a model.Song."""
from __future__ import annotations
import math
import os

from . import model, smf

# Krumhansl-Kessler key profiles
_MAJOR = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
_MINOR = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]


def _corr(x: list[float], y: list[float]) -> float:
    mx, my = sum(x) / 12, sum(y) / 12
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    den = math.sqrt(sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y))
    return num / den if den else 0.0


def guess_key(pc_weights: list[float]) -> tuple[int, bool]:
    """Krumhansl-Schmuckler. Returns (root 0=C..11=B, is_minor); (0, False) if empty."""
    if not any(pc_weights):
        return 0, False
    best, best_r = (0, False), -2.0
    for root in range(12):
        rot = [pc_weights[(root + i) % 12] for i in range(12)]
        for minor, prof in ((False, _MAJOR), (True, _MINOR)):
            r = _corr(rot, prof)
            if r > best_r + 1e-12:
                best, best_r = (root, minor), r
    return best


def load_song(src: "str | os.PathLike | bytes") -> model.Song:
    if isinstance(src, (bytes, bytearray, memoryview)):
        data = bytes(src)
    else:
        with open(src, "rb") as f:
            data = f.read()
    f = smf.rescale(smf.parse_smf(data), model.TICKS_PER_BEAT)

    tempo_bpm: float | None = None
    time_sig: tuple[int, int] | None = None
    tracks: list[model.Track] = []
    length = 0
    pc = [0.0] * 12

    for events in f.tracks:
        tname = ""
        progs: dict[int, int] = {}
        open_notes: dict[tuple[int, int], list[tuple[int, int]]] = {}
        done: dict[int, list[model.Note]] = {}
        end_tick = 0
        for e in events:
            end_tick = max(end_tick, e.tick)
            if e.kind == smf.META:
                if e.meta_type == 0x03 and not tname:
                    tname = e.data.decode("latin-1").strip("\x00 ").strip()
                elif e.meta_type == 0x51 and tempo_bpm is None and len(e.data) == 3:
                    us = int.from_bytes(e.data, "big")
                    if us > 0:
                        tempo_bpm = 60_000_000 / us
                elif e.meta_type == 0x58 and time_sig is None and len(e.data) >= 2:
                    time_sig = (e.data[0], 1 << e.data[1])
            elif e.kind == smf.PROGRAM:
                progs.setdefault(e.channel, e.a)
            elif e.kind == smf.NOTE_ON:
                open_notes.setdefault((e.channel, e.a), []).append((e.tick, e.b))
            elif e.kind == smf.NOTE_OFF:
                st = open_notes.get((e.channel, e.a))
                if st:
                    t0, vel = st.pop(0)
                    done.setdefault(e.channel, []).append(
                        model.Note(t0, max(1, e.tick - t0), e.a, max(1, vel)))
        for (ch, pitch), st in open_notes.items():  # unterminated notes
            for t0, vel in st:
                done.setdefault(ch, []).append(
                    model.Note(t0, max(1, end_tick - t0), pitch, max(1, vel)))
        for ch in sorted(done):
            notes = sorted(done[ch], key=lambda n: (n.start, n.pitch))
            drums = ch == 9
            if not drums:
                for n in notes:
                    pc[n.pitch % 12] += n.dur
            length = max(length, max(n.start + n.dur for n in notes))
            tracks.append(model.Track(
                name=tname or f"Channel {ch + 1}", channel=ch,
                program=progs.get(ch), notes=notes, is_drums=drums))
        length = max(length, end_tick)

    root, minor = guess_key(pc)
    return model.Song(tracks=tracks, tempo_bpm=tempo_bpm or 120.0,
                      time_sig=time_sig or (4, 4), length_ticks=length,
                      key_root=root, key_minor=minor)
