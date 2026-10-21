#!/usr/bin/env python3
"""Statistical "anatomy of a style" over a folder of real Yamaha style files (.sty / .prs).

Usage (run from a directory that does NOT contain the data):
    python3 -I tools/style_stats.py DATA_DIR [--inventory STY_Files_Inventory.xlsx] [--only 1,2,3] [--json out.json]

Sections printed as markdown (use --only to select): 1 channels, 2 fills, 3 intro/ending,
4 setup, 5 casm, 6 pitch, 7 chunks, 8 prs-vs-sty.

The parser is EOT based: the MTrk length field is wrong in some files, so we walk events to
the End-of-Track meta and treat everything after as trailing chunks (CASM, OTSc, ...).
Pure stdlib; openpyxl is only used (optionally) to read the inventory for the DGX-native /
PSR-tutorial split.
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import statistics as st
import sys

ROLES = ["RHY1", "RHY2", "BASS", "CHD1", "CHD2", "PAD", "PHR1", "PHR2"]   # channels 9..16
ROLE_OF = {8 + i: r for i, r in enumerate(ROLES)}                          # 0-based channel
SECTION_TYPES = ["Intro A", "Intro B", "Intro C", "Main A", "Main B", "Main C", "Main D",
                 "Fill In AA", "Fill In BB", "Fill In CC", "Fill In DD", "Fill In BA",
                 "Ending A", "Ending B", "Ending C"]
GROUP_OF = {"Intro A": "IntroA", "Intro B": "IntroBC", "Intro C": "IntroBC",
            "Ending A": "EndA", "Ending B": "EndBC", "Ending C": "EndBC"}
for _s in SECTION_TYPES:
    if _s.startswith(("Main", "Fill")):
        GROUP_OF[_s] = "Main/Fill"
GROUPS = ["Main/Fill", "IntroA", "IntroBC", "EndA", "EndBC"]
FILL_MAIN = {"Fill In AA": "Main A", "Fill In BB": "Main B", "Fill In CC": "Main C",
             "Fill In DD": "Main D", "Fill In BA": "Main B"}
# GM / XG drum note classes
DRUM = {"kick": {35, 36}, "snare": {37, 38, 39, 40}, "tom": {41, 43, 45, 47, 48, 50},
        "hat": {42, 44, 46}, "crash": {49, 55, 57, 52}, "ride": {51, 53, 59},
        "perc": {54, 56, 58, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84}}
NONSEC = {b"SFF1", b"SFF2", b"SInt"}


# ----------------------------------------------------------------------------- parsing
def _vlq(d, i):
    v = 0
    while True:
        b = d[i]
        i += 1
        v = (v << 7) | (b & 0x7F)
        if not b & 0x80:
            return v, i


def parse(path):
    d = open(path, "rb").read()
    ppq = int.from_bytes(d[12:14], "big")
    hdr_len = int.from_bytes(d[18:22], "big")
    i, t, status, ev = 22, 0, 0, []
    while True:
        dt, i = _vlq(d, i)
        t += dt
        s = d[i]
        if s == 0xFF:
            mt = d[i + 1]
            n, j = _vlq(d, i + 2)
            ev.append((t, "meta", mt, d[j:j + n]))
            i = j + n
            if mt == 0x2F:
                break
        elif s in (0xF0, 0xF7):
            n, j = _vlq(d, i + 1)
            ev.append((t, "sysex", 0, d[j:j + n]))
            i = j + n
        else:
            if s & 0x80:
                status = s
                i += 1
            k = 1 if status >> 4 in (0xC, 0xD) else 2
            ev.append((t, "ch", status, tuple(d[i:i + k])))
            i += k
    chunks, p = [], i
    while p + 8 <= len(d):
        n = int.from_bytes(d[p + 4:p + 8], "big")
        chunks.append((d[p:p + 4].decode("latin1"), d[p + 8:p + 8 + n], n))
        p += 8 + n
    return dict(path=path, name=os.path.basename(path), data=d, ppq=ppq, hdr_len=hdr_len,
                real_len=i - 22, ev=ev, chunks=chunks, eot=ev[-1][0], size=len(d))


def parse_casm(body):
    """-> list of (section_names, [ctab dict], [cntt (src, byte)])"""
    out = []

    def walk(b):
        p = 0
        while p + 8 <= len(b):
            n = int.from_bytes(b[p + 4:p + 8], "big")
            yield b[p:p + 4], b[p + 8:p + 8 + n]
            p += 8 + n
    for tag, cseg in walk(body):
        if tag != b"CSEG":
            continue
        names, tabs, ntts = [], [], []
        for t3, b3 in walk(cseg):
            if t3 == b"Sdec":
                names = [x.strip() for x in b3.decode("latin1").strip("\0").split(",") if x.strip()]
            elif t3 == b"Ctab" and len(b3) >= 26:
                tabs.append(dict(src=b3[0], name=b3[1:9].decode("latin1").strip(), dest=b3[9],
                                 edit=b3[10], nmute=b3[11:13].hex(), cmute=b3[13:18].hex(),
                                 sroot=b3[18], stype=b3[19], ntr=b3[20], ntt=b3[21],
                                 hk=b3[22], lo=b3[23], hi=b3[24], rtr=b3[25],
                                 ntt_raw=b3[21], extra=b3[26:].hex(), sff2=False))
            elif t3 == b"Ctb2" and len(b3) >= 40:
                # SFF2 layout (empirical, 47 bytes): 0 src, 1-8 name, 9 dest, 10 edit, 11-12 note mute,
                # 13-17 chord mute, 18 src root, 19 src type, 20-21 prefix (00 7f), then THREE 6-byte groups
                # (NTR, NTT, high key, note low, note high, RTR) at 22/28/34, then a 7-byte tail.
                g = [tuple(b3[22 + 6 * k:28 + 6 * k]) for k in range(3)]
                ntt = g[0][1]
                tabs.append(dict(src=b3[0], name=b3[1:9].decode("latin1").strip(), dest=b3[9],
                                 edit=b3[10], nmute=b3[11:13].hex(), cmute=b3[13:18].hex(),
                                 sroot=b3[18], stype=b3[19], ntr=g[0][0], ntt_raw=ntt,
                                 ntt=ntt, hk=g[0][2], lo=g[0][3], hi=g[0][4],
                                 rtr=g[0][5], groups=g, prefix=b3[20:22].hex(), extra=b3[40:].hex(), sff2=True))
            elif t3 == b"Cntt" and len(b3) >= 2:
                ntts.append((b3[0], b3[1]))
        out.append((names, tabs, ntts))
    return out


def load_style(path):
    f = parse(path)
    ev, ppq = f["ev"], f["ppq"]
    ts = [e for e in ev if e[1] == "meta" and e[2] == 0x58]
    num, den = (ts[0][3][0], 1 << ts[0][3][1]) if ts else (4, 4)
    f["num"], f["den"] = num, den
    f["bar"] = ppq * 4 * num // den
    f["beat"] = ppq * 4 // den
    f["fmt"] = next((e[3].decode() for e in ev if e[1] == "meta" and e[2] == 6
                     and e[3] in (b"SFF1", b"SFF2")), "?")
    marks = [(e[0], e[3].decode("latin1")) for e in ev if e[1] == "meta" and e[2] == 6
             and e[3] not in NONSEC]
    secs = []
    for k, (t, n) in enumerate(marks):
        end = marks[k + 1][0] if k + 1 < len(marks) else f["eot"]
        secs.append(dict(name=n, start=t, end=end, bars=(end - t) / f["bar"]))
    f["secs"] = secs
    # notes (paired)
    open_, notes = {}, []
    for t, kind, st_, dat in ev:
        if kind != "ch":
            continue
        hi, ch = st_ >> 4, st_ & 15
        if hi == 9 and dat[1]:
            open_.setdefault((ch, dat[0]), []).append((t, dat[1]))
        elif hi == 8 or (hi == 9 and not dat[1]):
            q = open_.get((ch, dat[0]))
            if q:
                t0, v = q.pop(0)
                notes.append(dict(t=t0, off=t, ch=ch, p=dat[0], v=v))
    for (ch, p), q in open_.items():
        for t0, v in q:
            notes.append(dict(t=t0, off=None, ch=ch, p=p, v=v))
    f["notes"] = notes
    for s in secs:
        s["notes"] = [n for n in notes if s["start"] <= n["t"] < s["end"]]
    # casm
    casm = next((b for tag, b, _ in f["chunks"] if tag == "CASM"), b"")
    f["casm"] = parse_casm(casm)
    f["tables"] = {}          # section name -> list of ctab dicts (possibly several CSEGs)
    f["cntt"] = {}
    for names, tabs, ntts in f["casm"]:
        for n in names:
            f["tables"].setdefault(n, []).extend(tabs)
            f["cntt"].setdefault(n, []).extend(ntts)
    # Notes on alt source channels (1-8) are attributed to the destination channel of that section's table,
    # so every later statistic is per ROLE (dest ch 9-16). n["src"] keeps the original channel.
    for s in secs:
        m = {t["src"]: t["dest"] for t in f["tables"].get(s["name"], []) if 8 <= t["dest"] <= 15}
        for n in s["notes"]:
            n["src"] = n["ch"]
            n["ch"] = m.get(n["ch"], n["ch"])
    f["notes"] = [n for s in secs for n in s["notes"]]
    return f


def drum_class(p):
    for k, v in DRUM.items():
        if p in v:
            return k
    return "other"


def fmean(x):
    return sum(x) / len(x) if x else 0.0


def md(rows, head):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def pct(a, b):
    return f"{100 * a / b:.0f}%" if b else "-"


# ----------------------------------------------------------------------------- analyses
def sec_notes(s, chans=range(8, 16)):
    return [n for n in s["notes"] if n["ch"] in chans]


def a1_channels(files):
    """Per section type x channel: fraction of files with notes, mean notes/bar."""
    rows = []
    for st_ in SECTION_TYPES:
        have = [(f, s) for f in files for s in f["secs"] if s["name"] == st_]
        if not have:
            continue
        cells = []
        for ch in range(8, 16):
            used = sum(1 for f, s in have if any(n["ch"] == ch for n in s["notes"]))
            npb = fmean([sum(1 for n in s["notes"] if n["ch"] == ch) / s["bars"] for f, s in have])
            cells.append(f"{used / len(have):.2f} / {npb:.1f}")
        alt = fmean([sum(1 for n in s["notes"] if n["src"] < 8) / s["bars"] for f, s in have])
        altf = sum(1 for f, s in have if any(n["src"] < 8 for n in s["notes"])) / len(have)
        bars = collections.Counter(round(s["bars"], 2) for f, s in have)
        rows.append([st_, len(have), ", ".join(f"{b:g}b x{c}" for b, c in sorted(bars.items()))] + cells
                    + [f"{altf:.2f} / {alt:.1f}"])
    return "cell = fraction of files with notes on that channel / mean notes per bar\n\n" + md(
        rows, ["section", "n", "length (bars) x files"] + ROLES + ["share via alt src ch1-8 (files / notes per bar)"])


def a2_fills(files):
    out = []
    # per fill type vs its main
    rows, chdrop, chnew = [], collections.Counter(), collections.Counter()
    tot = collections.Counter()
    vel = collections.defaultdict(list)
    crash_pos = collections.Counter()
    pairs = 0
    endcrash = collections.Counter()
    clsvel = collections.defaultdict(list)
    sim = collections.defaultdict(list)
    other_only = 0
    fills = 0
    tick_gaps = []
    fill_chan_notes = collections.Counter()
    main_chan_npb = collections.defaultdict(list)
    fill_chan_npb = collections.defaultdict(list)
    cls_main, cls_fill = collections.defaultdict(list), collections.defaultdict(list)
    for f in files:
        S = {s["name"]: s for s in f["secs"]}
        for fn, mn in FILL_MAIN.items():
            if fn not in S or mn not in S:
                continue
            fs_, ms = S[fn], S[mn]
            fills += 1
            fn_ = sec_notes(fs_)
            mn_ = sec_notes(ms)
            pairs += 1
            for ch in range(8, 16):
                a = sum(1 for n in fn_ if n["ch"] == ch)
                b = sum(1 for n in mn_ if n["ch"] == ch)
                fill_chan_notes[ch] += a
                fill_chan_npb[ch].append(a / fs_["bars"])
                main_chan_npb[ch].append(b / ms["bars"])
                if b and not a:
                    chdrop[ch] += 1
                if a and not b:
                    chnew[ch] += 1
            if all(n["ch"] in (8, 9) for n in fn_) and fn_:
                other_only += 1
            rh_f = [n for n in fn_ if n["ch"] in (8, 9)]
            rh_m = [n for n in mn_ if n["ch"] in (8, 9)]
            for c in list(DRUM) + ["other"]:
                cls_fill[c].append(sum(1 for n in rh_f if drum_class(n["p"]) == c) / fs_["bars"])
                cls_main[c].append(sum(1 for n in rh_m if drum_class(n["p"]) == c) / ms["bars"])
            for n in rh_f:
                clsvel["fill " + drum_class(n["p"])].append(n["v"])
            for n in rh_m:
                clsvel["main " + drum_class(n["p"])].append(n["v"])
            ec = [n for n in rh_f if drum_class(n["p"]) == "crash" and (fs_["end"] - n["t"]) <= f["beat"] // 8]
            endcrash["fills with crash within 1/8 beat of section end"] += bool(ec)
            endcrash["  ... of which on RHY2 (ch10)"] += any(n["ch"] == 9 for n in ec)
            endcrash["  ... of which on RHY1 (ch9)"] += any(n["ch"] == 8 for n in ec)
            endcrash["  ... mean gap to end (ticks@1920ppq-equivalent)"] += 0
            tick_gaps.extend(round((fs_["end"] - n["t"]) * 1920 / f["ppq"]) for n in ec)
            for ch in range(10, 16):
                a = {(round((n["t"] - fs_["start"]) / (f["ppq"] // 8)), n["p"]) for n in fn_ if n["ch"] == ch}
                if not a:
                    continue
                bestj = 0
                for k in range(int(ms["bars"])):
                    o = ms["start"] + k * f["bar"]
                    b = {(round((n["t"] - o) / (f["ppq"] // 8)), n["p"]) for n in mn_ if n["ch"] == ch and o <= n["t"] < o + f["bar"]}
                    if b:
                        bestj = max(bestj, len(a & b) / len(a | b))
                sim[ch].append(bestj)
            vel["fill rhythm"] += [n["v"] for n in rh_f]
            vel["main rhythm"] += [n["v"] for n in rh_m]
            vel["fill non-rhythm"] += [n["v"] for n in fn_ if n["ch"] > 9]
            vel["main non-rhythm"] += [n["v"] for n in mn_ if n["ch"] > 9]
            # crash placement: relative to fill bar in beats
            crashes = [n for n in rh_f if drum_class(n["p"]) == "crash"]
            tot_beats = fs_["bars"] * f["num"] * 4 / f["den"]
            pos = collections.Counter()
            for n in crashes:
                b = (n["t"] - fs_["start"]) / f["beat"]
                pos["first beat" if b < 1 else "last beat" if b >= tot_beats - 1 else "middle"] += 1
            crash_pos["has crash"] += 1 if crashes else 0
            crash_pos["crash on first beat"] += 1 if "first beat" in pos else 0
            crash_pos["crash in last beat"] += 1 if "last beat" in pos else 0
            mcr = [n for n in rh_m if drum_class(n["p"]) == "crash"]
            crash_pos["main has crash"] += 1 if mcr else 0
            # last-note analysis
            if rh_f:
                last = max(n["t"] for n in rh_f)
                crash_pos["last rhythm onset in last beat"] += 1 if (fs_["end"] - last) <= f["beat"] else 0
                lastn = [n for n in rh_f if n["t"] == last]
                crash_pos["last-onset note is crash"] += 1 if any(drum_class(n["p"]) == "crash" for n in lastn) else 0
    out.append(f"fill/main pairs analysed: {pairs} (Fill In BA compared with Main B)\n")
    rows = []
    for ch in range(8, 16):
        rows.append([ROLES[ch - 8], f"{fmean(main_chan_npb[ch]):.1f}", f"{fmean(fill_chan_npb[ch]):.1f}",
                     pct(chdrop[ch], pairs), pct(chnew[ch], pairs)])
    out.append(md(rows, ["channel", "main notes/bar", "fill notes/bar", "pairs where channel drops out in fill",
                         "pairs where fill has notes but main none"]))
    rows = [[c, f"{fmean(cls_main[c]):.2f}", f"{fmean(cls_fill[c]):.2f}"] for c in list(DRUM) + ["other"]]
    out.append("\nRhythm channels (9+10) drum-class notes per bar:\n")
    out.append(md(rows, ["class", "main", "fill"]))
    out.append("\nVelocity (mean / min / max): " + "; ".join(
        f"{k}: {fmean(v):.0f}/{min(v)}/{max(v)}" for k, v in vel.items() if v))
    out.append("\nCrash / ending behaviour (count of fill/main pairs): "
               + ", ".join(f"{k}={v}" for k, v in crash_pos.items()))
    endcrash.pop("  ... mean gap to end (ticks@1920ppq-equivalent)")
    out.append("\nCrash at the very end of the fill bar (pickup that sounds on the next downbeat): "
               + ", ".join(f"{k.strip()}={v}/{fills}" for k, v in endcrash.items())
               + f"; gap to section end in ticks@1920 PPQ: {dict(collections.Counter(tick_gaps).most_common(4))}")
    out.append("\nMean velocity by drum class (rhythm channels), main -> fill: " + "; ".join(
        f"{c}: {fmean(clsvel['main ' + c]):.0f} -> {fmean(clsvel['fill ' + c]):.0f}" for c in list(DRUM) + ["other"]
        if clsvel["main " + c] or clsvel["fill " + c]))
    out.append("\nNon-rhythm channels in a fill: best same-grid (1/8 beat) Jaccard similarity of the fill bar with ANY bar of its Main "
               "(median / share >= 0.9): " + "; ".join(
                   f"{ROLES[ch - 8]} {st.median(v):.2f} / {sum(x >= .9 for x in v) / len(v):.0%}" for ch, v in sim.items() if v))
    out.append(f"\nFills where ONLY ch9/ch10 carry notes: {other_only}/{fills} ({pct(other_only, fills)})")
    # first/last bar of main for comparison: where main notes density in last bar vs rest
    return "\n".join(out)


def a3_intro_end(files):
    rows = []
    for st_ in ["Intro A", "Intro B", "Intro C", "Ending A", "Ending B", "Ending C"]:
        have = [(f, s) for f in files for s in f["secs"] if s["name"] == st_]
        n = len(have)
        if not n:
            continue
        chord = sum(1 for f, s in have if any(x["ch"] in (11, 12, 13) for x in s["notes"]))
        bass = sum(1 for f, s in have if any(x["ch"] == 10 for x in s["notes"]))
        phr = sum(1 for f, s in have if any(x["ch"] in (14, 15) for x in s["notes"]))
        rhy = sum(1 for f, s in have if any(x["ch"] in (8, 9) for x in s["notes"]))
        only_rhy = sum(1 for f, s in have if s["notes"] and all(x["ch"] in (8, 9) for x in sec_notes(s)))
        crash_any = crash_last = crash_first = 0
        longfinal = stop_last = noteoff_before = overhang = 0
        tempo_in = 0
        final_dur = []
        last_onset_gap = []
        for f, s in have:
            nn = sec_notes(s)
            if not nn:
                continue
            beat = f["beat"]
            cr = [x for x in nn if x["ch"] in (8, 9) and drum_class(x["p"]) == "crash"]
            crash_any += bool(cr)
            crash_first += any(x["t"] - s["start"] < beat for x in cr)
            crash_last += any(s["end"] - x["t"] <= f["bar"] for x in cr)   # in last bar
            pit = [x for x in nn if x["ch"] >= 10 and x["off"] is not None]
            if pit:
                last = max(pit, key=lambda x: x["off"])
                longfinal += (last["off"] - last["t"] >= 2 * beat) and (s["end"] - last["off"] <= beat // 2 + 1)
                final_dur.append((last["off"] - last["t"]) / beat)
            onsets = [x["t"] for x in nn]
            gap = (s["end"] - max(onsets)) / beat
            last_onset_gap.append(gap)
            stop_last += (max(onsets) < s["end"] - beat)
            offs = [x["off"] for x in nn if x["off"] is not None]
            noteoff_before += (max(offs) <= s["end"])
            overhang += sum(1 for x in nn if x["off"] is not None and x["off"] > s["end"])
            tempo_in += sum(1 for e in f["ev"] if e[1] == "meta" and e[2] == 0x51 and s["start"] < e[0] < s["end"])
        rows.append([st_, n, pct(rhy, n), pct(bass, n), pct(chord, n), pct(phr, n), pct(only_rhy, n),
                     pct(crash_any, n), pct(crash_first, n), pct(crash_last, n),
                     pct(longfinal, n), f"{fmean(final_dur):.1f}",
                     f"{fmean(last_onset_gap):.2f}", pct(stop_last, n),
                     pct(noteoff_before, n), overhang, tempo_in])
    extra = []
    for st_ in ["Intro A", "Intro B", "Intro C", "Ending A", "Ending B", "Ending C"]:
        have = [(f, s) for f in files for s in f["secs"] if s["name"] == st_]
        tails, atbar, held, hold, nfin, ritn, ritlen, ritmin, ritstart, endcr, nstep = [], 0, 0, [], [], 0, [], [], [], 0, []
        for f, s in have:
            nn = sec_notes(s)
            if not nn:
                continue
            lt = max(x["t"] for x in nn)
            tails.append((s["end"] - lt) / f["beat"])
            atbar += abs(((lt - s["start"]) % f["bar"])) <= f["ppq"] // 8
            fin = [x for x in nn if x["t"] >= lt - f["ppq"] // 8]
            nfin.append(len(fin))
            endcr += any(x["ch"] < 10 and drum_class(x["p"]) == "crash" for x in fin)
            pit = [x for x in nn if x["ch"] >= 10 and x["off"] is not None]
            if pit:
                lo = max(x["off"] for x in pit)
                held += (s["end"] - lo) <= f["beat"]
                hold.append(max((x["off"] - x["t"]) for x in pit) / f["beat"])
            base = next(60e6 / int.from_bytes(e[3], "big") for e in f["ev"] if e[1] == "meta" and e[2] == 0x51)
            tem = [(e[0], 60e6 / int.from_bytes(e[3], "big")) for e in f["ev"] if e[1] == "meta" and e[2] == 0x51
                   and s["start"] < e[0] < s["end"]]
            if len(tem) >= 3 and tem[-1][1] < tem[0][1]:
                ritn += 1
                ritlen.append((tem[-1][0] - tem[0][0]) / f["beat"])
                ritmin.append(min(b for _, b in tem) / base)
                ritstart.append((s["end"] - tem[0][0]) / f["beat"])
                nstep.append(len(tem))
        n = len(have)
        m = lambda v, fmt="{:.1f}": fmt.format(st.median(v)) if v else "-"
        extra.append([st_, n, m(tails), pct(atbar, n), m(nfin, "{:.0f}"), pct(endcr, n), pct(held, n), m(hold),
                      f"{ritn}/{n}", m(nstep, "{:.0f}"), m(ritlen), m(ritstart), m(ritmin, "{:.2f}")])
    head2 = ["section", "n", "median beats from last onset to end", "last onset on a bar start", "notes in final hit (median)",
             "final hit has crash", "last pitched note-off within 1 beat of end", "longest pitched note (beats, median)",
             "tempo ramp (>=3 decreasing tempo events)", "ramp steps", "ramp length (beats)", "ramp starts N beats before end",
             "min tempo / base tempo"]
    head = ["section", "n", "rhythm", "bass", "chord(11-13)", "phrase", "rhythm ONLY", "crash any", "crash 1st beat",
            "crash last bar", "final pitched note >=2 beats & ends at bar end", "final pitched dur (beats)",
            "mean gap last onset->end (beats)", "last beat silent (no onset)", "all note-offs <= end",
            "notes overhanging end", "tempo changes inside"]
    return md(rows, head) + "\n\nTails and ritardando:\n\n" + md(extra, head2)


def _cc_name(c):
    return {0: "bankMSB", 32: "bankLSB", 7: "vol", 10: "pan", 91: "reverb", 93: "chorus", 94: "variation",
            71: "resonance", 72: "release", 73: "attack", 74: "cutoff", 11: "expr", 64: "sustain",
            1: "mod", 84: "portaCtl"}.get(c, f"cc{c}")


def a4_setup(files):
    out = []
    ctr = collections.defaultdict(collections.Counter)
    ccpresent = collections.defaultdict(collections.Counter)
    sysex = collections.Counter()
    sysex_files = collections.defaultdict(set)
    for f in files:
        first = f["secs"][0]["start"] if f["secs"] else 0
        seen = {}
        for t, kind, s_, dat in f["ev"]:
            if t >= first:
                break
            if kind == "ch":
                hi, ch = s_ >> 4, s_ & 15
                if hi == 0xB:
                    seen[(ch, dat[0])] = dat[1]
                    ccpresent[ch][dat[0]] += 1
                elif hi == 0xC:
                    seen[(ch, "pc")] = dat[0]
            elif kind == "sysex":
                key = dat[:6].hex() if len(dat) > 6 else dat.hex()
                # collapse device/part-specific bytes
                sysex[key] += 1
                sysex_files[key].add(f["name"])
        for (ch, k), v in seen.items():
            ctr[(ch, k)][v] += 1
        f["_setup"] = seen
    spread = collections.defaultdict(list)
    for f in files:
        first = f["secs"][0]["start"]
        ticks = [e[0] for e in f["ev"] if e[0] < first and e[1] in ("ch", "sysex")]
        spread[f["fmt"]].append(max(ticks) if ticks else 0)
    out.append("Setup layout: last setup event tick before first section (min/median/max over files, bar = "
               + str(files[0]["bar"]) + " ticks): " + "; ".join(
                   f"{k}: {min(v)}/{st.median(v):g}/{max(v)} ({sum(x == 0 for x in v)}/{len(v)} files entirely at tick 0)"
                   for k, v in sorted(spread.items())) + "\n")
    out.append("Setup = every event before the first section marker (tick 0 .. SInt .. one blank bar).\n")
    out.append("Per channel (ch9-16): value frequency across files (value:count). n=" + str(len(files)))
    rows = []
    for ch in range(8, 16):
        for k in ("pc", 0, 32, 7, 10, 91, 93, 94, 71, 72, 73, 74):
            c = ctr.get((ch, k))
            if not c:
                continue
            nfiles = sum(c.values())
            top = ", ".join(f"{v}:{n}" for v, n in c.most_common(6))
            vals = [v for v, n in c.items() for _ in range(n)]
            rows.append([ROLES[ch - 8], "program" if k == "pc" else _cc_name(k), nfiles,
                         f"{min(vals)}-{max(vals)} med {st.median(vals):g}", top])
    out.append(md(rows, ["role", "event", "files", "range", "top values"]))
    # channels 1-8 setup presence
    c18 = sum(1 for f in files if any(ch < 8 for (ch, k) in f["_setup"]))
    out.append(f"\nFiles with setup events on ch1-8 (alt source channels): {c18}/{len(files)}")
    out.append("\nSysex before first section (first 6 bytes hex; count / files):\n")
    rows = [[k, n, len(sysex_files[k])] for k, n in sysex.most_common(25)]
    out.append(md(rows, ["sysex prefix", "count", "files"]))
    # at section starts
    out.append("\nEvents AT a section's start tick (marker tick), by section type: files with any CC/PC at start, "
               "CC numbers seen, how often value == setup value (reset) :\n")
    rows = []
    inside = collections.Counter()
    for st_ in SECTION_TYPES:
        nfile = nev = 0
        ccs = collections.Counter()
        same = diff = 0
        sysx = 0
        for f in files:
            for s in f["secs"]:
                if s["name"] != st_:
                    continue
                evs = [e for e in f["ev"] if e[0] == s["start"] and e[1] == "ch" and (e[2] >> 4) in (0xB, 0xC, 0xE)]
                sx = [e for e in f["ev"] if e[0] == s["start"] and e[1] == "sysex"]
                sysx += len(sx)
                if evs:
                    nfile += 1
                for e in evs:
                    nev += 1
                    ch = e[2] & 15
                    if e[2] >> 4 == 0xB:
                        ccs[(e[3][0])] += 1
                        sv = f["_setup"].get((ch, e[3][0]))
                        if sv is not None and sv == e[3][1]:
                            same += 1
                        else:
                            diff += 1
                    elif e[2] >> 4 == 0xC:
                        ccs["PC"] += 1
                    else:
                        ccs["bend"] += 1
                # events inside section (not at start)
                for e in f["ev"]:
                    if s["start"] < e[0] < s["end"] and e[1] == "ch" and (e[2] >> 4) in (0xB, 0xC, 0xE, 0xA, 0xD):
                        inside[(e[2] >> 4, e[3][0] if e[2] >> 4 == 0xB else -1)] += 1
        n = sum(1 for f in files for s in f["secs"] if s["name"] == st_)
        rows.append([st_, f"{nfile}/{n}", nev, same, diff, sysx,
                     ", ".join(f"{_cc_name(k) if isinstance(k, int) else k}:{v}" for k, v in ccs.most_common(8))])
    out.append(md(rows, ["section", "sections with CC/PC at start", "events", "= setup val", "!= setup val", "sysex",
                         "which"]))
    out.append("\nChannel events strictly inside sections (not at start tick): "
               + (", ".join(f"{'CC' + _cc_name(b) if a == 0xB else hex(a)}:{n}" for (a, b), n in inside.most_common(12)) or "none"))
    # other meta
    mc = collections.Counter()
    for f in files:
        for t, kind, m, dat in f["ev"]:
            if kind == "meta":
                mc[m] += 1
    out.append("\nMeta events overall (type:count): " + ", ".join(f"0x{k:02x}:{v}" for k, v in sorted(mc.items())))
    fn = collections.Counter()
    for f in files:
        for t, kind, m, dat in f["ev"]:
            if kind == "meta" and m == 1:
                fn[dat[:3]] += 1
    out.append("Text (0x01) events by prefix: " + ", ".join(f"{k!r}:{v}" for k, v in fn.most_common(5)))
    # tempo
    tc = collections.Counter()
    for f in files:
        n = sum(1 for e in f["ev"] if e[1] == "meta" and e[2] == 0x51)
        tc[n] += 1
    out.append("Tempo events per file (n events: files): " + ", ".join(f"{k}:{v}" for k, v in sorted(tc.items())))
    ts = collections.Counter(f"{f['num']}/{f['den']}" for f in files)
    bpm = [60e6 / int.from_bytes(next(e[3] for e in f["ev"] if e[1] == "meta" and e[2] == 0x51), "big") for f in files]
    out.append(f"Time signatures: {dict(ts)}; first tempo bpm min/median/max {min(bpm):.0f}/{st.median(bpm):.0f}/{max(bpm):.0f}")
    out.append("PPQ: " + str(dict(collections.Counter(f["ppq"] for f in files))))
    return "\n".join(out)


def _tab_key(t):
    return (f"NTR{t['ntr']} NTT{t['ntt']} hk{t['hk']} lo{t['lo']:02x} hi{t['hi']:02x} RTR{t['rtr']} "
            f"cm{t['cmute']} nm{t['nmute']}")


def a5_casm(files):
    out = []
    for fmt in ("SFF1", "SFF2"):
        fs = [f for f in files if f["fmt"] == fmt]
        if fs:
            out.append(f"\n### {fmt}: {len(fs)} files\n")
            out.append(_a5_one(fs))
    return "\n".join(out)


def _a5_one(files):
    out = []
    # grouping per file: how CSEGs split sections
    groups = collections.Counter()
    for f in files:
        groups[tuple(sorted(len(n) for n, _, _ in f["casm"]))] += 0
    out.append("CSEG count per file: " + str(dict(collections.Counter(len(f["casm"]) for f in files))))
    ntab = collections.Counter(len(tabs) for f in files for names, tabs, _ in f["casm"])
    out.append("Ctab count per CSEG (n tables: CSEGs): " + str(dict(sorted(ntab.items()))))
    sd = collections.Counter()
    for f in files:
        for names, tabs, _ in f["casm"]:
            sd[", ".join(sorted(names, key=lambda x: SECTION_TYPES.index(x) if x in SECTION_TYPES else 99))] += 1
    out.append("Sdec groupings (CSEGs): " + "; ".join(f"[{k}] x{v}" for k, v in sd.most_common(8)))
    dup = sum(1 for f in files for n in SECTION_TYPES if sum(n in names for names, _, _ in f["casm"]) > 1)
    out.append(f"Sections listed in more than one CSEG: {dup}")
    # sections with no table
    miss = collections.Counter(s["name"] for f in files for s in f["secs"] if s["name"] not in f["tables"])
    out.append("Sections without any CASM table: " + (str(dict(miss)) or "none"))
    srcd = collections.Counter(("src>=8" if t["src"] >= 8 else "src<8 (alt source ch1-8)", "src==dest" if t["src"] == t["dest"] else "src!=dest") for f in files for ts in f["tables"].values() for t in ts)
    out.append("Table (src>=8, src==dest) counts: " + str(dict(srcd)))
    # per role and group
    sroot = collections.Counter((t["sroot"], t["stype"]) for f in files for ts in f["tables"].values() for t in ts if True)
    out.append("Source chord (root, type) over all tables: " + str(dict(sroot.most_common(8))))
    edit = collections.Counter(t["edit"] for f in files for ts in f["tables"].values() for t in ts)
    out.append("Editable byte (b10): " + str(dict(edit)))
    extra = collections.Counter(t["extra"] for f in files for ts in f["tables"].values() for t in ts)
    out.append("Ctab byte 26+: " + str(dict(extra)))
    mname = collections.Counter(t["name"] for f in files for ts in f["tables"].values() for t in ts if t["src"] >= 8 and t["src"] != t["dest"])
    # per role per group frequency tables (count a file once per group per distinct table)
    for g in GROUPS:
        out.append(f"\n#### Group {g} (value:files, a file counts once per distinct value)\n")
        rows = []
        nfiles_g = sum(1 for f in files if any(GROUP_OF.get(s["name"]) == g for s in f["secs"]))
        for ch in range(8, 16):
            vals = collections.defaultdict(collections.Counter)
            nfile = 0
            for f in files:
                seen = collections.defaultdict(set)
                for s in f["secs"]:
                    if GROUP_OF.get(s["name"]) != g:
                        continue
                    for t in f["tables"].get(s["name"], []):
                        if t["dest"] == ch:
                            for fld in ("ntr", "ntt", "hk", "rtr", "lo", "hi", "cmute"):
                                v = t[fld]
                                seen[fld].add(f"{v:x}" if fld in ("lo", "hi") else v)
                if seen:
                    nfile += 1
                for fld, vs in seen.items():
                    for v in vs:
                        vals[fld][v] += 1
            if not nfile:
                rows.append([ROLES[ch - 8], f"0/{nfiles_g}", "-", "-", "-", "-", "-", "-", "-"])
                continue
            rows.append([ROLES[ch - 8], f"{nfile}/{nfiles_g}"] + [
                ", ".join(f"{k}:{v}" for k, v in vals[fld].most_common(4)) for fld in ("ntr", "ntt", "hk", "rtr", "lo", "hi", "cmute")])
        out.append(md(rows, ["role", "files with table", "NTR", "NTT", "high key", "RTR", "note low(hex)", "note high(hex)", "chord mute"]))
    # cntt
    if not any(v for f in files for v in f["cntt"].values()):
        out.append("\nNo Cntt chunks in these files (SFF2 folds the Cntt byte into the Ctb2 NTT byte: 0x81 = bass).")
    else:
        out.append("\n#### Cntt (src ch -> byte) frequency by role\n")
        rows = []
        for ch in range(8, 16):
            c = collections.Counter()
            for f in files:
                seen = set()
                for n, ntt in [x for v in f["cntt"].values() for x in v]:
                    if n == ch:
                        seen.add(ntt)
                for v in seen:
                    c[f"{v:02x}"] += 1
            rows.append([ROLES[ch - 8], ", ".join(f"{k}:{v}" for k, v in c.most_common())])
        out.append(md(rows, ["role", "Cntt byte1 : files"]))
    # per field per role (all groups): modal
    out.append("\n#### Field-wise distribution per role (all tables, by destination role)\n")
    rows = []
    for ch in range(8, 16):
        T = [t for f in files for ts in f["tables"].values() for t in ts if t["dest"] == ch]
        if not T:
            continue
        row = [ROLES[ch - 8], len(T)]
        for fld in ("ntr", "ntt", "hk", "rtr"):
            c = collections.Counter(t[fld] for t in T)
            row.append(", ".join(f"{k}:{v}" for k, v in c.most_common(4)))
        for fld in ("lo", "hi", "cmute", "nmute"):
            c = collections.Counter((f"{t[fld]:02x}" if isinstance(t[fld], int) else t[fld]) for t in T)
            row.append(", ".join(f"{k}:{v}" for k, v in c.most_common(4)))
        rows.append(row)
    out.append(md(rows, ["role", "tables", "NTR", "NTT", "high key", "RTR", "note low", "note high", "chord mute", "note mute"]))
    # Intro/Ending vs Main differences
    out.append("\n#### Intro B/C and Ending B/C vs Main (same file): which fields differ, per role\n")
    rows = []
    for ch in range(8, 16):
        diff = collections.Counter()
        cmp_n = 0
        absent = 0
        for f in files:
            m = f["tables"].get("Main A", [])
            mt = next((t for t in m if t["dest"] == ch), None)
            for sn in ("Intro B", "Intro C", "Ending B", "Ending C"):
                it = next((t for t in f["tables"].get(sn, []) if t["dest"] == ch), None)
                if mt is None and it is None:
                    continue
                if mt is None or it is None:
                    absent += 1
                    continue
                cmp_n += 1
                for fld in ("ntr", "ntt", "hk", "lo", "hi", "rtr", "cmute", "nmute"):
                    if mt[fld] != it[fld]:
                        diff[fld] += 1
        rows.append([ROLES[ch - 8], cmp_n, absent, ", ".join(f"{k}:{v}" for k, v in diff.most_common()) or "-"])
    out.append(md(rows, ["role", "compared (file x section)", "table missing in one", "fields that differ (count)"]))
    # what are the intro-B/C chord-mute values vs main
    cm = collections.defaultdict(collections.Counter)
    for f in files:
        for sn, ts in f["tables"].items():
            for t in ts:
                if t["dest"] in (10, 11, 12, 13, 14, 15):
                    cm[(GROUP_OF.get(sn, sn), ROLES[t["dest"] - 8])][(t["cmute"], t["nmute"], t["ntt"], t["ntr"])] += 1
    out.append("\n#### (group, role) -> top (chord-mute, note-mute, NTT, NTR) tuples (count of section-table instances)\n")
    rows = []
    for k in sorted(cm):
        rows.append([k[0], k[1], "; ".join(f"{a}/{b}/{c}/{d} x{n}" for (a, b, c, d), n in cm[k].most_common(3))])
    out.append(md(rows, ["group", "role", "cmute/nmute/NTT/NTR"]))
    T2 = [(sn, t) for f in files for sn, ts in f["tables"].items() for t in ts if t.get("sff2")]
    if T2:
        out.append("\n#### Ctb2-only details (47-byte body; 3 six-byte groups = NTR,NTT,highkey,low,high,RTR)\n")
        out.append("Prefix bytes 20-21: " + str(dict(collections.Counter(t["prefix"] for _, t in T2))))
        out.append("Tail bytes 40-46: " + str(dict(collections.Counter(t["extra"] for _, t in T2).most_common(6))))
        out.append("Source chord (root,type): " + str(dict(collections.Counter((t["sroot"], t["stype"]) for _, t in T2).most_common(8))))
        out.append("NTT raw byte (0x81 = bass flag): " + str(dict(collections.Counter(t["ntt_raw"] for _, t in T2))))
        rows = []
        for ch in range(8, 16):
            tt = [t for _, t in T2 if t["dest"] == ch]
            if not tt:
                continue
            d2 = sum(t["groups"][1] != t["groups"][0] for t in tt)
            d3 = sum(t["groups"][2] != t["groups"][0] for t in tt)
            g2 = collections.Counter(t["groups"][1][:2] for t in tt if t["groups"][1] != t["groups"][0])
            rows.append([ROLES[ch - 8], len(tt), pct(d2, len(tt)), pct(d3, len(tt)),
                         ", ".join(f"NTR{a}/NTT{b}:{n}" for (a, b), n in g2.most_common(4))])
        out.append(md(rows, ["role", "tables", "group2 != group1", "group3 != group1", "group2 (ntr/ntt) when different"]))
    return "\n".join(out)


def a6_pitch(files):
    out = []
    P = collections.defaultdict(list)
    PC = collections.defaultdict(collections.Counter)
    for f in files:
        for s in f["secs"]:
            tabs = {t["src"]: t for t in f["tables"].get(s["name"], [])}
            for n in s["notes"]:
                if n["ch"] < 8:
                    continue
                t = tabs.get(n["src"])
                root = t["sroot"] if t and t["sroot"] < 12 else 0
                P[n["ch"]].append(n["p"] - root)
                PC[n["ch"]][(n["p"] - root) % 12] += 1
    rows = []
    for ch in range(10, 16):
        v = sorted(P[ch])
        if not v:
            continue
        q = lambda x: v[int(x * (len(v) - 1))]
        pcs = PC[ch]
        tot = sum(pcs.values())
        ct = sum(pcs[x] for x in (0, 4, 7, 11)) / tot
        sc = sum(pcs[x] for x in (0, 2, 4, 5, 7, 9, 11)) / tot
        rows.append([ROLES[ch - 8], len(v), v[0], q(0.05), q(0.25), int(st.median(v)), q(0.75), q(0.95), v[-1],
                     f"{ct:.0%}", f"{sc:.0%}"])
    out.append("Pitch (MIDI note, source chord root removed so all = C) per channel over ALL sections:\n")
    out.append(md(rows, ["role", "notes", "min", "p5", "p25", "median", "p75", "p95", "max", "% CMaj7 tones", "% C-major scale"]))
    # per group
    out.append("\nSame, by section group (min / median / max):\n")
    rows = []
    for ch in range(10, 16):
        row = [ROLES[ch - 8]]
        for g in GROUPS:
            v = [n["p"] for f in files for s in f["secs"] if GROUP_OF.get(s["name"]) == g for n in s["notes"] if n["ch"] == ch]
            row.append(f"{min(v)} / {int(st.median(v))} / {max(v)}" if v else "-")
        rows.append(row)
    out.append(md(rows, ["role"] + GROUPS))
    # per-file medians spread
    out.append("\nPer-file median pitch spread (min/median/max over files, files with >=8 notes):\n")
    rows = []
    for ch in range(10, 16):
        meds, lows, highs = [], [], []
        for f in files:
            v = [n["p"] for n in f["notes"] if n["ch"] == ch]
            if len(v) >= 8:
                meds.append(st.median(v))
                lows.append(min(v))
                highs.append(max(v))
        if meds:
            rows.append([ROLES[ch - 8], len(meds), f"{min(meds):g} / {st.median(meds):g} / {max(meds):g}",
                         f"{min(lows)} / {st.median(lows):g} / {max(lows)}", f"{min(highs)} / {st.median(highs):g} / {max(highs)}"])
    out.append(md(rows, ["role", "files", "file-median: min/med/max", "file-lowest: min/med/max", "file-highest: min/med/max"]))
    # polyphony of chord channels
    out.append("\nMean simultaneous onsets per onset time (polyphony) and notes/bar by role (Main sections):\n")
    rows = []
    for ch in range(10, 16):
        poly, dens, mono = [], [], []
        for f in files:
            for s in f["secs"]:
                if not s["name"].startswith("Main"):
                    continue
                ns = [n for n in s["notes"] if n["ch"] == ch]
                if not ns:
                    continue
                c = collections.Counter(n["t"] for n in ns)
                poly.append(fmean(list(c.values())))
                dens.append(len(ns) / s["bars"])
                dur = [(n["off"] - n["t"]) / f["beat"] for n in ns if n["off"] is not None]
                mono.append(fmean(dur))
        if poly:
            rows.append([ROLES[ch - 8], f"{fmean(poly):.2f}", f"{fmean(dens):.1f}", f"{fmean(mono):.2f}"])
    out.append(md(rows, ["role", "notes per onset", "notes/bar", "mean note length (beats)"]))
    # drums
    dc = collections.defaultdict(collections.Counter)
    for f in files:
        for n in f["notes"]:
            if n["ch"] in (8, 9):
                dc[n["ch"]][n["p"]] += 1
    out.append("\nDrum notes used (top 14 per rhythm channel):")
    for ch in (8, 9):
        tot = sum(dc[ch].values())
        out.append(f"- {ROLES[ch - 8]}: " + ", ".join(f"{p}:{c * 100 / tot:.0f}%" for p, c in dc[ch].most_common(14)))
    # velocity per role
    out.append("\nVelocity per role (all sections; min/p5/median/p95/max):\n")
    rows = []
    for ch in range(8, 16):
        v = sorted(n["v"] for f in files for n in f["notes"] if n["ch"] == ch)
        if v:
            q = lambda x: v[int(x * (len(v) - 1))]
            rows.append([ROLES[ch - 8], len(v), v[0], q(.05), int(st.median(v)), q(.95), v[-1]])
    out.append(md(rows, ["role", "notes", "min", "p5", "median", "p95", "max"]))
    return "\n".join(out)


def a7_chunks(files):
    sizes = collections.defaultdict(list)
    order = collections.Counter()
    for f in files:
        order[" ".join(t for t, _, _ in f["chunks"])] += 1
        for t, _, n in f["chunks"]:
            sizes[t].append(n)
    rows = [[t, len(v), f"{min(v)} / {int(st.median(v))} / {max(v)}"] for t, v in sizes.items()]
    out = [md(rows, ["chunk", "files", "size min/median/max (bytes)"]), "\nChunk order: " + str(dict(order))]
    bad = [(f["name"][:25], f["hdr_len"], f["real_len"]) for f in files if f["hdr_len"] != f["real_len"]]
    out.append(f"\nMTrk length field != real EOT length in {len(bad)}/{len(files)} files, e.g. " + str(bad[:4]))
    tr = sum(len(f["data"]) - 22 - f["real_len"] - sum(8 + n for _, _, n in f["chunks"]) for f in files)
    out.append(f"Unparsed trailing bytes after chunks (total): {tr}")
    rows = []
    for f in files:
        mt = f["real_len"]
        rows.append([f["name"][:28], f["fmt"], f["size"], mt, sum(n for t, _, n in f["chunks"] if t == "CASM"),
                     sum(n for t, _, n in f["chunks"] if t == "OTSc")])
    out.append("\n" + md(rows, ["file", "fmt", "file bytes", "MTrk bytes", "CASM", "OTSc"]))
    # first 16 bytes of OTSc / FNRc / Cmbi
    for tag in ("OTSc", "Cmbi", "FNRc", "ASnc"):
        ex = next(((f["name"], b[:24].hex()) for f in files for t, b, _ in f["chunks"] if t == tag), None)
        if ex:
            out.append(f"- {tag} head ({ex[0][:20]}): {ex[1]}")
    # OTSc internals
    ot = collections.Counter()
    for f in files:
        for t, b, n in f["chunks"]:
            if t == "OTSc":
                p = 0
                kinds = []
                while p + 8 <= len(b):
                    m = int.from_bytes(b[p + 4:p + 8], "big")
                    kinds.append(b[p:p + 4].decode("latin1"))
                    p += 8 + m
                ot[tuple(sorted(set(kinds)))] += 1
    out.append("OTSc sub-chunk tags per file: " + str(dict(ot)))
    return "\n".join(out)


def a8_prs_sty(files, source=None):
    source = source or {}
    def grp(f):
        ext = f["name"].rsplit(".", 1)[-1].lower()
        return f"{source.get(f['name'], '?')} / .{ext} / {f['fmt']}"
    G = collections.defaultdict(list)
    for f in files:
        G[grp(f)].append(f)
    rows = []
    for g, fs in sorted(G.items()):
        c = fs
        def sc(fn):
            return fmean([fn(f) for f in c])
        alt = sum(1 for f in c if any(n["src"] < 8 for n in f["notes"]))
        tab_alt = sum(1 for f in c if any(t["src"] < 8 for ts in f["tables"].values() for t in ts))
        msb = collections.Counter()
        for f in c:
            for t, k, s_, d in f["ev"]:
                if t < f["secs"][0]["start"] and k == "ch" and s_ >> 4 == 0xB and d[0] == 0 and (s_ & 15) >= 10:
                    msb[d[1]] += 1
        sx = collections.Counter()
        for f in c:
            for t, k, s_, d in f["ev"]:
                if t < f["secs"][0]["start"] and k == "sysex":
                    sx[d[:3].hex()] += 1
        cp = collections.Counter(next((e[3][:21].decode("latin1") for e in f["ev"] if e[1] == "meta" and e[2] == 2), "-") for f in c)
        rows.append([g, len(c), f"{sc(lambda f: f['size']) / 1024:.0f}", f"{sc(lambda f: f['real_len']) / 1024:.0f}",
                     f"{sc(lambda f: sum(n for t, _, n in f['chunks'] if t == 'CASM')):.0f}",
                     f"{sc(lambda f: sum(n for t, _, n in f['chunks'] if t == 'OTSc')):.0f}",
                     f"{alt}/{len(c)}", f"{tab_alt}/{len(c)}",
                     f"{sc(lambda f: len(f['casm'])):.1f}",
                     ", ".join(f"{k}:{v}" for k, v in msb.most_common(4)),
                     ", ".join(f"{k}:{v}" for k, v in sx.most_common(4)),
                     ", ".join(sorted({tag for f in c for tag, _, _ in f["chunks"]} - {"CASM", "OTSc"})) or "-",
                     str(sorted({f["ppq"] for f in c}))])
    out = [md(rows, ["group (source / ext / SFF)", "n", "file KB", "MTrk KB", "CASM B", "OTSc B", "notes on alt src ch1-8",
                     "Ctab src<8", "CSEGs", "bank MSB ch11-16 in lead-in bar", "sysex prefixes in lead-in bar", "extra chunks", "PPQ"])]
    return "\n".join(out)


ANALYSES = {"1": ("1. Which channels carry notes, per section", a1_channels),
            "2": ("2. Fill In vs Main", a2_fills),
            "3": ("3. Intro / Ending anatomy", a3_intro_end),
            "4": ("4. Setup events and section-start events", a4_setup),
            "5": ("5. CASM Ctab / Cntt", a5_casm),
            "6": ("6. Pitch register, drums, velocity", a6_pitch),
            "7": ("7. Chunks", a7_chunks),
            "8": ("8. DGX-native .prs vs PSR-tutorial .sty", None)}


def read_inventory(path):
    try:
        import openpyxl
    except ImportError:
        return {}
    ws = openpyxl.load_workbook(path, read_only=True)["Files"]
    return {r[1]: r[5] for r in ws.iter_rows(min_row=2, values_only=True) if r[1]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--inventory")
    ap.add_argument("--only", default="1,2,3,4,5,6,7,8")
    a = ap.parse_args()
    paths = sorted(p for p in glob.glob(os.path.join(a.dir, "*")) if p.lower().endswith((".sty", ".prs")))
    files = [load_style(p) for p in paths]
    inv = read_inventory(a.inventory) if a.inventory else {}
    print(f"# {len(files)} style files\n")
    for k in a.only.split(","):
        title, fn = ANALYSES[k]
        print(f"\n## {title}\n")
        print(fn(files) if k != "8" else a8_prs_sty(files, inv))


if __name__ == "__main__":
    sys.exit(main())
