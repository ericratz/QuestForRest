'''
render/helpers.py
Shared rendering primitives used across all render modules.
'''

import os
import pygame

SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720

# ── Image cache ───────────────────────────────────────────────────────────────

_image_cache: dict = {}


def init_display():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("QuestForRest")
    try:
        import ctypes
        hwnd = pygame.display.get_wm_info().get("window")
        if hwnd:
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            ctypes.windll.user32.BringWindowToTop(hwnd)
    except Exception:
        pass
    return screen


def _load_image(path):
    if path not in _image_cache:
        _image_cache[path] = pygame.image.load(path).convert()
    return _image_cache[path]


def _bg(screen, image_path):
    w, h = screen.get_size()
    screen.blit(pygame.transform.scale(_load_image(image_path), (w, h)), (0, 0))


def _overlay(screen, alpha=185):
    w, h = screen.get_size()
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.fill((0, 0, 0, alpha))
    screen.blit(surf, (0, 0))


# ── Font cache ────────────────────────────────────────────────────────────────
# Looks for assets/font.ttf first; falls back to SysFont("Arial").
# Drop any TTF into assets/font.ttf to use a custom typeface.

_FONT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "font.ttf")
if not os.path.exists(_FONT_PATH):
    _FONT_PATH = None   # will use SysFont fallback

_font_cache: dict = {}


def _make_font(size: int) -> pygame.font.Font:
    if _FONT_PATH:
        return pygame.font.Font(_FONT_PATH, size)
    return pygame.font.SysFont("Arial", size)


def _fonts(height: int):
    '''Return (font, small_font) cached by pixel size.'''
    sz_main  = max(int(height * 0.035), 18)
    sz_small = max(int(height * 0.025), 14)
    key = (sz_main, sz_small)
    if key not in _font_cache:
        _font_cache[key] = (_make_font(sz_main), _make_font(sz_small))
    return _font_cache[key]


# ── Fade transition ───────────────────────────────────────────────────────────
# Call trigger_fade_in() whenever a major screen change occurs.
# display.render() calls _tick_draw_fade() each frame automatically.

_fade_alpha = 0
_FADE_SPEED  = 680   # alpha units per second → full fade-in in ~375 ms


def trigger_fade_in():
    global _fade_alpha
    _fade_alpha = 255


def _tick_draw_fade(screen, dt_ms: int):
    global _fade_alpha
    if _fade_alpha <= 0:
        return
    _fade_alpha = max(0, _fade_alpha - int(_FADE_SPEED * dt_ms / 1000))
    if _fade_alpha > 0:
        w, h = screen.get_size()
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill((0, 0, 0, _fade_alpha))
        screen.blit(surf, (0, 0))


# ── pygame.Rect helpers ───────────────────────────────────────────────────────

def _blit_center(screen, surf: pygame.Surface, cx: int, y: int) -> int:
    '''Blit surf centred horizontally at cx, top edge at y. Returns bottom y.'''
    r = surf.get_rect(midtop=(cx, y))
    screen.blit(surf, r)
    return r.bottom


def _blit_right(screen, surf: pygame.Surface, right_x: int, y: int) -> int:
    '''Blit surf so its right edge is at right_x. Returns bottom y.'''
    r = surf.get_rect(topright=(right_x, y))
    screen.blit(surf, r)
    return r.bottom


# ── HP bar ────────────────────────────────────────────────────────────────────

_hp_font_cache: dict = {}


def _draw_hp_bar(screen, x, y, w, h, current, maximum, label=""):
    ratio  = current / max(1, maximum)
    color  = (80, 200, 80) if ratio > 0.5 else (220, 180, 0) if ratio > 0.25 else (200, 60, 60)
    rect   = pygame.Rect(x, y, w, h)
    fill_r = pygame.Rect(x, y, int(w * ratio), h)
    pygame.draw.rect(screen, (50, 50, 50),    rect)
    pygame.draw.rect(screen, color,           fill_r)
    pygame.draw.rect(screen, (120, 120, 120), rect, 1)
    if label:
        sz = max(h - 2, 10)
        if sz not in _hp_font_cache:
            _hp_font_cache[sz] = _make_font(sz)
        fnt = _hp_font_cache[sz]
        t   = fnt.render(label, True, (255, 255, 255))
        screen.blit(t, t.get_rect(center=rect.center))
