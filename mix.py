#!/usr/bin/env python3
"""Small, deterministic audio-mix presets for GarageBand exports."""

import argparse

import numpy as np
from pedalboard import (
    Chorus,
    Compressor,
    Delay,
    HighpassFilter,
    HighShelfFilter,
    LowpassFilter,
    Pedalboard,
    Reverb,
)
from pedalboard.io import AudioFile


PRESETS = {
    "dry": dict(
        chain=lambda: [HighpassFilter(40), Compressor(-20, 2.0, 10, 150)],
        tail=0.5,
        hiss=0.0,
    ),
    "room": dict(
        chain=lambda: [
            HighpassFilter(60),
            Compressor(-18, 2.5, 15, 200),
            Reverb(
                room_size=0.55,
                damping=0.5,
                wet_level=0.22,
                dry_level=0.8,
                width=0.9,
            ),
        ],
        tail=2.0,
        hiss=0.0,
    ),
    "hall": dict(
        chain=lambda: [
            HighpassFilter(60),
            Compressor(-18, 2.0, 20, 250),
            Reverb(
                room_size=0.9,
                damping=0.35,
                wet_level=0.35,
                dry_level=0.7,
                width=1.0,
            ),
        ],
        tail=4.0,
        hiss=0.0,
    ),
    "oldrecord": dict(
        chain=lambda: [
            HighpassFilter(90),
            Compressor(-18, 2.5, 15, 200),
            Reverb(
                room_size=0.82,
                damping=0.55,
                wet_level=0.32,
                dry_level=0.75,
                width=0.9,
            ),
            LowpassFilter(6500),
        ],
        tail=3.0,
        hiss=0.002,
    ),
    "musicbox": dict(
        chain=lambda: [
            HighpassFilter(150),
            HighShelfFilter(4000, 3.0),
            Chorus(rate_hz=0.6, depth=0.15, mix=0.25),
            Delay(delay_seconds=0.28, feedback=0.25, mix=0.18),
            Reverb(room_size=0.6, wet_level=0.25, dry_level=0.8),
        ],
        tail=2.5,
        hiss=0.0,
    ),
}


def mix(source: str, destination: str, preset: str) -> None:
    settings = PRESETS[preset]
    with AudioFile(source) as audio_file:
        audio = audio_file.read(audio_file.frames)
        sample_rate = audio_file.samplerate
    tail = np.zeros(
        (audio.shape[0], int(sample_rate * settings["tail"])),
        dtype=audio.dtype,
    )
    audio = np.concatenate([audio, tail], axis=1)
    output = Pedalboard(settings["chain"]())(audio, sample_rate)
    peak = float(np.abs(output).max()) or 1.0
    output = output / peak * 0.89
    if settings["hiss"]:
        noise = np.random.default_rng(1).standard_normal(output.shape)
        output = output + (noise * settings["hiss"]).astype(output.dtype)
    with AudioFile(destination, "w", sample_rate, output.shape[0]) as audio_file:
        audio_file.write(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("destination")
    parser.add_argument("--preset", choices=sorted(PRESETS), default="room")
    args = parser.parse_args()
    mix(args.source, args.destination, args.preset)


if __name__ == "__main__":
    main()
