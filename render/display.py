'''
display.py
Master render dispatcher and main game view.
Shared primitives live in render_helpers.py.
Adventure renders in render_adventure.py.
Village/menu renders in render_village.py.
'''

import pygame
import state.gamestate as gamestate
from render.helpers import init_display, _bg, _overlay, _fonts, _tick_draw_fade
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
    # text may contain \n for multi-line messages (e.g. rest shows day)
    lines = text.split("\n")
    if earn_line:
        lines += ["", earn_line]
    lines += ["", "Press any key."]
    for line in lines:
        t = font.render(line, True, (255, 255, 255))
        screen.blit(t, (cx - t.get_width() // 2, y)); y += font.get_height() + 10


def _render_game(screen, wState, pState, area):
    w, h    = screen.get_size()
    font, small = _fonts(h)

    _bg(screen, area.image)

    # HUD
    hud_h = small.get_height() + 16
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

    _dusk_areas = {"duskwall", "duskwall_tavern", "duskwall_shop"}
    _in_dusk    = wState.area in _dusk_areas
    right_parts = [f"Gold: {pState.gold}g"]
    if wState.duskwall_unlocked:
        right_parts.append(f"Marks: {pState.marks}")
    right_parts.append(f"Food: {pState.food}")
    if pState.debt > 0:
        if _in_dusk:
            days_left = max(0, 28 - wState.day)
        else:
            days_left = max(0, 14 - wState.day)
        debt_color_flag = days_left <= 3
        _curr = "marks" if _in_dusk else "g"
        right_parts.append(f"Debt: {pState.debt}{_curr} ({days_left}d)")
    else:
        debt_color_flag = False
    debt_color = (220, 80, 80) if debt_color_flag else (200, 200, 200)
    right_t = small.render("   ".join(right_parts), True, debt_color)
    screen.blit(right_t, (w - right_t.get_width() - 10, 8))

    # Bottom options
    text_pad  = 10
    opt_w     = w // 2

    choices   = list(area.choices.values())
    n_choices = len(choices)
    n_rows    = max(2, -(-n_choices // 2))

    opt_row_h  = font.get_height() + text_pad * 2
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
                         pygame.Rect(ox, oy, opt_w, opt_row_h), 1)
        if has:
            _, desc = choices[i]
            t = font.render(desc, True, (255, 255, 255) if sel else (150, 150, 160))
            screen.blit(t, (ox + opt_w // 2 - t.get_width() // 2, oy + text_pad))

    # Rest confirmation overlay
    if wState.rest_confirm:
        _overlay(screen, 200)
        lines = ["Rest until morning?", "",
                 "Your health will be restored to full.",
                 "The day will advance.", "",
                 "Enter: Rest    ESC: Cancel"]
        cy = h // 2 - font.get_height() * len(lines) // 2
        for line in lines:
            t = font.render(line, True, (255, 255, 255))
            screen.blit(t, (w // 2 - t.get_width() // 2, cy))
            cy += font.get_height() + 10

    # Confirmation dialog
    elif wState.menu_confirm:
        _overlay(screen, 200)
        if wState.menu_confirm == "Saved":
            lines = ["Game saved!", "", "Press any key to continue"]
        else:
            lines = [f"{wState.menu_confirm} - are you sure?", "", "Enter: Yes    ESC: No"]
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

    if wState.options_open:
        _overlay(screen, 200)
        cx    = w // 2
        cy    = h // 3
        bar_w = int(w * 0.32)
        bar_x = cx - bar_w // 2

        hdr = font.render("Options", True, (255, 255, 255))
        screen.blit(hdr, (cx - hdr.get_width() // 2, cy))
        cy += font.get_height() + 30

        def _draw_bar(label, value, selected, y):
            sel_col  = (255, 255, 0)   if selected else (200, 200, 200)
            bar_col  = (100, 200, 100) if selected else (80, 140, 80)
            filled   = int(bar_w * value)
            pct      = round(value * 100)
            prefix   = "> " if selected else "  "
            lbl = font.render(prefix + label, True, sel_col)
            screen.blit(lbl, (cx - lbl.get_width() // 2, y))
            y += font.get_height() + 8
            pygame.draw.rect(screen, (50, 50, 50),      pygame.Rect(bar_x,          y, bar_w, 18))
            pygame.draw.rect(screen, bar_col,            pygame.Rect(bar_x,          y, filled, 18))
            pygame.draw.rect(screen, (120, 120, 120),   pygame.Rect(bar_x,          y, bar_w, 18), 1)
            if selected:
                al = font.render("<", True, (180, 255, 180))
                ar = font.render(">", True, (180, 255, 180))
                screen.blit(al, (bar_x - al.get_width() - 6, y - 1))
                screen.blit(ar, (bar_x + bar_w + 6,          y - 1))
            pct_t = small.render(f"{pct}%", True, sel_col)
            screen.blit(pct_t, (cx - pct_t.get_width() // 2, y + 22))
            return y + 48

        cy = _draw_bar("Music Volume", wState.music_volume, wState.options_bar == 0, cy)
        cy += 8
        cy = _draw_bar("SFX Volume",   wState.sfx_volume,   wState.options_bar == 1, cy)
        cy += 16

        hint = small.render("Up/Down: switch    Left/Right: adjust    ESC: Back", True, (130, 130, 130))
        screen.blit(hint, (cx - hint.get_width() // 2, cy))

    elif wState.work_result:
        _render_work_result(screen, wState, font, small, w, h)


def _render_game_over(screen, wState, pState, area):
    w, h = screen.get_size()
    font, small = _fonts(h)
    cx = w // 2
    cy = h // 3

    if wState.game_over == "debt_paid":
        screen.fill((15, 20, 30))
        _overlay(screen, 0)
        title      = "Quest for Rest"
        title_color = (200, 185, 120)
        body = [
            f"{pState.name} - Day {wState.day}",
            "",
            f"Both debts paid.  Both dungeons cleared.",
            f"Level {pState.level}  ·  {pState.kills} monsters defeated",
            "",
            "Rest well.",
        ]
    else:
        _bg(screen, area.image)
        _overlay(screen, 220)
        title      = "Game Over"
        title_color = (220, 80, 80)
        body = [
            "You failed to pay your debt by the deadline.",
            "The innkeeper evicts you with nothing.",
            "",
            "Better luck next time.",
        ]

    t = font.render(title, True, title_color)
    screen.blit(t, (cx - t.get_width() // 2, cy))
    cy += font.get_height() + 20

    line_color = (200, 190, 160) if wState.game_over == "debt_paid" else (220, 220, 220)
    for line in body:
        t = font.render(line, True, line_color)
        screen.blit(t, (cx - t.get_width() // 2, cy))
        cy += font.get_height() + 10

    cy += 20
    hint = small.render("Press Enter to return to the main menu.", True, (100, 95, 80))
    screen.blit(hint, (cx - hint.get_width() // 2, cy))


# ── Master render dispatcher ──────────────────────────────────────────────────

def render(screen, wState, pState, area, dt: int = 0):
    if wState.ending_mode:
        village.render_ending(screen, wState)
    elif wState.game_over:
        _render_game_over(screen, wState, pState, area)
    elif wState.quest_completion_popup:
        village.render_quest_popup(screen, wState, pState, area)
    elif wState.achievement_popup:
        village.render_achievement_popup(screen, wState, pState, area)
    elif wState.quest_expired_popup:
        village.render_quest_expired_popup(screen, wState, pState, area)
    elif wState.new_debt_popup:
        village.render_new_debt_popup(screen, wState, pState, area)
    elif wState.map_open:
        village.render_map(screen, wState, area)
    elif wState.intro_mode:
        village.render_intro(screen, wState, pState)
    elif wState.name_input_mode:
        village.render_name_input(screen, wState, area)
    elif wState.area == "start_screen":
        village.render_main_menu(screen, wState, area)
    elif wState.adventure_select_mode:
        adventure.render_adventure_select(screen, wState, pState, area)
    elif wState.familiar_naming_mode:
        village.render_familiar_naming(screen, wState, pState)
    elif wState.inventory_open:
        village.render_inventory(screen, wState, pState, area)
    elif wState.trapped_chest_mode:
        adventure.render_trapped_chest(screen, wState, pState)
    elif wState.passive_select_mode:
        village.render_passive_select(screen, wState, pState)
    elif wState.in_combat or wState.post_combat_mode:
        adventure.render_combat(screen, wState, pState)
    elif wState.campfire_prompt:
        adventure.render_campfire_prompt(screen, wState, pState)
    elif wState.boss_warning_mode:
        adventure.render_boss_warning(screen, wState, pState)
    elif wState.adventure_trade_mode:
        adventure.render_adventure_trade(screen, wState, pState)
    elif wState.post_room_mode:
        adventure.render_post_room(screen, wState, pState)
    elif wState.stash_open:
        village.render_stash(screen, wState, pState, area)
    elif wState.questboard_open:
        village.render_questboard(screen, wState, pState, area)
    elif wState.quests_open:
        village.render_quests(screen, wState, pState, area)
    elif wState.innkeeper_open:
        village.render_innkeeper(screen, wState, pState, area)
    elif wState.currency_exchange_open:
        village.render_currency_exchange(screen, wState, pState, area)
    elif wState.dialogue_open:
        village.render_dialogue(screen, wState, area)
    elif wState.shop_mode:
        village.render_shop(screen, wState, pState, area)
    else:
        _render_game(screen, wState, pState, area)

    _tick_draw_fade(screen, dt)
    pygame.display.flip()
