#!/usr/bin/env python3
"""make_sfx.py - makes every sound effect of Rescue Pets From the Ice from code (original, made for this game).

  python tools/make_sfx.py            # writes store-assets/audio/<Name>.ogg (Ogg Vorbis, 44.1 kHz mono)
  python tools/make_sfx.py TapIce1    # only these sounds

Needs numpy, scipy and soundfile (pip install numpy scipy soundfile; soundfile's wheel brings libsndfile with
Vorbis). Every sound is synthesised here, with fixed random seeds. An Ogg file gets a random stream serial
number each time it is written, so a sound whose samples haven't changed is NOT written again
(store-assets/audio/sources.json keeps a hash of each sound's samples), and the uploader
(tools/upload_models.py) then skips it. The look of the sound: bright, cartoony and
icy: glassy bell partials, crisp crunches, celesta-like FM bells in a major key, a touch of reverb.

The names are the cue names in src/replicated/AudioConfig.luau (which gives each its volume). Loudness:
each file is normalised to the same short-term loudness (the loudest 100 ms at LOUDNESS_DB), then kept
under PEAK, so AudioConfig's volumes alone set the mix.
"""
import hashlib, json, os, sys
import numpy as np
from scipy import signal
import soundfile

RATE = 44100
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "store-assets", "audio")
LOUDNESS_DB = -14.0
PEAK = 0.93
TAU = 2 * np.pi

# ------------------------------------------------------------------------------------------------ basics

def t_axis(seconds):
    return np.arange(int(seconds * RATE)) / RATE


def silence(seconds):
    return np.zeros(int(seconds * RATE))


def place(track, sound, at):
    """Mixes `sound` into `track` starting `at` seconds in (the track grows if needed)."""
    start = int(at * RATE)
    end = start + len(sound)
    if end > len(track):
        track = np.concatenate([track, np.zeros(end - len(track))])
    track[start:end] += sound
    return track


def mix(*parts):
    """parts: (sound, at) pairs."""
    track = np.zeros(1)
    for sound, at in parts:
        track = place(track, sound, at)
    return track


def note(name):
    """'C5', 'F#4', 'Bb3' -> Hz."""
    names = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    semitone = names[name[0]]
    rest = name[1:]
    if rest.startswith("#"):
        semitone, rest = semitone + 1, rest[1:]
    elif rest.startswith("b"):
        semitone, rest = semitone - 1, rest[1:]
    midi = 12 * (int(rest) + 1) + semitone
    return 440.0 * 2 ** ((midi - 69) / 12)


def decay(t, seconds):
    """Exponential decay reaching -60 dB at `seconds`."""
    return np.exp(-6.9 * t / seconds)


def attack(t, seconds):
    return np.clip(t / max(seconds, 1e-4), 0, 1)


def fade_out(sound, seconds=0.02):
    n = min(len(sound), int(seconds * RATE))
    if n > 0:
        sound = sound.copy()
        sound[-n:] *= np.linspace(1, 0, n)
    return sound


def band(sound, low, high, order=2):
    nyq = RATE / 2
    low, high = max(low, 20) / nyq, min(high, nyq * 0.95) / nyq
    b, a = signal.butter(order, [low, high], btype="band")
    return signal.lfilter(b, a, sound)


def highpass(sound, cutoff, order=2):
    b, a = signal.butter(order, cutoff / (RATE / 2), btype="high")
    return signal.lfilter(b, a, sound)


def lowpass(sound, cutoff, order=2):
    b, a = signal.butter(order, min(cutoff / (RATE / 2), 0.95), btype="low")
    return signal.lfilter(b, a, sound)


def noise(rng, seconds):
    return rng.uniform(-1, 1, int(seconds * RATE))


