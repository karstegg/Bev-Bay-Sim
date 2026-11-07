# Yamaha "MIDI Song to Style" v1.2.0: what we can learn from it

Source: Yamaha's own free Windows tool (installer from the Yamaha download page). Examined **statically only**: the
installer was unpacked and the strings, UI resource names and QML sources inside the executable were read. Nothing was
run, no code or assets were copied into this repo, and none of the behaviour below was verified by running it. The
conversion core is compiled C++, so what follows is what its UI, parameter names and templates reveal, not its algorithm.

## What the tool is
- Qt 6 / QML desktop app, 64-bit, ~71 MB. Internal project name "SMFsegmenter".
- Two modes: **Easy** (drop a MIDI file, get a style) and **Edit** (piano roll, part assignment, section markers,
  per-part detail parameters, built-in style playback, chord palette).
- Outputs SFF1.0 or SFF2.0. Target model list (decides format/limits): PSR-E473, EW425, I300, E383/YPT-380, EW320,
  EZ-310, E483, E583, I610, I510, KB-318/319, PRIMARY-01, Genos, PSR-SX900/700/600, PSR-A5000, Genos2, PSR-SX920/720.
  The DGX-670 is not listed (it is SX600-class in practice).
- "Save to Computer" or "Save to Instrument" (sends the style to the keyboard's User drive over MIDI/USB).
- Optional anonymous usage data upload (setting "Allow Data To Be Sent", Firebase endpoints in the binary). Check that
  setting if you run it.

## Authoring convention: a marker template (MarkerTemplate.mid, 960 ppq, 4/4)
The tool ships a 9-track template: marker track plus Rhythm1, Rhythm2, Bass, Chord1, Chord2, Pad, Phrase1, Phrase2
(channels 9..16), each with GM/XG reset and bank/program setup. Section markers and lengths in the template:

| marker | bars | | marker | bars |
|---|---|---|---|---|
| Intro I | 1 | | Break | 1 |
| Fill A..D | 1 each | | Ending I | 1 |
| Main A..D | 2 each | | Intro II / Ending II | 4 each |
| | | | Intro III / Ending III | 4 each |

So Yamaha's own convention is I/II/III for intros and endings (= our A/B/C), 1-bar fills, 2-bar mains.
"Use SMF Marker as Section Marker" lets a song that already carries these markers skip the section analysis.

## Parameter vocabulary exposed in the detail editor (per part)
Preset, SourceRoot, SourceType, TrkSwByRoot, TrkSwByType (= the per-root / per-chord-type source-channel switches, the
muted-notes / muted-chords bits of CASM), LowerSplit / UpperSplit and Low / Main / Hi zones (SFF2 note ranges),
Ntr, Ntt, OnBass, HighKey, LoLimit, LoOctaveShiftCut, HiLimit, HiOctaveShiftCut, Rtr, AppendRoot, Ngen (+ note, velocity,
length, CC), OutCh. Validation message: HiLim and LoLim must be at least one octave (11 keys) apart, HiLim under C6.

Part presets offered: Bass, Bass (Intro), Chord, Phrase melodic, Phrase chordal, Maj-min (Intro), Chromatic,
Drum with cymbal, Drum no cymbal, SFX, Chord Min11, Guitar Stroke, Guitar Arpeggio, "StyOriginated" (keep the original
style's values). Behaviour names that appear next to them: Stable for Main, Active for Main, Semi-active Bass,
Stable Low Root, Stable min11 (Low cut), Root only, Root and 5th, Major minor, snapMin, convMin.
Retrigger/length choices: 8th, 8th dot, 8th tri, 4th, 4th dot, 4th tri, 2nd, 2nd dot, 2nd tri.
SMF channel categories used by the analysis: Pad, MeloChord, Melody, VocalHarmony, Score, Other.
Conversion modes: simple, KeyTrns, AreaSimple, AreaKeyTrns, AreaCRTrns; chord handling options "snap chord note",
"chord conversion", "fix chord progression", "same as previous".

## Other features
- Section lists include D variants and cross fills (Intro D, Ending D, Fill In AB/BA/CD/DC) for the newer models;
  "2 Main" and "4 Main" data formats (choose which sections form a 2-variation style).
- Per-section **key signature editor**, per-section **beat (time signature) editor**, per-section tempo view.
- **Reanalyze** dialog: tick each SMF channel as *melody part* (left out of the style) or as an assigned part.
- Chord palette to audition the style with chosen chords (or chords from the connected instrument).
- Total style file size limit shown to the user.
- Voice list import (bank MSB/LSB/PC to voice name) for the Genos2 voice set, used for track icons/names.

## What we can do with it
1. **Read markers on import.** If the MIDI has the Yamaha marker names (Intro I..III, Fill A..D, Main A..D, Break,
   Ending I..III) turn them into section ranges, prefill the recipe and show them on the painter ruler. Also offer
   "export marker template" so a song can be marked in a DAW.
2. **Per-section source key and time signature** in the recipe, instead of one global tonic.
3. **Part presets in the writer and the Style Player** (Bass, Chord, Phrase melodic/chordal, Chromatic, drums with or
   without cymbal, intro variants), instead of one fixed NTR/NTT per role. Add "octave shift vs cut" for out-of-limit
   notes next to our limit folding.
4. **Validate Ctab limits** the same way (>= 11 keys between low and high limit, high limit below C6) and a style size cap.
5. **Melody roles:** add VocalHarmony / MeloChord / Score / Other to melody detection and to the painter role list;
   keep the "melody, leave out" tick as the main control.
6. **2-Main mode** for songs that only have two grooves.
7. **Direct transfer** to the instrument is exactly our roadmap item "laptop to DGX over MIDI"; their tool proves the
   idea is practical, but the transfer protocol is not documented here.
8. **Comparison test:** the best check is a side-by-side: same MIDI converted by their tool and by ours, then compare
   sections, Ctab tables and CASM with `dump_sty`.

## Second pass: the analysis pipeline (from its debug/log strings)
The tool's classes are `smfSegmenter` (+ Config/Settings), `quantize`, `ChromaVectorExtractor`, a separate chord
detection library (`ChordDetectExport`, `chd` facade) and a `partAssigner`. Its debug menu has "Rhythm analysis",
"Section estimation" and "Label analysis" dumps, so the stages are, in order:
1. **Read and check the SMF**: division, tempo, time signature, format; then **quantize** (a base grid and an offset
   ratio; there is a "Export quantized SMF" debug action).
2. **Melody part estimation** per channel: counts of note-ons, mono-melody vs multi-note melody, "melody sequence"
   runs, ratio of too-short notes and polyphony ratio decide melody / not melody (`judge_poly`).
3. **Part assignment** (`partAssigner`): each channel gets a recommended style part (hard or soft recommendation from
   its channel conversion info); leftover channels are placed in the remaining free parts; unison channels handled.
4. **Section estimation**: every track's note pattern per bar is hashed and given a label and sub-label; bars get a
   label and a super-label. Main candidates come from chord-progression "suites" in these kinds: agreeing suite,
   agreeing half region, loop sequence, far loop sequence, longer suite, pre-"double" longer suite, suite with an
   extra fill. Candidates are then thinned by priority rules: remove same-area duplicates, overlap importance, the
   "3 big parts" rule, fill label, bar size, inner rhythm group, "alliancy", tempo difference, and a per-channel
   similarity deviation threshold. Irregular meter ("IrrMeter") is handled separately. Intro, ending and instrumental
   labels are assigned last.
5. **Note adaptation when copying bars into sections**: each note is checked for collision and crossover with its
   neighbours, with low and high pitch limits, on-time, off-time and a time reference (notes are trimmed or moved).
6. **Writer**: 2-main or 4-main data format, fill accompaniment setting, per-section time signature ("indivTS"),
   fixed or edited tempo for Main A, Ctab name field filled from a 13-preset list (BassMain, BassIntr, ChrdMain,
   PhrsMain, Maj-min, Chroma, Drum4cc, Drum, SFX, ChrdMn11, ChrdArp, ChrdStrV, ChrdGApB), size check against the model's
   limit with a message that suggests using fewer bars.

## Real-style statistics for the Ctab values (our 28 reference styles, SFF1 Ctab)
Most common values per destination part (`ntr` 0 = root trans, 1 = root fixed; NTT is the SFF1 value, 3 = bass):
- RHY1/RHY2: ntr1, ntt0 (bypass), high key 6, limits 0-127, rtr1.
- BASS: ntr0, ntt3, high key mostly 11 (also 3 and 8), low limit 28, high limit 122 or 127, rtr2.
- CHD1: ntr0 or 1, ntt2 (chord), high key 3-8. CHD2: ntr1, ntt0 or 2, high key 3 or 7.
- PAD: ntr1, ntt2, high key 3; some pads use ntr0 with a narrow range 53-64.
- PHR1/PHR2: ntr0, ntt3, high key 3 or 5, low limit 28; sometimes chord tables instead.
- All values seen across files: ntr in {0,1}, ntt in {0,1,2,3,4,5}; no bass-on flag set in these files.
These are good defaults for per-role presets in our writer. The Ctab "name" in factory styles is the instrument label
(Bass, MainDrum, Piano...), not a preset name.
