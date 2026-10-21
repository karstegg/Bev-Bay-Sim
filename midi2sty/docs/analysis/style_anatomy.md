# Anatomy of a DGX-670 style (28 real files)

Source: 28 user-owned working styles (14 SFF1, 14 SFF2; 11 `.prs`, 17 `.sty/.STY`; 5 are DGX-native, 23 PSR-tutorial). The data are
NOT in the repo. Every number below is produced by `tools/style_stats.py` (`python3 -I tools/style_stats.py DATA_DIR --inventory X.xlsx`);
the appendix is its raw output. Roles are by DESTINATION channel: RHY1=ch9 ... PHR2=ch16. Notes recorded on "alt source" channels 1-8 are attributed
to the destination named in that section's table (see 5). Corpus: PPQ 1920 (26 files) / 96 (2), all 4/4, first tempo 60-139 bpm (median 95).
Canonical marker order in 26/28 files: `Main A-D, Fill In AA BB CC DD, Intro A B C, Ending A B C, Fill In BA`. All 15 sections are present in 28/28. Sections are
contiguous, whole bars, no gaps; the first one starts one bar after SInt (lead-in bar holds only setup, 0 notes); EOT = end of last section. The MTrk length field matched the
EOT-walked length in 28/28 of these files (the parser is EOT based anyway).

## Key findings

**1. Channels / density (table 1).** RHY2 (ch10) is the MAIN DRUM KIT (kick 35/36, snare 38/40, hat 42/44/46, ride 51, crash 49/57; 12-25 notes/bar, present in 93-100% of sections) and
RHY1 (ch9) is auxiliary PERCUSSION (tambourine 54: 29%, maracas 70: 21%, shaker 82: 12%, congas 62-64, cowbell 56). Table names confirm (`main-drum/dr/drs` on ch10, `add-drum/prc` on ch9).
Total notes/bar (sum over the 8 channels): Intro A ~11, Main A/B/C/D ~49/64/87/100, Fill AA/BB/CC/DD/BA ~61/78/99/109/56, Intro B ~59, Intro C ~104, Ending A ~14, B ~65, C ~94.
Channel presence rises A to D: BASS 93/96/100/100%, CHD1 96/93/100/100%, CHD2 57/93/96/100%, PAD 75/100/100/100%, PHR1 32/54/89/100%, PHR2 18/29/54/61%, RHY1 57/82/89/89%.
Intro A is always 1 bar and rhythm only (93% of files; RHY2 9.2 notes/bar). Lengths: Main 4 bars (23/28) or 2; Fills 1 bar (140/140); Intro B 2 bars x11 / 4 bars x10 (range 1-8); Intro C 8 bars x12 / 4 bars x8 (range 1-10);
Ending A 1 bar x13 / 2 bars x13; Ending B 2 bars x12 / 3 x7 (2-8); Ending C 2-14 bars (5/6/9 bars common).

**2. Fills.** Fill In X is NOT rhythm-only: only 1/140 fills has notes on ch9/10 only. Non-rhythm channels keep playing at Main density (CHD1 13.5 vs 13.4 notes/bar, PAD 4.5 vs 3.5, PHR1 7.1 vs 6.5); a channel
that plays in the Main drops out of the fill in <=4% of pairs. The fill bar is a variant of one of the Main's bars: median same-grid (1/8 beat) Jaccard with the best Main bar is 0.80-0.83 for CHD1/CHD2/PHR, 1.00 for PAD (64% identical), 0.59 for BASS; rhythm
channels differ (0.58). Drum changes Main -> Fill (notes/bar, rhythm channels): snare 2.1 -> 3.8, tom 0.36 -> 2.4, crash 0.05 -> 2.1, hat 6.8 -> 5.4, kick unchanged (2.7); RHY2 16.0 -> 20.1 notes/bar. Velocity: tom 61 -> 73, snare 83 -> 75, crash 67 -> 59, overall mean 64 -> 65.
**Fills end on a crash**: 132/140 fills have a crash (note 49 x177, 57 x88, 55 x20, 52 x10) within 1/8 beat of the section end, typically 20 ticks (1/96 beat @1920 PPQ; 1 tick @96 PPQ) before the end, i.e. a pickup that sounds on the next downbeat; 122/140 on RHY2, mean velocity 71 (18-124),
duration ~1/96 beat. Only 21/140 fills have a crash on their first beat and only 10/140 Mains contain any crash. Fill In BA (leads into A) is sparser than BB (56 vs 78 notes/bar).

**3. Intros / Endings (table 3).** Intro A: rhythm only, no bass/chords (4%), crash at the very end 82%. Intro B/C: bass 75/96%, chord channels (ch12-14) 86/96%, phrases 50/96%; ALL end with a crash 20 ticks before the end (96/100%), final-onset gap 0.01 beat,
pitched notes are held to within 1 beat of the end (86/96%), longest pitched note 4.0/4.5 beats (median); no tempo events, no overhang (100% of note-offs <= section end; 0 notes cross a section end; last note-off == EOT in 15/28 files).
Endings: the final hit is a big chord (median 15/14/10 simultaneous notes for A/B/C across bass+chords+drums) on a bar start (A 79%, B 54%, C 39%) a median 4.0 beats before the end, then it rings: last beat silent (no onset) in 93/96/82% of Endings A/B/C
(Intro: 0%); last pitched note-off within 1 beat of the end 71/61/57%; the crash coincides with the final hit in 29/57/43% (any crash in the ending 32/82/96%). Ritardando = tempo events inside the section: Ending A none; Ending B 9/28 and C 12/28 files
(median 8-9 steps over 2.0 / 3.6 beats starting 6.8 / 10.8 beats before the end, down to 0.56 / 0.67 of base tempo; steps are 1/4-1/2 beat apart, decreasing); SFF1 PSR-tutorial files also drop to 50 bpm at the last tick(s) of Ending A/B/C.

**4. Setup (table 4).** Layout: SFF1 = all setup events at tick 0; SFF2 = sysex/CC spread ~5 ticks apart over ticks 164-623 of the lead-in bar (XG-On `43 10 4C 00 00 7E 00` at tick 164 in the 14 SFF2 files, none in SFF1). Header order: timesig, tempo, [copyright 0x02 in 13/28], SFF1/SFF2 marker, 32-byte track name, 4 fixed sysex
(`43 76 1A 10 01 01 01 01 01 01 01 01` 27/28, `43 73 39 11 00 46 00` 28/28, two `43 73 01 51 05 00 {01|02} 08 00..` 26/28), `SInt`, GM reset `7E 7F 09 01`, then per channel CC7/10/91/93/94/71/74, bank MSB/LSB, program. Plus 20-40 XG sysex (`43 10 4C 02 01 ..` reverb/chorus/variation types, `43 10 4C 08 pp ..` part params, `43 10 4C 30 nn ..` drum-note params).
Per-role values (files / median): RHY1/2 bank MSB 127 (23/25, 28/28) LSB 0, program = kit (0, 80, 83 common), vol 67/75, reverb 24/23, chorus rare (5/3 files), pan not sent. BASS MSB 8 (19) or 0 (9), LSB 0/2/112+, program 17 (18 files) or 33, vol 65, reverb 0 in 25/28, chorus 6 files, pan 1 file.
CHD1/CHD2/PAD/PHR1/PHR2: vol 55/55/44/62/60, reverb 27/31/36/28/38, chorus 20/30/23/28/22 (in 15-18 of 28 files), pan sent in 18/21/6/22/18 files (median 52/49/76/72/53), variation CC94 in 6-13 files, MSB 0 (16) / 8 (10) / 104 (2), LSB 112-122 for DGX native voices.
Section starts: 12-17/28 files (more for Intro C / Ending B,C: 17-21) re-send channel CCs at each section start (vol, expr, bank, pc, pan - a mixer reset; identical values in every section of a file), 14 files never. Inside sections: CC11 expression (27k events, only in 8 files: ballad/DGX-native), pitch bend (5.9k), CC74/CC1.
No per-section volume scheme exists beyond that.

**5. CASM (tables in appendix).** SFF1 uses `Ctab` (27 B body; 31 B in a few with a 5-byte extra `02 00 18 xx yy`); `Cntt` only in 6/14 SFF1 files (8 have none). SFF2 uses `Ctb2` (47 B body, 14/14, NEVER Cntt):
byte map 0 src, 1-8 name, 9 dest, 10 editable (always 1), 11-12 note mute (0FFF in 98%), 13-17 chord mute, 18 src root (always 0), 19 src type (Maj7=2 in 79%, Maj=0 in 19%), 20-21 prefix (`00 7F` in 85%), then 3 six-byte groups (NTR, NTT, high key, low, high, RTR) at 22/28/34 (group 2 differs from group 1 in 25-61% of
non-rhythm tables = guitar/other chord-type variants; rhythm 0%), 7-byte tail at 40 (`00 00 00 00 00 00 00` / `...80 00 00` / `... 7F 00 00` / drum extra `00 01 00 18 31 xx 00`). In Ctb2 the NTT byte folds in Cntt: bass = `0x81`.
Grouping: 1-15 CSEGs per file (2 in 11/14 SFF1, 3-7 in SFF2), sections never repeated. Typical SFF2 split: `[Intro A, Main A-D, Fill AA-DD,BA, Ending A]`, `[Intro B, Ending B]`, `[Intro C, Ending C]`; typical SFF1: one big group (Main/Fills/Intro A/Ending A, often + Intro B/Ending B) + `[Intro C, Ending C]`. Tables per CSEG 8-16 (alt source channels 1-8 add extra tables mapping to the same dest in 11/14 SFF2 and 6/14 SFF1 files).
Modal values (value : share of tables):
- RHY1/RHY2 (all sections, both formats, 100%): NTR 1 (fixed), NTT 0, high key 6, low 00 high 7F, RTR 1, chord mute `07FFFFFFFF`, note mute `0FFF`.
- BASS Main/Fill: NTR 0, NTT 3 (SFF1) / 0x81 (SFF2), high key 3 (50%) / 8 (30%) / 11, low 0x1C (95%), high 7F, RTR 2 (SFF1 100%, SFF2 ~70%, else 4), chord mute `03FFFFFFFF`.
- CHD1/CHD2/PAD Main: NTR 1 + NTT 2 + RTR 1 (62% SFF1 / 51% SFF2 of tables), alternatives NTR 0/NTT 2, NTR 0/NTT 3 (bass-like), high key 7 (SFF1 26%, SFF2 40%; also 3-6, 8), low 0 / high 7F (a few PAD/PHR with a 0x32-0x40 window), chord mute `03FFFFFFFF`.
- PHR1/PHR2 Main: NTR 1/NTT 2 (SFF1 64 of 128 tables), NTR 0/NTT 3 (SFF1 44), NTR 0/NTT 1 melody only in SFF2 (19); high key 5-8.
- Intro A and Ending A tables == Main tables (same group in 11/14 files).
- Intro B/C and Ending B/C differ from Main in 100% of the non-rhythm roles (rhythm identical): share of non-rhythm tables with NTT 0 (bypass) = SFF1 53% (Intro) / 42% (Ending) vs 6% in Main; SFF2 88% / 89% vs 3%; NTR 0: 79%/73% (SFF1), 95% (SFF2); RTR 1: ~90-96%; bass in B/C mostly NTR 0/NTT 0/RTR 1 (SFF2: 36 of 48 tables) ; SFF2 chord mute `03FFF800FF` in 43-44% of B/C tables (0% in Main) - chord-type mute mask, plus high-key 8/7 spread.
- Cntt byte 1 (SFF1): rhythm 00; bass 81 (5/6 files) ; chord/pad/phrase 02 (mostly), 00, 05, 03.

**6. Pitch registers in source chord CMaj7 (ALL sections, role = destination, root removed).** BASS min 17, p5/p25/median/p75/p95 = 24/24/28/31/38 (Main/Fill: 24/24/24/31/36; file lowest 24, file highest median 36). CHD1 p5/p25/med/p75/p95 = 43/55/60/67/104 (Main/Fill 48/55/59/64/101);
CHD2 43/55/63/69/98; PAD 44/55/60/67/80 (Main/Fill 55/55/59/64/76, polyphony 3.0, notes 6 beats long); PHR1 48/55/62/67/98; PHR2 46/55/63/74/105. Per-file medians vary 48-79 (CHD), 51-73 (PAD), 48-81 (PHR). Chord-tone share (C E G B): BASS 79%, CHD 70-72%, PAD 75%, PHR 67-69%; C-major-scale share 88-93% (bass 93%): material is diatonic to C.
Polyphony (notes per onset, Main): BASS 1.04, CHD1 1.8, CHD2 2.2, PAD 3.0, PHR1 1.6, PHR2 2.5; mean note length (beats): bass 0.9, chords 1.3, PHR 2.0-2.1, PAD 6.0. Velocity median / p5 / p95: RHY1 53/20/99, RHY2 67/29/113, BASS 64/55/110, CHD 67-76/25-33/113-118, PAD 64/31/110, PHR 65-76/30-39/113-114 (note floor 1 for ghost notes).

