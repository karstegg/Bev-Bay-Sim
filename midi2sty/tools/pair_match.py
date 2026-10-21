"""Helpers to compare a song MIDI with a Yamaha style (.sty/.prs) made from it.

EOT-based SMF parser (MTrk length is unreliable in some style files).
Usage: python3 pair_match.py song.mid style.sty [--shift N]   (prints best song-track/bars per style section+channel)
"""
import sys, collections

def load(path):
    d = open(path, 'rb').read()
    ppq = int.from_bytes(d[12:14], 'big'); ntrk = int.from_bytes(d[10:12], 'big')
    def vlq(i):
        v = 0
        while True:
            b = d[i]; i += 1; v = (v << 7) | (b & 0x7f)
            if not b & 0x80: return v, i
    i = 14; trks = []
    for _ in range(ntrk):
        if d[i:i+4] != b'MTrk': break
        i += 8; t = 0; ev = []; status = 0
        while True:
            dt, i = vlq(i); t += dt; s = d[i]
            if s == 0xff:
                mt = d[i+1]; n, j = vlq(i+2); ev.append((t, 'meta', mt, d[j:j+n])); i = j + n
                if mt == 0x2f: break
            elif s in (0xf0, 0xf7):
                n, j = vlq(i+1); ev.append((t, 'sysex', d[j:j+n])); i = j + n
            else:
                if s & 0x80: status = s; i += 1
                k = 1 if status >> 4 in (0xc, 0xd) else 2
                ev.append((t, 'ch', status, tuple(d[i:i+k]))); i += k
        trks.append(ev)
    return ppq, trks

def meta_info(trks):
    ts = (4, 4); tempo = None; marks = []
    for ev in trks:
        for e in ev:
            if e[1] == 'meta':
                if e[2] == 0x58: ts = (e[3][0], 2**e[3][1])
                elif e[2] == 0x51 and tempo is None: tempo = 60e6/int.from_bytes(e[3], 'big')
                elif e[2] == 6: marks.append((e[0], e[3].decode('latin1')))
    return ts, tempo, marks

def notes_of(ev):
    """-> list of (start,end,ch,pitch,vel)"""
    on = {}; out = []
    for e in ev:
        if e[1] != 'ch': continue
        st, (a, *b) = e[2], e[3]
        k = st >> 4; ch = st & 15
        if k == 9 and b and b[0] > 0: on[(ch, a)] = (e[0], b[0])
        elif k == 8 or k == 9:
            if (ch, a) in on:
                s, v = on.pop((ch, a)); out.append((s, e[0], ch, a, v))
    return out

def track_names(ev):
    for e in ev:
        if e[1] == 'meta' and e[2] == 3: return e[3].decode('latin1').strip('\0 ')
    return ''

def programs(ev):
    p = {}
    for e in ev:
        if e[1] == 'ch' and e[2] >> 4 == 0xc: p.setdefault(e[2] & 15, e[3][0])
    return p

def sections(trks):
    ts, tempo, marks = meta_info(trks)
    end = max(e[0] for ev in trks for e in ev)
    s = [(t, n) for t, n in marks if n not in ('SFF1', 'SFF2', 'SInt')]
    return [(n, t, s[i+1][0] if i+1 < len(s) else end) for i, (t, n) in enumerate(s)]

def bar_sig(notes, bar_start, bar_len, ppq, shift=0, drums=False, grid=4):
    """(pc-set histogram, onset-grid set) for a bar. grid = steps per quarter."""
    pcs = collections.Counter(); ons = set()
    for s, e, ch, p, v in notes:
        if bar_start <= s < bar_start + bar_len:
            pcs[(p + shift) % 12 if not drums else p] += 1
            ons.add(round((s - bar_start) * grid / ppq))
    return pcs, ons

