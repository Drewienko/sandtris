"""
SoundManager — programmatic SFX via numpy, no asset files required.

Usage:
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.mixer.init()
    sm = SoundManager()
    sm.register(event_bus)      # wires observer callbacks
    sm.start_music()            # desktop only; web defers to first gesture
"""

import numpy as np
import pygame

from sandtris.core.event_bus import GameEventBus

_SR = 44100  # sample rate

# Musical constants (Hz)
C3, E3, G3 = 131, 165, 196
C4, E4, G4 = 262, 330, 392

_COMBO_NOTES = [C3, E3, G3, C4, E4, G4]  # index = combo level - 1


# ---------------------------------------------------------------------------
# Low-level primitives
# ---------------------------------------------------------------------------

def _sine(freq: float, n: int) -> np.ndarray:
    t = np.linspace(0, n / _SR, n, dtype=np.float32)
    return np.sin(2 * np.pi * freq * t)


def _noise(n: int) -> np.ndarray:
    return np.random.uniform(-1, 1, n).astype(np.float32)


def _sweep(f0: float, f1: float, n: int) -> np.ndarray:
    freqs = np.linspace(f0, f1, n, dtype=np.float32)
    phase = np.cumsum(2 * np.pi * freqs / _SR)
    return np.sin(phase).astype(np.float32)


def _adsr(
    n: int,
    attack: float = 0.05,
    decay: float = 0.1,
    sustain: float = 0.8,
    release: float = 0.3,
) -> np.ndarray:
    env = np.ones(n, dtype=np.float32)
    a, d, r = int(n * attack), int(n * decay), int(n * release)
    if a:
        env[:a] = np.linspace(0, 1, a)
    if d:
        env[a:a + d] = np.linspace(1, sustain, d)
    env[a + d:n - r] = sustain
    if r:
        env[n - r:] = np.linspace(sustain, 0, r)
    return env


def _grain(n: int, amount: float = 0.03) -> np.ndarray:
    return 1.0 + np.random.uniform(-amount, amount, n).astype(np.float32)


def _to_sound(samples: np.ndarray) -> pygame.Sound:
    samples = np.clip(samples, -1, 1)
    stereo = np.column_stack([samples, samples])
    return pygame.sndarray.make_sound((stereo * 32767).astype(np.int16))


# ---------------------------------------------------------------------------
# SFX builders
# ---------------------------------------------------------------------------

def _build_move() -> pygame.Sound:
    n = int(_SR * 0.035)
    s = _sine(110, n) * 0.8 + _noise(n) * 0.06
    return _to_sound(s * _adsr(n, attack=0.25, decay=0.1, sustain=0.4, release=0.65) * 0.11)


def _build_rotate() -> pygame.Sound:
    n = int(_SR * 0.05)
    s = _sweep(220, 150, n) * 0.6 + _noise(n) * 0.25
    return _to_sound(s * _adsr(n, attack=0.06, decay=0.1, sustain=0.7, release=0.5) * 0.17)


def _build_hard_drop() -> pygame.Sound:
    n = int(_SR * 0.065)
    s = _sweep(250, 80, n) * 0.55 + _noise(n) * 0.4
    return _to_sound(s * _adsr(n, attack=0.02, decay=0.15, sustain=0.5, release=0.4) * 0.26)


def _build_clear(connections: int) -> pygame.Sound:
    if connections == 1:
        freqs, ms = [C3, E3, G3], 420
    elif connections == 2:
        freqs, ms = [C3, E3, G3, C4], 520
    else:
        freqs, ms = [C3, E3, G3, C4, E4], 650
    n = int(_SR * ms / 1000)
    mixed = sum(_sine(f, n) for f in freqs) / len(freqs)
    mixed = mixed * 0.93 + _noise(n) * 0.04
    return _to_sound(
        mixed * _adsr(n, attack=0.06, decay=0.08, sustain=0.80, release=0.35)
        * _grain(n, 0.02) * 0.30
    )


def _build_combo(level: int) -> pygame.Sound:
    freq = _COMBO_NOTES[min(level - 1, len(_COMBO_NOTES) - 1)]
    n = int(_SR * 0.11)
    s = _sine(freq, n) * 0.75 + _noise(n) * 0.06
    return _to_sound(s * _adsr(n, attack=0.05, decay=0.1, sustain=0.6, release=0.55)
                     * _grain(n, 0.02) * 0.22)


