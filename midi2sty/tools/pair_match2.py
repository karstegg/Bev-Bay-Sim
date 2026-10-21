"""Song-MIDI <-> Yamaha style pair matcher (analysis helper; reads files, writes nothing).
Usage: python -I pair_match2.py song.mid style.sty [shift]
Robust parser: ignores MTrk length (walks to End-Of-Track), handles multi-track SMF.
"""
import sys, collections

def vlq(d, i):
    v = 0
    while True:
        b = d[i]; i += 1; v = (v << 7) | (b & 0x7f)
        if not b & 0x80: return v, i

def parse(path):
    """-> dict(ppq, tracks=[{name, notes:{ch:[(start,end,pitch,vel)]}, progs:{ch:prog}, markers:[(t,txt)], ts, bpm, eot}])"""
    d = open(path, 'rb').read()
    ppq = int.from_bytes(d[12:14], 'big'); i = 14; tracks = []
    while d[i:i+4] == b'MTrk':
        i += 8; t = 0; st = 0; tr = dict(name='', notes=collections.defaultdict(list), progs={}, markers=[], ts=None, bpm=None)
        on = {}
        while True:
            dt, i = vlq(d, i); t += dt; s = d[i]
            if s == 0xff:
                mt = d[i+1]; n, j = vlq(d, i+2); body = d[j:j+n]; i = j+n
                if mt == 3 and not tr['name']: tr['name'] = body.decode('latin1').strip('\0 ')
                elif mt == 6: tr['markers'].append((t, body.decode('latin1')))
                elif mt == 0x58 and not tr['ts']: tr['ts'] = (body[0], 2**body[1])
                elif mt == 0x51 and not tr['bpm']: tr['bpm'] = 60e6/int.from_bytes(body, 'big')
                if mt == 0x2f: break
            elif s in (0xf0, 0xf7):
                n, j = vlq(d, i+1); i = j+n
            else:
                if s & 0x80: st = s; i += 1
                k = 1 if st >> 4 in (0xc, 0xd) else 2
                a = d[i]; b = d[i+1] if k == 2 else 0; i += k
                ch = st & 15; ty = st >> 4
                if ty == 0xc: tr['progs'].setdefault(ch, a)
                elif ty == 9 and b > 0: on[(ch, a)] = (t, b)
                elif ty == 8 or (ty == 9 and b == 0):
                    if (ch, a) in on:
                        t0, v = on.pop((ch, a)); tr['notes'][ch].append((t0, t, a, v))
        tr['eot'] = t; tracks.append(tr)
        # next chunk: EOT-based (style files with wrong MTrk length)
    return dict(ppq=ppq, tracks=tracks, raw=d, end=i)

def sections(tr):
    m = [(t, n) for t, n in tr['markers'] if n not in ('SFF1', 'SFF2', 'SInt')]
    return [(n, t, (m[k+1][0] if k+1 < len(m) else tr['eot'])) for k, (t, n) in enumerate(m)]

FOLD = {3: 4, 10: 11, 8: 7}   # chord-quality folding: m3->M3, b7->M7, b6->5 (style is written over CMaj7)

def bar_roots(song, bass_idx, sbar, offset=0):
    """root pitch-class per song bar from the bass track: duration-weighted, 3x weight for notes on the downbeat."""
    tr = song['tracks'][bass_idx]; w = collections.defaultdict(lambda: [0.0]*12)
    for ch, ns in tr['notes'].items():
        for s, e, p, v in ns:
            s -= offset
            if s < 0: continue
            b, r = divmod(s, sbar)
            w[b][p % 12] += (e-s) * (3 if r < sbar//8 else 1)
    roots = {b: max(range(12), key=lambda k: x[k]) for b, x in w.items()}
    last = 0
    for b in range(max(roots)+1 if roots else 0):
        if b in roots: last = roots[b]
        else: roots[b] = last
    return roots

def per_bar(notes, ppq, bar, drums, shift=0, offset=0, roots=None, mode='pc'):
    """{bar: Counter{(16th slot, pc|pitch)}} ; offset in ticks removed from starts."""
    out = collections.defaultdict(collections.Counter)
    for s, e, p, v in notes:
        s -= offset
        if s < 0: continue
        b, r = divmod(s, bar)
        if drums: k = p
        elif roots is not None: k = FOLD.get((p - roots.get(b, 0)) % 12, (p - roots.get(b, 0)) % 12)
        else: k = (p+shift) % 12
        out[b][(round(r / (ppq/4)), 0 if mode == 'rhythm' else k)] += 1
    return out

def sim(a, b):
    if not a and not b: return 1.0
    ks = set(a) | set(b)
    return sum(min(a[k], b[k]) for k in ks) / sum(max(a[k], b[k]) for k in ks)

def match(song, style, shift, topn=3, song_off=0, only=None, bass_idx=None, mode='pc'):
    """For each (style section, style ch 8..15): best (score, song track idx, song ch, start bar, nbars).
    Score = mean per-bar weighted-Jaccard of (16th slot, pitch-class) after +shift on song pitches."""
    sp, yp = song['ppq'], style['ppq']
    ytr = style['tracks'][0]; ts = ytr['ts'] or (4, 4)
    ybar = yp*4*ts[0]//ts[1]; sbar = sp*4*ts[0]//ts[1]
    cache = {}
    roots = bar_roots(song, bass_idx, sbar, song_off) if bass_idx is not None else None
    for ti, tr in enumerate(song['tracks']):
        for sch, sn in tr['notes'].items():
            cache[(ti, sch)] = per_bar(sn, sp, sbar, sch == 9, shift, song_off, roots, mode)
    nb = max(tr['eot'] for tr in song['tracks']) // sbar + 1
    res = {}; means = match.means = {}
    for name, a, b in sections(ytr):
        if only and name not in only: continue
        nbars = max(1, round((b-a)/ybar))
        for ch in range(8, 16):
            sec = [(s-a, e-a, p, v) for s, e, p, v in ytr['notes'].get(ch, []) if a <= s < b]
            if not sec: continue
            drums = ch in (8, 9)
            Y = per_bar(sec, yp, ybar, drums, 0, 0, {i: 0 for i in range(nbars)} if roots is not None else None, mode)
            best = []
            for (ti, sch), C in cache.items():
                if drums != (sch == 9): continue
                for b0 in range(0, nb-nbars+1):
                    sc = sum(sim(Y.get(i, collections.Counter()), C.get(b0+i, collections.Counter())) for i in range(nbars)) / nbars
                    best.append((sc, ti, sch, b0, nbars))
            best.sort(reverse=True)
            res[(name, ch)] = best[:topn]
            means[(name, ch)] = sum(x[0] for x in best) / max(1, len(best))
    return res

def fmt(song, v):
    return [(round(s, 2), song['tracks'][t]['name'] or ('trk%d' % t), c+1, b, n) for s, t, c, b, n in v]

if __name__ == '__main__':
    song = parse(sys.argv[1]); sty = parse(sys.argv[2]); shift = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    for k, v in match(song, sty, shift).items():
        print(k[0], 'ch', k[1]+1, fmt(song, v[:2]))
