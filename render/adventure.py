'''
render_adventure.py
Renders for adventure mode: location select, combat, post-room, wanderer trade
'''

import pygame
import state.gamestate as gamestate
from .helpers import _bg, _overlay, _fonts, _draw_hp_bar


def render_adventure_select(screen, wState, pState, area):
    w, h = screen.get_size()
    font, small = _fonts(h)
    _bg(screen, area.image)
    _overlay(screen, 160)
    cx = w // 2
    y  = int(h * 0.20)

    hdr = font.render("Choose Adventure", True, (255, 255, 255))
    screen.blit(hdr, (cx - hdr.get_width() // 2, y))
    y += font.get_height() + 24

    for i, loc in enumerate(gamestate.ADVENTURE_LOCATIONS):
        unlocked = i < wState.adventure_locations_unlocked
        done     = i in wState.adventure_locations_complete
        selected = (i == wState.adventure_select_index)

        if not unlocked:
            color = (60, 60, 60)
            label = f"  {loc['name']}  [Locked]"
        elif done:
            color  = (255, 255, 0) if selected else (160, 200, 160)
            label  = ("> " if selected else "  ") + loc["name"] + "  [Complete]"
        else:
            color  = (255, 255, 0) if selected else (220, 220, 220)
            label  = ("> " if selected else "  ") + loc["name"]

        screen.blit(font.render(label, True, color), (cx - 200, y))
        y += font.get_height() + 8

    y += 12
    sel_loc = gamestate.ADVENTURE_LOCATIONS[wState.adventure_select_index]
    desc = small.render(sel_loc["desc"], True, (170, 170, 170))
    screen.blit(desc, (cx - desc.get_width() // 2, y))
    y += small.get_height() + 8
    room_info = small.render("10 rooms  |  Final room: Boss battle", True, (120, 120, 120))
    screen.blit(room_info, (cx - room_info.get_width() // 2, y))
    y += small.get_height() + 18

    food_color = (220, 80, 80) if pState.food < 1 else (160, 200, 140)
    food_req = small.render(f"Requires 1 Food  (You have: {pState.food})", True, food_color)
    screen.blit(food_req, (cx - food_req.get_width() // 2, y))

    if wState.adventure_select_msg:
        y += small.get_height() + 6
        msg_t = small.render(wState.adventure_select_msg, True, (220, 100, 100))
        screen.blit(msg_t, (cx - msg_t.get_width() // 2, y))

    hint = small.render("Enter: Start   ESC: Back", True, (130, 130, 130))
    screen.blit(hint, (cx - hint.get_width() // 2, h - hint.get_height() - 15))
    pygame.display.flip()


def render_combat(screen, wState, pState):
    w, h = screen.get_size()
    font, small = _fonts(h)

    loc_image = gamestate.ADVENTURE_LOCATIONS[wState.adventure_loc_index]["image"]
    _bg(screen, loc_image)
    _overlay(screen, 170)

    monster = wState.combat_monster

    room_txt = small.render(
        f"Room {wState.adventure_room + 1} / 10  —  "
        f"{gamestate.ADVENTURE_LOCATIONS[wState.adventure_loc_index]['name']}",
        True, (180, 180, 180))
    screen.blit(room_txt, (w // 2 - room_txt.get_width() // 2, 12))

    if not wState.post_combat_mode and monster:
        # Monster panel (left)
        panel_top = 50
        m_name = font.render(monster.name, True, (230, 100, 100))
        screen.blit(m_name, (60, panel_top))
        _draw_hp_bar(screen, 60, panel_top + font.get_height() + 6,
                     int(w * 0.35), 22, monster.hp, monster.max_hp,
                     f"{monster.hp} / {monster.max_hp}")

        if wState.combat_examined:
            ey = panel_top + font.get_height() + 36
            for line in [f"ATK: {monster.attack}", f"DEF: {monster.defense}"]:
                t = small.render(line, True, (200, 180, 140))
                screen.blit(t, (60, ey))
                ey += small.get_height() + 4

        # Player panel (right)
        px, py = int(w * 0.60), panel_top
        pname = font.render(pState.name or "Hero", True, (100, 180, 230))
        screen.blit(pname, (px, py))
        _draw_hp_bar(screen, px, py + font.get_height() + 6,
                     int(w * 0.35), 22, pState.health, pState.get_max_health(),
                     f"{pState.health} / {pState.get_max_health()}")
        stat_y = py + font.get_height() + 36
        for line in [f"ATK: {pState.get_attack()}   DEF: {pState.get_defense()}",
                     f"Food: {pState.food}"]:
            t = small.render(line, True, (180, 180, 180))
            screen.blit(t, (px, stat_y))
            stat_y += small.get_height() + 4

        # Combat log
        log_y = int(h * 0.42)
        pygame.draw.line(screen, (60, 60, 80), (40, log_y - 10), (w - 40, log_y - 10), 1)
        for line in wState.combat_log[-4:]:
            t = small.render(line, True, (210, 210, 210))
            screen.blit(t, (w // 2 - t.get_width() // 2, log_y))
            log_y += small.get_height() + 6

        # Action grid
        text_pad  = 10
        opt_row_h = font.get_height() + text_pad * 2
        opt_w     = w // 2
        for i, action in enumerate(gamestate.COMBAT_ACTIONS):
            row = i // 2
            col = i % 2
            ox  = col * opt_w
            oy  = h - opt_row_h * (2 - row)
            sel = (i == wState.combat_nav_index)

            bg = pygame.Surface((opt_w, opt_row_h), pygame.SRCALPHA)
            bg.fill((100, 100, 140, 200) if sel else (20, 20, 30, 150))
            screen.blit(bg, (ox, oy))
            pygame.draw.rect(screen, (200, 200, 255) if sel else (50, 50, 70),
                             (ox, oy, opt_w, opt_row_h), 1)

            dim = ((action == "Flee" and pState.food <= 0) or
                   (action == "Use Potion" and not any(
                       it.consumable and "heal" in it.use_effect for it in pState.inventory)))
            label_color = ((255, 255, 255) if sel and not dim else
                           (100, 100, 100) if dim else (150, 150, 160))
            t = font.render(action, True, label_color)
            screen.blit(t, (ox + opt_w // 2 - t.get_width() // 2, oy + text_pad))

    # Post-combat overlay
    if wState.post_combat_mode:
        _overlay(screen, 200)
        cy     = h // 4
        lines  = []
        gold, item_str = wState.post_combat_loot
        hint_lines = []

        if wState.combat_result == "victory":
            if wState.adventure_complete:
                lines += ["Adventure Complete!", ""]
            else:
                lines += [f"{monster.name if monster else 'Enemy'} defeated!", ""]
            if gold:
                lines.append(f"+ {gold} gold")
            if item_str:
                lines.append(f"+ {item_str}")
            for lvl in wState.post_combat_levelups:
                lines.append(f"Level Up!  Now level {lvl}!")
            if wState.adventure_complete:
                hint_lines = ["[ Enter: Return to Village ]", "[ I: Open Inventory ]"]
            else:
                hint_lines = ["[ Enter: Next Room ]", "[ I: Open Inventory ]",
                              "[ ESC: Retreat to Village ]"]
        elif wState.combat_result == "defeat":
            lines += ["You have been defeated.", "",
                      "Your inventory was lost. Gold halved."]
            hint_lines = ["[ Enter: Return to Village ]", "[ I: Open Inventory ]"]
        elif wState.combat_result == "fled":
            lines += ["You fled safely."]
            hint_lines = ["[ Enter: Return to Village ]", "[ I: Open Inventory ]"]

        for line in lines:
            t = font.render(line, True, (255, 255, 255))
            screen.blit(t, (w // 2 - t.get_width() // 2, cy))
            cy += font.get_height() + 10

        if wState.combat_result == "victory" and wState.post_combat_quest_completions:
            cy += 8
            for qname in wState.post_combat_quest_completions:
                qt = font.render(f"Quest Complete: {qname}!", True, (255, 215, 50))
                screen.blit(qt, (w // 2 - qt.get_width() // 2, cy))
                cy += font.get_height() + 8

        hint_y = h - font.get_height() * len(hint_lines) - 20 * len(hint_lines) - 10
        for line in hint_lines:
            ht = font.render(line, True, (200, 220, 255))
            screen.blit(ht, (w // 2 - ht.get_width() // 2, hint_y))
            hint_y += font.get_height() + 20

    pygame.display.flip()


def render_post_room(screen, wState, pState):
    w, h = screen.get_size()
    font, small = _fonts(h)
    loc_image = gamestate.ADVENTURE_LOCATIONS[wState.adventure_loc_index]["image"]
    _bg(screen, loc_image)
    _overlay(screen, 180)
    cx = w // 2

    room_txt = small.render(
        f"Room {wState.adventure_room + 1} / 10  —  "
        f"{gamestate.ADVENTURE_LOCATIONS[wState.adventure_loc_index]['name']}",
        True, (180, 180, 180))
    screen.blit(room_txt, (cx - room_txt.get_width() // 2, 12))

    cy = h // 4
    for line in wState.post_room_lines:
        t = font.render(line, True, (255, 255, 255))
        screen.blit(t, (cx - t.get_width() // 2, cy))
        cy += font.get_height() + 12

    if wState.in_adventure:
        hint_lines = ["[ Enter: Next Room ]", "[ I: Open Inventory ]",
                      "[ ESC: Retreat to Village ]"]
    else:
        hint_lines = ["[ Enter: Return to Village ]", "[ I: Open Inventory ]"]
    hint_y = h - font.get_height() * len(hint_lines) - 20 * len(hint_lines) - 10
    for line in hint_lines:
        ht = font.render(line, True, (200, 220, 255))
        screen.blit(ht, (cx - ht.get_width() // 2, hint_y))
        hint_y += font.get_height() + 20

    pygame.display.flip()


def render_adventure_trade(screen, wState, pState):
    w, h = screen.get_size()
    font, small = _fonts(h)
    loc_image = gamestate.ADVENTURE_LOCATIONS[wState.adventure_loc_index]["image"]
    _bg(screen, loc_image)
    _overlay(screen, 180)
    cx = w // 2
    cy = h // 3

    hdr = font.render("A trading wanderer approaches!", True, (255, 255, 255))
    screen.blit(hdr, (cx - hdr.get_width() // 2, cy))
    cy += font.get_height() + 20

    item = wState.adventure_trade_item
    if item:
        offer = font.render(f"He offers: {item.name}  for  {item.price}g", True, (255, 215, 50))
        screen.blit(offer, (cx - offer.get_width() // 2, cy))
        cy += font.get_height() + 10
        gold_t = small.render(f"Your gold: {pState.gold}g", True, (180, 180, 180))
        screen.blit(gold_t, (cx - gold_t.get_width() // 2, cy))
        cy += small.get_height() + 20
        if pState.gold >= item.price:
            hint_color, hint_text = (130, 200, 130), "Enter: Buy   ESC: Decline"
        else:
            hint_color, hint_text = (200, 100, 100), "Cannot afford.   ESC: Decline"
        hint = small.render(hint_text, True, hint_color)
        screen.blit(hint, (cx - hint.get_width() // 2, cy))
    pygame.display.flip()
