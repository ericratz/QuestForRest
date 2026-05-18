'''
render_helpers.py
Shared rendering primitives used across all render modules
'''

import pygame

SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720

_image_cache = {}


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


def _fonts(height):
    return (pygame.font.SysFont("Arial", max(int(height * 0.035), 18)),
            pygame.font.SysFont("Arial", max(int(height * 0.025), 14)))


def _draw_hp_bar(screen, x, y, w, h, current, maximum, label=""):
    ratio = current / max(1, maximum)
    color = (80, 200, 80) if ratio > 0.5 else (220, 180, 0) if ratio > 0.25 else (200, 60, 60)
    pygame.draw.rect(screen, (50, 50, 50),       (x, y, w, h))
    pygame.draw.rect(screen, color,              (x, y, int(w * ratio), h))
    pygame.draw.rect(screen, (120, 120, 120),    (x, y, w, h), 1)
    if label:
        font = pygame.font.SysFont("Arial", max(h - 2, 10))
        t = font.render(label, True, (255, 255, 255))
        screen.blit(t, (x + w // 2 - t.get_width() // 2, y + h // 2 - t.get_height() // 2))