**7. Other chunks (appendix table).** After the MTrk: `CASM` always (429-5014 B); `OTSc` in 27/28 (SFF1 5.6-8.5 KB, 8356 B typical = four `MTrk` bodies of 2081 B, one per One Touch Setting; SFF2 12.6-16.1 KB; each file's OTSc is unique, no two identical); absent in `Red_red_w.sty` (PPQ 96) which still loads;
`FNRc` x2 (323 / 1283 B, SFF1: Proud Mary, Sheriff Reggae; starts with sub-tag `FNRP`), `ASnc` x2 (13.8 / 16.3 KB, DGX-native: 70sGlamPiano, JazzPop; sub-tag `AsCm`), `Cmbi` x1 (861 B, 70sGlamPiano; sub-tags `CmMx/MainCmSy`). No `MH`, `MDB`, `AASM`, `AFil`. Order: CASM, OTSc, [ASnc], [Cmbi] / [FNRc]. File size 20-90 KB, MTrk 13-67 KB.

**8. DGX-native .prs vs PSR-tutorial .sty.** The extension carries no information (11 .prs = 5 DGX-native SFF2 + 5 tutorial SFF2 + 1 tutorial SFF1; .sty = 13 SFF1 + 4 SFF2); what matters is the SFF version. SFF1 (14 files): `SFF1` marker, Ctab (+optional Cntt), all setup at tick 0, no XG-On, 2 CSEGs typical, OTSc ~8.4 KB, median file 35 KB, 2 old files PPQ 96, 5-7 of 14 have alt-source tables.
SFF2 (14 files): `SFF2` marker, Ctb2, setup spread over the lead-in bar with an XG-On at tick 164, 3-7 CSEGs, OTSc ~15 KB, bigger CASM (1.9-4.4 KB vs 0.7-1.4 KB), median 50 KB, alt-source tables (Intro B/C/Ending B/C written on ch1-6 and mapped to ch10-15) in 11/14, 13 files carry `(C)20xx YAMAHA Corp.` text. DGX-native vs tutorial SFF2: structurally identical; native files differ only by ASnc/Cmbi chunks in 2/5,
slightly larger CASM (2.4 vs 2.6 KB: no real difference) and 179 vs 155 setup XG sysex in total (35 vs 31 per file). 

## Differences between `src/midi2sty/sty_writer.py` / mapper and the real files (fix list)

1. **Format mix is unseen**: writer emits `SFF2` marker + SFF1-style `Ctab`+`Cntt`. Real: SFF2 = `Ctb2` (47 B, no Cntt) 14/14; SFF1 = `Ctab` (Cntt in 6/14). 0/28 files combine SFF2 with Ctab. Fix: write `SFF1` (+Ctab, drop Cntt or keep: 8/14 SFF1 files have none) or implement Ctb2 per 5.
2. **Setup is too thin**: add the 4 fixed sysex before `SInt` (`43 76 1A 10 01 01 01 01 01 01 01 01`, `43 73 39 11 00 46 00`, 2x `43 73 01 51 05 00 01|02 08 00 00 00 00 00 00 00`), XG-On only for SFF2 and at tick 164; for SFF2 spread setup ~5 ticks apart inside the lead-in bar.
3. **Mix values**: ours CC7=100, CC10=64, no CC91/93/94. Real: vol RHY1 67 / RHY2 75 / BASS 65 / CHD 55 / PAD 44 / PHR 60-62; reverb 24/23/0/27-31/36/28-38; chorus 0 for rhythm+bass, 20-30 for chords/PAD/PHR; pan centre (unsent) for rhythm and bass, 50-75 for chords/PHR. Rhythm: bank MSB 127 LSB 0 (ours ok), bass bank MSB 8 or 0 program 17/33.
4. **Roles swapped**: mapper sends main drums to RHY1 and hats/shakers to RHY2; real: main kit on RHY2 (ch10), percussion/tambourine/shaker/conga on RHY1 (ch9).
5. **Section set/order/length**: writer default makes 10 sections (no Fill In BA, Intro B/C, Ending B/C), Intro A = 2 bars. Real: 15 sections always, Intro A = 1 bar (28/28), order Main A-D, Fills, Intro A-C, Ending A-C, Fill In BA; Intro B 2/4 bars, C 8/4, Ending A 1-2, B 2-3, C 5-9.
6. **Missing `fn:<Section>\0` text meta (0x01)** after every section marker (all 390 sections in 26/28 files; absent only in the two PPQ-96 files).
7. **No end-of-section crash**: add crash 49 (vel ~70, ~1/96 beat long) on RHY2 at end-20 ticks (@1920 PPQ) of every Fill (132/140), Intro A (82%), Intro B/C (96/100%); Fills must keep chord/bass/phrase channels (a Main-bar variant) and change drums (+snare, +toms 41-50 ~2.4/bar, -hat), not be rhythm-only.
8. **Endings**: final hit on a bar start (A 79%) a median 4 beats before the end, held (last pitched note-off within 1 beat of the end), last beat silent (93-96%); for Ending B/C ~1/3-1/2 of styles add a tempo ritardando (8-9 events, last 2-4 beats, to 0.56-0.67 of base tempo).
9. **Tables**: PHR roles use NTR0/NTT1(melody): real is NTR1/NTT2 (chord) or NTR0/NTT3. For Intro B/C and Ending B/C write the bypass table (non-rhythm NTT 0, NTR 0, RTR 1, bass RTR 1; SFF2 chord mute `03FFF800FF`) instead of the Main table; group CSEGs as `[Main*/Fill*/Intro A/Ending A]`, `[Intro B, Ending B]`, `[Intro C, Ending C]` (writer: one CSEG per section, 8 tables each). Bass high key 3 or 8, low 0x1C, RTR 2 (SFF1) are fine; chord/PAD high key 7 fine.
10. **No OTSc / one-touch chunk** (27/28 real files carry it; `Red_red_w` loads without). Optional: `(C)` text 0x02 meta (13/28).
11. Register rules for the mapper (CMaj7): BASS 24-38 (median 28; hard floor 17), CHD1/CHD2/PAD 48/55-67/69 (median 60; PAD 55-76), PHR 48-74 (median 62-63); fold anything outside p5-p95 by octaves.


---

# Appendix: raw output of tools/style_stats.py



### 1. Which channels carry notes, per section

cell = fraction of files with notes on that channel / mean notes per bar

| section | n | length (bars) x files | RHY1 | RHY2 | BASS | CHD1 | CHD2 | PAD | PHR1 | PHR2 | share via alt src ch1-8 (files / notes per bar) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Intro A | 28 | 1b x28 | 0.32 / 1.4 | 1.00 / 9.2 | 0.04 / 0.0 | 0.00 / 0.0 | 0.00 / 0.0 | 0.04 / 0.1 | 0.00 / 0.0 | 0.00 / 0.0 | 0.04 / 0.0 |
| Intro B | 28 | 1b x3, 2b x11, 3b x1, 4b x10, 5b x2, 8b x1 | 0.68 / 4.8 | 1.00 / 13.4 | 0.75 / 3.9 | 0.79 / 16.9 | 0.54 / 8.3 | 0.54 / 4.5 | 0.43 / 4.9 | 0.25 / 2.4 | 0.50 / 14.2 |
| Intro C | 28 | 1b x1, 2b x1, 4b x8, 5b x2, 6b x2, 8b x12, 9b x1, 10b x1 | 0.82 / 10.0 | 1.00 / 15.3 | 0.96 / 6.8 | 0.93 / 22.8 | 0.86 / 23.8 | 0.89 / 6.4 | 0.86 / 11.7 | 0.71 / 7.3 | 0.61 / 29.8 |
| Main A | 28 | 2b x5, 4b x23 | 0.57 / 3.7 | 0.93 / 12.2 | 0.93 / 4.1 | 0.96 / 13.5 | 0.57 / 7.4 | 0.75 / 2.1 | 0.32 / 3.0 | 0.18 / 2.8 | 0.50 / 3.6 |
| Main B | 28 | 2b x5, 4b x23 | 0.82 / 7.5 | 0.96 / 14.2 | 0.96 / 4.8 | 0.93 / 14.9 | 0.93 / 12.1 | 1.00 / 3.3 | 0.54 / 4.7 | 0.29 / 2.8 | 0.61 / 3.8 |
| Main C | 28 | 2b x4, 4b x24 | 0.89 / 10.6 | 0.96 / 17.2 | 1.00 / 5.5 | 1.00 / 16.4 | 0.96 / 19.3 | 1.00 / 4.1 | 0.89 / 9.1 | 0.54 / 4.6 | 0.61 / 5.3 |
| Main D | 28 | 2b x4, 4b x24 | 0.89 / 15.2 | 1.00 / 22.0 | 1.00 / 6.4 | 1.00 / 17.0 | 1.00 / 19.4 | 1.00 / 4.1 | 1.00 / 11.2 | 0.61 / 4.8 | 0.64 / 5.1 |
| Fill In AA | 28 | 1b x28 | 0.64 / 4.1 | 1.00 / 18.1 | 0.93 / 4.9 | 0.96 / 15.2 | 0.57 / 8.7 | 0.79 / 2.9 | 0.36 / 3.8 | 0.25 / 3.4 | 0.57 / 4.1 |
| Fill In BB | 28 | 1b x28 | 0.82 / 7.9 | 1.00 / 19.2 | 0.96 / 6.2 | 0.96 / 17.7 | 0.89 / 13.8 | 0.93 / 4.3 | 0.57 / 5.6 | 0.32 / 3.0 | 0.64 / 5.0 |
| Fill In CC | 28 | 1b x28 | 0.89 / 10.6 | 1.00 / 21.4 | 1.00 / 6.2 | 1.00 / 18.2 | 0.93 / 23.4 | 1.00 / 4.7 | 0.82 / 9.5 | 0.54 / 4.8 | 0.64 / 9.2 |
| Fill In DD | 28 | 1b x28 | 0.89 / 13.7 | 1.00 / 25.4 | 1.00 / 6.9 | 1.00 / 18.4 | 0.96 / 20.3 | 1.00 / 6.0 | 0.93 / 12.4 | 0.57 / 5.4 | 0.61 / 5.7 |
| Fill In BA | 28 | 1b x28 | 0.75 / 5.6 | 1.00 / 16.5 | 0.96 / 2.7 | 0.96 / 7.9 | 0.96 / 11.2 | 0.89 / 4.6 | 0.75 / 5.1 | 0.39 / 2.4 | 0.57 / 4.6 |
| Ending A | 28 | 1b x13, 2b x13, 4b x2 | 0.39 / 0.7 | 0.93 / 1.7 | 0.96 / 0.9 | 0.96 / 2.7 | 0.86 / 2.8 | 0.96 / 2.4 | 0.68 / 1.4 | 0.39 / 1.1 | 0.57 / 0.9 |
| Ending B | 28 | 1b x1, 2b x12, 3b x7, 4b x4, 5b x3, 8b x1 | 0.75 / 5.6 | 0.96 / 11.1 | 0.96 / 4.7 | 0.96 / 15.3 | 0.82 / 12.2 | 1.00 / 6.3 | 0.64 / 6.8 | 0.46 / 3.1 | 0.57 / 15.0 |
| Ending C | 28 | 2b x4, 3b x2, 4b x4, 5b x5, 6b x4, 8b x3, 9b x4, 10b x1, 14b x1 | 0.79 / 9.3 | 1.00 / 16.7 | 1.00 / 6.0 | 1.00 / 18.7 | 0.93 / 19.2 | 1.00 / 6.9 | 0.93 / 10.6 | 0.86 / 6.7 | 0.61 / 23.3 |

### 2. Fill In vs Main

fill/main pairs analysed: 140 (Fill In BA compared with Main B)

| channel | main notes/bar | fill notes/bar | pairs where channel drops out in fill | pairs where fill has notes but main none |
|---|---|---|---|---|
| RHY1 | 8.9 | 8.4 | 3% | 3% |
| RHY2 | 16.0 | 20.1 | 0% | 4% |
| BASS | 5.1 | 5.4 | 0% | 0% |
| CHD1 | 15.3 | 15.5 | 1% | 2% |
| CHD2 | 14.1 | 15.5 | 2% | 1% |
| PAD | 3.4 | 4.5 | 4% | 1% |
| PHR1 | 6.5 | 7.3 | 4% | 7% |
| PHR2 | 3.5 | 3.8 | 2% | 6% |

Rhythm channels (9+10) drum-class notes per bar:

| class | main | fill |
|---|---|---|
| kick | 2.74 | 2.71 |
| snare | 2.10 | 3.81 |
| tom | 0.36 | 2.38 |
| hat | 6.81 | 5.36 |
| crash | 0.05 | 2.11 |
| ride | 1.44 | 1.06 |
| perc | 10.27 | 9.69 |
| other | 1.11 | 1.39 |

Velocity (mean / min / max): fill rhythm: 65/1/127; main rhythm: 64/1/127; fill non-rhythm: 70/1/127; main non-rhythm: 71/1/127

Crash / ending behaviour (count of fill/main pairs): has crash=138, crash on first beat=21, crash in last beat=137, main has crash=10, last rhythm onset in last beat=140, last-onset note is crash=134

Crash at the very end of the fill bar (pickup that sounds on the next downbeat): fills with crash within 1/8 beat of section end=132/140, ... of which on RHY2 (ch10)=122/140, ... of which on RHY1 (ch9)=10/140; gap to section end in ticks@1920 PPQ: {20: 115, 8: 7, 16: 5, 164: 3}

Mean velocity by drum class (rhythm channels), main -> fill: kick: 86 -> 86; snare: 83 -> 75; tom: 61 -> 73; hat: 66 -> 64; crash: 67 -> 59; ride: 66 -> 70; perc: 52 -> 53; other: 77 -> 82

Non-rhythm channels in a fill: best same-grid (1/8 beat) Jaccard similarity of the fill bar with ANY bar of its Main (median / share >= 0.9): BASS 0.56 / 25%; CHD1 0.80 / 42%; CHD2 0.88 / 47%; PAD 1.00 / 67%; PHR1 0.75 / 44%; PHR2 0.69 / 45%

Fills where ONLY ch9/ch10 carry notes: 1/140 (1%)

### 3. Intro / Ending anatomy

| section | n | rhythm | bass | chord(11-13) | phrase | rhythm ONLY | crash any | crash 1st beat | crash last bar | final pitched note >=2 beats & ends at bar end | final pitched dur (beats) | mean gap last onset->end (beats) | last beat silent (no onset) | all note-offs <= end | notes overhanging end | tempo changes inside |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Intro A | 28 | 100% | 4% | 4% | 0% | 93% | 82% | 0% | 82% | 0% | 0.7 | 0.09 | 0% | 100% | 0 | 0 |
| Intro B | 28 | 100% | 75% | 86% | 50% | 14% | 100% | 14% | 100% | 21% | 1.6 | 0.01 | 0% | 100% | 0 | 0 |
| Intro C | 28 | 100% | 96% | 96% | 96% | 4% | 100% | 43% | 100% | 25% | 1.4 | 0.01 | 0% | 100% | 0 | 0 |
| Ending A | 28 | 100% | 96% | 100% | 75% | 0% | 32% | 32% | 18% | 50% | 5.4 | 5.60 | 93% | 100% | 0 | 0 |
| Ending B | 28 | 100% | 96% | 100% | 75% | 0% | 82% | 25% | 50% | 43% | 4.2 | 4.65 | 96% | 100% | 0 | 82 |
| Ending C | 28 | 100% | 100% | 100% | 100% | 0% | 96% | 61% | 43% | 32% | 4.8 | 4.23 | 82% | 100% | 0 | 181 |

Tails and ritardando:

| section | n | median beats from last onset to end | last onset on a bar start | notes in final hit (median) | final hit has crash | last pitched note-off within 1 beat of end | longest pitched note (beats, median) | tempo ramp (>=3 decreasing tempo events) | ramp steps | ramp length (beats) | ramp starts N beats before end | min tempo / base tempo |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Intro A | 28 | 0.0 | 0% | 1 | 82% | 7% | 0.7 | 0/28 | - | - | - | - |
| Intro B | 28 | 0.0 | 0% | 1 | 96% | 86% | 4.0 | 0/28 | - | - | - | - |
| Intro C | 28 | 0.0 | 0% | 1 | 100% | 96% | 4.5 | 0/28 | - | - | - | - |
| Ending A | 28 | 4.0 | 79% | 15 | 29% | 71% | 4.0 | 0/28 | - | - | - | - |
| Ending B | 28 | 4.0 | 54% | 14 | 57% | 61% | 4.0 | 9/28 | 8 | 2.0 | 6.8 | 0.56 |
| Ending C | 28 | 4.0 | 39% | 10 | 43% | 57% | 7.0 | 12/28 | 9 | 3.6 | 10.8 | 0.67 |

### 4. Setup events and section-start events

Setup layout: last setup event tick before first section (min/median/max over files, bar = 7680 ticks): SFF1: 0/0/0 (14/14 files entirely at tick 0); SFF2: 352/461.5/623 (0/14 files entirely at tick 0)

Setup = every event before the first section marker (tick 0 .. SInt .. one blank bar).

Per channel (ch9-16): value frequency across files (value:count). n=28
| role | event | files | range | top values |
|---|---|---|---|---|
| RHY1 | program | 25 | 0-88 med 80 | 0:4, 83:4, 80:4, 87:2, 45:2, 88:1 |
| RHY1 | bankMSB | 25 | 126-127 med 127 | 127:23, 126:2 |
| RHY1 | bankLSB | 25 | 0-0 med 0 | 0:25 |
| RHY1 | vol | 24 | 36-119 med 67 | 60:2, 58:2, 70:2, 77:2, 74:2, 64:1 |
| RHY1 | reverb | 23 | 0-100 med 24 | 20:4, 34:2, 26:2, 31:1, 28:1, 16:1 |
| RHY1 | chorus | 5 | 3-33 med 17 | 17:2, 3:1, 5:1, 33:1 |
| RHY1 | variation | 1 | 82-82 med 82 | 82:1 |
| RHY1 | resonance | 2 | 62-67 med 64.5 | 62:1, 67:1 |
| RHY1 | cutoff | 1 | 66-66 med 66 | 66:1 |
| RHY2 | program | 28 | 0-91 med 81.5 | 80:5, 83:4, 91:3, 17:2, 73:2, 88:2 |
| RHY2 | bankMSB | 28 | 127-127 med 127 | 127:28 |
| RHY2 | bankLSB | 28 | 0-0 med 0 | 0:28 |
| RHY2 | vol | 28 | 49-112 med 75 | 70:4, 80:3, 76:3, 68:2, 60:2, 79:2 |
| RHY2 | reverb | 24 | 0-60 med 23 | 14:4, 20:3, 26:3, 38:2, 34:2, 32:1 |
| RHY2 | chorus | 3 | 3-11 med 10 | 3:1, 10:1, 11:1 |
| RHY2 | resonance | 1 | 62-62 med 62 | 62:1 |
| BASS | program | 28 | 17-52 med 17 | 17:18, 33:6, 35:1, 38:1, 18:1, 52:1 |
| BASS | bankMSB | 28 | 0-8 med 8 | 8:19, 0:9 |
| BASS | bankLSB | 28 | 0-116 med 1 | 0:13, 2:5, 112:4, 114:2, 1:2, 5:1 |
| BASS | vol | 26 | 42-102 med 65 | 65:5, 55:2, 64:2, 72:2, 57:1, 47:1 |
| BASS | pan | 1 | 65-65 med 65 | 65:1 |
| BASS | reverb | 28 | 0-33 med 0 | 0:25, 10:1, 3:1, 33:1 |
| BASS | chorus | 6 | 6-30 med 15 | 6:2, 30:1, 24:1, 18:1, 12:1 |
| BASS | resonance | 3 | 0-56 med 0 | 0:2, 56:1 |
| BASS | release | 1 | 72-72 med 72 | 72:1 |
| BASS | cutoff | 7 | 0-62 med 50 | 56:1, 32:1, 50:1, 62:1, 58:1, 12:1 |
| CHD1 | program | 28 | 0-28 med 4 | 3:6, 5:4, 4:3, 27:3, 1:3, 0:2 |
| CHD1 | bankMSB | 28 | 0-104 med 0 | 0:16, 8:10, 104:2 |
| CHD1 | bankLSB | 28 | 0-122 med 112.5 | 117:6, 0:5, 2:4, 113:3, 118:2, 122:1 |
| CHD1 | vol | 27 | 35-111 med 55 | 60:3, 74:2, 47:2, 55:2, 79:2, 62:1 |
| CHD1 | pan | 18 | 11-95 med 52.5 | 94:2, 48:2, 42:2, 38:2, 78:2, 54:1 |
| CHD1 | reverb | 26 | 0-78 med 27.5 | 34:3, 15:3, 0:3, 26:2, 36:2, 50:2 |
| CHD1 | chorus | 17 | 10-94 med 20 | 18:2, 14:2, 15:1, 10:1, 94:1, 49:1 |
| CHD1 | variation | 10 | 5-127 med 23.5 | 127:2, 14:2, 30:1, 22:1, 25:1, 5:1 |
| CHD1 | resonance | 5 | 58-75 med 65 | 70:1, 58:1, 63:1, 65:1, 75:1 |
| CHD1 | cutoff | 9 | 51-84 med 66 | 74:2, 52:1, 51:1, 62:1, 60:1, 72:1 |
| CHD2 | program | 27 | 0-62 med 5 | 0:5, 1:4, 27:3, 4:3, 25:2, 10:1 |
| CHD2 | bankMSB | 27 | 0-104 med 0 | 0:17, 8:6, 104:4 |
| CHD2 | bankLSB | 27 | 0-122 med 112 | 0:7, 117:5, 112:2, 122:2, 6:2, 115:2 |
| CHD2 | vol | 28 | 37-115 med 55 | 41:2, 56:2, 68:2, 47:2, 55:2, 48:2 |
| CHD2 | pan | 21 | 29-95 med 49 | 34:3, 74:2, 44:2, 94:2, 76:1, 45:1 |
| CHD2 | reverb | 27 | 0-87 med 31 | 22:3, 42:2, 26:2, 31:2, 34:2, 54:1 |
| CHD2 | chorus | 18 | 8-76 med 30 | 18:2, 32:2, 50:2, 28:1, 10:1, 8:1 |
| CHD2 | variation | 6 | 12-127 med 21 | 24:1, 18:1, 13:1, 12:1, 127:1, 42:1 |
| CHD2 | resonance | 3 | 71-77 med 75 | 77:1, 71:1, 75:1 |
| CHD2 | release | 3 | 45-82 med 69 | 45:1, 69:1, 82:1 |
| CHD2 | attack | 2 | 38-74 med 56 | 74:1, 38:1 |
| CHD2 | cutoff | 8 | 50-84 med 59 | 54:2, 70:2, 50:1, 61:1, 57:1, 84:1 |
| PAD | program | 28 | 1-95 med 49.5 | 50:8, 89:4, 48:4, 18:3, 49:2, 4:2 |
| PAD | bankMSB | 28 | 0-104 med 0 | 0:18, 8:7, 104:3 |
| PAD | bankLSB | 28 | 0-121 med 2 | 0:11, 112:4, 116:2, 2:2, 1:2, 118:2 |
| PAD | vol | 28 | 29-112 med 44.5 | 41:3, 40:2, 55:2, 33:2, 44:2, 52:2 |
| PAD | pan | 6 | 39-95 med 76.5 | 80:2, 68:1, 73:1, 39:1, 95:1 |
| PAD | reverb | 25 | 0-80 med 36 | 52:2, 0:2, 30:2, 50:2, 36:2, 32:2 |
| PAD | chorus | 16 | 5-127 med 23 | 23:2, 10:2, 16:1, 30:1, 12:1, 5:1 |
| PAD | variation | 6 | 4-54 med 18 | 30:1, 25:1, 4:1, 10:1, 11:1, 54:1 |
| PAD | resonance | 7 | 58-78 med 62 | 62:1, 78:1, 58:1, 66:1, 60:1, 61:1 |
| PAD | release | 5 | 46-68 med 55 | 68:1, 55:1, 46:1, 50:1, 60:1 |
| PAD | attack | 11 | 0-52 med 40 | 44:2, 40:2, 52:2, 34:2, 0:1, 35:1 |
| PAD | cutoff | 13 | 36-84 med 51 | 70:2, 55:2, 36:1, 49:1, 43:1, 50:1 |
| PHR1 | program | 28 | 0-88 med 24.5 | 3:7, 27:5, 88:2, 7:2, 28:2, 2:1 |
| PHR1 | bankMSB | 28 | 0-104 med 0 | 0:16, 8:10, 104:2 |
| PHR1 | bankLSB | 28 | 0-124 med 21.5 | 0:5, 3:3, 2:3, 117:3, 1:2, 112:2 |
| PHR1 | vol | 27 | 29-106 med 62 | 71:3, 69:2, 40:2, 50:2, 68:2, 36:2 |
| PHR1 | pan | 22 | 16-96 med 72 | 44:2, 34:2, 72:2, 38:2, 92:2, 96:2 |
| PHR1 | reverb | 26 | 0-80 med 27.5 | 32:3, 0:3, 26:3, 30:2, 27:2, 24:2 |
| PHR1 | chorus | 16 | 8-76 med 28 | 20:3, 53:2, 18:1, 44:1, 68:1, 76:1 |
| PHR1 | variation | 13 | 10-127 med 17 | 15:2, 48:1, 16:1, 26:1, 14:1, 37:1 |
| PHR1 | resonance | 5 | 50-81 med 71 | 57:1, 81:1, 71:1, 50:1, 75:1 |
| PHR1 | release | 3 | 0-112 med 45 | 112:1, 45:1, 0:1 |
| PHR1 | attack | 2 | 0-41 med 20.5 | 0:1, 41:1 |
| PHR1 | cutoff | 8 | 50-127 med 82.5 | 109:1, 81:1, 127:1, 86:1, 50:1, 52:1 |
| PHR2 | program | 24 | 1-89 med 27 | 3:3, 27:3, 28:2, 18:2, 82:1, 66:1 |
| PHR2 | bankMSB | 24 | 0-104 med 0 | 0:15, 8:8, 104:1 |
| PHR2 | bankLSB | 24 | 0-126 med 112 | 0:8, 117:5, 112:4, 2:2, 8:1, 114:1 |
| PHR2 | vol | 23 | 30-120 med 60 | 40:2, 70:2, 44:1, 58:1, 86:1, 108:1 |
| PHR2 | pan | 18 | 31-95 med 53 | 74:1, 94:1, 50:1, 49:1, 81:1, 54:1 |
| PHR2 | reverb | 22 | 0-127 med 38 | 27:2, 50:2, 8:2, 20:2, 116:1, 30:1 |
| PHR2 | chorus | 15 | 10-80 med 22 | 20:1, 12:1, 40:1, 45:1, 32:1, 14:1 |
| PHR2 | variation | 12 | 8-50 med 17.5 | 12:2, 26:2, 20:1, 50:1, 16:1, 19:1 |
| PHR2 | resonance | 6 | 58-81 med 68.5 | 66:1, 69:1, 68:1, 58:1, 75:1, 81:1 |
| PHR2 | release | 1 | 74-74 med 74 | 74:1 |
| PHR2 | attack | 2 | 53-60 med 56.5 | 53:1, 60:1 |
| PHR2 | cutoff | 9 | 49-100 med 72 | 81:1, 73:1, 49:1, 66:1, 72:1, 54:1 |

Files with setup events on ch1-8 (alt source channels): 20/28

Sysex before first section (first 6 bytes hex; count / files):

| sysex prefix | count | files |
|---|---|---|
| 437301510500 | 52 | 26 |
| 437339110046 | 28 | 28 |
| 7e7f0901f7 | 28 | 28 |
| 43104c020100 | 28 | 28 |
| 43104c080807 | 28 | 28 |
| 43104c080907 | 28 | 28 |
| 43761a100101 | 27 | 27 |
| 43104c020140 | 25 | 25 |
| 43104c02015a | 24 | 24 |
| 43104c302a05 | 20 | 19 |
| 43104c020120 | 20 | 20 |
| 43104c302c05 | 19 | 18 |
| 43104c302e05 | 18 | 17 |
| 43104c020142 | 16 | 16 |
| 43104c00007e | 14 | 14 |
| 43104c020146 | 14 | 14 |
| 43104c302405 | 14 | 14 |
| 43104c302a02 | 13 | 13 |
| 43104c020148 | 13 | 13 |
| 43104c302e02 | 13 | 12 |
| 43104c302c02 | 12 | 12 |
| 43104c020144 | 12 | 12 |
| 43104c02014a | 11 | 11 |
| 43104c020102 | 10 | 10 |
| 43104c302305 | 10 | 9 |

Events AT a section's start tick (marker tick), by section type: files with any CC/PC at start, CC numbers seen, how often value == setup value (reset) :

| section | sections with CC/PC at start | events | = setup val | != setup val | sysex | which |
|---|---|---|---|---|---|---|
| Intro A | 6/28 | 43 | 9 | 29 | 0 | vol:25, bankMSB:5, bankLSB:5, PC:5, pan:3 |
| Intro B | 16/28 | 75 | 15 | 55 | 0 | expr:24, vol:24, bankMSB:6, bankLSB:5, PC:5, cutoff:4, pan:3, variation:2 |
| Intro C | 17/28 | 104 | 15 | 76 | 1 | expr:40, vol:25, bankMSB:9, bend:8, bankLSB:5, PC:5, pan:5, cutoff:3 |
| Main A | 12/28 | 55 | 9 | 41 | 0 | vol:25, expr:9, bankMSB:5, bankLSB:5, PC:5, pan:3, cutoff:1, chorus:1 |
| Main B | 16/28 | 61 | 11 | 45 | 0 | vol:25, expr:13, bankMSB:6, bankLSB:5, PC:5, pan:3, cutoff:2, chorus:2 |
| Main C | 16/28 | 68 | 13 | 50 | 0 | vol:25, expr:20, bankMSB:7, bankLSB:5, PC:5, pan:3, cutoff:2, variation:1 |
| Main D | 17/28 | 66 | 13 | 48 | 0 | vol:25, expr:19, bankMSB:8, bankLSB:5, PC:5, pan:3, variation:1 |
| Fill In AA | 14/28 | 70 | 10 | 55 | 0 | vol:25, expr:24, bankMSB:6, bankLSB:5, PC:5, pan:3, cutoff:1, chorus:1 |
| Fill In BB | 16/28 | 60 | 10 | 45 | 0 | vol:25, expr:12, bankMSB:6, bankLSB:5, PC:5, pan:3, cutoff:2, chorus:2 |
| Fill In CC | 16/28 | 69 | 14 | 50 | 0 | vol:25, expr:20, bankMSB:8, bankLSB:5, PC:5, pan:3, cutoff:2, variation:1 |
| Fill In DD | 16/28 | 64 | 13 | 46 | 0 | vol:25, expr:17, bankMSB:8, bankLSB:5, PC:5, pan:3, variation:1 |
| Fill In BA | 12/28 | 55 | 9 | 41 | 0 | vol:25, expr:11, bankMSB:5, bankLSB:5, PC:5, pan:3, variation:1 |
| Ending A | 17/28 | 84 | 10 | 67 | 0 | expr:38, vol:25, bankMSB:6, bankLSB:5, PC:5, pan:3, bend:2 |
| Ending B | 21/28 | 112 | 13 | 94 | 0 | expr:63, vol:25, bankMSB:5, bankLSB:5, PC:5, pan:3, cutoff:2, variation:2 |
| Ending C | 21/28 | 135 | 19 | 104 | 1 | expr:72, vol:25, bankMSB:14, bend:7, bankLSB:5, PC:5, cutoff:3, pan:3 |

Channel events strictly inside sections (not at start tick): CCexpr:27098, 0xe:5897, CCcutoff:1111, CCmod:969, CCattack:118, CCportaCtl:84, CCbankLSB:78, 0xc:78, CCrelease:74, CCbankMSB:49, CCvariation:16, CCpan:6

Meta events overall (type:count): 0x01:390, 0x02:13, 0x03:28, 0x06:476, 0x2f:28, 0x51:311, 0x58:28
Text (0x01) events by prefix: b'fn:':390
Tempo events per file (n events: files): 1:10, 6:2, 10:1, 12:2, 14:1, 15:1, 16:2, 17:3, 18:1, 19:2, 21:1, 27:1, 39:1
Time signatures: {'4/4': 28}; first tempo bpm min/median/max 60/95/139
PPQ: {1920: 26, 96: 2}

### 5. CASM Ctab / Cntt


### SFF1: 14 files

CSEG count per file: {2: 11, 4: 1, 15: 1, 1: 1}
Ctab count per CSEG (n tables: CSEGs): {8: 18, 9: 16, 10: 2, 11: 2, 12: 2, 13: 1, 15: 1}
Sdec groupings (CSEGs): [Intro A, Intro B, Main A, Main B, Main C, Main D, Fill In AA, Fill In BB, Fill In CC, Fill In DD, Fill In BA, Ending A, Ending B] x4; [Intro C, Ending C] x4; [Intro A, Main A, Main B, Main C, Main D, Fill In AA, Fill In BB, Fill In CC, Fill In DD, Fill In BA, Ending A] x3; [Intro B, Intro C, Ending B, Ending C] x3; [Intro C] x3; [Intro A, Main A, Main B, Main C, Main D, Fill In AA, Fill In BB, Fill In CC, Fill In DD, Fill In BA, Ending A, Ending B] x2; [Intro B, Intro C, Ending C] x2; [Ending C] x2
Sections listed in more than one CSEG: 0
Sections without any CASM table: {}
Table (src>=8, src==dest) counts: {('src>=8', 'src==dest'): 1592, ('src<8 (alt source ch1-8)', 'src!=dest'): 314, ('src>=8', 'src!=dest'): 71}
Source chord (root, type) over all tables: {(0, 2): 1558, (0, 0): 384, (0, 14): 35}
Editable byte (b10): {1: 1710, 0: 267}
Ctab byte 26+: {'00': 1936, '0200183937': 26, '020001313e': 15}

#### Group Main/Fill (value:files, a file counts once per distinct value)

| role | files with table | NTR | NTT | high key | RTR | note low(hex) | note high(hex) | chord mute |
|---|---|---|---|---|---|---|---|---|
| RHY1 | 14/14 | 1:14 | 0:14 | 6:14 | 1:14 | 0:14 | 7f:14 | 07ffffffff:14 |
| RHY2 | 14/14 | 1:14 | 0:14 | 6:14, 0:2 | 1:14, 3:2 | 0:14 | 7f:14 | 07ffffffff:14, 0400000000:3 |
| BASS | 14/14 | 0:14, 1:1 | 3:13, 1:1, 0:1 | 3:7, 8:4, 11:3 | 2:14, 1:1 | 1c:13, 1a:1 | 7f:11, 2a:1, 73:1, 7a:1 | 03ffffffff:14 |
| CHD1 | 14/14 | 1:10, 0:7 | 2:11, 3:3, 0:2, 1:1 | 7:6, 6:3, 3:3, 4:2 | 1:12, 2:3 | 0:13, 28:2, 34:1 | 7f:12, 78:2, 4b:1, 3f:1 | 03ffffffff:14, 002ffc7c50:2 |
| CHD2 | 14/14 | 1:13, 0:4 | 2:13, 3:3, 0:2 | 7:7, 3:4, 4:2, 6:2 | 1:14, 2:1 | 0:14, 29:1 | 7f:11, 79:2, 34:1, 39:1 | 03ffffffff:14, 002ffc7c50:1 |
| PAD | 14/14 | 1:11, 0:5 | 2:14, 3:1 | 7:6, 6:3, 5:2, 8:2 | 1:14, 2:1 | 0:10, 35:2, 37:1, 28:1 | 7f:10, 40:2, 42:1, 3f:1 | 03ffffffff:14, 002ffc7c50:1 |
| PHR1 | 14/14 | 0:8, 1:7 | 2:9, 3:7 | 5:4, 3:3, 8:3, 7:3 | 1:13, 2:1 | 0:8, 28:2, 38:1, 3f:1 | 7f:12, 43:1, 4a:1, 38:1 | 03ffffffff:14 |
| PHR2 | 13/14 | 1:9, 0:6 | 2:11, 3:4, 0:1 | 5:3, 7:3, 6:3, 3:2 | 1:13, 2:2 | 0:11, 28:1, 1c:1, 43:1 | 7f:12, 33:1, 4e:1 | 03ffffffff:13 |

#### Group IntroA (value:files, a file counts once per distinct value)

| role | files with table | NTR | NTT | high key | RTR | note low(hex) | note high(hex) | chord mute |
|---|---|---|---|---|---|---|---|---|
| RHY1 | 14/14 | 1:14 | 0:14 | 6:14 | 1:14 | 0:14 | 7f:14 | 07ffffffff:14 |
| RHY2 | 14/14 | 1:14 | 0:14 | 6:14, 0:2 | 1:14, 3:2 | 0:14 | 7f:14 | 07ffffffff:14, 0400000000:3 |
| BASS | 14/14 | 0:14, 1:1 | 3:12, 1:1, 5:1, 0:1 | 3:7, 8:4, 11:3 | 2:14, 1:1 | 1c:13, 1a:1 | 7f:11, 2a:1, 73:1, 7a:1 | 03ffffffff:14 |
| CHD1 | 14/14 | 1:9, 0:8 | 2:10, 3:3, 1:2, 0:2 | 7:6, 6:3, 3:3, 4:2 | 1:12, 2:3 | 0:13, 28:2, 34:1 | 7f:12, 78:2, 4b:1, 3f:1 | 03ffffffff:14, 002ffc7c50:2 |
| CHD2 | 14/14 | 1:12, 0:5 | 2:12, 3:3, 0:2, 5:1 | 7:7, 3:4, 4:2, 6:2 | 1:14, 2:1 | 0:14, 29:1 | 7f:11, 79:2, 34:1, 39:1 | 03ffffffff:14, 002ffc7c50:1 |
| PAD | 14/14 | 1:10, 0:6 | 2:13, 5:1, 3:1 | 7:6, 6:3, 5:2, 8:2 | 1:14, 2:1 | 0:10, 35:2, 37:1, 28:1 | 7f:10, 40:2, 42:1, 3f:1 | 03ffffffff:14, 002ffc7c50:1 |
| PHR1 | 14/14 | 0:9, 1:6 | 2:8, 3:7, 5:1 | 5:4, 3:3, 8:3, 7:3 | 1:13, 2:1 | 0:8, 28:2, 38:1, 17:1 | 7f:12, 43:1, 38:1, 34:1 | 03ffffffff:14 |
| PHR2 | 13/14 | 1:8, 0:7 | 2:10, 3:4, 1:1, 0:1 | 5:3, 7:3, 6:3, 3:2 | 1:13, 2:2 | 0:11, 28:1, 1c:1, 43:1 | 7f:12, 33:1, 4e:1 | 03ffffffff:12, 07ffffffff:1 |

#### Group IntroBC (value:files, a file counts once per distinct value)

| role | files with table | NTR | NTT | high key | RTR | note low(hex) | note high(hex) | chord mute |
|---|---|---|---|---|---|---|---|---|
| RHY1 | 14/14 | 1:14 | 0:14 | 6:14 | 1:14 | 0:14 | 7f:14 | 07ffffffff:14 |
| RHY2 | 14/14 | 1:14 | 0:14 | 6:14, 0:1 | 1:14, 3:1 | 0:14 | 7f:14 | 07ffffffff:14, 0400000000:2 |
| BASS | 14/14 | 0:14, 1:1 | 0:10, 3:7, 5:2, 1:1 | 3:8, 8:4, 11:3 | 2:10, 1:9 | 1c:13, 1a:1, 1b:1 | 7f:11, 27:1, 73:1, 7a:1 | 03ffffffff:14 |
| CHD1 | 14/14 | 0:13, 1:7 | 0:11, 2:7, 1:2, 4:1 | 6:4, 8:4, 7:4, 4:2 | 1:14, 2:2 | 0:12, 36:2, 38:2, 28:1 | 7f:11, 41:2, 43:2, 45:1 | 03ffffffff:14, 002ffc7c50:1 |
| CHD2 | 14/14 | 0:13, 1:8 | 0:11, 2:8, 5:2, 3:1 | 7:5, 6:4, 3:3, 8:3 | 1:14, 2:1 | 0:13, 39:1, 28:1, 34:1 | 7f:10, 79:2, 44:1, 33:1 | 03ffffffff:14, 002ffc7c50:1 |
| PAD | 14/14 | 0:14, 1:4 | 0:10, 2:7, 5:2, 4:1 | 8:5, 6:4, 7:4, 5:2 | 1:14 | 0:8, 37:3, 35:2, 36:2 | 7f:10, 42:2, 46:2, 40:2 | 03ffffffff:14 |
| PHR1 | 14/14 | 0:14, 1:5 | 0:10, 2:6, 5:2, 3:2 | 5:4, 8:4, 3:3, 7:2 | 1:14 | 0:8, 3c:1, 38:1, 17:1 | 7f:11, 4c:1, 4b:1, 43:1 | 03ffffffff:14 |
| PHR2 | 14/14 | 0:14, 1:5 | 0:10, 2:6, 3:3, 1:1 | 6:6, 5:3, 7:3, 9:2 | 1:14, 2:1 | 0:13, 3b:2, 28:2, 1c:1 | 7f:13, 46:2, 33:1, 4e:1 | 03ffffffff:13, 07ffffffff:1 |

#### Group EndA (value:files, a file counts once per distinct value)

| role | files with table | NTR | NTT | high key | RTR | note low(hex) | note high(hex) | chord mute |
|---|---|---|---|---|---|---|---|---|
| RHY1 | 13/14 | 1:13 | 0:13 | 6:13 | 1:13 | 0:13 | 7f:13 | 07ffffffff:13 |
| RHY2 | 14/14 | 1:14 | 0:14 | 6:14, 0:2 | 1:14, 3:2 | 0:14 | 7f:14 | 07ffffffff:14, 0400000000:3 |
| BASS | 14/14 | 0:14, 1:1 | 3:12, 1:1, 5:1, 0:1 | 3:7, 8:4, 11:3 | 2:14, 1:1 | 1c:13, 1a:1 | 7f:11, 2a:1, 73:1, 7a:1 | 03ffffffff:14 |
| CHD1 | 14/14 | 1:9, 0:8 | 2:10, 3:3, 1:2, 0:2 | 7:6, 6:3, 3:3, 4:2 | 1:12, 2:3 | 0:13, 28:2, 34:1 | 7f:12, 78:2, 4b:1, 3f:1 | 03ffffffff:14, 002ffc7c50:2 |
| CHD2 | 14/14 | 1:12, 0:5 | 2:12, 3:3, 0:2, 5:1 | 7:7, 3:4, 4:2, 6:2 | 1:14, 2:1 | 0:14, 29:1 | 7f:11, 79:2, 34:1, 39:1 | 03ffffffff:14, 002ffc7c50:1 |
| PAD | 14/14 | 1:10, 0:6 | 2:13, 5:1, 3:1 | 7:6, 6:3, 5:2, 8:2 | 1:14, 2:1 | 0:10, 35:2, 37:1, 28:1 | 7f:10, 40:2, 42:1, 3f:1 | 03ffffffff:14, 002ffc7c50:1 |
| PHR1 | 14/14 | 0:9, 1:6 | 2:8, 3:7, 5:1 | 5:4, 3:3, 8:3, 7:3 | 1:13, 2:1 | 0:8, 28:2, 38:1, 17:1 | 7f:12, 43:1, 38:1, 34:1 | 03ffffffff:14 |
| PHR2 | 13/14 | 1:8, 0:7 | 2:10, 3:4, 1:1, 0:1 | 5:3, 7:3, 6:3, 3:2 | 1:13, 2:2 | 0:11, 28:1, 1c:1, 43:1 | 7f:12, 33:1, 4e:1 | 03ffffffff:12, 07ffffffff:1 |

#### Group EndBC (value:files, a file counts once per distinct value)

| role | files with table | NTR | NTT | high key | RTR | note low(hex) | note high(hex) | chord mute |
|---|---|---|---|---|---|---|---|---|
| RHY1 | 14/14 | 1:14 | 0:14 | 6:14 | 1:14 | 0:14 | 7f:14 | 07ffffffff:14 |
| RHY2 | 14/14 | 1:14 | 0:14 | 6:14, 0:1 | 1:14, 3:1 | 0:14 | 7f:14 | 07ffffffff:14, 0400000000:2 |
| BASS | 14/14 | 0:14, 1:1 | 0:9, 3:9, 5:2, 1:1 | 3:8, 8:4, 11:3 | 2:12, 1:8 | 1c:13, 1a:1, 1b:1 | 7f:11, 2a:1, 27:1, 73:1 | 03ffffffff:14 |
| CHD1 | 14/14 | 0:12, 1:7 | 0:10, 2:7, 3:2, 1:2 | 8:5, 6:4, 7:4, 4:2 | 1:14, 2:2 | 0:12, 36:1, 28:1, 24:1 | 7f:11, 78:2, 45:1, 64:1 | 03ffffffff:14, 002ffc7c50:1 |
| CHD2 | 14/14 | 0:13, 1:9 | 0:10, 2:9, 3:2, 5:2 | 7:5, 6:4, 3:3, 8:3 | 1:14, 2:1 | 0:13, 39:1, 29:1, 42:1 | 7f:10, 79:2, 44:1, 34:1 | 03ffffffff:14, 002ffc7c50:1 |
| PAD | 14/14 | 0:14, 1:7 | 2:10, 0:9, 5:2, 4:1 | 8:5, 6:4, 7:4, 5:2 | 1:14 | 0:9, 37:3, 35:2, 36:2 | 7f:10, 42:2, 46:2, 40:2 | 03ffffffff:14 |
| PHR1 | 14/14 | 0:13, 1:5 | 0:9, 2:6, 3:4, 5:2 | 5:4, 8:4, 3:3, 7:2 | 1:14 | 0:8, 3c:1, 38:1, 17:1 | 7f:12, 4c:1, 4b:1, 43:1 | 03ffffffff:14 |
| PHR2 | 14/14 | 0:14, 1:7 | 0:9, 2:8, 3:4, 1:1 | 6:6, 7:4, 5:3, 9:2 | 1:14, 2:2 | 0:13, 28:2, 35:1, 1c:1 | 7f:13, 40:1, 33:1, 4e:1 | 03ffffffff:13, 07ffffffff:1 |

#### Cntt (src ch -> byte) frequency by role

| role | Cntt byte1 : files |
|---|---|
| RHY1 | 00:6 |
| RHY2 | 00:6 |
| BASS | 81:5, 00:2, 85:1, 03:1, 80:1, 02:1, 05:1 |
| CHD1 | 00:4, 02:3, 81:2, 01:1, 03:1 |
| CHD2 | 02:5, 00:3, 05:1, 03:1, 81:1 |
| PAD | 02:6, 00:3, 05:2, 03:1 |
| PHR1 | 02:5, 00:2, 05:2, 03:1, 81:1, 80:1 |
| PHR2 | 02:5, 00:2, 01:1, 03:1, 80:1 |

#### Field-wise distribution per role (all tables, src>=8)

| role | tables | NTR | NTT | high key | RTR | note low | note high | chord mute | note mute |
|---|---|---|---|---|---|---|---|---|---|
| RHY1 | 209 | 1:209 | 0:209 | 6:209 | 1:209 | 00:209 | 7f:209 | 07ffffffff:209 | 0fff:209 |
| RHY2 | 251 | 1:251 | 0:251 | 6:225, 0:26 | 1:225, 3:26 | 00:251 | 7f:251 | 07ffffffff:210, 0400000000:41 | 0fff:251 |
| BASS | 225 | 0:210, 1:15 | 3:160, 0:40, 1:13, 5:8 | 3:107, 11:60, 8:58 | 2:187, 1:38 | 1c:193, 1a:30, 1b:2 | 7f:180, 73:15, 7a:15, 2a:12 | 03ffffffff:225 | 0fff:225 |
| CHD1 | 303 | 0:161, 1:142 | 2:186, 0:55, 3:35, 1:19 | 7:96, 3:56, 6:54, 4:26 | 1:266, 2:37 | 00:252, 28:26, 34:11, 36:5 | 7f:236, 78:26, 3f:11, 4b:11 | 03ffffffff:279, 002ffc7c50:24 | 0fff:288, 0780:13, 07ff:2 |
| CHD2 | 279 | 1:191, 0:88 | 2:174, 0:56, 3:37, 5:8 | 7:112, 3:67, 6:32, 4:26 | 1:265, 2:14 | 00:255, 29:14, 42:4, 39:2 | 7f:210, 79:28, 39:15, 34:14 | 03ffffffff:266, 002ffc7c50:13 | 0fff:279 |
| PAD | 231 | 1:130, 0:101 | 2:183, 0:25, 3:11, 5:8 | 7:82, 6:45, 8:39, 5:26 | 1:220, 2:11 | 00:146, 35:30, 37:18, 28:11 | 7f:150, 40:30, 3f:22, 42:16 | 03ffffffff:220, 002ffc7c50:11 | 0fff:231 |
| PHR1 | 232 | 0:146, 1:86 | 2:110, 3:85, 0:25, 5:8 | 8:58, 5:56, 3:45, 7:41 | 1:210, 2:22 | 00:127, 28:26, 17:15, 2d:15 | 7f:167, 38:15, 43:11, 34:11 | 03ffffffff:232 | 0fff:232 |
| PHR2 | 247 | 0:124, 1:123 | 2:136, 3:52, 0:47, 1:6 | 5:56, 6:50, 7:46, 4:30 | 1:221, 2:26 | 00:196, 28:19, 43:15, 1c:13 | 7f:213, 33:15, 4e:15, 46:3 | 03ffffffff:241, 07ffffffff:6 | 0fff:247 |

#### Intro B/C and Ending B/C vs Main (same file): which fields differ, per role

| role | compared (file x section) | table missing in one | fields that differ (count) |
|---|---|---|---|
| RHY1 | 56 | 0 | - |
| RHY2 | 56 | 0 | hk:4, rtr:4, cmute:4 |
| BASS | 56 | 0 | ntt:32, rtr:20, hi:3, hk:2, lo:2 |
| CHD1 | 56 | 0 | ntt:30, hk:21, hi:16, ntr:15, lo:10, rtr:8, cmute:4 |
| CHD2 | 56 | 0 | ntt:31, ntr:23, hk:18, hi:9, lo:7, rtr:1 |
| PAD | 55 | 1 | ntt:35, ntr:24, lo:20, hi:20, hk:19, cmute:4, rtr:4 |
| PHR1 | 56 | 0 | ntt:35, hi:21, lo:14, ntr:13, hk:10, rtr:4 |
| PHR2 | 52 | 4 | ntt:27, ntr:17, hk:11, lo:5, rtr:4, cmute:4, hi:3 |

#### (group, role) -> top (chord-mute, note-mute, NTT, NTR) tuples (count of section-table instances)

| group | role | cmute/nmute/NTT/NTR |
|---|---|---|
| EndA | BASS | 03ffffffff/0fff/3/0 x12; 03ffffffff/0fff/1/0 x1; 03ffffffff/0fff/5/0 x1 |
| EndA | CHD1 | 03ffffffff/0fff/2/1 x8; 03ffffffff/0fff/3/0 x3; 03ffffffff/0fff/2/0 x3 |
| EndA | CHD2 | 03ffffffff/0fff/2/1 x12; 03ffffffff/0fff/3/0 x3; 03ffffffff/0fff/0/1 x2 |
| EndA | PAD | 03ffffffff/0fff/2/1 x10; 03ffffffff/0fff/2/0 x3; 03ffffffff/0fff/5/0 x1 |
| EndA | PHR1 | 03ffffffff/0fff/3/0 x7; 03ffffffff/0fff/2/1 x6; 03ffffffff/0fff/2/0 x2 |
| EndA | PHR2 | 03ffffffff/0fff/2/1 x8; 03ffffffff/0fff/3/0 x4; 03ffffffff/0fff/2/0 x2 |
| EndBC | BASS | 03ffffffff/0fff/3/0 x11; 03ffffffff/0fff/0/0 x11; 03ffffffff/0fff/5/0 x3 |
| EndBC | CHD1 | 03ffffffff/0fff/0/0 x11; 03ffffffff/0fff/2/1 x8; 03ffffffff/0fff/0/1 x4 |
| EndBC | CHD2 | 03ffffffff/0fff/2/1 x11; 03ffffffff/0fff/0/0 x11; 03ffffffff/0fff/0/1 x4 |
| EndBC | PAD | 03ffffffff/0fff/0/0 x11; 03ffffffff/0fff/2/1 x7; 03ffffffff/0fff/2/0 x5 |
| EndBC | PHR1 | 03ffffffff/0fff/0/0 x11; 03ffffffff/0fff/2/1 x6; 03ffffffff/0fff/3/0 x5 |
| EndBC | PHR2 | 03ffffffff/0fff/0/0 x13; 03ffffffff/0fff/2/1 x7; 03ffffffff/0fff/3/0 x5 |
| IntroA | BASS | 03ffffffff/0fff/3/0 x12; 03ffffffff/0fff/1/0 x1; 03ffffffff/0fff/5/0 x1 |
| IntroA | CHD1 | 03ffffffff/0fff/2/1 x8; 03ffffffff/0fff/3/0 x3; 03ffffffff/0fff/2/0 x3 |
| IntroA | CHD2 | 03ffffffff/0fff/2/1 x12; 03ffffffff/0fff/3/0 x3; 03ffffffff/0fff/0/1 x2 |
| IntroA | PAD | 03ffffffff/0fff/2/1 x10; 03ffffffff/0fff/2/0 x3; 03ffffffff/0fff/5/0 x1 |
| IntroA | PHR1 | 03ffffffff/0fff/3/0 x7; 03ffffffff/0fff/2/1 x6; 03ffffffff/0fff/2/0 x2 |
| IntroA | PHR2 | 03ffffffff/0fff/2/1 x8; 03ffffffff/0fff/3/0 x4; 03ffffffff/0fff/2/0 x2 |
| IntroBC | BASS | 03ffffffff/0fff/0/0 x14; 03ffffffff/0fff/3/0 x8; 03ffffffff/0fff/5/0 x3 |
| IntroBC | CHD1 | 03ffffffff/0fff/0/0 x14; 03ffffffff/0fff/2/1 x7; 03ffffffff/0fff/0/1 x4 |
| IntroBC | CHD2 | 03ffffffff/0fff/0/0 x15; 03ffffffff/0fff/2/1 x9; 03ffffffff/0fff/0/1 x4 |
| IntroBC | PAD | 03ffffffff/0fff/0/0 x14; 03ffffffff/0fff/2/1 x4; 03ffffffff/0fff/2/0 x4 |
| IntroBC | PHR1 | 03ffffffff/0fff/0/0 x14; 03ffffffff/0fff/2/1 x5; 03ffffffff/0fff/5/0 x3 |
| IntroBC | PHR2 | 03ffffffff/0fff/0/0 x19; 03ffffffff/0fff/2/1 x4; 03ffffffff/0fff/2/0 x3 |
| Main/Fill | BASS | 03ffffffff/0fff/3/0 x117; 03ffffffff/0fff/1/0 x9; 03ffffffff/0fff/0/1 x9 |
| Main/Fill | CHD1 | 03ffffffff/0fff/2/1 x81; 03ffffffff/0fff/3/0 x27; 03ffffffff/0fff/2/0 x27 |
| Main/Fill | CHD2 | 03ffffffff/0fff/2/1 x117; 03ffffffff/0fff/3/0 x27; 03ffffffff/0fff/0/1 x18 |
| Main/Fill | PAD | 03ffffffff/0fff/2/1 x99; 03ffffffff/0fff/2/0 x27; 002ffc7c50/0fff/2/0 x9 |
| Main/Fill | PHR1 | 03ffffffff/0fff/2/1 x63; 03ffffffff/0fff/3/0 x63; 03ffffffff/0fff/2/0 x18 |
| Main/Fill | PHR2 | 03ffffffff/0fff/2/1 x81; 03ffffffff/0fff/3/0 x36; 03ffffffff/0fff/2/0 x18 |

### SFF2: 14 files

CSEG count per file: {3: 5, 5: 3, 7: 1, 6: 1, 2: 2, 4: 2}
Ctab count per CSEG (n tables: CSEGs): {4: 1, 5: 1, 6: 2, 7: 3, 8: 14, 9: 4, 10: 10, 11: 4, 12: 4, 13: 3, 14: 8, 16: 1}
Sdec groupings (CSEGs): [Intro C, Ending C] x10; [Intro B, Ending B] x7; [Intro A, Main A, Main B, Main C, Main D, Fill In AA, Fill In BB, Fill In CC, Fill In DD, Fill In BA, Ending A] x5; [Main D, Fill In DD] x3; [Intro B] x3; [Main C, Fill In CC] x2; [Ending B] x2; [Intro A, Main A, Main B, Fill In AA, Fill In BB] x2
Sections listed in more than one CSEG: 0
Sections without any CASM table: {}
Table (src>=8, src==dest) counts: {('src<8 (alt source ch1-8)', 'src!=dest'): 500, ('src>=8', 'src==dest'): 1493}
Source chord (root, type) over all tables: {(0, 2): 1486, (0, 0): 257, (0, 8): 229, (0, 19): 12, (0, 14): 9}
Editable byte (b10): {1: 1993}
Ctab byte 26+: {'000000007f0000': 496, '00010018313c00': 22, '800000007f0000': 34, '00000000800000': 598, '00010018314600': 33, '76000000800000': 11, '00010018315000': 22, '00000018315000': 11, '00000000000000': 670, '00010018316200': 11, '80000000000000': 16, '0000000000000200183142': 15, '00010018394600': 11, '00010018314c00': 11, '80000000800000': 21, '00010018313700': 11}

#### Group Main/Fill (value:files, a file counts once per distinct value)

| role | files with table | NTR | NTT | high key | RTR | note low(hex) | note high(hex) | chord mute |
|---|---|---|---|---|---|---|---|---|
| RHY1 | 12/14 | 1:12 | 0:12 | 6:12 | 1:12 | 0:12 | 7f:12 | 07ffffffff:12 |
| RHY2 | 14/14 | 1:14 | 0:14 | 6:14, 0:1 | 1:14, 3:1 | 0:14 | 7f:14 | 07ffffffff:14, 0400000000:1 |
| BASS | 14/14 | 0:14, 1:1 | 129:14, 0:1 | 3:7, 8:6, 6:1, 11:1 | 2:10, 4:4, 1:1 | 1c:14, 0:1 | 7f:13, 33:1 | 03ffffffff:13, 000009f700:1, 03fff608ff:1, 03c0000000:1 |
| CHD1 | 14/14 | 1:9, 0:8 | 2:10, 129:7, 1:2, 130:1 | 7:9, 3:4, 8:3, 6:3 | 1:10, 2:6, 4:2, 3:1 | 0:11, 1c:3, 28:1, 26:1 | 7f:13, 33:2, 35:1 | 03ffffffff:14, 002ffc7c50:4, 0000000053:1, 03ffffffac:1 |
| CHD2 | 14/14 | 0:11, 1:9 | 2:11, 129:4, 1:2, 0:2 | 7:7, 3:4, 6:4, 8:3 | 1:12, 2:5, 3:2 | 0:13, 3d:1, 60:1, 2e:1 | 7f:13, 32:2, 48:1, 45:1 | 03ffffffff:14, 002ffc7c50:5, 000009f700:1, 03fff608ff:1 |
| PAD | 14/14 | 0:8, 1:8 | 2:12, 1:2, 129:2, 0:1 | 7:11, 6:3, 2:1, 0:1 | 1:12, 2:2, 0:1 | 0:12, 32:1, 2c:1, 27:1 | 7f:13, 37:1, 32:1 | 03ffffffff:14, 002ffc7c50:4 |
| PHR1 | 14/14 | 1:8, 0:7 | 2:9, 1:4, 129:4 | 7:11, 3:3, 1:1, 8:1 | 1:11, 2:2, 3:1 | 0:11, 28:3, 26:2, 34:1 | 7f:12, 33:4 | 03ffffffff:14 |
| PHR2 | 7/14 | 0:6, 1:3 | 129:4, 1:4, 2:3, 0:1 | 8:3, 3:2, 0:1, 7:1 | 2:5, 1:5 | 0:4, 28:1, 39:1, 1c:1 | 7f:5, 33:1, 4e:1, 32:1 | 03ffffffff:7, 002ffc7c50:2 |

#### Group IntroA (value:files, a file counts once per distinct value)

| role | files with table | NTR | NTT | high key | RTR | note low(hex) | note high(hex) | chord mute |
|---|---|---|---|---|---|---|---|---|
| RHY1 | 12/14 | 1:12 | 0:12 | 6:12 | 1:12 | 0:12 | 7f:12 | 07ffffffff:12 |
| RHY2 | 14/14 | 1:14 | 0:14 | 6:14, 0:1 | 1:14, 3:1 | 0:14 | 7f:14 | 07ffffffff:14, 0400000000:1 |
| BASS | 13/14 | 0:13 | 129:12, 128:1 | 3:6, 8:6, 11:1 | 2:10, 4:3 | 1c:13 | 7f:12, 33:1 | 03ffffffff:12, 0000046e7f:1, 03fffb9180:1 |
| CHD1 | 14/14 | 0:8, 1:8 | 2:8, 129:7, 1:1, 0:1 | 7:8, 3:4, 5:2, 6:2 | 1:10, 2:6, 4:2 | 0:11, 1c:3, 28:1, 26:1 | 7f:13, 33:2, 35:1 | 03ffffffff:14, 002ffc7c50:3 |
| CHD2 | 13/14 | 0:9, 1:8 | 2:8, 129:4, 1:2, 0:2 | 7:7, 6:4, 3:3, 8:2 | 1:10, 2:5, 3:2 | 0:12, 60:1, 2e:1, 33:1 | 7f:12, 32:2, 45:1, 2f:1 | 03ffffffff:13, 002ffc7c50:4, 07ffffffff:1 |
| PAD | 14/14 | 0:9, 1:7 | 2:11, 129:2, 1:1, 0:1 | 7:11, 6:3, 2:1, 8:1 | 1:12, 2:2 | 0:11, 32:1, 2c:1, 27:1 | 7f:12, 37:1, 32:1 | 03ffffffff:14, 002ffc7c50:3 |
| PHR1 | 11/14 | 1:7, 0:5 | 2:8, 129:2, 1:1, 0:1 | 7:9, 3:3 | 1:9, 3:1, 2:1 | 0:9, 28:1, 34:1, 26:1 | 7f:10, 33:1 | 03ffffffff:10, 07ffffffff:1 |
| PHR2 | 6/14 | 0:6, 1:2 | 129:4, 2:3, 0:2, 1:1 | 3:2, 8:2, 0:1, 7:1 | 1:5, 2:4 | 0:4, 28:1, 39:1, 27:1 | 7f:4, 33:1, 4e:1, 32:1 | 03ffffffff:5, 07ffffffff:1, 002ffc7c50:1 |

#### Group IntroBC (value:files, a file counts once per distinct value)

| role | files with table | NTR | NTT | high key | RTR | note low(hex) | note high(hex) | chord mute |
|---|---|---|---|---|---|---|---|---|
| RHY1 | 12/14 | 1:12 | 0:12 | 6:12 | 1:12 | 0:12 | 7f:12 | 07ffffffff:12 |
| RHY2 | 14/14 | 1:14 | 0:14 | 6:14, 0:1 | 1:14, 3:1 | 0:14 | 7f:14 | 07ffffffff:14, 0400000000:1 |
| BASS | 14/14 | 0:14, 1:1 | 0:12, 129:2, 1:1, 128:1 | 3:9, 8:6, 6:1, 5:1 | 1:11, 4:2, 2:2 | 1c:13, 0:2 | 7f:13, 33:1, 34:1 | 03fff800ff:12, 000007ff00:12, 03ffffffff:4, 07ffffffff:1 |
| CHD1 | 14/14 | 0:14, 1:1 | 0:14, 2:1, 3:1 | 8:5, 7:3, 5:2, 10:2 | 1:14 | 0:9, 28:4, 37:2, 3b:1 | 7f:7, 33:3, 46:3, 35:2 | 03fff800ff:12, 000007ff00:12, 03ffffffff:3, 07ffffffff:1 |
| CHD2 | 13/14 | 0:12, 1:4 | 0:12, 2:2, 3:2 | 7:5, 8:4, 3:2, 6:2 | 1:13, 3:1 | 0:9, 28:2, 24:2, 31:1 | 7f:9, 33:2, 45:2, 41:2 | 03fff800ff:11, 000007ff00:11, 03ffffffff:5, 07ffffffff:2 |
| PAD | 14/14 | 0:14, 1:1 | 0:13, 2:2, 3:1 | 8:6, 7:5, 9:3, 4:3 | 1:14 | 0:6, 36:4, 24:3, 32:1 | 7f:7, 2f:2, 41:2, 34:1 | 03fff800ff:12, 000007ff00:12, 03ffffffff:3, 07ffffffff:1 |
| PHR1 | 14/14 | 0:14, 1:1 | 0:12, 2:3, 1:2 | 8:6, 7:5, 3:1, 4:1 | 1:14 | 0:7, 28:4, 36:3, 1c:2 | 7f:8, 33:3, 41:2, 27:1 | 03fff800ff:12, 000007ff00:12, 07ffffffff:2, 03ffffffff:2 |
| PHR2 | 10/14 | 0:10, 1:1 | 0:10, 2:1, 3:1 | 7:3, 2:2, 10:2, 8:2 | 1:10 | 0:7, 28:2, 39:1, 24:1 | 7f:8, 33:2, 4e:1, 48:1 | 03fff800ff:8, 000007ff00:8, 03ffffffff:3, 07ffffffff:2 |

#### Group EndA (value:files, a file counts once per distinct value)

| role | files with table | NTR | NTT | high key | RTR | note low(hex) | note high(hex) | chord mute |
|---|---|---|---|---|---|---|---|---|
| RHY1 | 12/14 | 1:12 | 0:12 | 6:12 | 1:12 | 0:12 | 7f:12 | 07ffffffff:12 |
| RHY2 | 14/14 | 1:14 | 0:14 | 6:14, 0:1 | 1:14, 3:1 | 0:14 | 7f:14 | 07ffffffff:14, 0400000000:1 |
| BASS | 13/14 | 0:13 | 129:12, 128:1 | 3:6, 8:6, 11:1 | 2:10, 4:3 | 1c:13 | 7f:12, 33:1 | 03ffffffff:12, 0000046e7f:1, 03fffb9180:1 |
| CHD1 | 14/14 | 1:8, 0:7 | 2:8, 129:6, 1:1, 0:1 | 7:8, 3:4, 5:2, 8:2 | 1:10, 2:6, 4:2 | 0:11, 1c:3, 28:1, 26:1 | 7f:13, 33:2, 35:1 | 03ffffffff:14, 002ffc7c50:3 |
| CHD2 | 13/14 | 0:10, 1:7 | 2:9, 129:4, 1:2, 0:2 | 7:7, 3:4, 6:4, 0:1 | 1:10, 2:5, 3:2 | 0:12, 3d:1, 60:1, 2e:1 | 7f:12, 32:2, 48:1, 45:1 | 03ffffffff:13, 002ffc7c50:4, 07ffffffff:1 |
| PAD | 14/14 | 0:8, 1:7 | 2:11, 129:2, 0:1, 1:1 | 7:11, 6:2, 2:1, 11:1 | 1:12, 2:2 | 0:12, 32:1, 27:1 | 7f:13, 32:1 | 03ffffffff:14, 002ffc7c50:2 |
| PHR1 | 13/14 | 1:8, 0:6 | 2:9, 129:3, 1:1, 0:1 | 7:10, 3:3, 8:1 | 1:10, 2:2, 3:1 | 0:10, 28:2, 34:1, 26:1 | 7f:11, 33:2 | 03ffffffff:12, 07ffffffff:1 |
| PHR2 | 7/14 | 0:7, 1:2 | 129:4, 2:3, 0:2, 1:2 | 8:3, 3:2, 0:1, 7:1 | 2:5, 1:5 | 0:4, 28:1, 39:1, 1c:1 | 7f:5, 33:1, 4e:1, 32:1 | 03ffffffff:6, 07ffffffff:1, 002ffc7c50:1 |

#### Group EndBC (value:files, a file counts once per distinct value)

| role | files with table | NTR | NTT | high key | RTR | note low(hex) | note high(hex) | chord mute |
|---|---|---|---|---|---|---|---|---|
| RHY1 | 12/14 | 1:12 | 0:12 | 6:12 | 1:12 | 0:12 | 7f:12 | 07ffffffff:12 |
| RHY2 | 14/14 | 1:14 | 0:14 | 6:14, 0:1 | 1:14, 3:1 | 0:14 | 7f:14 | 07ffffffff:14, 0400000000:1 |
| BASS | 14/14 | 0:14, 1:1 | 0:12, 129:2, 1:1, 128:1 | 3:8, 8:6, 6:1, 5:1 | 1:11, 4:2, 2:2 | 1c:13, 0:2 | 7f:13, 33:1, 34:1 | 03fff800ff:12, 000007ff00:12, 03ffffffff:3, 07ffffffff:1 |
| CHD1 | 14/14 | 0:14, 1:1 | 0:14, 2:1, 3:1 | 8:5, 7:3, 5:2, 10:2 | 1:14 | 0:9, 28:4, 37:2, 3b:1 | 7f:7, 33:3, 46:3, 35:2 | 03fff800ff:12, 000007ff00:12, 03ffffffff:3, 07ffffffff:1 |
| CHD2 | 13/14 | 0:12, 1:4 | 0:12, 2:2, 3:1 | 7:5, 8:4, 3:2, 6:2 | 1:13, 3:1 | 0:10, 28:2, 24:2, 31:1 | 7f:9, 33:2, 45:2, 41:2 | 03fff800ff:11, 000007ff00:11, 03ffffffff:4, 07ffffffff:2 |
| PAD | 14/14 | 0:14, 1:1 | 0:13, 2:2, 3:1 | 8:6, 7:5, 9:3, 4:3 | 1:14 | 0:6, 36:4, 24:3, 32:1 | 7f:7, 41:2, 34:1, 2e:1 | 03fff800ff:12, 000007ff00:12, 03ffffffff:3, 07ffffffff:1 |
| PHR1 | 14/14 | 0:14, 1:1 | 0:12, 2:3, 1:2 | 8:6, 7:5, 3:1, 4:1 | 1:14 | 0:7, 28:3, 36:3, 1c:2 | 7f:8, 33:3, 41:2, 27:1 | 03fff800ff:12, 000007ff00:12, 07ffffffff:2, 03ffffffff:2 |
| PHR2 | 10/14 | 0:10, 1:1 | 0:10, 2:1, 3:1 | 7:3, 2:2, 10:2, 8:2 | 1:10 | 0:7, 28:2, 39:1, 24:1 | 7f:8, 33:2, 4e:1, 48:1 | 03fff800ff:8, 000007ff00:8, 03ffffffff:3, 07ffffffff:2 |

#### Cntt (src ch -> byte) frequency by role

| role | Cntt byte1 : files |
|---|---|
| RHY1 |  |
| RHY2 |  |
| BASS |  |
| CHD1 |  |
| CHD2 |  |
| PAD |  |
| PHR1 |  |
| PHR2 |  |

#### Field-wise distribution per role (all tables, src>=8)

| role | tables | NTR | NTT | high key | RTR | note low | note high | chord mute | note mute |
|---|---|---|---|---|---|---|---|---|---|
| RHY1 | 176 | 1:176 | 0:176 | 6:176 | 1:176 | 00:176 | 7f:176 | 07ffffffff:176 | 0fff:176 |
| RHY2 | 225 | 1:225 | 0:225 | 6:210, 0:15 | 1:210, 3:15 | 00:225 | 7f:225 | 07ffffffff:210, 0400000000:15 | 0fff:225 |
| BASS | 260 | 0:256, 1:4 | 129:163, 0:83, 1:8, 128:6 | 8:120, 3:118, 11:12, 5:6 | 2:130, 1:81, 4:49 | 1c:248, 00:12 | 7f:239, 33:19, 34:2 | 03ffffffff:144, 000007ff00:43, 03fff800ff:43, 03fffb9180:11 | 0fff:260 |
| CHD1 | 312 | 0:214, 1:98 | 2:114, 0:98, 129:75, 1:12 | 7:109, 8:54, 3:51, 6:37 | 1:225, 2:65, 4:16, 3:6 | 00:216, 28:42, 1c:27, 37:12 | 7f:220, 33:49, 35:21, 46:18 | 03ffffffff:182, 000007ff00:45, 03fff800ff:45, 002ffc7c50:36 | 0fff:302, 0008:5, 0ff7:5 |
| CHD2 | 316 | 0:204, 1:112 | 2:144, 0:97, 129:45, 1:22 | 7:113, 6:56, 3:53, 8:46 | 1:241, 2:56, 3:19 | 00:219, 24:17, 2e:15, 60:11 | 7f:220, 32:22, 45:19, 2f:13 | 03ffffffff:180, 002ffc7c50:46, 000007ff00:38, 03fff800ff:38 | 0fff:316 |
| PAD | 302 | 0:214, 1:88 | 2:173, 0:94, 129:22, 1:11 | 7:162, 8:35, 6:29, 11:16 | 1:270, 2:28, 0:4 | 00:213, 36:26, 32:15, 24:12 | 7f:226, 41:12, 32:11, 37:9 | 03ffffffff:179, 000007ff00:45, 03fff800ff:45, 002ffc7c50:31 | 0fff:302 |
| PHR1 | 234 | 0:149, 1:85 | 2:100, 0:76, 1:32, 129:26 | 7:131, 3:41, 8:38, 10:8 | 1:206, 2:17, 3:11 | 00:139, 28:37, 36:18, 26:13 | 7f:167, 33:37, 41:10, 46:6 | 03ffffffff:152, 000007ff00:37, 03fff800ff:37, 07ffffffff:8 | 0fff:234 |
| PHR2 | 168 | 0:136, 1:32 | 0:63, 129:41, 2:34, 1:28 | 3:41, 8:35, 7:25, 10:17 | 1:119, 2:49 | 00:105, 28:25, 39:13, 27:11 | 7f:115, 33:25, 4e:13, 32:11 | 03ffffffff:105, 000007ff00:21, 03fff800ff:21, 002ffc7c50:13 | 0fff:168 |

#### Intro B/C and Ending B/C vs Main (same file): which fields differ, per role

| role | compared (file x section) | table missing in one | fields that differ (count) |
|---|---|---|---|
| RHY1 | 44 | 3 | - |
| RHY2 | 56 | 0 | - |
| BASS | 52 | 2 | ntt:50, cmute:43, rtr:40, hk:14, lo:4, hi:2 |
| CHD1 | 55 | 1 | ntt:53, cmute:51, hk:37, lo:26, hi:25, ntr:21, rtr:20 |
| CHD2 | 49 | 3 | cmute:47, ntt:41, hk:29, hi:27, lo:20, rtr:20, ntr:15 |
| PAD | 55 | 1 | ntt:49, cmute:47, hk:35, hi:30, lo:29, ntr:21, rtr:8 |
| PHR1 | 41 | 9 | ntt:39, cmute:37, hk:25, lo:22, ntr:21, hi:17, rtr:8 |
| PHR2 | 22 | 11 | ntt:18, cmute:18, hk:12, lo:10, rtr:8, hi:8, ntr:4 |

#### (group, role) -> top (chord-mute, note-mute, NTT, NTR) tuples (count of section-table instances)

| group | role | cmute/nmute/NTT/NTR |
|---|---|---|
| EndA | BASS | 03ffffffff/0fff/129/0 x11; 03ffffffff/0fff/128/0 x1; 03fffb9180/0fff/129/0 x1 |
| EndA | CHD1 | 03ffffffff/0fff/2/1 x7; 03ffffffff/0fff/129/0 x5; 002ffc7c50/0fff/1/0 x1 |
| EndA | CHD2 | 03ffffffff/0fff/2/1 x6; 03ffffffff/0fff/129/0 x4; 002ffc7c50/0fff/2/0 x3 |
| EndA | PAD | 03ffffffff/0fff/2/1 x7; 03ffffffff/0fff/2/0 x5; 002ffc7c50/0fff/2/0 x2 |
| EndA | PHR1 | 03ffffffff/0fff/2/1 x8; 03ffffffff/0fff/129/0 x3; 03ffffffff/0fff/2/0 x1 |
| EndA | PHR2 | 03ffffffff/0fff/129/0 x4; 03ffffffff/0fff/2/0 x2; 03ffffffff/0fff/0/1 x1 |
| EndBC | BASS | 000007ff00/0fff/0/0 x19; 03fff800ff/0fff/0/0 x19; 000007ff00/0fff/1/0 x2 |
| EndBC | CHD1 | 000007ff00/0fff/0/0 x23; 03fff800ff/0fff/0/0 x23; 03ffffffff/0fff/0/0 x2 |
| EndBC | CHD2 | 000007ff00/0fff/0/0 x18; 03fff800ff/0fff/0/0 x18; 000007ff00/0fff/2/1 x2 |
| EndBC | PAD | 000007ff00/0fff/0/0 x21; 03fff800ff/0fff/0/0 x21; 000007ff00/0fff/2/0 x2 |
| EndBC | PHR1 | 000007ff00/0fff/0/0 x17; 03fff800ff/0fff/0/0 x17; 07ffffffff/0fff/0/0 x3 |
| EndBC | PHR2 | 000007ff00/0fff/0/0 x11; 03fff800ff/0fff/0/0 x11; 07ffffffff/0fff/0/0 x3 |
| IntroA | BASS | 03ffffffff/0fff/129/0 x11; 03ffffffff/0fff/128/0 x1; 03fffb9180/0fff/129/0 x1 |
| IntroA | CHD1 | 03ffffffff/0fff/2/1 x7; 03ffffffff/0fff/129/0 x6; 002ffc7c50/0fff/1/0 x1 |
| IntroA | CHD2 | 03ffffffff/0fff/2/1 x6; 03ffffffff/0fff/129/0 x4; 002ffc7c50/0fff/2/0 x3 |
| IntroA | PAD | 03ffffffff/0fff/2/1 x7; 03ffffffff/0fff/2/0 x5; 002ffc7c50/0fff/2/0 x2 |
| IntroA | PHR1 | 03ffffffff/0fff/2/1 x7; 03ffffffff/0fff/129/0 x2; 03ffffffff/0fff/2/0 x1 |
| IntroA | PHR2 | 03ffffffff/0fff/129/0 x4; 03ffffffff/0fff/2/0 x2; 03ffffffff/0fff/0/1 x1 |
| IntroBC | BASS | 000007ff00/0fff/0/0 x18; 03fff800ff/0fff/0/0 x18; 000007ff00/0fff/1/0 x2 |
| IntroBC | CHD1 | 000007ff00/0fff/0/0 x22; 03fff800ff/0fff/0/0 x22; 03ffffffff/0fff/0/0 x2 |
| IntroBC | CHD2 | 000007ff00/0fff/0/0 x16; 03fff800ff/0fff/0/0 x16; 000007ff00/0fff/2/1 x2 |
| IntroBC | PAD | 000007ff00/0fff/0/0 x20; 03fff800ff/0fff/0/0 x20; 000007ff00/0fff/2/0 x2 |
| IntroBC | PHR1 | 000007ff00/0fff/0/0 x16; 03fff800ff/0fff/0/0 x16; 07ffffffff/0fff/0/0 x3 |
| IntroBC | PHR2 | 000007ff00/0fff/0/0 x10; 03fff800ff/0fff/0/0 x10; 07ffffffff/0fff/0/0 x3 |
| Main/Fill | BASS | 03ffffffff/0fff/129/0 x111; 03fffb9180/0fff/129/0 x9; 0000046e7f/0fff/129/0 x9 |
| Main/Fill | CHD1 | 03ffffffff/0fff/2/1 x71; 03ffffffff/0fff/129/0 x49; 002ffc7c50/0fff/2/0 x18 |
| Main/Fill | CHD2 | 03ffffffff/0fff/2/1 x64; 03ffffffff/0fff/129/0 x35; 002ffc7c50/0fff/2/0 x27 |
| Main/Fill | PAD | 03ffffffff/0fff/2/1 x72; 03ffffffff/0fff/2/0 x45; 002ffc7c50/0fff/2/0 x18 |
| Main/Fill | PHR1 | 03ffffffff/0fff/2/1 x68; 03ffffffff/0fff/1/0 x26; 03ffffffff/0fff/129/0 x21 |
| Main/Fill | PHR2 | 03ffffffff/0fff/129/0 x33; 03ffffffff/0fff/2/0 x18; 002ffc7c50/0fff/1/0 x11 |

#### Ctb2-only details (47-byte body; 3 six-byte groups = NTR,NTT,highkey,low,high,RTR)

Prefix bytes 20-21: {'007f': 1672, '367f': 32, '345f': 21, '005f': 73, '347f': 12, '2a7f': 4, '2e7f': 4, '357f': 11, '325f': 47, '327f': 76, '323e': 8, '003e': 8, '395f': 2, '307f': 2, '337f': 5, '3242': 6, '3542': 2, '0040': 4, '344e': 4}
Tail bytes 40-46: {'00000000000000': 670, '00000000800000': 598, '000000007f0000': 496, '800000007f0000': 34, '00010018314600': 33, '00010018313c00': 22}
Source chord (root,type): {(0, 2): 1486, (0, 0): 257, (0, 8): 229, (0, 19): 12, (0, 14): 9}
NTT raw byte (0x81 = bass flag): {1: 113, 0: 912, 129: 372, 2: 565, 130: 16, 128: 6, 3: 9}
| role | tables | group2 != group1 | group3 != group1 | group2 (ntr/ntt) when different |
|---|---|---|---|---|
| RHY1 | 176 | 0% | 1% |  |
| RHY2 | 225 | 0% | 0% |  |
| BASS | 260 | 25% | 25% | NTR0/NTT129:41, NTR0/NTT0:22, NTR0/NTT3:2 |
| CHD1 | 312 | 62% | 41% | NTR0/NTT0:54, NTR0/NTT2:35, NTR1/NTT2:30, NTR2/NTT1:22 |
| CHD2 | 316 | 51% | 29% | NTR0/NTT0:45, NTR1/NTT2:44, NTR0/NTT2:30, NTR2/NTT1:16 |
| PAD | 302 | 51% | 33% | NTR1/NTT2:67, NTR0/NTT0:58, NTR0/NTT129:11, NTR0/NTT1:11 |
| PHR1 | 234 | 52% | 38% | NTR0/NTT0:44, NTR2/NTT1:33, NTR1/NTT2:22, NTR0/NTT129:11 |
| PHR2 | 168 | 48% | 27% | NTR0/NTT0:30, NTR0/NTT2:17, NTR1/NTT2:17, NTR0/NTT129:8 |

### 6. Pitch register, drums, velocity

Pitch (MIDI note, source chord root removed so all = C) per channel over ALL sections:

| role | notes | min | p5 | p25 | median | p75 | p95 | max | % CMaj7 tones | % C-major scale |
|---|---|---|---|---|---|---|---|---|---|---|
| BASS | 5822 | 17 | 24 | 24 | 28 | 31 | 38 | 104 | 79% | 93% |
| CHD1 | 17813 | 24 | 43 | 55 | 60 | 67 | 104 | 125 | 72% | 89% |
| CHD2 | 16931 | 24 | 43 | 55 | 63 | 69 | 98 | 124 | 70% | 89% |
| PAD | 5119 | 24 | 44 | 55 | 60 | 67 | 80 | 96 | 75% | 91% |
| PHR1 | 8621 | 31 | 48 | 55 | 62 | 67 | 98 | 125 | 69% | 90% |
| PHR2 | 5283 | 24 | 46 | 55 | 63 | 74 | 105 | 124 | 67% | 88% |

Same, by section group (min / median / max):

| role | Main/Fill | IntroA | IntroBC | EndA | EndBC |
|---|---|---|---|---|---|
| BASS | 19 / 24 / 99 | 97 / 97 / 97 | 19 / 31 / 102 | 24 / 24 / 104 | 17 / 31 / 100 |
| CHD1 | 36 / 59 / 124 | - | 24 / 60 / 125 | 36 / 59 / 108 | 24 / 60 / 125 |
| CHD2 | 36 / 60 / 124 | - | 24 / 65 / 122 | 36 / 59 / 104 | 24 / 63 / 124 |
| PAD | 24 / 59 / 96 | 55 / 59 / 64 | 24 / 62 / 92 | 24 / 59 / 71 | 24 / 60 / 92 |
| PHR1 | 31 / 64 / 121 | - | 36 / 60 / 125 | 36 / 60 / 98 | 33 / 62 / 125 |
| PHR2 | 36 / 59 / 122 | - | 36 / 65 / 124 | 36 / 59 / 71 | 24 / 65 / 124 |

Per-file median pitch spread (min/median/max over files, files with >=8 notes):

| role | files | file-median: min/med/max | file-lowest: min/med/max | file-highest: min/med/max |
|---|---|---|---|---|
| BASS | 28 | 24 / 28 / 36 | 17 / 24 / 31 | 31 / 36 / 104 |
| CHD1 | 28 | 48 / 60 / 79 | 24 / 42 / 60 | 60 / 77.5 / 125 |
| CHD2 | 28 | 48 / 60 / 72 | 24 / 48 / 67 | 55 / 77 / 124 |
| PAD | 28 | 51 / 60 / 73 | 24 / 51 / 60 | 64 / 70 / 96 |
| PHR1 | 28 | 48 / 62.5 / 77 | 31 / 49 / 67 | 48 / 71.5 / 125 |
| PHR2 | 24 | 52 / 65 / 81 | 24 / 55 / 67 | 60 / 77 / 124 |

Mean simultaneous onsets per onset time (polyphony) and notes/bar by role (Main sections):

| role | notes per onset | notes/bar | mean note length (beats) |
|---|---|---|---|
| BASS | 1.04 | 5.3 | 0.86 |
| CHD1 | 1.82 | 15.9 | 1.28 |
| CHD2 | 2.19 | 16.8 | 1.26 |
| PAD | 2.97 | 3.6 | 5.97 |
| PHR1 | 1.64 | 10.2 | 1.99 |
| PHR2 | 2.48 | 9.3 | 2.11 |

Drum notes used (top 14 per rhythm channel):
- RHY1: 54:29%, 70:21%, 82:12%, 64:6%, 62:5%, 63:3%, 56:3%, 83:2%, 40:2%, 35:2%, 24:2%, 42:2%, 48:1%, 53:1%
- RHY2: 42:25%, 36:7%, 35:7%, 40:7%, 51:6%, 44:6%, 82:4%, 54:4%, 38:4%, 33:4%, 46:3%, 49:3%, 53:2%, 57:2%

Velocity per role (all sections; min/p5/median/p95/max):

| role | notes | min | p5 | median | p95 | max |
|---|---|---|---|---|---|---|
| RHY1 | 8791 | 1 | 20 | 53 | 99 | 127 |
| RHY2 | 17227 | 1 | 29 | 67 | 113 | 127 |
| BASS | 5822 | 26 | 55 | 64 | 110 | 127 |
| CHD1 | 17813 | 1 | 25 | 67 | 118 | 127 |
| CHD2 | 16931 | 1 | 33 | 76 | 113 | 127 |
| PAD | 5119 | 3 | 31 | 64 | 110 | 127 |
| PHR1 | 8621 | 1 | 30 | 66 | 116 | 127 |
| PHR2 | 5283 | 1 | 39 | 77 | 113 | 127 |

### 7. Chunks

| chunk | files | size min/median/max (bytes) |
|---|---|---|
| CASM | 28 | 429 / 1350 / 5014 |
| OTSc | 27 | 5646 / 12573 / 16129 |
| ASnc | 2 | 13851 / 15097 / 16344 |
| Cmbi | 1 | 861 / 861 / 861 |
| FNRc | 2 | 323 / 803 / 1283 |

Chunk order: {'CASM OTSc ASnc Cmbi': 1, 'CASM OTSc': 23, 'CASM OTSc ASnc': 1, 'CASM OTSc FNRc': 2, 'CASM': 1}

MTrk length field != real EOT length in 0/28 files, e.g. []
Unparsed trailing bytes after chunks (total): 0

| file | fmt | file bytes | MTrk bytes | CASM | OTSc |
|---|---|---|---|---|---|
| 70sGlamPiano.T609.prs | SFF2 | 89567 | 56623 | 2049 | 16129 |
| 80sAnalogBallad(InThe Air WO | SFF2 | 47360 | 32176 | 2409 | 12737 |
| 80sChristmas.T560(Last Chris | SFF2 | 53539 | 35544 | 1939 | 16018 |
| 80sGuitarPop.T549  SX9 P(eve | SFF2 | 64155 | 44079 | 4419 | 15619 |
| 80sMovieBallad.T559  SX9 P.S | SFF2 | 62517 | 46657 | 3249 | 12573 |
| 90'sPowerBallad(Everything I | SFF2 | 84460 | 66561 | 2324 | 15537 |
| CarelessWhis.STY | SFF1 | 48641 | 39523 | 724 | 8356 |
| Chris de Burgh_Lady in Red.s | SFF1 | 30280 | 23872 | 724 | 5646 |
| CollinsBeat.T014.sty | SFF2 | 31242 | 13988 | 1272 | 15944 |
| DoThatToMeOne.sty | SFF1 | 36981 | 27572 | 884 | 8487 |
| Down On Corner.sty | SFF1 | 34846 | 25680 | 724 | 8404 |
| EltonJohn_nikita.sty | SFF1 | 38299 | 28479 | 1314 | 8468 |
| If tomorow_never comes.T014. | SFF2 | 30435 | 13384 | 1044 | 15969 |
| JazzPop.T547.prs | SFF2 | 61808 | 27410 | 1939 | 16069 |
| LovelyShuffle.T552.prs | SFF2 | 44763 | 26252 | 2574 | 15899 |
| Massachusets.sty | SFF1 | 31317 | 22057 | 864 | 8358 |
| MotorCity.T552.prs | SFF2 | 55037 | 35651 | 3399 | 15949 |
| NoWoman.T014.STY | SFF1 | 43287 | 33862 | 982 | 8405 |
| OrchRockBallad1.T548  SX9 P( | SFF2 | 55092 | 36936 | 2119 | 15999 |
| OrganBallad.T609.prs | SFF2 | 61293 | 42969 | 2229 | 16057 |
| Proud_Mary_Ty.STY | SFF1 | 41101 | 26402 | 5014 | 8356 |
| Red_red_w.sty | SFF1 | 20046 | 19587 | 429 | 0 |
| SheriffReggae.S647.prs | SFF1 | 29348 | 19467 | 1023 | 8489 |
| Sum69.T014.sty | SFF1 | 35318 | 25725 | 1199 | 8356 |
| SweetHo.T014.STY | SFF1 | 40057 | 30508 | 1154 | 8357 |
| Takeit.T014.sty | SFF1 | 35877 | 26048 | 1387 | 8404 |
| Wonder8Beat.T549  SX9 P(Just | SFF2 | 46493 | 31924 | 1939 | 12592 |
| Wonderful2nite.STY | SFF1 | 33811 | 24693 | 724 | 8356 |
- OTSc head (70sGlamPiano.T609.pr): 4d54726b00000fad00f009437301500501012af700f00943
- Cmbi head (70sGlamPiano.T609.pr): 436d4d78000001a54d61696e436d53790000001500000000
- FNRc head (Proud_Mary_Ty.STY): 464e52500000003e06d51104044d6e616d0000000e49276d
- ASnc head (70sGlamPiano.T609.pr): 4173436d000000723c0000005010000073785f6900017378
OTSc sub-chunk tags per file: {('MTrk',): 27}

### 8. DGX-native .prs vs PSR-tutorial .sty

| group (source / ext / SFF) | n | file KB | MTrk KB | CASM B | OTSc B | notes on alt src ch1-8 | Ctab src<8 | CSEGs | bank MSB ch11-16 in lead-in bar | sysex prefixes in lead-in bar | extra chunks | PPQ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DGX Native / .prs / SFF2 | 5 | 61 | 37 | 2438 | 16021 | 5/5 | 5/5 | 4.0 | 8:15, 0:9, 104:4 | 43104c:179, 437301:10, 43761a:5, 437339:5 | ASnc, Cmbi | [1920] |
| PSR Tutorial / .prs / SFF1 | 1 | 29 | 19 | 1023 | 8489 | 1/1 | 1/1 | 2.0 | 0:6 | 43104c:20, 437301:2, 43761a:1, 437339:1 | FNRc | [1920] |
| PSR Tutorial / .prs / SFF2 | 5 | 59 | 42 | 2642 | 15182 | 5/5 | 5/5 | 4.4 | 8:16, 0:6, 104:6 | 43104c:155, 437301:10, 43761a:5, 437339:5 | - | [1920] |
| PSR Tutorial / .sty / SFF1 | 13 | 35 | 27 | 1240 | 7535 | 5/13 | 6/13 | 3.1 | 0:58, 8:19 | 43104c:334, 437301:22, 43761a:13, 437339:13 | FNRc | [96, 1920] |
| PSR Tutorial / .sty / SFF2 | 4 | 42 | 26 | 1876 | 14270 | 3/4 | 3/4 | 3.2 | 0:12, 8:10, 104:2 | 43104c:93, 437301:8, 43761a:4, 437339:4 | - | [1920] |
