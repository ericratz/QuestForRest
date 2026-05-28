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

def _stat_label(stat, value):
    if stat == "flee_bonus":
        return f"Flee +{int(value * 100)}%"
    elif stat == "reflect":
        return f"Reflect {int(value * 100)}%"
    elif value < 0:
        return f"{stat.capitalize()} {value}"
    else:
        return f"{stat.capitalize()} +{value}"


def _consumable_desc(use_effect):
    if "heal" in use_effect:
        return f"Heals {use_effect['heal']} HP"
    elif "food" in use_effect:
        return f"+{use_effect['food']} Food"
    elif "cure" in use_effect:
        return "Cures status effects"
    elif "flee" in use_effect:
        return "Guaranteed escape"
    elif "buff_attack" in use_effect:
        return f"+{use_effect['buff_attack']} ATK (this run)"
    return ""


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


def render_shop(screen, wState, pState, area):
    w, h = screen.get_size()
    font, small = _fonts(h)
    _bg(screen, area.image)
    _overlay(screen)
    cx = w // 2
    y  = 40

    title = "Shop  —  Buy" if wState.shop_mode == "buy" else "Shop  —  Sell"
    t = font.render(title, True, (255, 255, 255))
    screen.blit(t, (cx - t.get_width() // 2, y)); y += font.get_height() + 8
    t = font.render(f"Gold: {pState.gold}g", True, (255, 215, 50))
    screen.blit(t, (cx - t.get_width() // 2, y)); y += font.get_height() + 24

    if wState.shop_mode == "buy":
        equip_list  = sorted([i for i in wState.shop_inventory if not i.consumable],
                             key=lambda i: i.price)
        supply_list = sorted([i for i in wState.shop_inventory if i.consumable]
                             + gamestate.PERM_SHOP_ITEMS, key=lambda i: i.price)

        pygame.draw.line(screen, (60, 60, 80), (cx, y - 8), (cx, h - 40), 1)

        def draw_buy_col(items, col_idx, x, x_end, label):
            cy = y
            active  = (wState.shop_col == col_idx)
            hdr_col = (255, 255, 255) if active else (150, 150, 150)
            screen.blit(font.render(label, True, hdr_col), (x, cy))
            cy += font.get_height() + 10
            if not items:
                screen.blit(small.render("Nothing here.", True, (80, 80, 80)), (x, cy))
                return
            for i, item in enumerate(items):
                selected   = active and (i == wState.shop_index)
                can_afford = pState.gold >= item.price
                name_col   = (255, 255, 0) if selected else (215, 215, 215)
                price_col  = ((220, 80, 80) if (selected and not can_afford) else
                              (255, 215, 50) if selected else (150, 150, 150))
                prefix = "> " if selected else "  "
                desc   = (_consumable_desc(item.use_effect) if item.consumable
                          else "  ".join(_stat_label(k, v) for k, v in item.stats.items()))
                price_surf = font.render(f"{item.price}g", True, price_col)
                screen.blit(font.render(prefix + item.name, True, name_col), (x, cy))
                screen.blit(price_surf, (x_end - price_surf.get_width(), cy))
                cy += font.get_height()
                screen.blit(small.render("    " + desc, True, (170, 170, 170)), (x, cy))
                cy += small.get_height() + 6

        draw_buy_col(equip_list,  0, 20,      cx - 10,  "Equipment")
        draw_buy_col(supply_list, 1, cx + 20, w  - 10,  "Supplies")

    else:
        col_name  = cx - 260
        col_stats = cx - 20
        col_price = cx + 160
        groups = _group_sorted_inventory(pState.inventory)
        if not groups:
            m = font.render("Nothing to sell.", True, (120, 120, 120))
            screen.blit(m, (cx - m.get_width() // 2, y))
        else:
            for i, (item, count) in enumerate(groups):
                selected  = (i == wState.shop_index)
                price     = max(1, item.price // 2)
                name_col  = (255, 255, 0) if selected else (215, 215, 215)
                price_col = (255, 215, 50) if selected else (150, 150, 150)
                prefix    = "> " if selected else "  "
                cnt       = f" (x{count})" if count > 1 else ""
                stats_str = (_consumable_desc(item.use_effect) if item.consumable
                             else "  ".join(_stat_label(k, v) for k, v in item.stats.items()))
                screen.blit(font.render(prefix + item.name + cnt, True, name_col), (col_name,  y))
                screen.blit(small.render(stats_str, True, (170, 170, 170)),                     (col_stats, y + 4))
                screen.blit(font.render(f"{price}g", True, price_col),                          (col_price, y))
                y += font.get_height() + 8

    if wState.shop_msg:
        msg_t = small.render(wState.shop_msg, True, (130, 220, 130))
        screen.blit(msg_t, (cx - msg_t.get_width() // 2, h - small.get_height() * 2 - 30))
    hint_text = ("←→ Switch column   ↑↓ Navigate   Enter: Buy   ESC: Back"
                 if wState.shop_mode == "buy" else "↑↓ Navigate   Enter: Sell   ESC: Back")
    hint = small.render(hint_text, True, (130, 130, 130))
    screen.blit(hint, (cx - hint.get_width() // 2, h - hint.get_height() - 15))


def _group_sorted_inventory(inventory):
    """Sort by name and collapse duplicates → [(item, count), ...]."""
    groups = []
    for item in sorted(inventory, key=lambda it: it.name):
        if groups and groups[-1][0].name == item.name:
            groups[-1] = (groups[-1][0], groups[-1][1] + 1)
        else:
            groups.append((item, 1))
    return groups


def render_inventory(screen, wState, pState, area):
    w, h = screen.get_size()
    font, small = _fonts(h)
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
    groups = _group_sorted_inventory(pState.inventory)
    if groups:
        pState.inventory_index = min(pState.inventory_index, len(groups) - 1)
    ry = 18
    screen.blit(font.render("Inventory", True, (255, 255, 255)), (inv_x, ry))
    ry += font.get_height() + 12
    if not groups:
        screen.blit(font.render("No items", True, (110, 110, 110)), (inv_x, ry))
    else:
        for i, (inv_item, count) in enumerate(groups):
            sel   = (i == pState.inventory_index and pState.active_panel == "inventory")
            color = (255, 255, 0) if sel else (215, 215, 215)
            tag   = " [use]" if inv_item.consumable else ""
            cnt   = f" (x{count})" if count > 1 else ""
            screen.blit(font.render(("> " if sel else "  ") + inv_item.name + tag + cnt, True, color),
                        (inv_x, ry))
            ry += font.get_height() + 4

        if pState.active_panel == "inventory" and 0 <= pState.inventory_index < len(groups):
            sel_item = groups[pState.inventory_index][0]
            ry += 10
            pygame.draw.line(screen, (80, 80, 100), (inv_x, ry), (w - 15, ry), 1)
            ry += 8
            if sel_item.consumable:
                desc = _consumable_desc(sel_item.use_effect)
                if desc:
                    screen.blit(small.render(desc, True, (170, 220, 170)), (inv_x, ry))
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
                    label = _stat_label(stat, d) if stat not in ("flee_bonus", "reflect") \
                        else _stat_label(stat, nv)
                    screen.blit(font.render(label, True, col),
                                (inv_x, ry)); ry += font.get_height() + 4

    if pState.active_panel == "equipment":
        hint_text = "→ Inventory  |  Enter: Unequip  |  ESC: Close"
    else:
        hint_text = "← Equipment  |  Enter: Equip/Use  |  ESC: Close"
    hint = small.render(hint_text, True, (130, 130, 130))
    screen.blit(hint, (inv_x, h - hint.get_height() - 15))


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
        groups = _group_sorted_inventory(items)
        py = 60
        col_hdr = font.render(label, True, (255, 255, 255) if active else (150, 150, 150))
        screen.blit(col_hdr, (x, py)); py += font.get_height() + 10
        if not groups:
            screen.blit(small.render("Empty", True, (80, 80, 80)), (x, py))
        for i, (it, count) in enumerate(groups):
            sel   = active and (i == index)
            color = (255, 255, 0) if sel else (215, 215, 215)
            cnt   = f" (x{count})" if count > 1 else ""
            screen.blit(font.render(("> " if sel else "  ") + it.name + cnt, True, color), (x, py))
            py += font.get_height() + 4

    draw_panel(pState.inventory, wState.stash_inv_index,
               wState.stash_panel == "inventory", 40,      "Inventory")
    draw_panel(pState.stash,     wState.stash_stash_index,
               wState.stash_panel == "stash",     cx + 20, "Stash")

    hint = small.render("←→ Switch panel   Enter: Transfer   ESC: Close", True, (130, 130, 130))
    screen.blit(hint, (cx - hint.get_width() // 2, h - hint.get_height() - 15))


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
    screen.blit(small.render("    Earn gold and 1 food. Heals you fully.", True, (170, 170, 170)), (80, y)); y += small.get_height() + 4
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

    # Quest accept warning popup
    elif wState.questboard_confirm == "quest_accept":
        _overlay(screen, 210)
        py = h // 3
        quest = next((q for q in quests.QUESTS if q["id"] == wState.questboard_quest_id), None)
        q_name = quest["name"] if quest else "?"
        q_days = quest.get("days") if quest else None
        for line, color in [
            (f"Accept '{q_name}'?",                                       (255, 255, 255)),
            ("",                                                            (255, 255, 255)),
            ("Warning: Failing this quest will cost you half your gold!", (220, 100, 80)),
            (f"Due in {q_days} days." if q_days else "",                   (180, 160, 80)),
            ("",                                                            (255, 255, 255)),
        ]:
            if line:
                t = font.render(line, True, color)
                screen.blit(t, (cx - t.get_width() // 2, py))
            py += font.get_height() + 10
        conf = font.render("[ Enter: Accept ]      [ ESC: Cancel ]", True, (200, 220, 255))
        screen.blit(conf, (cx - conf.get_width() // 2, py))



def _wrap_text(text, font, max_w):
    words = text.split()
    lines, line = [], ""
    for word in words:
        test = (line + " " + word).strip()
        if font.size(test)[0] <= max_w:
            line = test
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines or [""]


def render_quests(screen, wState, pState, area):
    w, h = screen.get_size()
    font, small = _fonts(h)
    _bg(screen, area.image)
    _overlay(screen)
    y = 30

    # Layout: quests fill left ~66%, achievements take right ~31%
    q1_x  = int(w * 0.03)
    q2_x  = int(w * 0.36)
    ach_x = int(w * 0.70)
    qcw   = int(w * 0.30)   # each quest column wrap width
    acw   = int(w * 0.27)   # achievement column wrap width
    div_x = int(w * 0.68)   # main divider (quests | achievements)
    mid_x = q2_x - int(w * 0.015)  # soft divider between quest columns

    # Headers
    hdr = font.render("Quests", True, (255, 255, 255))
    screen.blit(hdr, (div_x // 2 - hdr.get_width() // 2, y))
    ach_hdr = font.render("Achievements", True, (200, 170, 80))
    screen.blit(ach_hdr, (ach_x, y))
    y += font.get_height() + 20

    pygame.draw.line(screen, (60, 60, 80), (div_x, y - 8), (div_x, h - 40), 1)
    pygame.draw.line(screen, (40, 40, 60), (mid_x, y - 8), (mid_x, h - 40), 1)

    active = [q for q in quests.QUESTS if q["id"] in pState.active_quests]

    # ── Quests: two columns ───────────────────────────────────────────────────
    def _draw_quest_col(quest_list, col_x):
        qy = y
        for quest in quest_list:
            done             = quest["id"] in pState.quests_complete
            progress, target = quests.quest_progress(quest, pState)
            name_color = (130, 200, 130) if done else (220, 220, 220)
            mark       = "[DONE]" if done else f"[{progress}/{target}]"
            screen.blit(font.render(f"{mark}  {quest['name']}", True, name_color), (col_x, qy))
            qy += font.get_height() + 2
            desc_color = (140, 140, 140) if done else (180, 180, 180)
            for dline in _wrap_text("  " + quest["desc"], small, qcw):
                screen.blit(small.render(dline, True, desc_color), (col_x, qy))
                qy += small.get_height() + 2
            if not done:
                if quest["reward"] > 0:
                    screen.blit(small.render(f"  Reward: {quest['reward']}g",
                                             True, (200, 180, 80)), (col_x, qy))
                    qy += small.get_height() + 4
                due = pState.quest_due_dates.get(quest["id"])
                if due is not None:
                    days_left = due - wState.day
                    if days_left > 0:
                        due_color = (220, 80, 80) if days_left <= 2 else (180, 160, 80)
                        due_text  = f"  Due: Day {due}  ({days_left}d left)"
                    elif days_left == 0:
                        due_color = (220, 80, 80)
                        due_text  = f"  Due: Day {due}  (FINAL DAY)"
                    else:
                        due_color = (220, 80, 80)
                        due_text  = f"  Due: Day {due}  (OVERDUE)"
                    screen.blit(small.render(due_text, True, due_color), (col_x, qy))
                    qy += small.get_height() + 4
            qy += 8

    if not active:
        screen.blit(font.render("No active quests.", True, (120, 120, 120)), (q1_x, y))
    else:
        split        = (len(active) + 1) // 2
        _draw_quest_col(active[:split], q1_x)
        _draw_quest_col(active[split:], q2_x)

    # ── Achievements ──────────────────────────────────────────────────────────
    ay = y
    for ach in quests.ACHIEVEMENTS:
        done       = ach["id"] in pState.achievements_unlocked
        name_color = (255, 215, 50) if done else (120, 120, 120)
        mark       = "[DONE]" if done else "[    ]"
        screen.blit(font.render(f"{mark}  {ach['name']}", True, name_color), (ach_x, ay))
        ay += font.get_height() + 2
        desc_color = (170, 145, 60) if done else (90, 90, 90)
        for dline in _wrap_text("  " + ach["desc"], small, acw):
            screen.blit(small.render(dline, True, desc_color), (ach_x, ay))
            ay += small.get_height() + 2
        reward = ach.get("reward", 0)
        if reward > 0:
            rew_color = (200, 170, 50) if done else (80, 70, 30)
            screen.blit(small.render(f"  Reward: {reward}g", True, rew_color), (ach_x, ay))
            ay += small.get_height() + 2
        ay += 8

    hint = small.render("ESC / Q: Close", True, (130, 130, 130))
    screen.blit(hint, (w // 2 - hint.get_width() // 2, h - hint.get_height() - 15))


def render_achievement_popup(screen, wState, pState, area):
    w, h = screen.get_size()
    font, small = _fonts(h)
    _bg(screen, area.image)
    _overlay(screen, 210)
    cx = w // 2
    cy = h // 3

    hdr = font.render("Achievement Unlocked!", True, (255, 215, 50))
    screen.blit(hdr, (cx - hdr.get_width() // 2, cy)); cy += font.get_height() + 24

    for name in wState.achievement_popup:
        ach = next((a for a in quests.ACHIEVEMENTS if a["name"] == name), None)
        name_t = font.render(name, True, (255, 255, 255))
        screen.blit(name_t, (cx - name_t.get_width() // 2, cy)); cy += font.get_height() + 6
        if ach:
            desc_t = small.render(ach["desc"], True, (190, 160, 80))
            screen.blit(desc_t, (cx - desc_t.get_width() // 2, cy)); cy += small.get_height() + 4
            reward = ach.get("reward", 0)
            if reward > 0:
                rew_t = small.render(f"Reward: +{reward}g", True, (255, 215, 50))
                screen.blit(rew_t, (cx - rew_t.get_width() // 2, cy))
        cy += small.get_height() + 20

    hint = small.render("Press any key to continue.", True, (130, 130, 130))
    screen.blit(hint, (cx - hint.get_width() // 2, cy))


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


def render_quest_expired_popup(screen, wState, pState, area):
    w, h = screen.get_size()
    font, small = _fonts(h)
    _bg(screen, area.image)
    _overlay(screen, 210)
    cx = w // 2
    cy = h // 4

    hdr = font.render("Quest Failed!", True, (220, 80, 80))
    screen.blit(hdr, (cx - hdr.get_width() // 2, cy)); cy += font.get_height() + 24

    for qname, penalty in wState.quest_expired_popup:
        name_t = font.render(qname, True, (200, 200, 200))
        screen.blit(name_t, (cx - name_t.get_width() // 2, cy)); cy += font.get_height() + 8
        pen_t = font.render(f"Penalty: -{penalty}g", True, (220, 80, 80))
        screen.blit(pen_t, (cx - pen_t.get_width() // 2, cy)); cy += font.get_height() + 6
        sub_t = small.render("(half your current gold)", True, (170, 100, 100))
        screen.blit(sub_t, (cx - sub_t.get_width() // 2, cy)); cy += small.get_height() + 20

    cy += 8
    pool_t = small.render("This quest has been returned to the quest pool.", True, (160, 160, 160))
    screen.blit(pool_t, (cx - pool_t.get_width() // 2, cy))

    hint = small.render("Press any key to continue.", True, (130, 130, 130))
    screen.blit(hint, (cx - hint.get_width() // 2, h - hint.get_height() - 15))


def render_new_debt_popup(screen, wState, pState, area):
    w, h = screen.get_size()
    font, small = _fonts(h)
    _bg(screen, area.image)
    _overlay(screen, 210)
    cx = w // 2
    cy = h // 4

    hdr = font.render("First Debt Cleared!", True, (255, 215, 50))
    screen.blit(hdr, (cx - hdr.get_width() // 2, cy)); cy += font.get_height() + 20

    for line, color in [
        ("The innkeeper congratulates you on repaying your debt.", (220, 220, 220)),
        ("However, he presents you with a much larger arrangement.", (200, 180, 130)),
        ("",                                                          (255, 255, 255)),
        ("New Debt:  1,000g",                                         (220, 80, 80)),
        ("Due by Day 28",                                             (200, 120, 80)),
        ("",                                                          (255, 255, 255)),
        ("Good luck.",                                                (160, 160, 160)),
    ]:
        t = font.render(line, True, color)
        screen.blit(t, (cx - t.get_width() // 2, cy)); cy += font.get_height() + 10

    hint = small.render("Press any key to continue.", True, (130, 130, 130))
    screen.blit(hint, (cx - hint.get_width() // 2, h - hint.get_height() - 15))