def sim(a, b):
    """combined similarity of two (pcs, ons) signatures, 0..1"""
    (pa, oa), (pb, ob) = a, b
    if not pa and not pb: return 1.0
    if not pa or not pb: return 0.0
    ks = set(pa) | set(pb)
    num = sum(min(pa[k], pb[k]) for k in ks); den = sum(max(pa[k], pb[k]) for k in ks)
    j = num / den
    jo = len(oa & ob) / max(1, len(oa | ob))
    return 0.5 * j + 0.5 * jo

def bar_roots(notes, bar_song, nbars):
    """dominant (duration-weighted, low-register favoured) pitch class per bar of a bass track; carries previous root over empty bars."""
    roots = []; prev = 0
    for b in range(nbars):
        h = collections.Counter()
        for s, e, ch, p, v in notes:
            if b*bar_song <= s < (b+1)*bar_song: h[p % 12] += (e - s) * (1.5 if p < 45 else 1.0)
        prev = h.most_common(1)[0][0] if h else prev
        roots.append(prev)
    return roots

def match_section(style_notes, sec_start, sec_end, bar_s, song_chan_notes, bar_song, ppq_s, ppq_m, shift, drums=False):
    """For one style channel's notes in a section, find best song window. Returns (score, start_bar, n_bars)."""
    nb = max(1, round((sec_end - sec_start) / bar_s))
    sty = [bar_sig(style_notes, sec_start + i*bar_s, bar_s, ppq_s, 0, drums) for i in range(nb)]
    last = max((n[0] for n in song_chan_notes), default=0) // bar_song + 1
    best = (0, None, nb)
    # shift: int (fixed song->style semitones) or list of per-bar ints (e.g. -bar_roots(...))
    sh = (lambda b: shift[b] if b < len(shift) else 0) if isinstance(shift, (list, tuple)) else (lambda b: shift)
    for b0 in range(0, last):
        sc = sum(sim(sty[i], bar_sig(song_chan_notes, (b0+i)*bar_song, bar_song, ppq_m, sh(b0+i), drums)) for i in range(nb)) / nb
        if sc > best[0]: best = (sc, b0, nb)
    return best

def main():
    song, sty = sys.argv[1], sys.argv[2]
    shift = int(sys.argv[sys.argv.index('--shift')+1]) if '--shift' in sys.argv else 0
    bassi = int(sys.argv[sys.argv.index('--bass')+1]) if '--bass' in sys.argv else None  # song MTrk index of bass -> per-bar -root shift
    ppq_m, mt = load(song); ppq_s, st = load(sty)
    ts, _, _ = meta_info(mt); tss, _, _ = meta_info(st)
    bar_m = ppq_m * 4 * ts[0] // ts[1]; bar_s = ppq_s * 4 * tss[0] // tss[1]
    mtr = []
    for ti, ev in enumerate(mt):
        by = collections.defaultdict(list)
        for n in notes_of(ev): by[n[2]].append(n)
        for ch, ns in by.items(): mtr.append((f"T{ti}:{track_names(ev)[:12]}/ch{ch+1}", ch == 9, ns))
    if bassi is not None:
        bn = notes_of(mt[bassi]); nbars = max(n[1] for n in bn) // bar_m + 1
        shift = [(-r) % 12 for r in bar_roots(bn, bar_m, nbars)]
    sn = [n for ev in st for n in notes_of(ev)]
    for name, a, b in sections(st):
        for ch in range(8, 16):
            ns = [n for n in sn if n[2] == ch and a <= n[0] < b]
            if not ns: continue
            res = [(match_section(ns, a, b, bar_s, m, bar_m, ppq_s, ppq_m, shift, d), lab) for lab, d, m in mtr if d == (ch in (8, 9))]
            (sc, b0, nb), lab = max(res, key=lambda r: r[0][0])
            print(f"{name:11} ch{ch+1:2} -> {lab:28} bars {b0+1}-{b0+nb} score {sc:.2f}")

if __name__ == '__main__':
    main()
