'''
display.py
Master render dispatcher and main game view.
Shared primitives live in render_helpers.py.
Adventure renders in render_adventure.py.
Village/menu renders in render_village.py.
'''

import pygame
import state.gamestate as gamestate
from render.helpers import init_display, _bg, _overlay, _fonts
import render.adventure as adventure
import render.village as village


# ── Main game view ────────────────────────────────────────────────────────────

def _render_work_result(screen, wState, font, small, w, h):
    _overlay(screen, 200)
    cx = w // 2
    y  = h // 2 - font.get_height() * 3
    text, gold, food = wState.work_result
    parts = []
    if gold > 0:
        parts.append(f"Earned {gold}g!")
    if food > 0:
        parts.append(f"Found {food} food!")
    earn_line = "  ".join(parts)
    lines = [text]
    if earn_line:
        lines += ["", earn_line]
    lines += ["", "Press any key."]
    for line in lines:
        t = font.render(line, True, (255, 255, 255))
        screen.blit(t, (cx - t.get_width() // 2, y)); y += font.get_height() + 10


def _render_game(screen, wState, pState, area):
    w, h    = screen.get_size()
    font_sz = max(int(h * 0.03), 16)
    font    = pygame.font.SysFont("Arial", font_sz)
    small   = pygame.font.SysFont("Arial", max(int(h * 0.025), 14))

    _bg(screen, area.image)

    # HUD
    hud_h = font.get_height() + 16
    hud = pygame.Surface((w, hud_h), pygame.SRCALPHA)
    hud.fill((0, 0, 0, 160))
    screen.blit(hud, (0, 0))

    name_xp  = (f"{pState.name}  " if pState.name else "") + \
               f"Lv.{pState.level}  XP:{pState.xp}/{pState.xp_to_next()}"
    hp_ratio = pState.health / max(1, pState.get_max_health())
    hp_color = (80, 200, 80) if hp_ratio > 0.5 else (220, 180, 0) if hp_ratio > 0.25 else (200, 60, 60)
    hp_str   = f"  HP:{pState.health}/{pState.get_max_health()}"
    nxp_t = small.render(name_xp, True, (200, 200, 200))
    hp_t  = small.render(hp_str,  True, hp_color)
    screen.blit(nxp_t, (10, 8))
    screen.blit(hp_t,  (10 + nxp_t.get_width(), 8))

    day_t = small.render(f"Day {wState.day}", True, (200, 200, 200))
    screen.blit(day_t, (w // 2 - day_t.get_width() // 2, 8))

    right_parts = [f"Gold: {pState.gold}g", f"Food: {pState.food}"]
    if pState.debt > 0:
        right_parts.append(f"Debt: {pState.debt}g")
    right_t = small.render("   ".join(right_parts), True, (200, 200, 200))
    screen.blit(right_t, (w - right_t.get_width() - 10, 8))

    # Bottom options
    text_pad  = 10
    opt_row_h = font.get_height() + text_pad * 2
    opt_w     = w // 2

    choices   = list(area.choices.values())
    n_choices = len(choices)
    n_rows    = max(2, -(-n_choices // 2))

    text_bar_h = font.get_height() + text_pad * 2
    text_bar_y = h - text_bar_h - opt_row_h * n_rows
    text_bar   = pygame.Surface((w, text_bar_h), pygame.SRCALPHA)
    text_bar.fill((0, 0, 0, 150))
    screen.blit(text_bar, (0, text_bar_y))
    screen.blit(font.render(area.text, True, (255, 255, 255)), (text_pad, text_bar_y + text_pad))

    n_slots = n_rows * 2
    for i in range(n_slots):
        row = i // 2
        col = i % 2
        ox  = col * opt_w
        oy  = h - opt_row_h * (n_rows - row)
        has = i < n_choices
        sel = has and (i == wState.nav_index)
        bg  = pygame.Surface((opt_w, opt_row_h), pygame.SRCALPHA)
        bg.fill((100, 100, 140, 200) if sel else (20, 20, 30, 150))
        screen.blit(bg, (ox, oy))
        pygame.draw.rect(screen, (200, 200, 255) if sel else (50, 50, 70),
                         (ox, oy, opt_w, opt_row_h), 1)
        if has:
            _, desc = choices[i]
            t = font.render(desc, True, (255, 255, 255) if sel else (150, 150, 160))
            screen.blit(t, (ox + opt_w // 2 - t.get_width() // 2, oy + text_pad))

    # Confirmation dialog
    if wState.menu_confirm:
        _overlay(screen, 200)
        if wState.menu_confirm == "Saved":
            lines = ["Game saved!", "", "Press any key to continue"]
        else:
            lines = [f"{wState.menu_confirm} — are you sure?", "", "Enter: Yes    ESC: No"]
        cy = h // 2 - font.get_height() * len(lines) // 2
        for line in lines:
            t = font.render(line, True, (255, 255, 255))
            screen.blit(t, (w // 2 - t.get_width() // 2, cy)); cy += font.get_height() + 10

    elif wState.menu_open:
        _overlay(screen, 200)
        my = 50
        screen.blit(font.render("Menu", True, (255, 255, 255)), (50, my)); my += font.get_height() + 20
        mx_hp = pState.get_max_health()
        stats = font.render(f"HP: {pState.health}/{mx_hp}   Gold: {pState.gold}g   Food: {pState.food}",
                            True, (180, 180, 180))
        screen.blit(stats, (50, my)); my += font.get_height() + 20
        for i, item in enumerate(gamestate.MENU_ITEMS):
            color  = (255, 255, 0) if i == wState.menu_index else (255, 255, 255)
            prefix = "> " if i == wState.menu_index else "  "
            screen.blit(font.render(prefix + item, True, color), (50, my)); my += font.get_height() + 10

    if wState.work_result:
        _render_work_result(screen, wState, font, small, w, h)


# ── Master render dispatcher ──────────────────────────────────────────────────

def render(screen, wState, pState, area):
    if wState.quest_completion_popup:
        village.render_quest_popup(screen, wState, pState, area)
        return

    if wState.name_input_mode:
        village.render_name_input(screen, wState, area)
        return

    if wState.area == "start_screen":
        village.render_main_menu(screen, wState, area)
        return

    if wState.adventure_select_mode:
        adventure.render_adventure_select(screen, wState, pState, area)
        return

    if wState.inventory_open:
        village.render_inventory(screen, wState, pState, area)
        return

    if wState.in_combat or wState.post_combat_mode:
        adventure.render_combat(screen, wState, pState)
        return

    if wState.adventure_trade_mode:
        adventure.render_adventure_trade(screen, wState, pState)
        return

    if wState.post_room_mode:
        adventure.render_post_room(screen, wState, pState)
        return

    if wState.stash_open:
        village.render_stash(screen, wState, pState, area)
        return

    if wState.questboard_open:
        village.render_questboard(screen, wState, pState, area)
        return

    if wState.quests_open:
        village.render_quests(screen, wState, pState, area)
        return

    if wState.innkeeper_open:
        village.render_innkeeper(screen, wState, pState, area)
        return

    if wState.shop_mode:
        village.render_shop(screen, wState, pState, area)
        return

    _render_game(screen, wState, pState, area)
    pygame.display.flip()
