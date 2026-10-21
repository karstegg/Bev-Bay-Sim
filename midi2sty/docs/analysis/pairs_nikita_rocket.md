# Pair analysis: NIKITA.mid -> EltonJohn_nikita.sty, ROCKET.mid -> 70sGlamPiano.T609.prs

Reference data (user's own files) was only read; nothing copied here. Helper: `tools/pair_match.py`
(EOT-based SMF parser, per-bar pitch-class + onset-grid similarity; `--bass N` transposes each song bar by minus its bass root).
Style bar numbers below are 1-based within each section; song bars 1-based (MTrk idx in brackets). Style ch numbers are 1-based
(9 RHY1, 10 RHY2, 11 BASS, 12 CHD1, 13 CHD2, 14 PAD, 15 PHR1, 16 PHR2).

## Verdicts
- NIKITA style = hand-made by a third-party arranger FROM the song (voices, groove motifs, bass motif reused), but re-composed, not copied.
- ROCKET .prs = generic Yamaha factory preset (T609). No track/bar/shift consistently matches (best non-trivial score <= 0.58, random shifts; see below).

## Pair 1: Nikita (song ppq 192, 84 bpm, G major, 122 bars; style ppq 96, 89 bpm)
Style CASM channel names: add-drum, main-dru, Bass, epiano, clean, Pad, strg, mutegtr; all Ctab source CMaj7 (root 0, type 2).
Section order in file (non-factory): Main A, Fill AA, Intro A, Ending A, Main B, Fill BB, Fill BA, Intro B, Ending B, Main C, Fill CC, Intro C(4), Ending C(5), Main D, Fill DD. Mains = 4 bars; Intro A 1, B 1, C 4; Ending A 1, B 2, C 5.

(a) Key. Song is G major (bass pc G 31%, D, C). Style is chord-relative CMaj7. Best evidence is NOT a global +5: the bass matches song
C-chord bars with shift 0 (21 of 24 bar hits >= 0.6 have shift 0; style "C1 . C1 . G1 A1" = song bass [5] bars 4, 7, 8, 15, 23 "C2 . C2 . G1 A1", the G1/A1 pickups at beats 3.5/3.75 identical pitch+onset, only octave C2->C1).
So rule: style C-source = song chord-C bars (IV of G); a per-chord transposition of -(chord root) is equivalent. CHD/PAD shell E-G-B (Cmaj7 without root) is a re-voicing (song voices C-E-G triad), not a transposition of song notes. Tempo 84 -> 89 (not preserved).
(b) Source mapping (confident = exact onset+pitch evidence):
- BASS (ch11, prog 33 = song Bass [5] prog 33): Main A-D bars 1-4 = song bass bar 7 (and 4) pattern, 0.60-0.80 Jaccard, onsets {0, 2(+1.75 syncopation added), 3.5, 3.75}; Main A/B bar1 lacks the pickup. Ending final bar = single whole root; song bar 122 is also a single whole root (G1) (J=1.0). Fill bass = a busy 10-note lick (new, also reused in Ending C bar 1 an octave higher; shape resembles song bass bars 95/99/101).
- RHY2 (ch10 main-dru): groove = song drum [4] bar 2 (first groove bar), lane map kick 35->36, snare 38->40, hat 42->42, claves 75->76 (claves pattern 2,6,10,13,15 identical, J=1.00); kick/snare got extra syncopation (kick at 0,7,8 vs song 0,8; snare 4,9,12 vs 4,12), 16th hats thinned. Song cymbal 57 on beat 1 of bar 2 / last bar -> style Ending last bar kick+crash (49).
- RHY1 (ch9 add-drum, notes 54,64,62,39: tambourine/conga) = generic/new; song has no such lanes.
- CHD1 (ch12 epiano prog 5 = song Keyboard [6] prog 5): voices shared; rhythm "whole chord at 0 + stab near 3-3.25" ~ song Keyboard bar 7 (chord at 0 + stab at 3.5). Pitches re-voiced (E-G-B). Medium.
- CHD2 (ch13 clean, prog 27 = song Guitar [7] prog 27): voice shared, 9-onset pattern (0,1,1.75,2,2.5,2.75,3.25,3.5,3.75) NOT found in song (best onset J 0.75): new rhythm, G-B-E chord.
- PAD (ch14, prog 50 vs song Strings [8] prog 49): whole-bar G3 B3 E4 = song Strings/Keyboard whole-chord (pcs match 1.0 at shift +5 on bar 3, trivial 1-onset). Weak.
- PHR1 (ch15 strg 49) empty in Main A/B, 8 notes Main C/D; PHR2 (ch16 mutegtr prog 28, no song track with 28): doubles bass rhythm + G/C figure with same 3.5 G, 3.75 A pickup. Generic/derived from bass.
(c) Unused song tracks: Melody [3] flute prog 73 (mono, pitch 67-93, starts bar 6), Trumpet [9] prog 56 (mono, 69-91, first bar 77, 94 notes), Crystal [10] prog 98 (mono, 79-98), Choir 1/2 [11,12] prog 52 (sparse, enter bar 21/76). None of those programs occurs in the style (style progs 0,80,33,5,27,50,49,28). Used tracks are bass [5] (mono, 28-53), Keyboard [6] and Guitar [7] (chordal, onset polyphony 0.79 / 1.00), Strings [8] (chordal, 0.29), drums [4]. Rule: unused = monophonic OR registers >= MIDI 69 median / sparse entry late in song; used = low mono bass + chordal (onset polyphony >= 0.25) + drums.
(d) Fills (vs last bar of same-letter Main): CHD1, CHD2, PAD, PHR2, RHY1 identical (J=1.00, same velocities) for AA/BB/CC/DD; only RHY2 and BASS change. RHY2: J 0.59-0.79, new lanes toms 43/44/45/48 (more toms in DD: 43,44,45,48 at beats 3-4) + crash 49 at tick offset 0.997 bar (end of fill, vel 64) in every fill/Intro B/Ending B; BASS 7-10 notes vs 5 (J 0.07-0.33). Fill In BA is sparse (3 chd notes held, 18 drum notes, bass C1 + G1 A1 pickup), acts as break/ending-like bar.
(e) Intro/Ending: Intro A = 1 bar, only hats 44 on quarters + crash at end (generic, no song material; song intro bar 1 is empty, bass/chords start bar 2). Intro B = 1 bar drum fill. Intro C (4 bars) = Main C groove for drums (RHY1 J=1.00, RHY2 1.00 bars 1-3), but bass/CHD parts new (J 0-0.57) and source ranges clamped via Ctab note ranges. Ending C (5 bars) bars 1-3 ~ Intro C bars 1-3 (J 0.76/0.74/0.68), drums = Main D (0.93-1.0), bass lick higher; last bar single bass/chord hit + kick + 49. Ending B = [Fill In BB bar (J=1.00 all channels) + Ending A bar (J 0.92)]; Ending A = 1 bar: C1 whole, chord hits, kick 36 (copy of the song's last bar: whole root + kick + crash).

## Pair 2: Rocket Man (song ppq 384, 69 bpm, Bb; style ppq 1920, 69 bpm, standard factory section order and lengths: Main 4 bars, Fill 1, Intro A 1/B 4/C 4, Ending A 2/B 5/C 6, Fill BA last)
- Verdict generic: best BASS match by bar is 0.4-0.57 (only trivial 1-3 onset bars reach 1.0, with shifts 5 and 7 inconsistent); CHD1 <= 0.42, CHD2/PAD/PHR <= 0.5 with random shifts (0,2,4,7,9,11); drum lanes (ride 51, pedal hat 44, 33, 38) differ from song lanes (36,51,40); no song program (bass 35, gtr 25, piano 0, strings 49) appears in style (programs 17,0,1,52,2,3,88,91, with notes on 0-idx ch 1-7 that SFF1 styles do not use) ; the 69 bpm coincidence is just the song's tempo equals a typical rounded tempo.
- Used as generic template only: key if forced is Bb -> C = +2 (song pcs Bb 36%, Eb, C, D#). Unused tracks: n/a. Section structure rules useful as a generic template: Fill ends with crash(49)/57 alternating roll crescendo vel 15->70 over the last 0.25 bar (AA) or a single crash at 0.997 (DD, 49 vel 70); Intro C bars 1-3 ~ Ending C bars 1-3 (J 0.84-0.91, ch10 J 1.0), Intro B bars 1-4 = Main A parts (ch13-16 J 1.0, drums J 0.3), Ending B bars 1-3 ~ Main B (drums 0.71-0.77, bass .67).
- Fills: only drums + a few chord notes change; BB/CC/DD keep CHD2/PHR1 identical to the Main last bar (J 0.66-1.0).

## Confidence
Confident: Nikita voices reused (33/5/27); bass motif C-bar shift 0; claves lane 75->76 identical rhythm; drum kick/snare/hat reprogrammed from song bar 2 with added syncopation; fills = Main last bar with only RHY2/BASS altered + crash at 0.997; Ending B = Fill BB + Ending A; Ending last bar = whole root + kick + crash; Rocket preset is generic.
Weak: CHD/PAD pitch sources (re-voiced, shift +5 evidence only 1-onset bars); PHR1/PHR2; Intro A/B origin; Ending C bass lick source; unused-track rule is based on only two songs (candidate rule: drop tracks with monophonic + median >= 69 or late entry).
