"""Generate realistic piano-like WAVs using additive synthesis.

Creates a `sounds/` directory next to this file and writes WAVs
named like C4.wav, Cs4.wav, D4.wav, Ds4.wav ... B4.wav across octaves 1..7.
The synthesis uses multiple harmonics, slight inharmonicity, an ADSR-like envelope,
and a short attack noise burst to approximate a piano hammer strike.
"""
import os
import wave
import struct
import math
import random

OUT_DIR = os.path.join(os.path.dirname(__file__), 'sounds')
SOUNDS_DIR = OUT_DIR
os.makedirs(OUT_DIR, exist_ok=True)

SAMPLE_RATE = 44100
DURATION = 2.8

# Semitones relative to A4 (0)
NOTE_SEMITONES = {
    'C': -9,
    'Cs': -8,
    'D': -7,
    'Ds': -6,
    'E': -5,
    'F': -4,
    'Fs': -3,
    'G': -2,
    'Gs': -1,
    'A': 0,
    'As': 1,
    'B': 2,
}

def freq_for(note, octave):
    semitone = NOTE_SEMITONES[note] + (octave - 4) * 12
    return 440.0 * (2.0 ** (semitone / 12.0))

def write_note(path, frequency, duration=DURATION, rate=SAMPLE_RATE):
    n_samples = int(rate * duration)
    max_amp = 30000

    # Harmonic amplitudes
    harmonics = [1.0, 0.58, 0.33, 0.20, 0.12, 0.08, 0.05]
    inharm = [1.0 + 0.0008 * (i**1.5) for i in range(len(harmonics))]

    attack = 0.005
    decay = 1.6

    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)

        frames = bytearray()
        for i in range(n_samples):
            t = i / rate
            if t < attack:
                env = t / attack
            else:
                env = math.exp(-(t - attack) / decay)

            sample = 0.0
            for idx, h_amp in enumerate(harmonics, start=1):
                partial_freq = frequency * idx * inharm[idx - 1]
                sample += h_amp * math.sin(2.0 * math.pi * partial_freq * t)

            # Attack hammer burst
            if t < 0.02:
                sample += (random.random() * 2 - 1) * (0.35 * math.exp(-t * 80))

            value = sample * 0.55 * env
            val = int(max(-32767, min(32767, value * max_amp)))
            frames.extend(struct.pack('<h', val))

        wf.writeframesraw(frames)

def generate_all_sounds():
    notes = ['C', 'Cs', 'D', 'Ds', 'E', 'F', 'Fs', 'G', 'Gs', 'A', 'As', 'B']
    octaves = range(1, 8)
    for octv in octaves:
        for n in notes:
            fname = f"{n}{octv}.wav"
            path = os.path.join(OUT_DIR, fname)
            if not os.path.isfile(path):
                f = freq_for(n, octv)
                write_note(path, f)

if __name__ == '__main__':
    print("Synthesizing full 12-tone chromatic piano sound library...")
    generate_all_sounds()
    print("Done! All sounds generated in 'sounds/' folder.")