def sweep_band(rng, seconds, f_from, f_to, q=2.5, chunk=0.01):
    """Noise through a band-pass whose centre glides from f_from to f_to (a whoosh). Overlap-added chunks."""
    source = noise(rng, seconds + 0.1)
    out = np.zeros(len(source))
    size = int(chunk * RATE)
    window = np.hanning(size * 2)
    for start in range(0, len(source) - size * 2, size):
        k = start / max(1, len(source) - size * 2)
        centre = f_from * (f_to / f_from) ** k
        piece = band(source[start:start + size * 2], centre / (1 + 1 / q), centre * (1 + 1 / q))
        out[start:start + size * 2] += piece * window
    return out[: int(seconds * RATE)]


def reverb(sound, amount=0.25, size=1.0, tail=1.2):
    """A small Schroeder reverb (four combs and two all-passes): an icy room."""
    padded = np.concatenate([sound, np.zeros(int(tail * RATE))])
    wet = np.zeros(len(padded))
    for delay_ms, feedback in ((29.7, 0.80), (37.1, 0.78), (41.1, 0.76), (43.7, 0.74)):
        d = int(delay_ms * size * RATE / 1000)
        a = np.zeros(d + 1)
        a[0], a[d] = 1, -feedback
        wet += signal.lfilter([1], a, padded)
    for delay_ms, gain in ((5.0, 0.7), (1.7, 0.7)):
        d = int(delay_ms * RATE / 1000)
        b = np.zeros(d + 1)
        a = np.zeros(d + 1)
        b[0], b[d] = -gain, 1
        a[0], a[d] = 1, -gain
        wet = signal.lfilter(b, a, wet)
    wet = highpass(wet, 300) / 4
    return fade_out(padded + amount * wet, 0.15)


def trim(sound, floor_db=-60):
    """Cuts the silent end."""
    level = np.abs(sound)
    threshold = level.max() * 10 ** (floor_db / 20)
    loud = np.nonzero(level > threshold)[0]
    end = (loud[-1] + int(0.02 * RATE)) if len(loud) else len(sound)
    return fade_out(sound[: min(end, len(sound))], 0.015)

# ------------------------------------------------------------------------------------------- instruments

def glass(freq, seconds, rng=None, partials=(1.0, 2.32, 4.25, 6.63), bright=1.0):
    """A glassy, inharmonic ping (ice): each higher partial is quieter and dies sooner."""
    t = t_axis(seconds)
    out = np.zeros(len(t))
    for i, ratio in enumerate(partials):
        detune = 1 + (rng.uniform(-0.01, 0.01) if rng is not None else 0)
        out += (bright ** i) * (0.62 ** i) * np.sin(TAU * freq * ratio * detune * t) * decay(t, seconds / (1 + 0.9 * i))
    return out * attack(t, 0.0015)


def bell(freq, seconds, index=2.2, ratio=3.5, attack_s=0.002):
    """A bright FM bell / celesta (the cartoony chime): the brightness dies faster than the tone."""
    t = t_axis(seconds)
    mod = index * decay(t, seconds * 0.35) * np.sin(TAU * freq * ratio * t)
    tone = np.sin(TAU * freq * t + mod) + 0.25 * np.sin(TAU * freq * 2 * t) * decay(t, seconds * 0.4)
    return tone * decay(t, seconds) * attack(t, attack_s)


def marimba(freq, seconds=0.45):
    """A soft mallet: the tone plus a quick 4th harmonic and a wooden knock."""
    t = t_axis(seconds)
    tone = np.sin(TAU * freq * t) * decay(t, seconds) + 0.35 * np.sin(TAU * freq * 3.98 * t) * decay(t, seconds * 0.18)
    return tone * attack(t, 0.002)


def brass(freq, seconds, rng):
    """A soft cartoon brass: detuned saws, low-passed, a little vibrato."""
    t = t_axis(seconds)
    vibrato = 1 + 0.004 * np.sin(TAU * 5.5 * t) * attack(t, 0.25)
    out = np.zeros(len(t))
    for detune in (-0.004, 0.0, 0.005):
        phase = np.cumsum(freq * (1 + detune) * vibrato) / RATE
        out += signal.sawtooth(TAU * phase)
    env = attack(t, 0.04) * np.clip((seconds - t) / 0.12, 0, 1) * (0.85 + 0.15 * decay(t, 0.4))
    return lowpass(out / 3, freq * 4.5) * env


