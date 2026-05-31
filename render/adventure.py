'''
render_adventure.py
Renders for adventure mode: location select, combat, post-room, wanderer trade
'''

import pygame
import state.gamestate as gamestate
import data.quests as quests_data
import data.monsters as monsters_data
from .helpers import _bg, _overlay, _fonts, _draw_hp_bar, load_portrait, load_monster_portrait


def render_adventure_select(screen, wState, pState, area):
    w, h = screen.get_size()
    font, small = _fonts(h)
    _bg(screen, area.image)
    _overlay(screen, 160)
    cx = w // 2
    y  = int(h * 0.20)

    is_duskwall = (wState.adventure_select_context == "duskwall")

    hdr_text = "Duskwall Adventures" if is_duskwall else "Choose Adventure"
    hdr = font.render(hdr_text, True, (255, 255, 255))
    screen.blit(hdr, (cx - hdr.get_width() // 2, y))
    y += font.get_height() + 24

    if is_duskwall:
        offset     = 2   # Duskwall dungeons start at index 2 in ADVENTURE_LOCATIONS
        max_shown  = wState.duskwall_locations_unlocked
        locs       = gamestate.ADVENTURE_LOCATIONS[offset:offset + 2]
    else:
        offset     = 0
        max_shown  = wState.adventure_locations_unlocked
        locs       = gamestate.ADVENTURE_LOCATIONS[:2]

    for rel_i, loc in enumerate(locs):
        abs_i    = offset + rel_i
        unlocked = rel_i < max_shown
        done     = abs_i in wState.adventure_locations_complete
        selected = (rel_i == wState.adventure_select_index)

        if not unlocked:
            color = (60, 60, 60)
            label = f"  {loc['name']}  [Locked]"
        elif done:
            color = (255, 255, 0) if selected else (160, 200, 160)
            label = ("> " if selected else "  ") + loc["name"] + "  [Complete]"
        else:
            color = (255, 255, 0) if selected else (220, 220, 220)
            label = ("> " if selected else "  ") + loc["name"]

        screen.blit(font.render(label, True, color), (cx - 200, y))
        y += font.get_height() + 8

    y += 12
    rel_sel  = wState.adventure_select_index
    abs_sel  = offset + rel_sel
    sel_locs = gamestate.ADVENTURE_LOCATIONS[offset:offset + 2]
    if rel_sel < len(sel_locs):
        sel_loc  = sel_locs[rel_sel]
        desc = small.render(sel_loc["desc"], True, (170, 170, 170))
        screen.blit(desc, (cx - desc.get_width() // 2, y))
        y += small.get_height() + 8
        n_rooms   = sel_loc["total_rooms"]
        room_info = small.render(f"{n_rooms} rooms  |  Final room: Boss battle", True, (120, 120, 120))
        screen.blit(room_info, (cx - room_info.get_width() // 2, y))
        y += small.get_height() + 18

    rel_idx = wState.adventure_select_index
    if is_duskwall:
        food_req_n = 5 if rel_idx >= 1 else 4
    elif rel_idx >= 1:
        food_req_n = 3
    else:
        food_req_n = 1
    food_color = (220, 80, 80) if pState.food < food_req_n else (160, 200, 140)
    food_req = small.render(f"Requires {food_req_n} Food  (You have: {pState.food})", True, food_color)
    screen.blit(food_req, (cx - food_req.get_width() // 2, y))

    if wState.adventure_select_msg:
        y += small.get_height() + 6
        msg_t = small.render(wState.adventure_select_msg, True, (220, 100, 100))
        screen.blit(msg_t, (cx - msg_t.get_width() // 2, y))

    hint = small.render("Enter: Start   ESC: Back", True, (130, 130, 130))
    screen.blit(hint, (cx - hint.get_width() // 2, h - hint.get_height() - 15))


def render_combat(screen, wState, pState):
    w, h = screen.get_size()
    font, small = _fonts(h)

    loc_image = gamestate.ADVENTURE_LOCATIONS[wState.adventure_loc_index]["image"]
    _bg(screen, loc_image)
    _overlay(screen, 170)

    monster = wState.combat_monster

    room_txt = small.render(
        f"Room {wState.adventure_room + 1} / {gamestate.ADVENTURE_LOCATIONS[wState.adventure_loc_index]['total_rooms']}  -  "
        f"{gamestate.ADVENTURE_LOCATIONS[wState.adventure_loc_index]['name']}",
        True, (180, 180, 180))
    screen.blit(room_txt, (w // 2 - room_txt.get_width() // 2, 12))

    if not wState.post_combat_mode and monster:
        panel_top = 50

        # Monster portrait — centered between the two stat panels
        m_portrait = load_monster_portrait(monster.name, int(h * 0.30))
        if m_portrait:
            mp_x = w // 2 - m_portrait.get_width() // 2
            mp_y = panel_top
            pygame.draw.rect(screen, (8, 8, 16),
                             (mp_x - 3, mp_y - 3, m_portrait.get_width() + 6, m_portrait.get_height() + 6))
            pygame.draw.rect(screen, (100, 80, 60),
                             (mp_x - 3, mp_y - 3, m_portrait.get_width() + 6, m_portrait.get_height() + 6), 2)
            screen.blit(m_portrait, (mp_x, mp_y))

        # Monster panel (left) — always at panel_top, independent of portrait
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

        effect_colors = {
            "poison":   (100, 220, 100),
            "weakened": (220, 140, 60),
            "stunned":  (220, 220, 80),
            "cursed":   (180, 80, 220),
        }
        for eff, turns in pState.status_effects.items():
            color   = effect_colors.get(eff, (180, 180, 180))
            dur_str = "~" if turns == -1 else str(turns)
            t = small.render(f"{eff.capitalize()} ({dur_str})", True, color)
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
                   (action == "Use Item" and not any(it.consumable for it in pState.inventory)) or
                   (action == "Examine" and wState.combat_examined))
            label_color = ((255, 255, 255) if sel and not dim else
                           (100, 100, 100) if dim else (150, 150, 160))
            t = font.render(action, True, label_color)
            screen.blit(t, (ox + opt_w // 2 - t.get_width() // 2, oy + text_pad))

        # Combat item selection overlay
        if wState.combat_item_mode:
            _overlay(screen, 180)
            consumables = [it for it in pState.inventory if it.consumable]
            panel_w = int(w * 0.55)
            panel_h = font.get_height() + 20 + (font.get_height() + 8) * max(1, len(consumables)) + 30
            px = w // 2 - panel_w // 2
            py = h // 2 - panel_h // 2
            pygame.draw.rect(screen, (20, 20, 35), (px, py, panel_w, panel_h))
            pygame.draw.rect(screen, (80, 80, 120), (px, py, panel_w, panel_h), 2)
            hdr = font.render("Use which item?", True, (255, 255, 255))
            screen.blit(hdr, (w // 2 - hdr.get_width() // 2, py + 10))
            iy = py + font.get_height() + 20
            if not consumables:
                screen.blit(font.render("No items.", True, (120, 120, 120)), (px + 16, iy))
            else:
                from render.village import _consumable_desc
                for idx, it in enumerate(consumables):
                    sel_i = (idx == wState.combat_item_index)
                    row_bg = pygame.Surface((panel_w - 4, font.get_height() + 6), pygame.SRCALPHA)
                    row_bg.fill((80, 80, 30, 200) if sel_i else (0, 0, 0, 0))
                    screen.blit(row_bg, (px + 2, iy - 2))
                    prefix = "> " if sel_i else "  "
                    desc = _consumable_desc(it.use_effect)
                    label = f"{prefix}{it.name}"
                    if desc:
                        label += f"  ({desc})"
                    col_i = (255, 255, 0) if sel_i else (210, 210, 210)
                    screen.blit(font.render(label, True, col_i), (px + 16, iy))
                    iy += font.get_height() + 8
            hint_i = small.render("Up/Down: Navigate   Enter: Use   ESC: Cancel", True, (100, 100, 100))
            screen.blit(hint_i, (w // 2 - hint_i.get_width() // 2, py + panel_h - small.get_height() - 6))

    # Post-combat overlay
    if wState.post_combat_mode:
        _overlay(screen, 200)
        cy     = h // 4
        lines  = []
        gold, item_str = wState.post_combat_loot
        hint_lines = []

        if wState.combat_result == "victory":
            if wState.adventure_complete:
                lines += ["Adventure Complete!", "",
                          "You feel you've had enough exploring for one day",
                          "and head back to town.",
                          "You head home and quickly fall asleep.", ""]
            else:
                lines += [f"{monster.name if monster else 'Enemy'} defeated!", ""]
            if gold:
                _dusk_locs = {2, 3}  # Outer Ruins, Abandoned Castle
                _loot_currency = "marks" if wState.adventure_loc_index in _dusk_locs else "gold"
                lines.append(f"+ {gold} {_loot_currency}")
            if item_str:
                lines.append(f"+ {item_str}")
            for lvl, hp_gain, atk_gain, def_gain in wState.post_combat_levelups:
                lines.append(f"Level Up!  Now level {lvl}!")
                gains = []
                if hp_gain:  gains.append(f"+{hp_gain} HP")
                if atk_gain: gains.append(f"+{atk_gain} ATK")
                if def_gain: gains.append(f"+{def_gain} DEF")
                if gains:    lines.append("  " + "  ".join(gains))
                lines.append("  Health restored to full.")
            if wState.adventure_complete:
                hint_lines = ["[ Enter: Return to Village ]", "[ I: Open Inventory ]"]
            else:
                hint_lines = ["[ Enter: Next Room ]", "[ I: Open Inventory ]",
                              "[ ESC: Retreat to Village ]"]
        elif wState.combat_result == "defeat":
            lines += ["You have been defeated.", "",
                      "All items are lost. Your gold is halved.",
                      "You wake up the next day in the village."]
            hint_lines = ["[ Enter: Wake Up ]"]
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
                cy += font.get_height() + 6
                q = next((q for q in quests_data.QUESTS if q["name"] == qname), None)
                if q and q["reward"] > 0:
                    rw = small.render(f"+{q['reward']}g reward", True, (200, 180, 80))
                    screen.blit(rw, (w // 2 - rw.get_width() // 2, cy))
                    cy += small.get_height() + 6

        hint_y = h - font.get_height() * len(hint_lines) - 20 * len(hint_lines) - 10
        for line in hint_lines:
            ht = font.render(line, True, (200, 220, 255))
            screen.blit(ht, (w // 2 - ht.get_width() // 2, hint_y))
            hint_y += font.get_height() + 20



def render_post_room(screen, wState, pState):
    w, h = screen.get_size()
    font, small = _fonts(h)
    loc_image = gamestate.ADVENTURE_LOCATIONS[wState.adventure_loc_index]["image"]
    _bg(screen, loc_image)
    _overlay(screen, 180)
    cx = w // 2

    room_txt = small.render(
        f"Room {wState.adventure_room + 1} / {gamestate.ADVENTURE_LOCATIONS[wState.adventure_loc_index]['total_rooms']}  -  "
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



def render_campfire_prompt(screen, wState, pState):
    w, h = screen.get_size()
    font, small = _fonts(h)
    loc_image = gamestate.ADVENTURE_LOCATIONS[wState.adventure_loc_index]["image"]
    _bg(screen, loc_image)
    _overlay(screen, 190)
    cx = w // 2
    cy = h // 3

    has_food = pState.food > 0
    heal_amt  = wState.campfire_pending_heal

    title = font.render("You find a warm campfire.", True, (255, 220, 140))
    screen.blit(title, (cx - title.get_width() // 2, cy))
    cy += font.get_height() + 20

    if has_food:
        sub = font.render(f"Build a fire and rest?  (costs 1 food, restores {heal_amt} HP)", True, (220, 220, 220))
        screen.blit(sub, (cx - sub.get_width() // 2, cy))
        cy += font.get_height() + 8
        food_t = small.render(f"Food: {pState.food}   HP: {pState.health}/{pState.get_max_health()}", True, (160, 200, 160))
        screen.blit(food_t, (cx - food_t.get_width() // 2, cy))
        cy += font.get_height() + 30
        hint = font.render("[ Enter: Rest ]   [ ESC: Move On ]", True, (200, 220, 255))
    else:
        sub = font.render("You have no food to cook. The cold fire offers no comfort.", True, (180, 180, 180))
        screen.blit(sub, (cx - sub.get_width() // 2, cy))
        cy += font.get_height() + 30
        hint = font.render("[ Enter / ESC: Move On ]", True, (200, 220, 255))

    screen.blit(hint, (cx - hint.get_width() // 2, cy))


def render_boss_warning(screen, wState, pState):
    w, h = screen.get_size()
    font, small = _fonts(h)
    loc = gamestate.ADVENTURE_LOCATIONS[wState.adventure_loc_index]
    _bg(screen, loc["image"])
    _overlay(screen, 200)
    cx = w // 2
    cy = h // 8

    hdr = font.render("A powerful presence stirs ahead...", True, (220, 80, 80))
    screen.blit(hdr, (cx - hdr.get_width() // 2, cy))
    cy += font.get_height() + 14

    pool = monsters_data.DUSKWALL_BOSS_POOL if loc.get("duskwall") else monsters_data.BOSS_POOL
    boss = pool[loc["boss_index"] % len(pool)]

    name_t = font.render(f"{boss.name}  -  boss of {loc['name']}", True, (220, 180, 100))
    screen.blit(name_t, (cx - name_t.get_width() // 2, cy))
    cy += font.get_height() + 10

    # Boss description flavour text
    if boss.description:
        desc_t = small.render(boss.description, True, (180, 160, 130))
        screen.blit(desc_t, (cx - desc_t.get_width() // 2, cy))
        cy += small.get_height() + 18

    # Boss stats
    divider = small.render("- Boss -", True, (160, 80, 80))
    screen.blit(divider, (cx - divider.get_width() // 2, cy))
    cy += small.get_height() + 6

    for line, color in [
        (f"HP:      {boss.max_hp}", (220, 80, 80)),
        (f"Attack:  {boss.attack}", (200, 160, 160)),
        (f"Defense: {boss.defense}", (200, 160, 160)),
    ]:
        t = small.render(line, True, color)
        screen.blit(t, (cx - t.get_width() // 2, cy))
        cy += small.get_height() + 6

    cy += 10
    # Player stats
    divider2 = small.render("- You -", True, (80, 120, 180))
    screen.blit(divider2, (cx - divider2.get_width() // 2, cy))
    cy += small.get_height() + 6

    for line, color in [
        (f"HP:      {pState.health} / {pState.get_max_health()}", (100, 180, 220)),
        (f"Attack:  {pState.get_attack()}", (220, 220, 220)),
        (f"Defense: {pState.get_defense()}", (220, 220, 220)),
    ]:
        t = small.render(line, True, color)
        screen.blit(t, (cx - t.get_width() // 2, cy))
        cy += small.get_height() + 6

    cy += 18
    enter_t = font.render("[ Enter: Face the Boss ]", True, (220, 80, 80))
    screen.blit(enter_t, (cx - enter_t.get_width() // 2, cy))
    cy += font.get_height() + 10
    esc_t = font.render("[ ESC: Retreat to Village ]", True, (130, 200, 130))
    screen.blit(esc_t, (cx - esc_t.get_width() // 2, cy))


def render_adventure_trade(screen, wState, pState):
    w, h = screen.get_size()
    font, small = _fonts(h)
    loc_image = gamestate.ADVENTURE_LOCATIONS[wState.adventure_loc_index]["image"]
    _bg(screen, loc_image)
    _overlay(screen, 180)
    cx = w // 2
    cy = h // 3

    # Wanderer portrait — left side
    wan = load_portrait("assets/images/Wanderer.jpeg", int(h * 0.45))
    if wan:
        wx = int(w * 0.08)
        wy = int(h * 0.25)
        screen.blit(wan, (wx, wy))

    hdr = font.render("A trading wanderer approaches!", True, (255, 255, 255))
    screen.blit(hdr, (cx - hdr.get_width() // 2, cy))
    cy += font.get_height() + 20

    item = wState.adventure_trade_item
    if item:
        _is_dusk  = wState.adventure_trade_dusk
        _currency = "marks" if _is_dusk else "g"
        _wallet   = pState.marks if _is_dusk else pState.gold
        offer = font.render(f"He offers: {item.name}  for  {item.price}{_currency}", True, (255, 215, 50))
        screen.blit(offer, (cx - offer.get_width() // 2, cy))
        cy += font.get_height() + 10
        wallet_label = "marks" if _is_dusk else "gold"
        wallet_t = small.render(f"Your {wallet_label}: {_wallet}{'' if _is_dusk else 'g'}", True, (180, 180, 180))
        screen.blit(wallet_t, (cx - wallet_t.get_width() // 2, cy))
        cy += small.get_height() + 20
        if _wallet >= item.price:
            hint_color, hint_text = (130, 200, 130), "Enter: Buy   ESC: Decline"
        else:
            hint_color, hint_text = (200, 100, 100), "Cannot afford.   ESC: Decline"
        hint = small.render(hint_text, True, hint_color)
        screen.blit(hint, (cx - hint.get_width() // 2, cy))


def render_trapped_chest(screen, wState, pState):
    w, h = screen.get_size()
    font, small = _fonts(h)
    loc_image = gamestate.ADVENTURE_LOCATIONS[wState.adventure_loc_index]["image"]
    _bg(screen, loc_image)
    _overlay(screen, 180)
    cx = w // 2
    cy = h // 3

    hdr = font.render("You spot a suspicious chest...", True, (255, 215, 50))
    screen.blit(hdr, (cx - hdr.get_width() // 2, cy))
    cy += font.get_height() + 20

    for line in ["It looks rigged. Could be loot, a trap, or both. Hard to say.",
                 f"Your HP: {pState.health} / {pState.get_max_health()}"]:
        t = small.render(line, True, (200, 200, 200))
        screen.blit(t, (cx - t.get_width() // 2, cy))
        cy += small.get_height() + 8

    cy += 16
    enter_t = font.render("[ Enter: Open it ]", True, (220, 120, 80))
    screen.blit(enter_t, (cx - enter_t.get_width() // 2, cy))
    cy += font.get_height() + 12
    esc_t = font.render("[ ESC: Walk away ]", True, (130, 200, 130))
    screen.blit(esc_t, (cx - esc_t.get_width() // 2, cy))
