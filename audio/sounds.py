'''
audio/sounds.py
Maps game sound names to files from the Kenney packs in assets/sfx/.
To swap any sound, just change its path in _FILE_MAP below.

Packs used:
  assets/sfx/kenney_rpg-audio/Audio/
  assets/sfx/kenney_ui-audio/Audio/
  assets/sfx/80-CC0-RPG-SFX/
  assets/sfx/SoundPack01/

Background music: assets/music/<name>.ogg  (village, dark_forest, deep_caverns)
'''

import os
import pygame

_SFX_DIR   = os.path.join(os.path.dirname(os.path.dirname(
                 os.path.abspath(__file__))), "assets", "sfx")
_MUSIC_DIR = os.path.join(os.path.dirname(os.path.dirname(
                 os.path.abspath(__file__))), "assets", "music")

_RPG_MUSIC = os.path.join(_MUSIC_DIR, "Monster RPG 2 OGG Music - Revised")

# ── Music file map ────────────────────────────────────────────────────────────
_MUSIC_MAP = {
    "village":      os.path.join(_MUSIC_DIR, "SNES RPG overworld loop II.wav"),
    "dark_forest":  os.path.join(_MUSIC_DIR, "ThroughFire.ogg"),
    "deep_caverns": os.path.join(_RPG_MUSIC, "underground.ogg"),
    "battle":       os.path.join(_RPG_MUSIC, "battle.ogg"),
    "boss":         os.path.join(_MUSIC_DIR, "cynicbattleloop.ogg"),
}

_RPG  = os.path.join(_SFX_DIR, "kenney_rpg-audio", "Audio")
_UI   = os.path.join(_SFX_DIR, "kenney_ui-audio",  "Audio")
_CC0  = os.path.join(_SFX_DIR, "80-CC0-RPG-SFX")
_SP01 = os.path.join(_SFX_DIR, "SoundPack01")

# ── Mapping: sound name → file path ──────────────────────────────────────────
_FILE_MAP = {
    "menu":       os.path.join(_UI,   "click1.ogg"),           # menu navigation
    "vol_sfx":    os.path.join(_UI,   "switch1.ogg"),          # SFX volume adjustment demo
    "error":      os.path.join(_UI,   "switch3.ogg"),          # can't do / not enough gold
    "purchase":   os.path.join(_RPG,  "clothBelt2.ogg"),       # buy item (gold + item exchange)
    "gold":       os.path.join(_CC0,  "item_misc_06.ogg"),     # find / earn gold / pay debt
    "pickup":     os.path.join(_RPG,  "cloth1.ogg"),           # find item / food in room
    "equip":      os.path.join(_RPG,  "knifeSlice2.ogg"),      # equip / unequip gear
    "hit":        os.path.join(_CC0,  "creature_misc_06.ogg"), # player attacks monster
    "hit_player": os.path.join(_CC0,  "creature_roar_01.ogg"), # monster attacks player
    "potion":     os.path.join(_SFX_DIR, "yodguard-potion-drink-3-540167.mp3"),  # drink potion
    "heal":       os.path.join(_CC0,  "spell_01.ogg"),         # campfire / fairy / rest heal
    "shrine":     os.path.join(_RPG,  "bookOpen.ogg"),        # shrine blessing
    "flee":       os.path.join(_RPG,  "drawKnife2.ogg"),      # escape combat
    "chest":      os.path.join(_RPG,  "metalLatch.ogg"),      # open chest
    "curse":      os.path.join(_RPG,  "creak1.ogg"),          # cursed room
    "defeat":     os.path.join(_SP01, "Downer01.ogg"),        # player dies
    "levelup":    os.path.join(_SP01, "Rise03.ogg"),          # level up fanfare
}

_sounds: dict        = {}
_sfx_volume: float   = 0.5
_music_volume: float = 0.5
_current_music: str  = ""
_pending: list       = []   # [(fire_at_ms, name, volume, exclusive), ...]
_priority_channel    = None  # dedicated pygame channel for exclusive sounds


# ── Public API ────────────────────────────────────────────────────────────────

def init():
    '''Call once after pygame.init(). Loads all mapped SFX files.'''
    global _priority_channel
    if not pygame.mixer.get_init():
        pygame.mixer.init(44100, -16, 2, 512)
    pygame.mixer.set_num_channels(16)
    _priority_channel = pygame.mixer.Channel(15)   # reserved for exclusive sounds
    for name, path in _FILE_MAP.items():
        if os.path.exists(path):
            try:
                _sounds[name] = pygame.mixer.Sound(path)
            except Exception:
                pass


def play(name: str, volume: float = 1.0):
    s = _sounds.get(name)
    if s:
        s.set_volume(max(0.0, min(1.0, volume * _sfx_volume)))
        s.play()


def play_exclusive(name: str, volume: float = 1.0):
    '''Stop all regular SFX and play this sound on the priority channel.
    Use for important one-shot sounds (level-up) that must not be buried.'''
    s = _sounds.get(name)
    if s and _priority_channel:
        pygame.mixer.stop()   # stop all non-priority channels
        s.set_volume(max(0.0, min(1.0, volume * _sfx_volume)))
        _priority_channel.play(s)


def play_delayed(name: str, delay_ms: int, volume: float = 1.0, exclusive: bool = False):
    '''Schedule a sound to play after delay_ms milliseconds.
    If exclusive=True, plays via play_exclusive (stops other SFX first).'''
    _pending.append((pygame.time.get_ticks() + delay_ms, name, volume, exclusive))


def tick():
    '''Call once per frame. Fires any pending delayed sounds whose time has come.'''
    now = pygame.time.get_ticks()
    fired = [p for p in _pending if p[0] <= now]
    for entry in fired:
        _pending.remove(entry)
        _, name, volume, exclusive = entry
        if exclusive:
            play_exclusive(name, volume)
        else:
            play(name, volume)


def set_sfx_volume(v: float):
    global _sfx_volume
    _sfx_volume = max(0.0, min(1.0, v))


def set_music_volume(v: float):
    global _music_volume
    _music_volume = max(0.0, min(1.0, v))
    pygame.mixer.music.set_volume(0.45 * _music_volume)


def set_music(name: str):
    '''Switch to a named music track. Silent if the file is missing.'''
    global _current_music
    if name == _current_music:
        return
    _current_music = name
    path = _MUSIC_MAP.get(name)
    if path and os.path.exists(path):
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(0.45 * _music_volume)
            pygame.mixer.music.play(-1)
        except Exception:
            pass
    else:
        pygame.mixer.music.stop()


def stop_music():
    global _current_music
    _current_music = ""
    pygame.mixer.music.stop()