def pad(freqs, seconds, rng, brightness=3.0):
    """A soft choir-ish pad: detuned saws per note, slow attack and release."""
    t = t_axis(seconds)
    out = np.zeros(len(t))
    for freq in freqs:
        for detune in (-0.006, 0.0, 0.007):
            out += signal.sawtooth(TAU * freq * (1 + detune) * t + rng.uniform(0, TAU))
    out = lowpass(out / (3 * len(freqs)), freqs[0] * brightness)
    env = attack(t, seconds * 0.25) * np.clip((seconds - t) / (seconds * 0.45), 0, 1)
    return out * env


def thump(seconds=0.35, f_from=110, f_to=42, level=1.0):
    """A soft low boom: a sine gliding down."""
    t = t_axis(seconds)
    freq = f_to + (f_from - f_to) * decay(t, seconds * 0.5)
    return level * np.sin(TAU * np.cumsum(freq) / RATE) * decay(t, seconds) * attack(t, 0.003)


def crunch(rng, seconds=0.05, low=1800, high=7000):
    """A short crisp noise burst (snow/ice crunch)."""
    t = t_axis(seconds)
    grains = noise(rng, seconds) * (rng.uniform(0, 1, len(t)) > 0.55)
    return band(grains, low, high) * decay(t, seconds) * attack(t, 0.001)


def crackle(rng, seconds, count, low, high, level=1.0):
    """`count` sparse little clicks (ice cracking), denser at the start."""
    t = t_axis(seconds)
    clicks = np.zeros(len(t))
    for _ in range(count):
        at = int(len(t) * rng.beta(1.2, 3.0))
        width = int(rng.uniform(0.0008, 0.003) * RATE)
        end = min(len(t), at + width)
        clicks[at:end] += rng.uniform(-1, 1, end - at) * rng.uniform(0.3, 1.0)
    return level * band(clicks, low, high)


def sparkle(rng, seconds, count, low=2600, high=7200, level=0.35, spread=None):
    """Many tiny high pings scattered in time (magic sparkle)."""
    spread = spread or seconds * 0.8
    out = silence(seconds + 0.3)
    for i in range(count):
        at = rng.uniform(0, spread) * (i / max(1, count - 1)) ** 0.6 if count > 1 else 0
        at = min(at, spread)
        freq = rng.uniform(low, high)
        ping = glass(freq, rng.uniform(0.08, 0.22), rng, partials=(1.0, 2.76), bright=0.6)
        out = place(out, ping * rng.uniform(0.4, 1.0) * level, at)
    return out


def arpeggio(notes, step, maker, **kwargs):
    """notes played `step` seconds apart with maker(freq, ...)."""
    return mix(*[(maker(note(n), **kwargs), i * step) for i, n in enumerate(notes)])

# ---------------------------------------------------------------------------------------------- sounds
# Each returns the finished samples. rng is seeded per sound, so a re-run is identical.

def tap_ice(variant):
    rng = np.random.default_rng(100 + variant)
    pitch = (2150, 2480, 1930, 2730)[variant - 1]
    body = glass(pitch, 0.13, rng, partials=(1.0, 1.73, 2.91, 4.4), bright=0.9) * 0.55
    tock = thump(0.05, 520, 300, 0.45)
    out = mix((crunch(rng, 0.045, 2200, 8000) * 1.1, 0), (body, 0.002), (tock, 0))
    return trim(reverb(out, 0.08, 0.6, 0.25))