def _build_combo_expire() -> pygame.Sound:
    n = int(_SR * 0.15)
    s = _noise(n) * 0.5 + _sweep(150, 70, n) * 0.4
    return _to_sound(s * _adsr(n, attack=0.2, decay=0.1, sustain=0.5, release=0.6) * 0.15)


def _build_level_up() -> pygame.Sound:
    freqs = [C3, E3, G3, C4]
    step_n = int(_SR * 0.09)
    tail_n = int(_SR * 0.22)
    total = np.zeros(step_n * len(freqs) + tail_n, dtype=np.float32)
    for i, f in enumerate(freqs):
        n = step_n if i < len(freqs) - 1 else step_n + tail_n
        tone = _sine(f, n) * 0.8 + _noise(n) * 0.06
        total[i * step_n:i * step_n + n] += (
            tone * _adsr(n, attack=0.04, decay=0.08, sustain=0.7, release=0.55) * 0.30
        )
    return _to_sound(total)


def _build_game_over() -> pygame.Sound:
    n = int(_SR * 1.2)
    tone = _sweep(300, 55, n)
    hiss = _noise(n)
    surge = int(n * 0.1)
    henv = np.zeros(n, dtype=np.float32)
    henv[:surge] = np.linspace(0, 1, surge)
    henv[surge:] = np.linspace(1, 0, n - surge)
    s = (tone * _adsr(n, attack=0.02, decay=0.08, sustain=0.65, release=0.5) * 0.22
         + hiss * henv * 0.10)
    return _to_sound(s * _grain(n, 0.04))


def _build_victory() -> pygame.Sound:
    freqs = [C3, G3, C4, G4]
    step_n = int(_SR * 0.07)
    tail_n = int(_SR * 0.18)
    total = np.zeros(step_n * len(freqs) + tail_n, dtype=np.float32)
    for i, f in enumerate(freqs):
        n = step_n if i < len(freqs) - 1 else step_n + tail_n
        tone = _sine(f, n) * 0.82 + _noise(n) * 0.05
        total[i * step_n:i * step_n + n] += (
            tone * _adsr(n, attack=0.03, decay=0.08, sustain=0.65, release=0.55) * 0.22
        )
    return _to_sound(total)


def _build_pause() -> pygame.Sound:
    n = int(_SR * 0.07)
    s = _sine(180, n) * 0.6 + _noise(n) * 0.2
    return _to_sound(s * _adsr(n, attack=0.05, decay=0.1, sustain=0.5, release=0.65) * 0.25)


def _build_menu_nav() -> pygame.Sound:
    n = int(_SR * 0.038)
    s = _noise(n) * 0.65 + _sine(220, n) * 0.25
    return _to_sound(s * _adsr(n, attack=0.05, decay=0.1, sustain=0.4, release=0.65) * 0.13)


def _build_menu_select() -> pygame.Sound:
    n = int(_SR * 0.11)
    s = _sine(G3, n) * 0.8 + _noise(n) * 0.08
    return _to_sound(
        s * _adsr(n, attack=0.04, decay=0.1, sustain=0.65, release=0.6)
        * _grain(n, 0.03) * 0.24
    )


# ---------------------------------------------------------------------------
# SoundManager
# ---------------------------------------------------------------------------

