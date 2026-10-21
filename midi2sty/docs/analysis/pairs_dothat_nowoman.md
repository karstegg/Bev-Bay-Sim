# Song MIDI -> style: pairs DOTHATTO / DoThatToMeOne and NOWOMAN / NoWoman.T014

Method: `tools/pair_match2.py` (EOT-based parser; per-bar weighted-Jaccard of (16th slot, pitch|pitch-class) sets; `xmatch` = exact pitch with fixed semitone shifts; `match(..., bass_idx=)` = chord-relative pitch classes, each song bar re-rooted on its bass root and m3/b7/b6 folded to M3/M7/5).
Baseline: a random song bar scores 0.05-0.15 (pc) / 0.15-0.30 (rhythm only) against a style bar. Scores below ~0.5 on sparse bars (PAD, 3-note stabs) are chance. All bar numbers are 0-based song bars; style files are PPQ 1920 (bar 7680), 4/4.

## 0. Facts common to both styles
- Section order in file: Main A-D, Fill AA/BB/CC/DD, Intro A/B/C, Ending A/B/C, Fill BA. Lengths (bars): Main 4, Fill 1, Intro A 1, Ending A 2 (both). DoThat: Intro B 2, Intro C 8, Ending B 3, Ending C 14. NoWoman: Intro B 4, Intro C 5, Ending B 4, Ending C 5.
- Tempo: style = song minus ~3 BPM (93->90, 78->75). Time sig 4/4 both.
- CASM (read from file): DoThat has one table for Main/Fill/Intro A-B/Ending A-B and a separate table for Intro C + Ending C with NTT=Bypass on every channel (notes are literal, no chord conversion). NoWoman: one table for Main+Fills, one for all Intro/Ending.
- Style chord-part pitch content is almost only chord tones of CMaj7: DoThat BASS pcs C48% G32% E7%; CHD1 C32 G25 E23; PAD C31 G26 E26. NoWoman BASS G37 C32 B10 E8; CHD E/G/B (Em7 voicing of C) 18-26% each; no D/F/A beyond ~5%. Voicings are Cmaj7 shells (e.g. E3 G3 B3, C4 E4 G4).
- Main A-D, fills and Intro A/B, Ending A/B are written on ONE chord (C), not on the song's progression. Only DoThat Intro C/Ending C contain literal progressions.