def crack(stage):
    """Crack stages 1-4: thin and high at 20%, deep with a creak and a thump at 80%."""
    rng = np.random.default_rng(200 + stage)
    seconds = (0.32, 0.45, 0.62, 0.9)[stage - 1]
    low = (2400, 1400, 800, 450)[stage - 1]
    high = (9000, 7000, 5000, 3800)[stage - 1]
    out = crackle(rng, seconds, 22 + 14 * stage, low, high, 1.0)
    burst = band(noise(rng, 0.12), low * 0.8, high) * decay(t_axis(0.12), 0.12) * 0.5
    out = mix((out, 0), (burst, 0))
    if stage >= 2:
        out = place(out, glass(note(("A6", "E6", "B5", "F#5")[stage - 1]), 0.3, rng) * 0.25, 0.01)
    if stage >= 3:
        out = place(out, thump(0.35 + 0.15 * (stage - 3), 140, 55, 0.7 + 0.2 * (stage - 3)), 0)
    if stage == 4:
        t = t_axis(0.5)  # a groaning creak: a low tone with a rough FM wobble
        creak = np.sin(TAU * 95 * t + 3 * np.sin(TAU * 31 * t)) * decay(t, 0.5) * attack(t, 0.05)
        out = place(out, lowpass(creak, 900) * 0.35, 0.08)
    return trim(reverb(out, 0.15, 0.9, 0.6))


def shatter():
    rng = np.random.default_rng(300)
    t = t_axis(0.35)
    blast = highpass(noise(rng, 0.35), 900) * decay(t, 0.35) * 0.7
    tinkles = silence(1.4)
    for i in range(46):
        at = 0.6 * (rng.uniform(0, 1) ** 1.8)
        ping = glass(rng.uniform(1900, 7000), rng.uniform(0.07, 0.25), rng, bright=0.8)
        tinkles = place(tinkles, ping * rng.uniform(0.25, 0.7), at)
    out = mix((blast, 0), (crackle(rng, 0.4, 120, 1200, 8000, 0.8), 0), (tinkles, 0.01), (thump(0.45, 120, 40, 0.9), 0))
    return trim(reverb(out, 0.25, 1.0, 0.9))


RESCUE = {
    # rarity: (arpeggio, step, extra)
    "Common": (["C5", "E5", "G5"], 0.085),
    "Uncommon": (["C5", "E5", "G5", "C6"], 0.08),
    "Rare": (["D5", "F#5", "A5", "D6", "F#6"], 0.07),
    "Epic": (["C5", "E5", "G5", "C6", "E6", "G6", "C7"], 0.06),
    "Legendary": (["G4", "C5", "E5", "G5", "C6", "E6", "G6"], 0.055),
    "Mythic": (["C5", "D5", "E5", "G5", "A5", "C6", "D6", "E6", "G6", "A6", "C7"], 0.04),
}


def rescue(rarity):
    rng = np.random.default_rng(400 + list(RESCUE).index(rarity))
    notes, step = RESCUE[rarity]
    rank = list(RESCUE).index(rarity)  # 0 Common .. 5 Mythic
    if rank <= 1:
        run = arpeggio(notes, step, marimba, seconds=0.5)
        top = bell(note(notes[-1]) * 2, 0.6) * 0.3
        out = mix((run, 0), (top, step * len(notes)), (sparkle(rng, 0.5, 6 + 4 * rank, level=0.25), 0.15))
        return trim(reverb(out, 0.2, 0.8, 0.7))
    run = arpeggio(notes, step, bell, seconds=0.7)
    end = step * len(notes)
    root = notes[0]
    chord = {"Rare": ["D5", "F#5", "A5"], "Epic": ["C5", "E5", "G5", "B5"],
             "Legendary": ["C5", "E5", "G5", "C6"], "Mythic": ["C5", "E5", "G5", "B5", "D6"]}[rarity]
    hold = 0.9 + 0.35 * (rank - 2)
    chime = mix(*[(bell(note(n), hold + 0.6, index=1.6) * 0.4, 0) for n in chord])
    parts = [(run * 0.8, 0), (chime, end), (sparkle(rng, hold, 10 + 8 * rank, level=0.3), end)]
    if rank >= 3:  # Epic and up: a low boom on the chord
        parts.append((thump(0.6, 100, 45, 0.8), end))
    if rarity in ("Legendary", "Mythic"):  # a cartoon brass fanfare: da-da-daaa
        horn = [("G4", 0.12), ("G4", 0.12), ("C5", hold + 0.4)] if rarity == "Legendary" else [("C5", 0.11), ("E5", 0.11), ("G5", hold + 0.6)]
        at = end - 0.3
        for name, length in horn:
            parts.append((brass(note(name), length, rng) * 0.32, at))
            parts.append((brass(note(name) * 1.5, length, rng) * 0.18, at))
            at += length + 0.02
    if rarity == "Mythic":  # a rising glissando and a choir pad under the chord
        t = t_axis(0.5)
        gliss = np.sin(TAU * np.cumsum(note("C5") * 2 ** (2 * t / 0.5)) / RATE) * attack(t, 0.05) * 0.18
        parts.append((gliss, 0.0))
        parts.append((pad([note("C4"), note("G4"), note("E5")], hold + 1.2, rng) * 0.6, end - 0.1))
        parts.append((sparkle(rng, 1.8, 40, 3000, 8000, level=0.28), end + 0.3))
    out = mix(*parts)
    return trim(reverb(out, 0.3, 1.1, 1.4))


