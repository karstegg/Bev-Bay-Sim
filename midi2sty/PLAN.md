# midi2sty

Convert a MIDI song (.mid) into a Yamaha SFF1 style file (.sty) loadable on a DGX-630.

## Pipeline (each stage = one module, contract in `model.py`)

| Stage | Module | Input -> Output |
|---|---|---|
| 1. SMF I/O | `smf.py` | bytes <-> raw events; normalise to 480 PPQ; no external deps |
| 2. Analyse | `analyze.py` | `.mid` -> `Song` (tracks, tempo, time sig, key, drum detection) |
| 3. Map & slice | `mapper.py` | `Song` -> `Style` (assign tracks to RHY1/2, BASS, CHD1/2, PAD, PHR1/2; cut bars into Intro/Main A-D/Fill/Ending; transpose chord parts to CMaj7 source) |
| 4. Write | `sty_writer.py` | `Style` -> `.sty` bytes (SMF type 0 + section markers + CASM chunk) |
| 5. CLI | `cli.py` | `midi2sty in.mid -o out.sty [--sections ...]` |
| 6. Validate | `validate.py` | re-parse a `.sty`, check markers, channels 9-16, CASM, section lengths |

## Orchestration
Parallel worker agents own disjoint files: (A) `smf.py`+`analyze.py`, (B) `sty_writer.py`+`validate.py`, (C) `mapper.py`+`cli.py`. Orchestrator (main session) owns `model.py`, integration, and end-to-end tests.

## Open questions
- Exact SFF1 spec details to verify (CASM Ctab fields, marker names, DGX-630 limits: SFF1 only, 8 style channels, ~ file size limit).
- Mapping heuristic quality: drums->RHY1, lowest mono line->BASS, etc. First cut is rule-based; later optional LLM/embedding assist.