## 1. Pair 1: DOTHATTO.mid <-> DoThatToMeOne.sty
### (a) Key / transposition
- Song: A major for bars 4-39 (bass roots A F# D E, repeated), modulates up a whole tone to B major from bar 40 (B G# E F#), ends on B (bar 80). Bars 0-2 root C (count-in/riff). Krumhansl on pitch-class mass says B major (misleading, B part is longer).
- Style source CMaj7. Transposition to source: +3 semitones for A sections, +1 for B sections. Exact-pitch evidence: Intro C lead = song pitches +3 (see (e)). Octave is kept for chord/lead parts (shift +3, not +3-12). BASS is dropped one more octave (song A1 33 -> style C1 24: net -9; style bass range 24-41 vs song 28-47).
### (c) Song tracks (13 SMF tracks)
| trk | name | ch/prog | n | median | notes/active bar | poly | lyric-onset hit |
|---|---|---|---|---|---|---|---|
| 11 | Melody | ch9 prog65 (alto sax) | 206 | 73 | 3.8 | 0.00 | 1.00 |
| 5 | Startheme | ch3 prog26 | 179 | 62 | 2.6 | 0.00 | 0.15 (intro hook, reused in outro) |
| 6 | Bass | ch4 prog33 | 306 | 38 | 3.9 | 0.00 | 0.48 |
| 7 | Guitar | ch5 prog25 | 497 | 61 | 6.1 | 0.24 | 0.60 (rhythm) |
| 8 | Violin | ch6 prog49 | 94 | 71 | 4.3 | 0.00 | 0.03 (bars 42-80 counter-line) |
| 9 | Piano | ch7 prog3 | 430 | 69 | 5.3 | 0.60 | 0.22 |
| 10 | Guitar 2 | ch8 prog24 | 18 | 68 | 2.6 | 0 | 0.02 |
| 12 | Drums | ch10 | 896 | | | | |
- NOT used: Melody (the lyric track: name "Melody", monophonic, 100% of the 186 Words-track syllables land on its onsets, register 63-80), Violin, Guitar 2. The Melody track never wins any section/channel above chance (best 0.41 on one Intro C channel, rhythm-coincidence).
- Used: Startheme (exact, Intro C), Bass (rhythm skeleton + roots), Drums (hat grid), Piano/Guitar chord roots (via the Intro C progression only).
### (b) Section x channel -> source
| section | RHY1 | RHY2 | BASS | CHD1 | CHD2 | PAD | PHR1 | PHR2 |
|---|---|---|---|---|---|---|---|---|
| Main A | new | new kit (hat 8ths like song) | new 1-5-1 on C, song-bass rhythm family | new | silent | new whole-note C | silent | silent |
| Main B | = Main A (28 vs 20 notes) | ~Main A (0.72) | = Main A exactly (1.00) | = Main A (1.00) | new (22 n) | = | silent | silent |
| Main C | 4 notes, new | 0.83 of A | 0.68 of A | 0.33 of A | 22 n | = | 126 n new | silent |
| Main D | new | 0.14 of A | 0.19 of A | = Main C (1.00) | 94 n | = | 96 n (0.76 of C) | silent |
| Intro A | drums only (1 bar, 8+14 hits) | | | | | | | |
| Intro B | 2 bars: bar 0 = bass C + chord whole note + CHD2 8ths; bar 1 = Main-A bar | | | | | | | |
| Intro C | song bars 0-7 | | song Bass roots 4-7 (C Am F G) | rewritten | **Startheme bars 0-3 x2** | chords C Am F G | **Startheme** (same as CHD2) | new |
| Ending A/B | = Main A bar 0 pattern, then 1 last bar | | | | | | | |
| Ending C | generic vamp (see (e)) | | | | | | | |
- RHY1 (percussion kit: 37,76,64,63,75,62,77) and RHY2 (kit 36,42,51,44,40,46,49) share only 37/62-64 and the 42/44 hat grid with the song drum track. The song drum track has no kick or snare (pitches 37-62: pedal hat, sidestick, ride, bongos); style RHY2 adds kick 36 (0,6,8,14) and snare 40 (4,12). Best per-bar drum match 0.38-0.44 (baseline 0.37): treat as NEW.
- BASS rhythm family: slot histogram song bass 0:25% 6:23% 8:14% 10:9% 12:17% 14:8%; style Main 0:19 6:19 8:19 12:14 14:19 (+11:7). Weak-to-moderate (rhythm Jaccard best 0.69-0.82 vs mean 0.25-0.29). Bass is 1-5-1 on C (C/G/E only), the song's bass movement is not copied.
### (d) Fills vs preceding Main bar (last bar of Main X)
- Fill AA/BB: BASS and CHD1/CHD2 shift by 1 note, PAD identical, RHY2 hit count about the same (13/13, 11/12) but hats thin out (9->7) and a crash 49 (+ ride 51 at 0) is added just before the bar end (slot 15.5-16). BASS onset set differs (7->6 notes).
- Fill CC/DD: PHR1 identical to the Main bar (0.97/1.00), CHD2 0.96 (DD), new tom/crash pitches {41,44,45,48,49,57}, CHD1 gets MORE notes (5->11), BASS unchanged length (4-5).
- Fill BA: sparse (RHY2 11, BASS 1 note, CHD1 3 notes): a stop/turnaround fill. AA/BB fills are near-clones (BASS, CHD1, PHR1, PAD sim 1.00, RHY2 0.79) -> fill = main-bar copy + drum change.
### (e) Intro / Ending
- **Intro C = song intro bars 0-7** (lyrics start bar 8, first syllable at 6144 ticks = bar 8.0): CHD2 and PHR1 contain Startheme bars 0-3 exactly, repeated twice, pitches +3, same octave, same onsets (per-bar similarity 0.71, 0.50, 0.29(bar 2 differs by one dropped note), 1.00 for bars 0-3; 8-bar mean 0.91 for both channels at shift +3 vs 0.2-0.3 for any other shift). Bass bars 4-7 follow song bass roots A F# D E -> C A F G with octave -1. PAD = the progression as whole-note chords (C, Am/C, F/C, G/B). Intro C has no chord conversion (NTT bypass), which is why it can carry a progression.
- Intro B (2 bars): Main-A-like content (bass pattern from Main A, 0.64 pc similarity to Startheme/Bass-bar coincidences only) -> generic.
- Intro A: 1 bar of drums = same hat/kick as Ending A bar 0 (RHY1 sim 1.00, RHY2 0.80).
- Ending A/B: bar 0 = Main A bar 0 (bass, CHD1, PAD, drums all = Main A bar 0 for A; B changes bass to C - C - G A G); last bar = bass whole-note C (4 beats), CHD1/PAD whole-note chord at slot 0, RHY2 2 hits (kick + crash) at slot 0. Final-bar rule: all melodic channels hold one chord/root for 4 beats.
- Ending C (14 bars): 2-bar loop repeated 7 times (C-G / C-G with E2/F2 fills) with C and F 8th-note stabs in CHD1 (C4 E4 G4 / C4 F4 A4); NOT from song (best per-bar 0.2-0.5). The song's last 14 bars (68-81) are in B (shift +1) - no correspondence. Last bar (13) is empty/tail. Generic.

## 2. Pair 2: NOWOMAN.mid <-> NoWoman.T014.STY
### (a) Key / transposition
- Song in C# major (bass roots C# G# A#m F# = I V vi IV, 4-bar loop; 112 bars, no modulation). Transposition to source: -1 semitone for pitched chord parts in the exact copies. Intro C/Ending C copies are exact at -13 (one semitone down and one octave down). BASS roots match at -1 (no octave change: bass register song 29-49 vs style 24-43).
- Song ppq 384; style 1920; style tempo 75 vs song 78.
### (c) Song tracks (10 SMF tracks)
| trk | ch/prog | n | median | notes/active bar | poly | lyric hit | role |
|---|---|---|---|---|---|---|---|
| 3 | ch1 prog18 (rock organ) | 551 | 75 | 8.2 | 0.76 | 0.19 | chords/organ, USED |
| 4 | ch2 prog35 (fretless) | 493 | 36 | 4.4 | 0.02 | 0.39 | bass, USED (roots) |
| 5 | ch3 prog17 | 610 | 75 | 10.9 | 0.56 | 0.30 | organ pad, from bar 18, weak |
| 6 | ch4 prog24 (nylon gtr) | 423 | 65 | 5.0 | 0.01 | 0.93 | **MELODY, NOT USED** |
| 7 | ch6 prog26 (steel gtr) | 959 | 56 | 9.3 | 0.65 | 0.52 | strumming rhythm gtr, not matched |
| 8 | ch7 prog26 | 83 | 68 | 8.3 | 0.22 | 0.00 | solo fragment bars 73-82, NOT USED |
| 9 | ch10 | 3177 | 42 | | | | drums, USED (RHY2) |
- Melody = the monophonic track (poly 0.01) whose onsets hit 93% of the 549 lyric syllables; it never matches any style channel above chance (best 0.29, Fill In BB/CC). Track 8 (short solo) also unmatched.
### (b) Section x channel -> source
| section | RHY1 | RHY2 | BASS | CHD1 | CHD2 | PAD | PHR1 | PHR2 |
|---|---|---|---|---|---|---|---|---|
| Main A | percussion (54 tamb, 82 shaker, 70 maracas) = song cabasa 69 (2,6,10,14) re-voiced (weak) | **song drum bars 3-4** (kick 35 at 4,12, stick 37 at 4,12, hat 42 16ths): 0.68 vs mean 0.48 | new (C/G/E, 6 notes/bar) | new Em7 shell | new | new | new | silent |
| Main B | 95 notes | 0.46 | new | silent | new | new | new | new (35 n) |
| Main C | 158 notes | 0.39 | new | new | new | new | new | new |
| Main D | **= Main C** (1.00 on RHY1, RHY2, CHD2, PAD, PHR1, PHR2) | | 28 vs 24 bass notes | | | | | |
| Intro B (4 bars) | | generic | roots follow song bass (exact pitch -1: 0.52 mean) | **song trk3 bars 2-5, shift -13** (0.78) | | | | trk3 (0.64) |
| Intro C (5 bars) | | generic | song bass roots (0.50) | **song trk3 bars 5-9, shift -13** (0.74-0.84, 5/5 bars >=0.6) | | | | trk3 (0.60) |
| Ending A (2) | | | | | | trk3 -13 (0.62) | | trk3 -13 (0.71) |
| Ending B (4) | | | | | | | | trk5 -1 (0.85, 2/3 bars) |
| Ending C (5) | | | | **song trk3 bars 110-112, -13 (0.84)** | | | | |
- Every style channel 8-16 is populated in every Main (full band written for all four mains), unlike DoThat.
### (d) Fills vs preceding Main bar
- Fill AA: RHY1 identical (1.00 sim, 14 notes), CHD2 and PHR1 identical onsets (1.00); RHY2 0.65 (17->21 hits, beat-4 hits 6->9, new pitches 40 snare, 43 tom, 55, 66); BASS changes (0.20, 6->6 notes); CHD1 doubles (5->10 notes).
- Fill BB: beat-4 hits unchanged (6->6), CHD1 0 -> 9 notes (Main B has no CHD1), PHR2 stays Main-B-like.
- Fill CC = Fill DD (RHY1, RHY2, CHD2, PHR1, PHR2 all 1.00): beat-4 hits 6->11, crash 57 at the very end (slot 16). Fill BA = Fill AA on RHY2/CHD2/PHR2 (1.00).
- Rule: fill keeps all pitched channels' onsets (CHD2/PHR1 identical) and only rewrites drums (+3..+5 hits in beats 3-4, toms/crash) and bass/CHD1 on the last beat.
### (e) Intro / Ending
- Intro B/C = song intro: trk3 (organ chords) bars 2-5 for B, bars 5-9 for C (shift -13); Main begins at bar 10 which is the song's first vocal bar (first lyric 15132 ticks = bar 9.85, "No woman" bar 10.5). So the two intro lengths are the 4/5 song bars just before the vocal, taken from different offsets. BASS roots exact at -1.
- Intro A: 1 bar, only RHY2 quarters (0,4,8,12,16) + RHY1 1 hit + PAD chord at the end (count-in); no bass.
- Ending A (2 bars): PAD and PHR2 = trk3 final-area chords at -13 (0.62/0.71); last bar contains only RHY1 hit + CHD1 3-note chord at the bar end (slot ~16 of the previous bar = anticipated final chord).
- Ending B/C = organ trk3 bars 108-112 (CHD1, 0.84 for C) plus generic drums/bass.

## 3. Cross-pair generalisation (also checked on Nikita: Intro C bass/CHD1/PAD matched song bars 1-4 at 0.87/0.90/1.00)
## 4. Rules, confident
1. Intro C (long intro, NTT=Bypass when it carries a progression) = song intro bars before the first vocal syllable, copied literally with transposition to C (shift = (0 - song tonic) mod 12; octave kept for CHD/PHR, bass -12 for DoThat). Exact pitch/onset (>=0.9 on 8/8 bars DoThat).
2. The song track(s) that carry the intro hook / organ chords are copied (Startheme -> CHD2+PHR1 identical; organ trk3 -> CHD1/PHR2, shift -13).
3. Melody/vocal track (monophonic, lyric-onset hit >=0.9, named "Melody" or nylon-guitar lead) is NOT used anywhere. Detect: monophonic + >0.9 of Words-track syllable onsets land on its note-ons.
4. Main/Fill/Intro A,B/Ending A,B pitched parts are authored on one chord (C): chord tones only (C,E,G,B), 3-note shells, bass 1-5-1 with 3rd on pickup beats. Song chord changes do not appear.
5. Main D (NoWoman) = Main C verbatim; Fill CC=DD, Fill AA~BA. Main B vs A (DoThat): BASS/CHD1/PAD identical, CHD2 added. Density rises A->D: DoThat note totals RHY2 45,44,54,62; CHD2 0,22,22,94; PHR1 0,0,126,96.
6. Last bar of Ending A/B (DoThat) = one root + one chord, 4 beats, kick+crash at slot 0; Ending C 14 bars = 2-bar vamp x7.
7. Fill = preceding Main bar for CHD2/PHR1/PAD (identical onsets) with drums rewritten (more hits in beat 4, tom/crash) and bass/CHD1 altered on the last beat; Fill BA is a sparse stop version.
8. Style tempo = song tempo - 3 BPM (both pairs).
## 5. Rules, weak
- BASS rhythm skeleton from song bass verse (slots 0,6,8,12,14): moderate evidence.
- NoWoman RHY2 groove from song drum bars 3-4 (0.68 vs 0.48 baseline) and RHY1 re-voices song cabasa; DoThat drums mostly new (+kick/snare added to a kickless song).
- Intro B (NoWoman) from song bars 2-5 and Intro C from bars 5-9 with trk3 (the repetition of the 4-bar loop makes the exact bars ambiguous: bars 2-5 and 98-102 score within 0.05).
- Ending C CHD1 (NoWoman) from song bars 108-112; Ending A/B parts partly from trk3 (0.5-0.7, few notes).
- Main-section CHD/PAD/PHR vs song piano/guitar: chance level (exact-pitch best 0.13-0.29), consider new.
## 6. Other song files (no matching style in ref/)
- Michael_McDonald_-_I_Keep_Forgetting.mid: 8 tracks, 60 bars, 96 bpm: BASS GUITA(prog37), CLAVINET (bars17-24 only), STRINGS, CHIMES, drums, 2x PIANO identical; no named melody track (voice likely in piano/strings).
- SACRIFIC.mid: 136 bars, 113 bpm, 'Melody' ch1 prog11 mono, Drum, Bass, Keyboard, Guitar, 'Back Figure'(ch5 prog82, 21 n/bar, bars 51-100), Pad (poly 0.92), Fantasy, Strings(4 notes).
- HAVERAIN.mid: 77 bars, 116 bpm, 18 tracks unnamed, drums split over 9 single-pitch tracks (36,38,42,49,51,46,48,45,41).
- EVBRTK.mid: 111 bars, 115 bpm: Muted Guitar (lead riff), Fret Noise, Fretless Bass, Strings, Distortion Gtr (bars 40-48), Piano, Drums; no vocal track.
- Style pairs that do exist in ref/: NIKITA.mid <-> EltonJohn_nikita.sty (see pairs_nikita_rocket.md); none for the four above.