def golden_sparkle():
    rng = np.random.default_rng(500)
    shimmer = sparkle(rng, 1.0, 34, 3200, 8500, level=0.45)
    ching = mix((bell(note("E7"), 0.8, index=3.0) * 0.4, 0), (bell(note("B7"), 0.7, index=2.5) * 0.3, 0.06))
    t = t_axis(0.9)
    rise = highpass(sweep_band(rng, 0.9, 2500, 9000, q=4), 1500) * attack(t, 0.6) * decay(t[::-1], 0.3)[::-1] * 0.25
    out = mix((rise, 0), (shimmer, 0.1), (ching, 0.55))
    return trim(reverb(out, 0.3, 1.0, 1.0))


def crystal_tick():
    rng = np.random.default_rng(600)
    out = mix((glass(note("E7"), 0.12, rng, partials=(1.0, 2.76), bright=0.5), 0), (glass(note("B7"), 0.09, rng, partials=(1.0,)) * 0.4, 0.035))
    return trim(reverb(out, 0.12, 0.6, 0.3))


def buy_building():
    rng = np.random.default_rng(700)
    t = t_axis(0.09)
    knock = lowpass(noise(rng, 0.09), 900) * decay(t, 0.09) * 0.8 + np.sin(TAU * 190 * t) * decay(t, 0.09)
    ching = mix((bell(note("E6"), 0.45, index=3.0) * 0.55, 0), (bell(note("A6"), 0.6, index=3.0) * 0.6, 0.07))
    out = mix((knock, 0), (thump(0.2, 160, 80, 0.5), 0), (ching, 0.09), (sparkle(rng, 0.4, 8, level=0.22), 0.16))
    return trim(reverb(out, 0.18, 0.8, 0.6))


def buy_upgrade():
    rng = np.random.default_rng(800)
    run = arpeggio(["G5", "B5", "D6", "G6"], 0.055, bell, seconds=0.4, index=1.8)
    out = mix((run, 0), (sparkle(rng, 0.45, 12, level=0.25), 0.12))
    return trim(reverb(out, 0.2, 0.8, 0.6))


def nope():
    """A soft low 'nope': two muted notes falling, with a little pitch bend down."""
    def boop(freq, seconds):
        t = t_axis(seconds)
        bend = freq * (1 - 0.06 * t / seconds)
        tone = signal.sawtooth(TAU * np.cumsum(bend) / RATE, 0.5)  # a triangle
        return lowpass(tone, 900) * attack(t, 0.01) * decay(t, seconds * 1.4) * np.clip((seconds - t) / 0.04, 0, 1)
    out = mix((boop(note("E4"), 0.12), 0), (boop(note("C4"), 0.17), 0.13))
    return trim(reverb(out, 0.08, 0.6, 0.2))


