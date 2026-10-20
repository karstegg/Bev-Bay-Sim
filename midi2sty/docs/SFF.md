# Yamaha style file notes (target: DGX-670, loads PSR-SX600-class styles = SFF2 / "SFF GE")

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
