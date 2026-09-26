---
name: garageband
description: Render an ABC score or MIDI file with GarageBand, export an MP3, and apply a local mix preset. Use for requests to compose a short instrumental piece, render a score, or make a GarageBand-backed MP3 on macOS.
---

# GarageBand renderer

Run the environment check before first use:

```bash
./garageband --doctor
```

Render an ABC score:

```bash
./garageband examples/rusty-waltz.abc --mix room
```

Outputs are written to `~/Music/GarageBand/exports/` unless `--out` is provided:

- `<name>.mid`
- `<name>-raw.mp3`
- `<name>.mp3`

Available mix presets: `none`, `dry`, `room`, `hall`, `oldrecord`, `musicbox`.

If GarageBand is already open, stop and ask the user to close or save their project. Only use `--force-close` after the user confirms that closing the current GarageBand project without saving is safe.

The export step uses macOS Accessibility automation. The terminal or agent host running this tool must have Accessibility permission.