class SoundManager:
    def __init__(self, sfx_volume: float = 0.7, music_volume: float = 0.25) -> None:
        self.sfx_volume = sfx_volume
        self.music_volume = music_volume
        self._muted = False
        self._music_started = False
        self._music_path: str | None = None

        pygame.mixer.set_num_channels(9)
        self._ch = {
            "move":   pygame.mixer.Channel(0),
            "rotate": pygame.mixer.Channel(1),
            "drop":   pygame.mixer.Channel(2),
            "lock":   pygame.mixer.Channel(3),
            "clear":  pygame.mixer.Channel(4),
            "ui":     pygame.mixer.Channel(5),
            "level":  pygame.mixer.Channel(6),
            "death":  pygame.mixer.Channel(7),
        }

        # pre-generate all sounds (cached in memory, zero cost per play)
        self._sounds: dict[str, pygame.Sound] = {
            "rotate":       _build_rotate(),
            "hard_drop":    _build_hard_drop(),
            "lock":         _build_hard_drop(),   # same as hard_drop by design
            "clear_1":      _build_clear(1),
            "clear_2":      _build_clear(2),
            "clear_3":      _build_clear(3),
            **{f"combo_{i}": _build_combo(i) for i in range(1, 7)},
            "combo_expire": _build_combo_expire(),
            "level_up":     _build_level_up(),
            "game_over":    _build_game_over(),
            "victory":      _build_victory(),
            "pause":        _build_pause(),
            "menu_nav":     _build_menu_nav(),
            "menu_select":  _build_menu_select(),
        }
        self._set_volumes()

    # ------------------------------------------------------------------
    # Volume / mute
    # ------------------------------------------------------------------

    def _set_volumes(self) -> None:
        v = 0.0 if self._muted else self.sfx_volume
        for snd in self._sounds.values():
            snd.set_volume(v)

    def set_sfx_volume(self, v: float) -> None:
        self.sfx_volume = max(0.0, min(1.0, v))
        self._set_volumes()

    def set_music_volume(self, v: float) -> None:
        self.music_volume = max(0.0, min(1.0, v))
        if not self._muted:
            pygame.mixer.music.set_volume(self.music_volume)

    def set_muted(self, muted: bool) -> None:
        self._muted = muted
        self._set_volumes()
        if muted:
            pygame.mixer.music.set_volume(0.0)
        else:
            pygame.mixer.music.set_volume(self.music_volume)

    # ------------------------------------------------------------------
    # Playback
    # ------------------------------------------------------------------

    def _play(self, channel: str, name: str) -> None:
        if self._muted:
            return
        snd = self._sounds.get(name)
        if snd is None:
            return
        ch = self._ch.get(channel)
        if ch is None:
            snd.play()
        else:
            ch.stop()
            ch.play(snd)

    # ------------------------------------------------------------------
    # Named play methods (called by observer callbacks)
    # ------------------------------------------------------------------

    def play_rotate(self) -> None:
        self._play("rotate", "rotate")

    def play_hard_drop(self) -> None:
        self._play("drop", "hard_drop")

    def play_lock(self) -> None:
        self._play("lock", "lock")

    def play_clear(self, connections: int = 1) -> None:
        key = f"clear_{min(connections, 3)}"
        self._play("clear", key)

    def play_combo(self, level: int = 1) -> None:
        key = f"combo_{min(level, 6)}"
        self._play("clear", key)

    def play_combo_expire(self) -> None:
        self._play("clear", "combo_expire")

    def play_level_up(self) -> None:
        self._play("level", "level_up")

    def play_game_over(self) -> None:
        self._play("death", "game_over")

    def play_victory(self) -> None:
        self._play("death", "victory")

    def play_pause(self) -> None:
        self._play("ui", "pause")

    def play_menu_nav(self) -> None:
        self._play("ui", "menu_nav")

    def play_menu_select(self) -> None:
        self._play("ui", "menu_select")

    def preview_volume(self) -> None:
        """Play menu_nav at current volume — call when settings slider moves."""
        self._play("ui", "menu_nav")

    # ------------------------------------------------------------------
    # Music
    # ------------------------------------------------------------------

    def load_music(self, path: str) -> None:
        try:
            pygame.mixer.music.load(path)
            self._music_path = path
            pygame.mixer.music.set_volume(self.music_volume)
        except Exception:
            self._music_path = None

    def start_music(self) -> None:
        if self._music_path and not self._music_started and not self._muted:
            try:
                pygame.mixer.music.play(-1)
                self._music_started = True
            except Exception:
                pass

    def stop_music(self) -> None:
        pygame.mixer.music.stop()
        self._music_started = False

    # ------------------------------------------------------------------
    # Observer registration
    # ------------------------------------------------------------------

    def register(self, bus: GameEventBus) -> None:
        bus.subscribe("rotate",       lambda **_: self.play_rotate())
        bus.subscribe("hard_drop",    lambda **_: self.play_hard_drop())
        bus.subscribe("lock",         lambda **_: self.play_lock())
        bus.subscribe("clear",        lambda connections=1, **_: self.play_clear(connections))
        bus.subscribe("combo",        lambda level=1, **_: self.play_combo(level))
        bus.subscribe("combo_expire", lambda **_: self.play_combo_expire())
        bus.subscribe("level_up",     lambda **_: self.play_level_up())
        bus.subscribe("game_over",    lambda **_: self.play_game_over())
        bus.subscribe("victory",      lambda **_: self.play_victory())
        bus.subscribe("pause",        lambda **_: self.play_pause())
        bus.subscribe("menu_nav",     lambda **_: self.play_menu_nav())
        bus.subscribe("menu_select",  lambda **_: self.play_menu_select())
