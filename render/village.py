'''
render_village.py
Renders for village screens: main menu, name input, shop, inventory,
stash, questboard, quests, innkeeper, quest popup
'''

import pygame
import state.gamestate as gamestate
import data.quests as quests
import state.save as save
from render.helpers import _bg, _overlay, _fonts, _draw_hp_bar

_SLOT_POSITIONS = {
    "head":   (0.50, 0.12),
    "amulet": (0.50, 0.32),
    "weapon": (0.18, 0.32),
    "shield": (0.82, 0.32),
    "body":   (0.50, 0.52),
    "ring":   (0.18, 0.52),
    "legs":   (0.50, 0.72),
}


def render_main_menu(screen, wState, area):
    w, h = screen.get_size()
    font, small = _fonts(h)
    _bg(screen, area.image)
    cx = w // 2
    y  = int(h * 0.45)

    if wState.main_menu_confirm == "new_game_notify":
        _overlay(screen, 160)
        for line in ["You have existing save files.", "", "Enter: Start New Game    ESC: Back"]:
            t = font.render(line, True, (255, 255, 255))
            screen.blit(t, (cx - t.get_width() // 2, y))
            y += font.get_height() + 8

    elif wState.main_menu_confirm == "load":
        _overlay(screen, 160)
        hdr = font.render("Select Save", True, (255, 255, 255))
        screen.blit(hdr, (cx - hdr.get_width() // 2, y))
        y += font.get_height() + 16
        for i, (slot, data) in enumerate(wState.available_saves):
            p     = data.get("player", {})
            name  = p.get("name", "Unknown")
            lvl   = p.get("level", 1)
            day   = data.get("world", {}).get("day", "?")
            label = f"Save {slot}  —  {name}  Lv.{lvl}  Day {day}"
            color  = (255, 255, 0) if i == wState.load_menu_index else (220, 220, 220)
            prefix = "> " if i == wState.load_menu_index else "  "
            t = font.render(prefix + label, True, color)
            screen.blit(t, (cx - t.get_width() // 2, y))
            y += font.get_height() + 10
        y += 10
        hint = small.render("Enter: Load    ESC: Back", True, (130, 130, 130))
        screen.blit(hint, (cx - hint.get_width() // 2, y))

    else:
        has_save = save.save_exists()
        for i, item in enumerate(gamestate.MAIN_MENU_ITEMS):
            unavailable = (item == "Load Game" and not has_save)
            color  = (80, 80, 80) if unavailable else (255, 255, 0) if i == wState.main_menu_index else (220, 220, 220)
            prefix = "> " if i == wState.main_menu_index and not unavailable else "  "
            t = font.render(prefix + item, True, color)
            screen.blit(t, (cx - t.get_width() // 2, y))
            y += font.get_height() + 12

    pygame.display.flip()


def render_name_input(screen, wState, area):
    w, h = screen.get_size()
    font, small = _fonts(h)
    _bg(screen, area.image)
    _overlay(screen, 160)
    cx = w // 2
    y  = h // 2 - font.get_height() * 3

    prompt = font.render("Enter your character's name:", True, (220, 220, 220))
    screen.blit(prompt, (cx - prompt.get_width() // 2, y))
    y += font.get_height() + 20

    cursor = "_" if (pygame.time.get_ticks() // 500) % 2 == 0 else " "
    name_surf = font.render(wState.name_input_buffer + cursor, True, (255, 255, 0))
    screen.blit(name_surf, (cx - name_surf.get_width() // 2, y))
    y += font.get_height() + 30

    hint = small.render("Enter to confirm   Backspace to delete", True, (130, 130, 130))
    screen.blit(hint, (cx - hint.get_width() // 2, y))
    pygame.display.flip()


def render_shop(screen, wState, pState, area):
    w, h = screen.get_size()
    font, small = _fonts(h)
    _bg(screen, area.image)
    _overlay(screen)
    cx        = w // 2
    col_name  = cx - 260
    col_stats = cx - 20
    col_price = cx + 160
    y = 40

    title = "Shop  —  Buy" if wState.shop_mode == "buy" else "Shop  —  Sell"
    t = font.render(title, True, (255, 255, 255))
    screen.blit(t, (cx - t.get_width() // 2, y)); y += font.get_height() + 8
    t = font.render(f"Gold: {pState.gold}", True, (255, 215, 50))
    screen.blit(t, (cx - t.get_width() // 2, y)); y += font.get_height() + 24

    if wState.shop_mode == "buy":
        items_list = wState.shop_inventory + gamestate.PERM_SHOP_ITEMS
        n_daily    = len(wState.shop_inventory)
    else:
        items_list = pState.inventory
        n_daily    = len(items_list)

    if not items_list:
        m = font.render("Nothing here." if wState.shop_mode == "buy" else "Nothing to sell.",
                        True, (120, 120, 120))
        screen.blit(m, (cx - m.get_width() // 2, y))
    else:
        can_afford = True
        for i, item in enumerate(items_list):
            selected   = (i == wState.shop_index)
            price      = item.price if wState.shop_mode == "buy" else max(1, item.price // 2)
            can_afford = pState.gold >= item.price if wState.shop_mode == "buy" else True
            name_color  = (255, 255, 0) if selected else (215, 215, 215)
            price_color = ((220, 80, 80) if (selected and not can_afford) else
                           (255, 215, 50) if selected else (150, 150, 150))
            prefix = "> " if selected else "  "
            if item.consumable:
                stats_str = (item.use_effect.get("heal") and f"Heals {item.use_effect['heal']} HP" or
                             item.use_effect.get("food") and f"+{item.use_effect['food']} Food" or "")
            else:
                stats_str = "  ".join(f"{k.capitalize()} +{v}" for k, v in item.stats.items())
            screen.blit(font.render(prefix + item.name, True, name_color), (col_name,  y))
            screen.blit(small.render(stats_str, True, (170, 170, 170)),               (col_stats, y + 4))
            screen.blit(font.render(f"{price}g", True, price_color),                  (col_price, y))
            y += font.get_height() + 8
        if wState.shop_mode == "buy" and not can_afford:
            m = small.render("Not enough gold.", True, (200, 80, 80))
            screen.blit(m, (cx - m.get_width() // 2, y + 8))

    if wState.shop_msg:
        msg_t = small.render(wState.shop_msg, True, (130, 220, 130))
        screen.blit(msg_t, (cx - msg_t.get_width() // 2, h - small.get_height() * 2 - 30))
    hint = small.render("Enter: Buy    ESC: Back" if wState.shop_mode == "buy"
                        else "Enter: Sell    ESC: Back", True, (130, 130, 130))
    screen.blit(hint, (cx - hint.get_width() // 2, h - hint.get_height() - 15))
    pygame.display.flip()


def render_inventory(screen, wState, pState, area):
    w, h = screen.get_size()
    font = pygame.font.SysFont("Arial", max(int(h * 0.028), 15))
    small = pygame.font.SysFont("Arial", max(int(h * 0.022), 12))
    _bg(screen, area.image)
    _overlay(screen)

    lp_w   = int(w * 0.40)
    stat_x = lp_w + 15
    stat_w = int(w * 0.18)
    inv_x  = stat_x + stat_w + 15

    pygame.draw.line(screen, (80, 80, 100), (lp_w, 0), (lp_w, h), 1)
    pygame.draw.line(screen, (80, 80, 100), (stat_x + stat_w, 0), (stat_x + stat_w, h), 1)

    # Paper doll
    slot_w = int(w * 0.09)
    slot_h = int(h * 0.09)
    hdr = font.render("Equipment", True, (255, 255, 255))
    screen.blit(hdr, (lp_w // 2 - hdr.get_width() // 2, 18))
    selected_slot = (gamestate.EQUIPMENT_SLOTS[pState.equip_slot_index]
                     if pState.active_panel == "equipment" else None)
    for slot_name, (xf, yf) in _SLOT_POSITIONS.items():
        sx = int(lp_w * xf - slot_w // 2)
        sy = int(h * yf - slot_h // 2)
        is_sel = (slot_name == selected_slot)
        pygame.draw.rect(screen, (45, 45, 58), (sx, sy, slot_w, slot_h))
        pygame.draw.rect(screen, (255, 255, 0) if is_sel else (110, 110, 135),
                         (sx, sy, slot_w, slot_h), 2 if is_sel else 1)
        screen.blit(small.render(slot_name.capitalize(), True, (130, 130, 155)), (sx + 4, sy + 3))
        eq = pState.equipment.get(slot_name)
        label = small.render(eq.name if eq else "Empty", True,
                             (210, 210, 255) if eq else (65, 65, 78))
        screen.blit(label, (sx + 4, sy + slot_h - small.get_height() - 4))

    # Stats column
    sy = 18
    screen.blit(font.render("Stats", True, (255, 255, 255)), (stat_x, sy))
    sy += font.get_height() + 14
    mx = pState.get_max_health()
    for text, color in [
        (f"HP:      {pState.health} / {mx}",          (220, 80, 80)),
        (f"Gold:    {pState.gold}",                    (255, 215, 50)),
        (f"Food:    {pState.food}",                    (180, 200, 140)),
        (f"Level:   {pState.level}",                   (220, 220, 220)),
        (f"XP:      {pState.xp} / {pState.xp_to_next()}", (220, 220, 220)),
        (f"Attack:  {pState.get_attack()}",            (220, 220, 220)),
        (f"Defense: {pState.get_defense()}",           (220, 220, 220)),
    ]:
        screen.blit(small.render(text, True, color), (stat_x, sy))
        sy += small.get_height() + 6
    if pState.debt > 0:
        screen.blit(small.render(f"Debt:    {pState.debt}g", True, (200, 80, 80)), (stat_x, sy))

    # Inventory list
    ry = 18
    screen.blit(font.render("Inventory", True, (255, 255, 255)), (inv_x, ry))
    ry += font.get_height() + 12
    if not pState.inventory:
        screen.blit(font.render("No items", True, (110, 110, 110)), (inv_x, ry))
    else:
        for i, inv_item in enumerate(pState.inventory):
            sel    = (i == pState.inventory_index and pState.active_panel == "inventory")
            color  = (255, 255, 0) if sel else (215, 215, 215)
            tag    = " [use]" if inv_item.consumable else ""
            screen.blit(font.render(("> " if sel else "  ") + inv_item.name + tag, True, color),
                        (inv_x, ry))
            ry += font.get_height() + 4

        if pState.active_panel == "inventory" and 0 <= pState.inventory_index < len(pState.inventory):
            sel_item = pState.inventory[pState.inventory_index]
            ry += 10
            pygame.draw.line(screen, (80, 80, 100), (inv_x, ry), (w - 15, ry), 1)
            ry += 8
            if sel_item.consumable:
                for k, v in sel_item.use_effect.items():
                    screen.blit(small.render(f"{k.capitalize()}: +{v}", True, (170, 220, 170)),
                                (inv_x, ry))
                    ry += small.get_height() + 4
            else:
                current = pState.equipment.get(sel_item.slot)
                screen.blit(small.render(f"Slot: {sel_item.slot.capitalize()}", True, (170, 170, 170)),
                            (inv_x, ry)); ry += small.get_height() + 4
                if current:
                    screen.blit(small.render(f"Replacing: {current.name}", True, (190, 150, 150)),
                                (inv_x, ry)); ry += small.get_height() + 4
                all_stats = set(sel_item.stats) | (set(current.stats) if current else set())
                for stat in sorted(all_stats):
                    nv   = sel_item.stats.get(stat, 0)
                    cv   = current.stats.get(stat, 0) if current else 0
                    d    = nv - cv
                    col  = (100, 230, 100) if d > 0 else (230, 100, 100) if d < 0 else (170, 170, 170)
                    sign = "+" if d >= 0 else ""
                    screen.blit(font.render(f"{stat.capitalize()}: {sign}{d}", True, col),
                                (inv_x, ry)); ry += font.get_height() + 4

    if pState.active_panel == "equipment":
        hint_text = "→ Inventory  |  Enter: Unequip  |  ESC: Close"
    else:
        hint_text = "← Equipment  |  Enter: Equip/Use  |  ESC: Close"
    hint = small.render(hint_text, True, (130, 130, 130))
    screen.blit(hint, (inv_x, h - hint.get_height() - 15))
    pygame.display.flip()


def render_stash(screen, wState, pState, area):
    w, h = screen.get_size()
    font, small = _fonts(h)
    _bg(screen, area.image)
    _overlay(screen)
    cx = w // 2

    hdr = font.render("Stash", True, (255, 255, 255))
    screen.blit(hdr, (cx - hdr.get_width() // 2, 18))
    pygame.draw.line(screen, (80, 80, 100), (cx, 50), (cx, h - 40), 1)

    def draw_panel(items, index, active, x, label):
        py = 60
        col_hdr = font.render(label, True, (255, 255, 255) if active else (150, 150, 150))
        screen.blit(col_hdr, (x, py)); py += font.get_height() + 10
        if not items:
            screen.blit(small.render("Empty", True, (80, 80, 80)), (x, py))
        for i, it in enumerate(items):
            sel   = active and (i == index)
            color = (255, 255, 0) if sel else (215, 215, 215)
            screen.blit(font.render(("> " if sel else "  ") + it.name, True, color), (x, py))
            py += font.get_height() + 4

    draw_panel(pState.inventory, wState.stash_inv_index,
               wState.stash_panel == "inventory", 40,      "Inventory")
    draw_panel(pState.stash,     wState.stash_stash_index,
               wState.stash_panel == "stash",     cx + 20, "Stash")

    hint = small.render("←→ Switch panel   Enter: Transfer   ESC: Close", True, (130, 130, 130))
    screen.blit(hint, (cx - hint.get_width() // 2, h - hint.get_height() - 15))
    pygame.display.flip()


def render_questboard(screen, wState, pState, area):
    w, h = screen.get_size()
    font, small = _fonts(h)
    _bg(screen, area.image)
    _overlay(screen)
    cx  = w // 2
    y   = int(h * 0.12)

    hdr = font.render("Quest Board", True, (255, 255, 255))
    screen.blit(hdr, (cx - hdr.get_width() // 2, y)); y += font.get_height() + 24

    board_items = ["odd_jobs"]
    if wState.questboard_quest_id:
        board_items.append("quest")
    sel_idx = min(wState.questboard_index, len(board_items) - 1)

    # Odd Jobs
    selected = (sel_idx == 0)
    col    = (255, 255, 0) if selected else (220, 220, 220)
    prefix = "> " if selected else "  "
    screen.blit(font.render(prefix + "Odd Jobs", True, col), (80, y)); y += font.get_height() + 4
    screen.blit(small.render("    Earn 3-15 gold and 1 food. Heals you fully.", True, (170, 170, 170)), (80, y)); y += small.get_height() + 4
    if selected:
        screen.blit(small.render("    Enter: Accept", True, (100, 200, 100)), (80, y))
    y += small.get_height() + 20

    # Daily quest
    if wState.questboard_quest_id:
        quest = next((q for q in quests.QUESTS if q["id"] == wState.questboard_quest_id), None)
        if quest:
            selected_q = (sel_idx == 1)
            col_q    = (255, 255, 0) if selected_q else (220, 220, 220)
            prefix_q = "> " if selected_q else "  "
            screen.blit(font.render(prefix_q + quest["name"], True, col_q), (80, y)); y += font.get_height() + 4
            screen.blit(small.render(f"    {quest['desc']}", True, (180, 180, 180)), (80, y)); y += small.get_height() + 4
            if quest["reward"] > 0:
                screen.blit(small.render(f"    Reward: {quest['reward']}g", True, (200, 180, 80)), (80, y)); y += small.get_height() + 4
            if selected_q:
                screen.blit(small.render("    Enter: Accept Quest", True, (100, 200, 100)), (80, y))
    else:
        screen.blit(small.render("  No new quests available today.", True, (100, 100, 100)), (80, y))

    hint = small.render("Up/Down: Navigate   ESC: Close", True, (130, 130, 130))
    screen.blit(hint, (cx - hint.get_width() // 2, h - hint.get_height() - 15))

    # Odd jobs confirm popup
    if wState.questboard_confirm == "odd_jobs":
        _overlay(screen, 210)
        py = h // 3
        for line in ["Take on Odd Jobs?", "",
                     "This will consume the entire day.",
                     "You will earn gold, food, and be healed.", ""]:
            t = font.render(line, True, (255, 255, 255))
            screen.blit(t, (cx - t.get_width() // 2, py))
            py += font.get_height() + 10
        conf = font.render("[ Enter: Confirm ]      [ ESC: Cancel ]", True, (200, 220, 255))
        screen.blit(conf, (cx - conf.get_width() // 2, py))

    pygame.display.flip()


def render_quests(screen, wState, pState, area):
    w, h = screen.get_size()
    font, small = _fonts(h)
    _bg(screen, area.image)
    _overlay(screen)
    cx = w // 2
    y  = 30

    hdr = font.render("Quests", True, (255, 255, 255))
    screen.blit(hdr, (cx - hdr.get_width() // 2, y)); y += font.get_height() + 20

    active = [q for q in quests.QUESTS if q["id"] in pState.active_quests]
    if not active:
        screen.blit(font.render("No active quests.", True, (120, 120, 120)), (80, y))
    for quest in active:
        done     = quest["id"] in pState.quests_complete
        progress, target = quests.quest_progress(quest, pState)
        name_color = (130, 200, 130) if done else (220, 220, 220)
        mark       = "[DONE]" if done else f"[{progress}/{target}]"
        screen.blit(font.render(f"{mark}  {quest['name']}", True, name_color), (80, y))
        y += font.get_height() + 2
        screen.blit(small.render(f"    {quest['desc']}", True,
                                 (140, 140, 140) if done else (180, 180, 180)), (80, y))
        y += small.get_height() + 4
        if quest["reward"] > 0 and not done:
            screen.blit(small.render(f"    Reward: {quest['reward']}g", True, (200, 180, 80)), (80, y))
            y += small.get_height() + 4
        y += 8

    hint = small.render("ESC: Close", True, (130, 130, 130))
    screen.blit(hint, (cx - hint.get_width() // 2, h - hint.get_height() - 15))
    pygame.display.flip()


def render_innkeeper(screen, wState, pState, area):
    w, h = screen.get_size()
    font, small = _fonts(h)
    _bg(screen, area.image)
    _overlay(screen)
    cx = w // 2
    y  = h // 2 - font.get_height() * 4

    hdr = font.render("The Innkeeper", True, (255, 255, 255))
    screen.blit(hdr, (cx - hdr.get_width() // 2, y)); y += font.get_height() + 20

    if pState.debt <= 0:
        for line in ["Your debt has been fully paid.", "Thank you, adventurer!", "", "ESC: Leave"]:
            t = font.render(line, True, (130, 200, 130))
            screen.blit(t, (cx - t.get_width() // 2, y)); y += font.get_height() + 10
    else:
        screen.blit(font.render(f"You owe:  {pState.debt}g", True, (220, 80, 80)),
                    (cx - font.size(f"You owe:  {pState.debt}g")[0] // 2, y)); y += font.get_height() + 10
        screen.blit(font.render(f"Your gold: {pState.gold}g", True, (255, 215, 50)),
                    (cx - font.size(f"Your gold: {pState.gold}g")[0] // 2, y)); y += font.get_height() + 20
        pay = min(10, pState.gold, pState.debt)
        hint_line = f"Enter: Pay {pay}g toward debt    ESC: Leave" if pay > 0 else "Not enough gold.    ESC: Leave"
        hint = small.render(hint_line, True, (130, 130, 130))
        screen.blit(hint, (cx - hint.get_width() // 2, y))
    pygame.display.flip()


def render_quest_popup(screen, wState, pState, area):
    w, h = screen.get_size()
    font, small = _fonts(h)
    _bg(screen, area.image)
    _overlay(screen, 210)
    cx = w // 2
    cy = h // 3

    hdr = font.render("Quest Complete!", True, (255, 215, 50))
    screen.blit(hdr, (cx - hdr.get_width() // 2, cy)); cy += font.get_height() + 24

    for qname in wState.quest_completion_popup:
        quest = next((q for q in quests.QUESTS if q["name"] == qname), None)
        name_t = font.render(qname, True, (255, 255, 255))
        screen.blit(name_t, (cx - name_t.get_width() // 2, cy)); cy += font.get_height() + 6
        if quest and quest["reward"] > 0:
            rew_t = small.render(f"Reward: +{quest['reward']}g", True, (200, 180, 80))
            screen.blit(rew_t, (cx - rew_t.get_width() // 2, cy))
        cy += small.get_height() + 20

    hint = small.render("Press any key to continue.", True, (130, 130, 130))
    screen.blit(hint, (cx - hint.get_width() // 2, cy))
    pygame.display.flip()