def click():
    t = t_axis(0.05)
    freq = 650 + 900 * decay(t, 0.012)
    pop = np.sin(TAU * np.cumsum(freq) / RATE) * decay(t, 0.05) * attack(t, 0.0008)
    return trim(pop)


def hover():
    """The softest tick (the mouse moving onto something clickable): a tiny rounded wooden-glass tap, ~30 ms."""
    t = t_axis(0.035)
    freq = 1900 + 500 * decay(t, 0.006)
    tick = np.sin(TAU * np.cumsum(freq) / RATE) * decay(t, 0.03) * attack(t, 0.0015)
    return trim(lowpass(tick, 4000))


def window_open():
    rng = np.random.default_rng(900)
    t = t_axis(0.18)
    freq = 480 + 700 * (t / 0.18) ** 0.7
    pop = np.sin(TAU * np.cumsum(freq) / RATE) * attack(t, 0.01) * decay(t, 0.2) * 0.8
    swish = sweep_band(rng, 0.18, 1200, 5000, q=2) * attack(t, 0.08) * decay(t, 0.18) * 0.35
    out = mix((swish, 0), (pop, 0.02), (glass(note("E6"), 0.15, rng, partials=(1.0, 2.76)) * 0.25, 0.12))
    return trim(reverb(out, 0.1, 0.6, 0.3))


def window_close():
    rng = np.random.default_rng(901)
    t = t_axis(0.16)
    freq = 1000 - 520 * (t / 0.16) ** 0.7
    pop = np.sin(TAU * np.cumsum(freq) / RATE) * attack(t, 0.006) * decay(t, 0.18) * 0.8
    swish = sweep_band(rng, 0.16, 4500, 1100, q=2) * decay(t, 0.16) * 0.3
    return trim(reverb(mix((swish, 0), (pop, 0)), 0.08, 0.6, 0.25))


def rebirth():
    rng = np.random.default_rng(1000)
    rise_s = 1.15
    t = t_axis(rise_s)
    whoosh = sweep_band(rng, rise_s, 180, 6500, q=1.8) * (t / rise_s) ** 1.6 * 0.9
    gliss = np.sin(TAU * np.cumsum(note("C4") * 2 ** (3 * (t / rise_s) ** 1.5)) / RATE) * (t / rise_s) ** 2 * 0.12
    chord = ["C5", "E5", "G5", "B5", "C6", "E6"]
    chime = mix(*[(bell(note(n), 2.2, index=1.8) * 0.33, i * 0.03) for i, n in enumerate(chord)])
    out = mix((whoosh, 0), (gliss, 0), (thump(0.9, 90, 35, 1.0), rise_s - 0.02), (chime, rise_s),
              (pad([note("C4"), note("G4"), note("E5")], 2.0, rng) * 0.4, rise_s),
              (sparkle(rng, 1.6, 44, 3000, 8500, level=0.3), rise_s + 0.05))
    return trim(reverb(out, 0.35, 1.2, 1.6))


def book_page():
    rng = np.random.default_rng(1100)
    run = arpeggio(["C5", "E5", "G5", "C6", "E6"], 0.07, bell, seconds=0.9, index=1.6)
    hold = mix(*[(bell(note(n), 1.3, index=1.2) * 0.35, 0) for n in ("C5", "E5", "G5", "C6")])
    out = mix((run * 0.8, 0), (hold, 0.38), (pad([note("C4"), note("G4")], 1.4, rng) * 0.35, 0.3),
              (sparkle(rng, 1.0, 22, level=0.28), 0.38))
    return trim(reverb(out, 0.3, 1.0, 1.2))


def book_new():
    rng = np.random.default_rng(1200)
    out = mix((bell(note("G5"), 0.4, index=2.6) * 0.7, 0), (bell(note("D6"), 0.6, index=2.6) * 0.8, 0.1),
              (sparkle(rng, 0.4, 10, level=0.25), 0.12))
    return trim(reverb(out, 0.2, 0.8, 0.6))


