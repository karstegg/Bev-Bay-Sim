# Yamaha style file notes (target: DGX-670, loads PSR-SX600-class styles = SFF2 / "SFF GE")

**Update:** structure below was checked directly against two real Yamaha-format files
(`working demo sty.sty`, `knjraus.aus` from jozphe/Yamaha-Style-Studio) parsed with `midi2sty.dump_sty`.
Still not tested on a DGX-670.

Sources: community reverse engineering (jozphe/Yamaha-Style-Studio `sff2Writer.ts`, psrtutorial.com forum threads).
No official Yamaha spec was available offline, so **nothing here is verified on hardware yet**.

## Used by `sty_writer.py`
- SMF type 0, 480 PPQ, one MTrk, then a `CASM` chunk (big-endian u32 length per chunk).
- Markers (meta 0x06) at tick 0: `SFF2`, `SInt`; then section markers (`Intro A`, `Main A`, `Fill In AA`, `Ending A` ...) placed back to back; `Fine` at the end.
- Setup at tick 0: track name, tempo, time sig, GM reset + XG On sysex, bank/program/volume/pan on channels 9-16.
- CASM = one `CSEG` per section: `Sdec` (section name, comma-separated if several), 8x `Ctab` (27-byte body), 8x `Cntt` (2 bytes).
- Ctab byte map (verified against that project's 14 real tables): 0 src ch, 1-8 name, 9 dest ch, 10 editable, 11-12 note mute,
  13-17 chord mute, 18 source chord root, 19 source chord type (2 = Maj7), 20 NTR, 21 NTT, 22 high key, 23-24 note low/high, 25 RTR, 26 pad.
- NTR: RootTrans 0, RootFixed 1, Guitar 2, Bypass 3. NTT: Bypass 0, Melody 1, Chord 2, Bass 3. Cntt byte 1 bit 7 = bass.

## Assumptions to check on the keyboard
- First section marker directly at tick 0 after SInt (real files may leave a gap bar).
- Optional chunks (OTSc one-touch settings, MH, MDB) omitted.
- One CSEG per section instead of grouped CSEGs.
- XG drum bank (MSB 127) for RHY1/RHY2; GM voices for the rest.

## Verified from real files (direct parse)
- Both files: SMF type 0, one MTrk, then CASM, then OTSc / FNRc / AASM / AFil (audio styles). The real `.sty` had PPQ 1920, the `.aus` 960, so PPQ is not fixed.
- Setup meta order at tick 0: time sig, tempo, copyright text (0x02, optional), `SFF2` marker, track name (32 bytes NUL-padded), `SInt` marker, GM reset sysex, then per-channel CC (7,10,91,93,94, bank 0/32) + program.
- **First section starts one bar after tick 0** (7680 = 1 bar at 1920 PPQ in 4/4; 2880 = 1 bar in 3/4 at 960). Fixed in the writer.
- Section markers are meta 0x06; the track ends (EOT) exactly at the end of the last section. There is **no `Fine` marker** (I had invented one; removed).
- Sections need not be in a canonical order. Lengths vary (Main 4 bars, Fill 1 bar, Intro 1-8 bars).
- CASM = several CSEGs that **group sections sharing one table**: `Sdec` = comma-separated names, then N `Ctab` (27-byte body), then N `Cntt` (2 bytes). N is the number of used source channels, not always 8.
- Ctab: rhythm parts (ch 9/10) use NTR Root Fixed(1), NTT Bypass(0), high key 6, RTR 1, chord-mute byte 0x07. Chord parts: NTR 1, NTT Chord(2), high key 7, RTR 1. Bass: NTR 0, NTT Bass(3), high key 8, note low 0x1C, RTR 2.
- Cntt second byte: bass parts `0x81`, others equal their NTT (0 rhythm, 1 melody, 2 chord). My earlier `0x83` guess was wrong.
- Sections not listed in an early CSEG's Sdec (Intro B/C, Ending B/C) get their own CSEG with Ctab tables that mute/rework channels.

## Still unverified
- No OTSc / MH written; hardware may or may not require them.
- Voice banks for DGX-670 (MegaVoice/Live! bank MSB 8) vs plain GM/XG.
- A factory style from your own DGX-670 would be the best ground truth: run `python -m midi2sty.dump_sty style.sty`.
