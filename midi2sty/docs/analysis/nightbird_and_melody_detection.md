# Night Bird <-> JazzPop.T547, melody detection, section finding

Reference data (user's own files, not in the repo): `nitebirdsShakatak.mid` (type 0, one MTrk, PPQ 1920, 4/4, 118 bpm, 193 active bars),
`JazzPop.T547.prs` (DGX preset, PPQ 1920, 4/4, 102 bpm, 28 bars). Scripts: `tools/section_finder.py` (new, stdlib only).
Confidence tags: **[C]** confident, **[W]** weak / needs a listening test.

## 1. Verdict on the pair

**[C] JazzPop is only a generic neighbour of Night Bird, not derived from it.** Same genre feel (jazz-pop, 16ths, 4/4) and same tonic (C minor),
but nothing in the style reproduces song material. Evidence (JazzPop Main/Fill bars vs best song bar; the same test run against unrelated
song MIDIs as a null):

| metric | Night Bird | unrelated songs (NIKITA, DOTHATTO, ROCKET, EVBRTK, NOWOMAN) |
|---|---|---|
| drums, 16-step onset cosine, Main A-D, 2-bar windows | 0.75 | 0.58 - 0.81 |
| bass, same metric | 0.86 | 0.73 - 0.81 |
| drums, exact (step,note) Jaccard, mean of best bar | 0.10 (max 0.25) | 0.12 - 0.16 (max 0.25 - 0.35) |
| drums, kick/snare/hat-class Jaccard (kit-independent) | 0.55 (max 0.73) | 0.51 - 0.61 |
| bass, (step, pc relative to bar root) Jaccard | 0.49 (max 0.71) | 0.45 - 0.52 (max 0.60 - 0.75) |
| pitched channels, best transposition, mean best-bar Jaccard | 0.23 - 0.68 per channel | same range for every other song |

Night Bird scores inside the null range everywhere. Where the max reaches 1.00 it is a 3-note one-shot chord that matches any chord.
Tempo differs too (102 vs 118). Harmonic resemblance is only the generic minor-key one (see below).

## 2. (a) Key and transposition

* **[C] Song key = C minor, no modulation.** Bass roots in the verse: C Bb Ab Ab F G C Bb Bb Bb Ab Ab F G; later 16-bar form
  Bb F Bb Eb Ab D G C (cycle of fourths into Cm). Pitch classes: C F G Ab Bb dominate. The song's own key-signature meta says C major
  (default, ignore it). `analyze.guess_key` returns (0, minor) = correct.
* **[C] Style source chords (Ctb2 bytes after chord-mute): Main A-D, Fill AA-DD, Intro A, Ending A, Fill BA = C Maj7.
  Intro B, Intro C, Ending B, Ending C = C minor (type 8)**, and their material uses Eb/Ab/Bb (bass roots e.g. Intro B
  C C C C C C Bb Ab / Ab G F G; Ending C C C C Eb F Eb F F G / Ab Ab Bb Bb C). Real styles therefore switch the source chord per section.
* **Song -> style transposition = 0 semitones**, source chord must be declared C minor (Cm/Cm7), not CMaj7.
* **[C] Bug in current mapper:** `transpose_shift` moves a minor song to its *relative major* (Cm -> shift -3, i.e. data written in A minor)
  while `sty_writer` always declares source CMaj7. The engine then reads A-minor material as C-major-source material: bass A becomes the
  6th, A natural over a Cm chord, etc. This is a very plausible cause of the "off key" complaint for any minor song. Fix: for minor songs
  shift tonic -> C (Night Bird: 0) and write source root C / type min (8) in the Ctab (offset 18/19, also at the Ctb2 equivalent).
  Major songs: tonic -> C, CMaj7 (as now).

## 3. (b) Style structure and song-track matching

JazzPop sections (start bar 2, 1-based bar 1 is the gap bar): Main A-D 2 bars each (rising density, about 55 -> 139 notes per bar from Main A to D),
Fill AA-DD 1 bar, Intro A 1 bar (bass only), Intro B 3 bars, Intro C 4 bars, Ending A/B/C 2 bars, Fill In BA 1 bar. Channels used:
RHY1 (ch9, percussion 54/70) RHY2 (ch10, kit 35/40/44/46), BASS, CHD1, CHD2, PAD, PHR1, PHR2 (PHR1 only light stabs, PHR2 only Main C/D and Intro/Ending).
**Intro B/C and Ending B/C store their pitched parts twice** (ch 2-6 = source ch 1-5 active; ch 11-15 same notes, muted by the Ctab).
OTSc/ASnc chunks follow the CASM (not written by midi2sty).

Role-level best song track per style channel (onset-grid cosine x density factor, best 2-bar window; "median" = the same track's score over
all bars, i.e. chance level for that track). Song channels 1-based:

| style channel | best song track | score (median) | meaning |
|---|---|---|---|
| RHY1+RHY2 | ch10 drums (only candidate) | 0.55-0.89 (0.54-0.86) | no lift over chance |
| BASS | ch2 (synth bass, XG prog 39) | 0.79-0.90 (0.64-0.70) | role match only, bars arbitrary (bars 10-16, 49) |
| CHD1 | ch8 (steel guitar comp, 3015 notes) | 0.72-0.84 (0.59-0.66) | role match only |
| CHD2 / PAD | ch4 (piano), ch5 (e-piano), ch9 (strings prog 48) | 0.5-1.0 (sparse, 1.0 = chance hit) | no meaningful match |
| PHR1/PHR2 | ch16 (pipe-voice octave stabs, bars 29-35, 53+) | 0.5-0.9 (sparse) | no meaningful match |

Reading: the per-role pairing BASS<-ch2, CHD<-ch8/ch4/ch5, PAD<-ch9, RHY<-ch10 is what a role heuristic would give anyway.
**No specific song bars correspond to any style section: treat every section as "generic".** Intro/Ending B and C differ from Mains
only in harmony (minor, moving bass) and band size, which is a style-design convention.

## 4. (c) Song tracks the style never uses (melody / vocal / solo)

Night Bird has no program changes at all. Voices are set by XG sysex (`F0 43 1n 4C 08 pp 03 vv`; bank MSB 119) and `analyze.py` reads
program = None for every track. Decoded programs (0-based): ch2 39 synth bass, ch3 1 piano, ch4 1 piano, ch5 4 e-piano, ch6 26 jazz gtr,
ch7 26 jazz gtr, ch8 25 steel gtr, ch9 48 strings, ch10 drums, ch11 74 recorder/pipe, ch16 75 pan-flute/pipe. No saxophone here.
By content the lead-like parts are:

| ch | prog | evidence | role in song |
|---|---|---|---|
| 11 | 74 | mono, med G5, 88 notes, bars 5-12 and 69-83 | intro/bridge melody (tier 2) |
| 16 | 75 | mono octave doublings (C5/C6, Bb4/Bb5), med 82, only chorus bars 29-35, 53-67 | chorus hook (tier 2) |
| 6 | 26 | mono, 83 notes in bars 85-100 only | solo lick (tier 1) |
| 7 | 26 | mono, 668 notes, verse bars 14-27 (Eb C Eb F Eb C C Bb B...) | verse line (tier 1) |
| 3 | 1 | mono, med G5, bars 13,15,17...: Bb C Eb D Bb C G | repeating hook/riff (tier 1) |

Never part of the accompaniment: those five. Accompaniment: ch2 bass, ch4/ch5/ch8 chord parts, ch9 strings, ch10 drums.

**Why the earlier conversions let a sax in (verified by running the mapper):** `assign_roles` puts every non-bass pitched track with
polyphony < 0.3 into PHR1/PHR2. DOTHATTO: `Melody` (GM 65 alto sax) -> PHR1; `Startheme` + `Violin` + `Guitar 2` -> PHR2.
ROCKET: `Melody` -> PHR1, `Strings` -> PHR2. Night Bird: ch3 -> PHR1; ch6+ch7+ch11 -> PHR2 (ch16 ends up in PAD). The writer then tags
PHR1/2 as NTR RootTrans + NTT Melody, so the line is re-transposed on every chord and, with the shift in section 2, ends up off key.
Also `smf.py` fails on NIKITA.mid and SACRIFIC.mid (running status is wrongly cleared after a meta event; both files continue running status across
`FF 01 ..`), and ignores XG sysex programs.

**Detection rule (implemented as `classify_parts`; per track+channel, score >= 3 = lead, >= 5 = tier 2):**
name keyword (melod, lead, vocal, vox, voice, solo, sax, tenor, alto, soprano, flute, whistle, trumpet, violin, theme, hook...) +3 unless the name
says bass/drum/pad/string/chord/organ/piano/choir; GM program in 56-87 (brass, reeds, pipes, synth lead), 40/41, 21-23, 109-111 +1.5
(programs also from XG sysex, last value at/before first note); monophonic (< 15% of onsets with >= 2 pitch classes sounding, octave doubling ignored)
+1; median pitch >= 66 +1 (55-65 +0.5); active on < 60% of bars +0.5; top-voice mean leap >= 1.8 semitones and < 50% repeated notes +1;
-1.5 repeated-note ostinato, -2 low register (<52) when no name/GM cue, -2 chordal (>= 45% onsets with >= 3 pcs), -3 bass.
Bass = GM 32-39, "bass" in name, or mono with median < 50.

Validation (21 MIDIs: 20 ref + 9 in `scratchpad/midis`, 174 pitched parts; labels = track names plus my reading of the note content; 37 parts left
unlabelled as ambiguous): 31 labelled leads. Tier 2 (>= 5): 16 hits, 0 false positives. Tier >= 1: 30 of 31 caught (miss: backing "Ooh" voices), 9 false
positives of 106 labelled non-leads (sparse mono string/choir/guitar counter-lines). **[W]** Thresholds were tuned on these same files,
labels are manual, so real precision is lower. The error is on the safe side for style building (dropping a counter-line costs little; keeping a melody ruins the style).
Policy: drop tier 2 automatically, tier 1 by default but offer it as PHR. If names are generic (Night Bird, "Track 1"), only content carries the decision.

## 5. (d) Section finding (`tools/section_finder.py`)

Method: per-bar features (drum onset grid by class, onset grid of non-lead pitched parts, chroma of chordal + bass, active-part set), bar x bar
similarity (0.40 chroma, 0.25 instrumentation, 0.20 pitched rhythm, 0.15 drum grid), checkerboard novelty (4-bar half window) + instrumentation
change + break/fill bar (drum count < 0.35 or > 1.25 of median) bonus, boundaries >= 8 bars apart; tier-2 lead entering >= 4 bars after the band starts
ends an intro; segments clustered by aligned similarity (>= 0.78) -> repeats; Intro = unique leading segment, Ending = unique/short trailing segment,
clusters ordered by density -> Main A..D; fill = the break/fill bar leading into the segment. Run: `python tools/section_finder.py song.mid [--no-parts]`.

Proposed ranges (1-based bars, inclusive; Mains = 4-bar loop at segment start; letters = similarity class):

| song | proposal |
|---|---|
| Night Bird | Intro 5-12; Main A 14-17 (fill 13); Main B 101-104; Main C 54-57; Main D 182-185 (fill 181); Ending 190-193. Segments start 5,14,29,37,54,70,78,86,101,118,133,148,158,169,182 |
| NIKITA | Intro 2-5; Main A 92-95 (fill 91); Main B 52-55; Main C 35-38; Main D 82-85 (fill 81); Ending 119-122 |
| ROCKET (38 bars) | Intro 2-9; Main A 11-14 (fill 10); Main B 19-22 (fill 18); Ending 34-37 |
| DOTHATTO | Intro 1-7; Main A 9-12 (fill 8); Main B 23-26 (fill 22); Main C 57-60 (fill 56); Main D 43-46 (fill 42); Ending 78-81 |

Check against what I read from the Night Bird bar table (sections are 1 break/fill bar + 15 bars: 5-12 intro, 13 break, 14-28 verse, 29-36 chorus,
37 break, 38-52 verse 2, 53 fill, 54-68 chorus, 69 break, 70-84 bridge, 85 break, 86-100, 101-116, 117 break, 118-132, 133-147...): all 10 hand-picked
boundaries are found within +-1 bar **[C]**; 5 extra boundaries (78, 148, 158, 169, 182) split long outro/bridge sections **[W]**.
NIKITA intro length (2-5) rests on the melody entering at bar 6 **[W]**; ROCKET/DOTHATTO structure agrees with visual inspection of density but
there is no ground truth **[W]**. Main letters follow density, not song order; the "Ending" for Night Bird is just the last 4 bars of a 29-bar vamp.

Limits: constant-time-signature assumption is only approximate (bars follow time-signature meta), no tempo-map awareness, thresholds untuned
beyond these songs.

## 6. Recommendations for the mapper

1. Use `classify_parts` (or equivalent) before `assign_roles`; never route tier-2 leads to PHR.
2. Read XG sysex programs; fix `smf.py` running status (do not clear on meta events).
3. Minor songs: shift tonic -> C and write Cm source chord (type 8) per section, as JazzPop does in Intro/Ending B/C.
4. Slice with song-derived bar ranges (`propose_ranges`), not fixed 4-bar blocks from bar 0 (Night Bird opens with 3 silent bars; Intro A/Ending A
   come out empty and are dropped by the current mapper), and take fills from the break/fill bar preceding a section.
