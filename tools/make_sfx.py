#!/usr/bin/env python3
"""Synthesize Threat Tide's sound effects as WAV files.

Every effect is generated from code here, so the audio is original and owned
outright (no licence to track). Re-run to regenerate after tweaking:

    python3 tools/make_sfx.py            # writes sound/sfx/*.wav

Names match table/tt_sound.vbs. Import the WAVs into the table's Sound Manager
with the same names (without .wav). Voice callouts (vo_*) are not made here. Mechanical sounds (flippers,
slings, kickers...) use the recorded samples that come with the VPX blank table.
"""
import pathlib
import wave

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "sound" / "sfx"
SR = 44100
rng = np.random.default_rng(7)  # fixed seed: same files every run


def t(sec):
    return np.arange(int(SR * sec)) / SR


def env(n, attack=0.005, release=None, curve=4.0):
    """Fast attack, exponential-ish decay over n samples."""
    a = max(1, int(SR * attack))
    e = np.ones(n)
    e[:a] = np.linspace(0, 1, a)
    tail = np.linspace(0, 1, n - a)
    e[a:] = (1 - tail) ** curve if release is None else np.exp(-tail * n / SR / release)
    return e


def tone(freq_start, freq_end, sec, shape="sine"):
    x = t(sec)
    f = np.geomspace(freq_start, freq_end, len(x))
    ph = 2 * np.pi * np.cumsum(f) / SR
    if shape == "square":
        return np.sign(np.sin(ph)) * 0.6
    if shape == "saw":
        return 2 * ((ph / (2 * np.pi)) % 1) - 1
    if shape == "tri":
        return 2 * np.abs(2 * ((ph / (2 * np.pi)) % 1) - 1) - 1
    return np.sin(ph)


def noise(sec, lowpass=None):
    n = rng.standard_normal(int(SR * sec))
    if lowpass:
        k = max(1, int(SR / lowpass))
        n = np.convolve(n, np.ones(k) / k, mode="same")
    return n


def thump(freq, sec, click=0.4):
    """Body thump plus a click: mechanical hits."""
    body = tone(freq * 1.8, freq, sec) * env(int(SR * sec), 0.001, curve=6)
    c = noise(0.012, lowpass=6000) * env(int(SR * 0.012), 0.0005, curve=3)
    out = body.copy()
    out[: len(c)] += c * click
    return out


def notes(seq, shape="square", gap=0.0, decay=3.0):
    """seq: list of (freq, seconds)."""
    parts = []
    for f, d in seq:
        s = tone(f, f, d, shape) * env(int(SR * d), 0.003, curve=decay)
        parts.append(s)
        if gap:
            parts.append(np.zeros(int(SR * gap)))
    return np.concatenate(parts)


def mix(*sigs):
    n = max(len(s) for s in sigs)
    out = np.zeros(n)
    for s in sigs:
        out[: len(s)] += s
    return out


def delay(sig, sec=0.09, fb=0.35, taps=4):
    d = int(SR * sec)
    out = np.zeros(len(sig) + d * taps)
    for i in range(taps + 1):
        out[i * d : i * d + len(sig)] += sig * (fb ** i)
    return out


def save(name, sig, peak_db=-3.0):
    sig = sig - np.mean(sig)
    sig = sig / (np.max(np.abs(sig)) + 1e-9) * (10 ** (peak_db / 20))
    fade = min(len(sig), int(SR * 0.004))
    sig[-fade:] *= np.linspace(1, 0, fade)
    data = (sig * 32767).astype("<i2")
    OUT.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    return name


C5, E5, G5, A5, C6, E6, G6 = 523.25, 659.25, 783.99, 880.0, 1046.5, 1318.5, 1568.0
A3, C4, E4, G4 = 220.0, 261.63, 329.63, 392.0


def build():
    made = []
    # Game cues
    made.append(save("sfx_card", mix(notes([(E6, 0.05), (A5 * 2, 0.09)], "square", decay=2),
                                     tone(4000, 2500, 0.03) * env(int(SR * 0.03)) * 0.2), -4))
    made.append(save("sfx_unlit", notes([(A3 * 2, 0.08)], "tri", decay=4), -8))
    made.append(save("sfx_combo", delay(notes([(C5, 0.06), (E5, 0.06), (G5, 0.06), (C6, 0.16)], "square"), 0.07, 0.3, 3), -3))
    made.append(save("sfx_edr", mix(tone(1400, 1400, 0.09, "square") * env(int(SR * 0.09), 0.002, curve=0.5),
                                    np.concatenate([np.zeros(int(SR * 0.12)), tone(1100, 1100, 0.14, "square") * env(int(SR * 0.14), 0.002, curve=1)])), -5))
    made.append(save("sfx_asset", mix(thump(70, 0.35, 0.8), noise(0.3, 1200) * env(int(SR * 0.3), 0.002, curve=3) * 0.5,
                                      tone(300, 90, 0.4, "saw") * env(int(SR * 0.4), 0.002, curve=3) * 0.4), -3))
    made.append(save("sfx_patch", notes([(G5, 0.08), (E5, 0.08), (C5, 0.2)], "tri", gap=0.02), -5))
    made.append(save("sfx_ballsave", delay(notes([(G4, 0.07), (C5, 0.07), (G5, 0.18)], "tri"), 0.08, 0.3, 2), -4))
    made.append(save("sfx_tilt_warning", notes([(180, 0.18), (180, 0.18)], "square", gap=0.08, decay=0.6), -5))
    made.append(save("sfx_gameover", delay(notes([(E5, 0.22), (C5, 0.22), (A3 * 2, 0.22), (E4, 0.6)], "tri", decay=1.5), 0.18, 0.3, 3), -3))
    made.append(save("sfx_lock_lit", notes([(C6, 0.05), (G6, 0.12)], "square", gap=0.03), -5))

    return made


if __name__ == "__main__":
    names = build()
    print(f"wrote {len(names)} files to {OUT.relative_to(ROOT)}: {', '.join(names)}")
