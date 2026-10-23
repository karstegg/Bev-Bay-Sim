# midi2sty roadmap

Status: the converter (`midi2sty`), the web Section Painter (arrange, mixer, arranger test page) and the recipe format work end to end on a laptop. Nothing has been verified with a cable to the DGX-670 yet.

## Next: use the real keyboard as the sound engine
1. **Laptop to DGX over MIDI** (USB-MIDI or a MIDI interface into the DGX MIDI port).
   - Choose the DGX as the *output* in the painter's playback and in the Style Player page, instead of the built-in soundfont player. Web MIDI in Chrome/Edge: list outputs, send per-channel setup first (bank MSB/LSB, program, volume, pan, reverb, chorus, delay), then notes, pitch bend and controllers.
   - Keep the internal soundfont as the fallback when no port is available.
   - Use it to confirm levels and instrument selections on the DGX itself after first-round testing in the page.
2. **Let Claude test on its own.** Add a small local bridge on the laptop (for example a Python MIDI service exposed to Claude as a tool) so Claude can:
   - play a style or MIDI file to the DGX, change sections and chords on a script,
   - record what the DGX plays back over USB-MIDI,
   - compare the recording with the intended style (sections, fills, endings, channel levels) and try variations (different styles and MIDI files) without manual steps.
   - Needs: a clear permission model (Claude can only reach that one MIDI port), recording storage, and a stop button.

## Later: style file quality
- SFF2 / SFF GE output (`Ctb2` tables) next to the SFF1 output.
- One-touch settings (OTSc) and other optional chunks, once a factory style from the DGX-670 has been dissected.
- Global effect settings (reverb/chorus/variation type and return levels) written as XG system messages, verified against the keyboard.
- Carry pitch bend and in-song controller moves into styles where the source bars allow it.
- Ritardando and ending variations for more songs; better fills built from song bars; Intro A/Break detection.

## Later: tooling
- **Master track at the top of the painter's song page:** a first row above all tracks where you mark the overall song sections (Intro, Main A-D, Fill, Break, Ending) once, for every track at the same time. Painting that row would assign the bars across all active tracks, so the per-track rows only need touching for exceptions.
- Style Player page: more of the real arranger behaviour (retrigger rules, chord-type masks, bass-on-chord, sync stop, OTS, tap tempo).
- Preview of a painted recipe as a style directly in the painter (build in the browser, no round trip).
- Real soundfont selection per style channel and per-channel effects in the Style Player page.