def heartbeat():
    """A soft, slow 'lub-dub' (the creature about to break free, at 80%): two low thumps."""
    def beat(freq, seconds, level):
        t = t_axis(seconds)
        glide = freq * (1 + 0.6 * decay(t, 0.03))
        body = np.sin(TAU * np.cumsum(glide) / RATE) * decay(t, seconds) * attack(t, 0.004)
        return lowpass(body, 300) * level
    out = mix((beat(62, 0.22, 1.0), 0), (beat(54, 0.26, 0.75), 0.16))
    return trim(reverb(out, 0.08, 0.7, 0.3))


def golden_alarm():
    """The Golden Glacier is coming: a bright three-note chime, twice, with a gold shimmer."""
    rng = np.random.default_rng(1300)
    notes = ["G5", "B5", "D6"]
    once = arpeggio(notes, 0.09, bell, seconds=0.5, index=2.8)
    out = mix((once, 0), (once * 0.85, 0.42), (bell(note("G6"), 0.9, index=2.0) * 0.5, 0.84),
              (sparkle(rng, 0.9, 18, 3200, 8000, level=0.25), 0.8))
    return trim(reverb(out, 0.25, 1.0, 0.9))


SOUNDS = {
    **{f"TapIce{v}": (lambda v=v: tap_ice(v)) for v in (1, 2, 3, 4)},
    **{f"Crack{s}": (lambda s=s: crack(s)) for s in (1, 2, 3, 4)},
    "Shatter": shatter,
    **{f"Rescue{r}": (lambda r=r: rescue(r)) for r in RESCUE},
    "GoldenSparkle": golden_sparkle,
    "CrystalTick": crystal_tick,
    "BuyBuilding": buy_building,
    "BuyUpgrade": buy_upgrade,
    "Nope": nope,
    "Click": click,
    "Hover": hover,
    "WindowOpen": window_open,
    "WindowClose": window_close,
    "Rebirth": rebirth,
    "BookPage": book_page,
    "BookNew": book_new,
    "Heartbeat": heartbeat,
    "GoldenAlarm": golden_alarm,
}


def master(sound):
    """Same short-term loudness for every file, then a peak limit."""
    sound = sound - np.mean(sound)
    window = int(0.1 * RATE)
    power = np.convolve(sound ** 2, np.ones(window) / window, mode="valid") if len(sound) > window else [np.mean(sound ** 2)]
    loudest = np.sqrt(np.max(power)) + 1e-9
    sound = sound * (10 ** (LOUDNESS_DB / 20) / loudest)
    peak = np.max(np.abs(sound))
    if peak > PEAK:
        sound *= PEAK / peak
    return sound


def main():
    names = sys.argv[1:] or list(SOUNDS)
    unknown = [n for n in names if n not in SOUNDS]
    if unknown:
        sys.exit("Unknown sound(s): %s. Known: %s" % (", ".join(unknown), ", ".join(SOUNDS)))
    os.makedirs(OUT, exist_ok=True)
    hashes_path = os.path.join(OUT, "sources.json")
    hashes = json.load(open(hashes_path, encoding="utf-8")) if os.path.exists(hashes_path) else {}
    for name in names:
        sound = master(SOUNDS[name]()).astype(np.float32)
        path = os.path.join(OUT, name + ".ogg")
        digest = hashlib.sha256(sound.tobytes()).hexdigest()
        if hashes.get(name) == digest and os.path.exists(path):
            print("%-18s unchanged" % name)
            continue
        soundfile.write(path, sound, RATE, format="OGG", subtype="VORBIS")
        hashes[name] = digest
        print("%-18s %5.2f s  peak %.2f  %s" % (name, len(sound) / RATE, np.max(np.abs(sound)), os.path.relpath(path)))
    with open(hashes_path, "w", encoding="utf-8") as handle:
        json.dump(hashes, handle, indent=1, sort_keys=True)


if __name__ == "__main__":
    main()
