'''
render_village.py
Renders for village screens: main menu, name input, shop, inventory,
stash, questboard, quests, innkeeper, quest popup
'''

import pygame
import state.gamestate as gamestate
import data.quests as quests
import data.dialogue as dialogue
import data.intro as intro
import data.passives as passives_data
import state.save as save
from render.helpers import _bg, _overlay, _fonts, _draw_hp_bar, load_portrait

def _stat_label(stat, value):
    if stat == "flee_bonus":
        return f"Flee +{int(value * 100)}%"
    elif stat == "reflect":
        return f"Reflect {int(value * 100)}%"
    elif stat == "block_chance":
        return f"Block +{value}%"
    elif value < 0:
        return f"{stat.capitalize()} {value}"
    else:
        return f"{stat.capitalize()} +{value}"


def _consumable_desc(use_effect):
    if "cure_all" in use_effect:
        return "Full heal + cure all"
    elif "heal" in use_effect:
        hp = use_effect['heal']
        return f"Heals {hp} HP" if hp < 9999 else "Full heal"
    elif "food" in use_effect:
        return f"+{use_effect['food']} Food"
    elif "cure_poison" in use_effect:
        return "Cures poison"
    elif "cure_stun" in use_effect:
        return "Cures stun"
    elif "cure_hex" in use_effect:
        return "Cures curse/weaken"
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
        bar_w = int(w * 0.52)
        bar_h = font.get_height() + 16
        for i, (slot, data) in enumerate(wState.available_saves):
            p       = data.get("player", {})
            name    = p.get("name", "Unknown")
            lvl     = p.get("level", 1)
            day     = data.get("world", {}).get("day", "?")
            label   = f"Save {slot}  —  {name}  Lv.{lvl}  Day {day}"
            selected = (i == wState.load_menu_index)
            bg_col  = (100, 100, 140, 200) if selected else (20, 20, 30, 150)
            bd_col  = (200, 200, 255)      if selected else (50, 50, 70)
            tx_col  = (255, 255, 255)      if selected else (150, 150, 160)
            bg = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
            bg.fill(bg_col)
            bx = cx - bar_w // 2
            screen.blit(bg, (bx, y))
            pygame.draw.rect(screen, bd_col, pygame.Rect(bx, y, bar_w, bar_h), 1)
            lbl = font.render(label, True, tx_col)
            screen.blit(lbl, (cx - lbl.get_width() // 2, y + (bar_h - font.get_height()) // 2))
            y += bar_h + 6
        y += 10
        hint = small.render("Enter: Load    ESC: Back", True, (130, 130, 130))
        screen.blit(hint, (cx - hint.get_width() // 2, y))

    else:
        has_save  = save.save_exists()
        bar_w     = int(w * 0.38)
        bar_h     = font.get_height() + 16
        for i, item in enumerate(gamestate.MAIN_MENU_ITEMS):
            unavailable = (item == "Load Game" and not has_save)
            selected    = (i == wState.main_menu_index and not unavailable)
            if unavailable:
                bg_col  = (15, 15, 20, 120)
                bd_col  = (45, 45, 55)
                tx_col  = (70, 70, 75)
            elif selected:
                bg_col  = (100, 100, 140, 200)
                bd_col  = (200, 200, 255)
                tx_col  = (255, 255, 255)
            else:
                bg_col  = (20, 20, 30, 150)
                bd_col  = (50, 50, 70)
                tx_col  = (150, 150, 160)
            bg = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
            bg.fill(bg_col)
            bx = cx - bar_w // 2
            screen.blit(bg, (bx, y))
            pygame.draw.rect(screen, bd_col, pygame.Rect(bx, y, bar_w, bar_h), 1)
            lbl = font.render(item, True, tx_col)
            screen.blit(lbl, (cx - lbl.get_width() // 2, y + (bar_h - font.get_height()) // 2))
            y += bar_h + 6



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

    _in_dusk   = (wState.area == "duskwall_shop")
    title = "Shop  -  Buy" if wState.shop_mode == "buy" else "Shop  -  Sell"
    t = font.render(title, True, (255, 255, 255))
    screen.blit(t, (cx - t.get_width() // 2, y)); y += font.get_height() + 8
    wallet_str = f"Marks: {pState.marks}" if _in_dusk else f"Gold: {pState.gold}g"
    t = font.render(wallet_str, True, (255, 215, 50))
    screen.blit(t, (cx - t.get_width() // 2, y)); y += font.get_height() + 24

    if wState.shop_mode == "buy":
        equip_list  = sorted([i for i in wState.shop_inventory if not i.consumable],
                             key=lambda i: i.price)
        perm_items  = (gamestate.DUSKWALL_PERM_SHOP_ITEMS
                       if wState.area == "duskwall_shop"
                       else gamestate.PERM_SHOP_ITEMS)
        supply_list = sorted([i for i in wState.shop_inventory if i.consumable]
                             + perm_items, key=lambda i: i.price)

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
            sel_item_ref = None
            for i, item in enumerate(items):
                selected   = active and (i == wState.shop_index)
                can_afford = (pState.marks if _in_dusk else pState.gold) >= item.price
                name_col   = (255, 255, 0) if selected else (215, 215, 215)
                price_col  = ((220, 80, 80) if (selected and not can_afford) else
                              (255, 215, 50) if selected else (150, 150, 150))
                prefix = "> " if selected else "  "
                desc   = (_consumable_desc(item.use_effect) if item.consumable
                          else "  ".join(_stat_label(k, v) for k, v in item.stats.items()))
                price_str  = f"{item.price} marks" if _in_dusk else f"{item.price}g"
                price_surf = font.render(price_str, True, price_col)
                screen.blit(font.render(prefix + item.name, True, name_col), (x, cy))
                screen.blit(price_surf, (x_end - price_surf.get_width(), cy))
                cy += font.get_height()
                screen.blit(small.render("    " + desc, True, (170, 170, 170)), (x, cy))
                cy += small.get_height() + 6
                if selected:
                    sel_item_ref = item
            # Stat comparison panel for the selected equipment item
            if active and sel_item_ref and not sel_item_ref.consumable:
                cy += 4
                pygame.draw.line(screen, (80, 80, 100), (x, cy), (x_end, cy), 1)
                cy += 6
                current = pState.equipment.get(sel_item_ref.slot)
                slot_lbl = sel_item_ref.slot.capitalize()
                screen.blit(small.render(f"Slot: {slot_lbl}", True, (150, 150, 170)), (x, cy))
                cy += small.get_height() + 3
                if current:
                    screen.blit(small.render(f"Replacing: {current.name}", True, (190, 150, 150)),
                                (x, cy))
                    cy += small.get_height() + 3
                all_stats = set(sel_item_ref.stats) | (set(current.stats) if current else set())
                for stat in sorted(all_stats):
                    nv  = sel_item_ref.stats.get(stat, 0)
                    cv  = current.stats.get(stat, 0) if current else 0
                    d   = nv - cv
                    col = (100, 230, 100) if d > 0 else (230, 100, 100) if d < 0 else (170, 170, 170)
                    lbl = (_stat_label(stat, d) if stat not in ("flee_bonus", "reflect", "block_chance")
                           else _stat_label(stat, nv))
                    screen.blit(small.render(lbl, True, col), (x, cy))
                    cy += small.get_height() + 3

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
                price     = max(1, item.price // 4) if _in_dusk else max(1, item.price // 2)
                price_str = f"{price} marks" if _in_dusk else f"{price}g"
                name_col  = (255, 255, 0) if selected else (215, 215, 215)
                price_col = (255, 215, 50) if selected else (150, 150, 150)
                prefix    = "> " if selected else "  "
                cnt       = f" (x{count})" if count > 1 else ""
                stats_str = (_consumable_desc(item.use_effect) if item.consumable
                             else "  ".join(_stat_label(k, v) for k, v in item.stats.items()))
                screen.blit(font.render(prefix + item.name + cnt, True, name_col), (col_name,  y))
                screen.blit(small.render(stats_str, True, (170, 170, 170)),                     (col_stats, y + 4))
                screen.blit(font.render(price_str,  True, price_col),                           (col_price, y))
                y += font.get_height() + 8

    if wState.shop_msg:
        msg_t = small.render(wState.shop_msg, True, (130, 220, 130))
        screen.blit(msg_t, (cx - msg_t.get_width() // 2, h - small.get_height() * 2 - 30))
    hint_text = ("Left/Right: Switch column   Up/Down: Navigate   Enter: Buy   ESC: Back"
                 if wState.shop_mode == "buy" else "Up/Down: Navigate   Enter: Sell   ESC: Back")
    hint = small.render(hint_text, True, (130, 130, 130))
    screen.blit(hint, (cx - hint.get_width() // 2, h - hint.get_height() - 15))


def render_currency_exchange(screen, wState, pState, area):
    w, h = screen.get_size()
    font, small = _fonts(h)
    _bg(screen, area.image)
    _overlay(screen)
    cx = w // 2
    cy = h // 4

    title = font.render("Currency Exchange", True, (255, 255, 255))
    screen.blit(title, (cx - title.get_width() // 2, cy)); cy += font.get_height() + 20

    gold_t  = font.render(f"Gold: {pState.gold}g", True, (255, 215, 50))
    marks_t = font.render(f"Marks: {pState.marks}", True, (100, 200, 255))
    screen.blit(gold_t,  (cx - gold_t.get_width()  // 2, cy)); cy += font.get_height() + 4
    screen.blit(marks_t, (cx - marks_t.get_width() // 2, cy)); cy += font.get_height() + 20

    rate = small.render("Buy: 25g per mark   |   Sell: 10g per mark", True, (160, 160, 160))
    screen.blit(rate, (cx - rate.get_width() // 2, cy)); cy += small.get_height() + 28

    options = [
        ("Buy 1 mark",  "Spend 25g, receive 1 mark"),
        ("Sell 1 mark", "Spend 1 mark, receive 10g"),
    ]
    sel = getattr(wState, "exchange_index", 0)
    for i, (label, desc) in enumerate(options):
        selected  = (i == sel)
        bg = pygame.Surface((int(w * 0.5), font.get_height() + 16), pygame.SRCALPHA)
        bg.fill((100, 100, 140, 200) if selected else (20, 20, 30, 150))
        bx = cx - bg.get_width() // 2
        screen.blit(bg, (bx, cy))
        pygame.draw.rect(screen, (200, 200, 255) if selected else (50, 50, 70),
                         pygame.Rect(bx, cy, bg.get_width(), bg.get_height()), 1)
        lbl = font.render(label, True, (255, 255, 255) if selected else (150, 150, 160))
        screen.blit(lbl, (cx - lbl.get_width() // 2, cy + 8))
        cy += bg.get_height() + 4
        desc_t = small.render(desc, True, (160, 160, 160))
        screen.blit(desc_t, (cx - desc_t.get_width() // 2, cy))
        cy += small.get_height() + 14

    cy += 10
    if wState.shop_msg:
        msg = small.render(wState.shop_msg, True, (130, 220, 130))
        screen.blit(msg, (cx - msg.get_width() // 2, cy))

    hint = small.render("Up/Down: Navigate   Enter: Confirm   ESC: Back", True, (100, 100, 100))
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
        _curr_inv = "marks" if wState.area in {"duskwall", "duskwall_tavern", "duskwall_shop"} else "g"
        screen.blit(small.render(f"Debt:    {pState.debt}{_curr_inv}", True, (200, 80, 80)), (stat_x, sy))
        sy += small.get_height() + 6
    sy += 4
    screen.blit(small.render(f"Crit:    {pState.get_crit_chance()}%",  True, (200, 200, 200)), (stat_x, sy)); sy += small.get_height() + 6
    screen.blit(small.render(f"Block:   {pState.get_block_chance()}%", True, (200, 200, 200)), (stat_x, sy)); sy += small.get_height() + 6
    if pState.chosen_passives:
        sy += 6
        screen.blit(small.render("Passives:", True, (180, 160, 100)), (stat_x, sy)); sy += small.get_height() + 4
        for pid in pState.chosen_passives:
            p_name = passives_data.PASSIVES.get(pid, {}).get("name", pid)
            screen.blit(small.render(f"  {p_name}", True, (160, 200, 160)), (stat_x, sy)); sy += small.get_height() + 3

    # Familiar panel (below stats if found)
    if pState.familiar.found:
        sy += 10
        pygame.draw.line(screen, (80, 80, 100), (stat_x, sy), (stat_x + stat_w, sy), 1)
        sy += 6
        fam = pState.familiar
        # Portrait — small thumbnail in the stats column
        fam_portrait = load_portrait("assets/images/The Familiar.jpeg", int(h * 0.13))
        if fam_portrait:
            fp_x = stat_x + (stat_w - fam_portrait.get_width()) // 2
            screen.blit(fam_portrait, (fp_x, sy))
            sy += fam_portrait.get_height() + 4
        screen.blit(small.render("Familiar:", True, (200, 170, 120)), (stat_x, sy)); sy += small.get_height() + 3
        screen.blit(small.render(f"  {fam.name}  Lv.{fam.level}", True, (220, 210, 180)), (stat_x, sy)); sy += small.get_height() + 3
        screen.blit(small.render(f"  ATK: {fam.get_attack()}", True, (200, 200, 200)), (stat_x, sy)); sy += small.get_height() + 3
        eq_name = fam.equipment.name if fam.equipment else "None"
        screen.blit(small.render(f"  Charm: {eq_name}", True, (170, 170, 200)), (stat_x, sy))

    # Inventory grid (10 rows x 2 columns)
    INV_COLS = 2
    INV_ROWS = 10
    groups = _group_sorted_inventory(pState.inventory)
    if groups:
        pState.inventory_index = min(pState.inventory_index, len(groups) - 1)

    ry = 18
    screen.blit(font.render("Inventory", True, (255, 255, 255)), (inv_x, ry))
    ry += font.get_height() + 8
    inv_top = ry

    hint_h      = small.get_height() + 15
    available_h = h - inv_top - hint_h
    grid_h      = int(available_h * 0.70)
    cell_w      = (w - 15 - inv_x) // INV_COLS - 2
    cell_h      = max(small.get_height() + 4, grid_h // INV_ROWS - 3)

    for row in range(INV_ROWS):
        for col in range(INV_COLS):
            idx     = row * INV_COLS + col
            cx_cell = inv_x + col * (cell_w + 2)
            cy_cell = inv_top + row * (cell_h + 3)
            sel     = (idx == pState.inventory_index and pState.active_panel == "inventory")
            bg_col  = (60, 60, 30)  if sel else (22, 22, 32)
            br_col  = (255, 255, 0) if sel else (55, 55, 75)
            pygame.draw.rect(screen, bg_col, (cx_cell, cy_cell, cell_w, cell_h))
            pygame.draw.rect(screen, br_col, (cx_cell, cy_cell, cell_w, cell_h), 1)
            if idx < len(groups):
                it, cnt = groups[idx]
                label   = it.name if len(it.name) <= 14 else it.name[:13] + "."
                if cnt > 1:
                    label += f" x{cnt}"
                lbl_surf = small.render(label, True, (255, 255, 0) if sel else (200, 200, 200))
                screen.blit(lbl_surf, (cx_cell + 4, cy_cell + (cell_h - small.get_height()) // 2))

    # Detail panel — bottom 30% of inventory section
    ry = inv_top + grid_h + 6
    pygame.draw.line(screen, (80, 80, 100), (inv_x, ry), (w - 15, ry), 1)
    ry += 8
    if pState.active_panel == "inventory" and 0 <= pState.inventory_index < len(groups):
        sel_item = groups[pState.inventory_index][0]
        name_surf = font.render(sel_item.name, True, (255, 255, 180))
        screen.blit(name_surf, (inv_x, ry)); ry += font.get_height() + 4
        if sel_item.consumable:
            desc = _consumable_desc(sel_item.use_effect)
            if desc:
                screen.blit(small.render(desc, True, (170, 220, 170)), (inv_x, ry))
                ry += small.get_height() + 4
            screen.blit(small.render("Press Enter to use.", True, (150, 150, 150)), (inv_x, ry))
        else:
            current = pState.equipment.get(sel_item.slot)
            screen.blit(small.render(f"Slot: {sel_item.slot.capitalize()}", True, (170, 170, 170)),
                        (inv_x, ry)); ry += small.get_height() + 4
            if current:
                screen.blit(small.render(f"Replacing: {current.name}", True, (190, 150, 150)),
                            (inv_x, ry)); ry += small.get_height() + 4
            all_stats = set(sel_item.stats) | (set(current.stats) if current else set())
            for stat in sorted(all_stats):
                nv    = sel_item.stats.get(stat, 0)
                cv    = current.stats.get(stat, 0) if current else 0
                d     = nv - cv
                col   = (100, 230, 100) if d > 0 else (230, 100, 100) if d < 0 else (170, 170, 170)
                label = (_stat_label(stat, d) if stat not in ("flee_bonus", "reflect")
                         else _stat_label(stat, nv))
                screen.blit(font.render(label, True, col),
                            (inv_x, ry)); ry += font.get_height() + 4
    elif not groups:
        screen.blit(font.render("No items", True, (110, 110, 110)), (inv_x, ry))

    if pState.active_panel == "equipment":
        hint_text = "> Inventory  |  Enter: Unequip  |  ESC: Close"
    else:
        fam_hint  = "  |  F: Unequip Charm" if (pState.familiar.found and pState.familiar.equipment) else ""
        hint_text = f"< Equipment  |  Enter: Equip/Use  |  ESC: Close{fam_hint}"
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

    hint = small.render("Left/Right: Switch panel   Enter: Transfer   ESC: Close", True, (130, 130, 130))
    screen.blit(hint, (cx - hint.get_width() // 2, h - hint.get_height() - 15))


def render_questboard(screen, wState, pState, area):
    w, h = screen.get_size()
    font, small = _fonts(h)
    _bg(screen, area.image)
    _overlay(screen)
    cx  = w // 2
    y   = int(h * 0.12)

    _dusk_areas = {"duskwall", "duskwall_tavern", "duskwall_shop"}
    board_title = "Bounty Board" if wState.area in _dusk_areas else "Quest Board"
    hdr = font.render(board_title, True, (255, 255, 255))
    screen.blit(hdr, (cx - hdr.get_width() // 2, y)); y += font.get_height() + 24

    _in_dusk  = wState.area in _dusk_areas
    fixed_job = "smuggle" if _in_dusk else "odd_jobs"
    board_items = [fixed_job]
    if wState.questboard_quest_id:
        board_items.append("quest")
    sel_idx = min(wState.questboard_index, len(board_items) - 1)

    # Fixed repeatable job row
    selected = (sel_idx == 0)
    col    = (255, 255, 0) if selected else (220, 220, 220)
    prefix = "> " if selected else "  "
    if _in_dusk:
        screen.blit(font.render(prefix + "Smuggle Run", True, col), (80, y)); y += font.get_height() + 4
        screen.blit(small.render("    Earn marks. Risky — chance of losing HP, gold, or items.", True, (170, 170, 170)), (80, y)); y += small.get_height() + 4
    else:
        screen.blit(font.render(prefix + "Odd Jobs", True, col), (80, y)); y += font.get_height() + 4
        screen.blit(small.render("    Earn gold and 1 food. Heals you fully.", True, (170, 170, 170)), (80, y)); y += small.get_height() + 4
    if selected:
        screen.blit(small.render("    Enter: Accept", True, (100, 200, 100)), (80, y))
    y += small.get_height() + 20

    # Daily quest/bounty
    if wState.questboard_quest_id:
        quest = next((q for q in quests.QUESTS if q["id"] == wState.questboard_quest_id), None)
        if quest:
            selected_q = (sel_idx == 1)
            col_q    = (255, 255, 0) if selected_q else (220, 220, 220)
            prefix_q = "> " if selected_q else "  "
            reward_suffix = " marks" if quest.get("area") == "duskwall" else "g"
            screen.blit(font.render(prefix_q + quest["name"], True, col_q), (80, y)); y += font.get_height() + 4
            screen.blit(small.render(f"    {quest['desc']}", True, (180, 180, 180)), (80, y)); y += small.get_height() + 4
            if quest["reward"] > 0:
                screen.blit(small.render(f"    Reward: {quest['reward']}{reward_suffix}", True, (200, 180, 80)), (80, y)); y += small.get_height() + 4
            if selected_q:
                screen.blit(small.render("    Enter: Accept Bounty" if _in_dusk else "    Enter: Accept Quest", True, (100, 200, 100)), (80, y))
    else:
        screen.blit(small.render("  No new bounties available today." if _in_dusk else "  No new quests available today.", True, (100, 100, 100)), (80, y))

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

    # Smuggle job confirm popup
    elif wState.questboard_confirm == "smuggle":
        _overlay(screen, 210)
        py = h // 3
        for line in ["Take a Smuggle Run?", "",
                     "This will consume the entire day.",
                     "You will earn marks — but risk losing HP, gold, or items.", ""]:
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
        penalty_str = ("Warning: Failing this bounty will cost you half your marks!"
                       if _in_dusk else "Warning: Failing this quest will cost you half your gold!")
        for line, color in [
            (f"Accept '{q_name}'?",   (255, 255, 255)),
            ("",                       (255, 255, 255)),
            (penalty_str,              (220, 100, 80)),
            (f"Due in {q_days} days." if q_days else "", (180, 160, 80)),
            ("",                       (255, 255, 255)),
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
    cx  = w // 2
    cy  = int(h * 0.18)

    _dusk      = wState.area == "duskwall"
    _curr      = "marks" if _dusk else "g"
    _curr_word = "marks" if _dusk else "gold"
    _npc_hdr   = "Guildmaster Rook" if _dusk else "Innkeeper Bram"
    _npc_id    = "duskwall_guild"    if _dusk else "restholm_innkeeper"

    # ── Header ────────────────────────────────────────────────────────────────
    hdr = font.render(_npc_hdr, True, (255, 255, 255))
    screen.blit(hdr, (cx - hdr.get_width() // 2, cy)); cy += font.get_height() + 6
    pygame.draw.line(screen, (100, 90, 70), (cx - 160, cy), (cx + 160, cy), 1)
    cy += 16

    # ── Debt / currency info ──────────────────────────────────────────────────
    wallet = pState.marks if _dusk else pState.gold
    if pState.debt > 0:
        owe_t  = font.render(f"You owe:    {pState.debt} {_curr_word}", True, (220, 80, 80))
        gold_t = font.render(f"Your {_curr_word}:  {wallet}", True, (255, 215, 50))
        screen.blit(owe_t,  (cx - owe_t.get_width()  // 2, cy)); cy += font.get_height() + 8
        screen.blit(gold_t, (cx - gold_t.get_width() // 2, cy)); cy += font.get_height() + 24
    else:
        paid_t = font.render("Debt fully paid. Thank you, adventurer!", True, (130, 200, 130))
        screen.blit(paid_t, (cx - paid_t.get_width() // 2, cy)); cy += font.get_height() + 24

    # ── Two-option menu ───────────────────────────────────────────────────────
    pay        = min(10, wallet, pState.debt) if pState.debt > 0 else 0
    can_pay    = pay > 0
    opt        = wState.innkeeper_option

    if pState.debt > 0:
        pay_label = f"Pay {pay} {_curr_word} toward debt" if can_pay else f"Not enough {_curr_word}"
    else:
        pay_label = "Debt paid - nothing to pay"

    options = [pay_label, f"Talk to {_npc_hdr}"]

    opt_w  = int(w * 0.46)
    opt_h  = font.get_height() + 20
    opt_x  = cx - opt_w // 2

    for i, label in enumerate(options):
        sel      = (i == opt)
        disabled = (i == 0 and not can_pay)
        bg       = pygame.Surface((opt_w, opt_h), pygame.SRCALPHA)
        bg.fill((100, 100, 140, 200) if sel else (20, 20, 30, 150))
        screen.blit(bg, (opt_x, cy))
        pygame.draw.rect(screen, (200, 200, 255) if sel else (50, 50, 70),
                         pygame.Rect(opt_x, cy, opt_w, opt_h), 1)
        col = (180, 180, 180) if disabled else (255, 255, 255) if sel else (160, 160, 170)
        t   = font.render(label, True, col)
        screen.blit(t, (cx - t.get_width() // 2, cy + 10))
        cy += opt_h + 8

    cy += 10
    hint = small.render("Up/Down: Navigate    Enter: Select    ESC: Leave", True, (110, 110, 110))
    screen.blit(hint, (cx - hint.get_width() // 2, cy))


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
        ("The road ahead leads to Duskwall - and a second debt.", (200, 180, 130)),
        ("",                                                       (255, 255, 255)),
        ("New Debt:  200 marks",                                    (220, 80, 80)),
        ("Due by Day 28",                                           (200, 120, 80)),
        ("",                                                         (255, 255, 255)),
        ("Good luck.",                                               (160, 160, 160)),
    ]:
        t = font.render(line, True, color)
        screen.blit(t, (cx - t.get_width() // 2, cy)); cy += font.get_height() + 10

    hint = small.render("Press any key to continue.", True, (130, 130, 130))
    screen.blit(hint, (cx - hint.get_width() // 2, h - hint.get_height() - 15))


def render_dialogue(screen, wState, area):
    w, h = screen.get_size()
    font, small = _fonts(h)
    _bg(screen, area.image)
    _overlay(screen, 170)

    box_w = int(w * 0.78)
    box_h = int(h * 0.28)
    box_x = (w - box_w) // 2
    box_y = h - box_h - int(h * 0.06)
    pad   = 20

    # ── Portrait ──────────────────────────────────────────────────────────────
    portrait_path = dialogue.get_portrait(wState.dialogue_npc_id)
    portrait_surf = None
    p_w = 0
    if portrait_path:
        p_h = int(h * 0.38)
        portrait_surf = load_portrait(portrait_path, p_h)
        if portrait_surf:
            p_w   = portrait_surf.get_width()
            p_h   = portrait_surf.get_height()
            p_x   = box_x
            p_y   = box_y - p_h
            # Dark framed backing
            pygame.draw.rect(screen, (10, 10, 20), (p_x - 2, p_y - 2, p_w + 4, p_h + 4))
            pygame.draw.rect(screen, (160, 140, 100), (p_x - 2, p_y - 2, p_w + 4, p_h + 4), 2)
            screen.blit(portrait_surf, (p_x, p_y))

    box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    box.fill((10, 10, 20, 220))
    screen.blit(box, (box_x, box_y))
    pygame.draw.rect(screen, (160, 140, 100), pygame.Rect(box_x, box_y, box_w, box_h), 2)

    # Name plate — shifted right of portrait if present
    name_x    = box_x + (p_w + 8 if portrait_surf else 0)
    npc_name  = dialogue.get_name(wState.dialogue_npc_id)
    name_surf = font.render(npc_name, True, (255, 220, 130))
    name_bg   = pygame.Surface((name_surf.get_width() + pad * 2, font.get_height() + 10), pygame.SRCALPHA)
    name_bg.fill((10, 10, 20, 220))
    screen.blit(name_bg, (name_x, box_y - font.get_height() - 10))
    pygame.draw.rect(screen, (160, 140, 100),
                     pygame.Rect(name_x, box_y - font.get_height() - 10,
                                 name_surf.get_width() + pad * 2, font.get_height() + 10), 2)
    screen.blit(name_surf, (name_x + pad, box_y - font.get_height() - 5))

    # Dialogue text — shifted right to clear portrait if it sits inside the box
    text_x   = box_x + pad + (p_w + 8 if portrait_surf else 0)
    lines    = wState.dialogue_lines
    line_idx = wState.dialogue_line_index
    if lines:
        line_surf = font.render(lines[line_idx], True, (230, 230, 220))
        screen.blit(line_surf, (text_x, box_y + pad))

    page_str  = f"{line_idx + 1} / {len(lines)}"
    page_surf = small.render(page_str, True, (120, 120, 120))
    screen.blit(page_surf, (box_x + box_w - page_surf.get_width() - pad,
                             box_y + box_h - page_surf.get_height() - 10))

    is_last   = line_idx >= len(lines) - 1
    hint_text = "[ ESC / Enter: Close ]" if is_last else "[ Enter: Continue ]   [ ESC: Close ]"
    hint_surf = small.render(hint_text, True, (110, 110, 110))
    screen.blit(hint_surf, (box_x + pad, box_y + box_h - hint_surf.get_height() - 10))


# ── Intro sequence ────────────────────────────────────────────────────────────

def render_intro(screen, wState, pState):
    w, h    = screen.get_size()
    font, small = _fonts(h)
    phase   = wState.intro_phase
    cx      = w // 2

    # ── White room phases (opening / name / qa / qa_response) ─────────────────
    if phase in ("opening", "name", "qa", "qa_response"):
        heaven = load_portrait("assets/images/Heaven.jpeg", h)
        if heaven:
            screen.blit(heaven, (w // 2 - heaven.get_width() // 2, 0))
        else:
            screen.fill((235, 230, 220))   # fallback parchment-white
        _overlay(screen, 60)   # light tint to keep text readable

        # Robed man portrait — right side of screen
        _robe_h  = int(h * 0.55)
        robe_img = load_portrait("assets/images/Man In White Robe.jpeg", _robe_h)
        if robe_img:
            robe_x = int(w * 0.62)
            robe_y = int(h * 0.18)
            screen.blit(robe_img, (robe_x, robe_y))

        # Robed-man label — shadowed white so it reads over any background
        lbl_y   = int(h * 0.08)
        lbl_sh  = font.render("Robed Man", True, (0, 0, 0))
        lbl_txt = font.render("Robed Man", True, (240, 235, 220))
        screen.blit(lbl_sh,  (cx - lbl_sh.get_width()  // 2 + 2, lbl_y + 2))
        screen.blit(lbl_txt, (cx - lbl_txt.get_width() // 2,     lbl_y))
        rule_y = lbl_y + font.get_height() + 6
        pygame.draw.line(screen, (180, 170, 150), (cx - 140, rule_y), (cx + 140, rule_y), 1)

        # ── Shared helper: dark-backed text box at the bottom ─────────────────
        box_pad  = 18
        box_text_y = int(h * 0.74)
        box_h_px   = font.get_height() + box_pad * 2
        box_surf   = pygame.Surface((w, box_h_px), pygame.SRCALPHA)
        box_surf.fill((0, 0, 0, 180))
        screen.blit(box_surf, (0, box_text_y))
        pygame.draw.line(screen, (120, 110, 95), (0, box_text_y),     (w, box_text_y),     1)
        pygame.draw.line(screen, (120, 110, 95), (0, box_text_y + box_h_px),
                                                  (w, box_text_y + box_h_px), 1)

        def _blit_line_shadowed(text, color=(240, 235, 220)):
            sh  = font.render(text, True, (0, 0, 0))
            txt = font.render(text, True, color)
            ty  = box_text_y + box_pad
            screen.blit(sh,  (cx - sh.get_width()  // 2 + 2, ty + 2))
            screen.blit(txt, (cx - txt.get_width() // 2,     ty))

        hint_y  = int(h * 0.92)
        prog_y  = int(h * 0.86)

        def _blit_small_shadowed(text, y, color=(200, 190, 165)):
            sh  = small.render(text, True, (0, 0, 0))
            txt = small.render(text, True, color)
            screen.blit(sh,  (cx - sh.get_width()  // 2 + 1, y + 1))
            screen.blit(txt, (cx - txt.get_width() // 2,     y))

        if phase == "opening":
            lines     = intro.OPENING_LINES
            idx       = wState.intro_line_index
            line_text = lines[idx] if idx < len(lines) else ""
            _blit_line_shadowed(line_text)

            _blit_small_shadowed(f"{idx + 1} / {len(lines)}", prog_y, (180, 170, 140))
            _blit_small_shadowed("[ Enter / Space: Continue ]   [ ESC: Skip ]", hint_y)

        elif phase == "name":
            # Prompt in the box
            _blit_line_shadowed('"Before you go - your name?"')

            buf        = wState.name_input_buffer
            cursor     = "_" if pygame.time.get_ticks() % 1000 < 500 else " "
            input_surf = font.render(buf + cursor, True, (20, 20, 20))
            inp_box_w  = max(280, input_surf.get_width() + 40)
            inp_box_x  = cx - inp_box_w // 2
            inp_box_y  = int(h * 0.84)
            pygame.draw.rect(screen, (210, 205, 195), pygame.Rect(inp_box_x, inp_box_y, inp_box_w, font.get_height() + 16))
            pygame.draw.rect(screen, (120, 110, 90),  pygame.Rect(inp_box_x, inp_box_y, inp_box_w, font.get_height() + 16), 2)
            screen.blit(input_surf, (inp_box_x + 14, inp_box_y + 8))

            _blit_small_shadowed("[ Enter: Confirm ]", hint_y)

        elif phase in ("qa", "qa_response"):
            if phase == "qa":
                # Prompt in the box
                prompt_text = f'"Right, {pState.name}. Any questions before you go?"'
                _blit_line_shadowed(prompt_text)

                # Menu options above the box
                opt_y = int(h * 0.48)
                for i, (label_text, _) in enumerate(intro.QA_OPTIONS):
                    selected = (i == wState.intro_qa_index)
                    prefix   = ">  " if selected else "   "
                    full     = prefix + label_text
                    sh  = font.render(full, True, (0, 0, 0))
                    txt = font.render(full, True, (255, 240, 180) if selected else (200, 190, 165))
                    screen.blit(sh,  (cx - sh.get_width()  // 2 + 2, opt_y + 2))
                    screen.blit(txt, (cx - txt.get_width() // 2,     opt_y))
                    opt_y += font.get_height() + 10

                _blit_small_shadowed("[ Up/Down: Navigate ]   [ Enter: Select ]", hint_y)

            else:  # qa_response
                resp      = wState.intro_qa_response
                r_idx     = wState.intro_line_index
                line_text = resp[r_idx] if r_idx < len(resp) else ""
                _blit_line_shadowed(line_text)

                _blit_small_shadowed(f"{r_idx + 1} / {len(resp)}", prog_y, (180, 170, 140))
                _blit_small_shadowed("[ Enter / Space / ESC: Continue ]", hint_y)

    # ── Closing / arrival (dark) ───────────────────────────────────────────────
    else:  # phase == "closing"
        screen.fill((10, 8, 12))

        lines   = intro.CLOSING_LINES
        c_idx   = wState.intro_line_index
        is_last = c_idx >= len(lines) - 1

        # Show last few lines (trailing context window)
        visible = lines[max(0, c_idx - 2): c_idx + 1]
        base_y  = h // 2 - font.get_height() * len(visible) // 2
        for i, vline in enumerate(visible):
            alpha = 255 if i == len(visible) - 1 else 100
            if vline:
                col = (alpha, alpha, alpha)
                t   = font.render(vline, True, col)
                screen.blit(t, (cx - t.get_width() // 2, base_y + i * (font.get_height() + 12)))

        hint_text = "[ Enter / Space: Finish ]" if is_last else "[ Enter / Space: Continue ]"
        hint = small.render(hint_text, True, (60, 55, 50))
        screen.blit(hint, (cx - hint.get_width() // 2, int(h * 0.88)))


# ── Passive skill selection ───────────────────────────────────────────────────

def render_passive_select(screen, wState, pState):
    w, h = screen.get_size()
    font, small = _fonts(h)
    _overlay(screen, 230)

    cx  = w // 2
    cy  = int(h * 0.12)

    milestone = wState.passive_pending_milestone
    hdr = font.render(f"Level {milestone} - Choose a Passive Skill", True, (255, 215, 80))
    screen.blit(hdr, (cx - hdr.get_width() // 2, cy))
    cy += font.get_height() + 6

    sub = small.render("This choice is permanent for this run.", True, (160, 150, 100))
    screen.blit(sub, (cx - sub.get_width() // 2, cy))
    cy += small.get_height() + 30

    options = wState.passive_select_options
    card_w  = int(w * 0.55)
    card_h  = int(h * 0.18)
    card_x  = cx - card_w // 2
    pad     = 16

    for i, pid in enumerate(options):
        passive  = passives_data.PASSIVES.get(pid, {})
        selected = (i == wState.passive_select_index)

        bg_col  = (50, 80, 50, 220)  if selected else (25, 25, 35, 200)
        bdr_col = (130, 210, 110)    if selected else (70, 70, 90)

        card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        card.fill(bg_col)
        screen.blit(card, (card_x, cy))
        pygame.draw.rect(screen, bdr_col, pygame.Rect(card_x, cy, card_w, card_h), 2)

        prefix   = ">  " if selected else "   "
        name_col = (220, 255, 200) if selected else (210, 210, 210)
        name_t   = font.render(prefix + passive.get("name", pid), True, name_col)
        screen.blit(name_t, (card_x + pad, cy + pad))

        desc_t = small.render(passive.get("desc", ""), True, (180, 180, 180))
        screen.blit(desc_t, (card_x + pad + 18, cy + pad + font.get_height() + 8))

        cy += card_h + 12

    hint = small.render("[ Up/Down: Navigate ]   [ Enter: Confirm ]", True, (120, 110, 90))
    screen.blit(hint, (cx - hint.get_width() // 2, int(h * 0.90)))


# ── Map screen ────────────────────────────────────────────────────────────────

def render_map(screen, wState, area):
    w, h = screen.get_size()
    font, small = _fonts(h)

    screen.fill((12, 10, 16))
    _overlay(screen, 0)   # no additional overlay — just the dark bg

    cx = w // 2
    cy = int(h * 0.12)

    hdr = font.render("Map", True, (200, 190, 150))
    screen.blit(hdr, (cx - hdr.get_width() // 2, cy))
    cy += font.get_height() + 4

    sub = small.render("Travel between towns", True, (90, 85, 70))
    screen.blit(sub, (cx - sub.get_width() // 2, cy))

    # ── Town nodes ────────────────────────────────────────────────────────────
    node_y   = int(h * 0.45)
    r_x      = int(w * 0.28)   # Restholm X
    d_x      = int(w * 0.72)   # Duskwall  X
    node_r   = int(h * 0.055)

    # Road connecting the two towns (dotted line)
    road_y = node_y
    for dx in range(r_x + node_r + 10, d_x - node_r - 10, 18):
        pygame.draw.circle(screen, (60, 55, 45), (dx, road_y), 2)

    towns = [
        {"label": "Restholm", "x": r_x, "current": wState.area == "village",  "idx": 0},
        {"label": "Duskwall",  "x": d_x, "current": wState.area == "duskwall", "idx": 1},
    ]

    for t in towns:
        selected  = (t["idx"] == wState.map_cursor)
        is_here   = t["current"]
        bdr_color = (220, 200, 100) if selected else (100, 95, 80)
        fill_col  = (35, 32, 25) if is_here else (22, 20, 18)
        pygame.draw.circle(screen, fill_col,  (t["x"], node_y), node_r)
        pygame.draw.circle(screen, bdr_color, (t["x"], node_y), node_r, 3 if selected else 1)

        label_col = (255, 235, 140) if selected else (170, 160, 130)
        lbl = font.render(t["label"], True, label_col)
        screen.blit(lbl, (t["x"] - lbl.get_width() // 2, node_y + node_r + 10))

        if is_here:
            here = small.render("(You are here)", True, (120, 180, 120))
            screen.blit(here, (t["x"] - here.get_width() // 2, node_y + node_r + font.get_height() + 16))
        elif selected:
            go = small.render("[ Enter: Travel ]", True, (180, 170, 120))
            screen.blit(go, (t["x"] - go.get_width() // 2, node_y + node_r + font.get_height() + 16))

    hint = small.render("[ Arrows: Select ]   [ Enter: Travel ]   [ ESC: Close ]", True, (70, 65, 55))
    screen.blit(hint, (cx - hint.get_width() // 2, int(h * 0.88)))


# ── Ending sequence ───────────────────────────────────────────────────────────

def render_ending(screen, wState):
    w, h = screen.get_size()
    font, small = _fonts(h)
    cx  = w // 2
    idx = wState.ending_line_index
    lines = intro.ENDING_LINES

    # Warm white room — mirrors the intro's visual language
    heaven = load_portrait("assets/images/Heaven.jpeg", h)
    if heaven:
        screen.blit(heaven, (w // 2 - heaven.get_width() // 2, 0))
    else:
        screen.fill((240, 235, 225))
    _overlay(screen, 60)

    # Robed man portrait — right side
    robe_img = load_portrait("assets/images/Man In White Robe.jpeg", int(h * 0.55))
    if robe_img:
        screen.blit(robe_img, (int(w * 0.62), int(h * 0.18)))

    # Robed man label + rule
    label = font.render("Robed Man", True, (90, 78, 62))
    screen.blit(label, (cx - label.get_width() // 2, int(h * 0.12)))
    rule_y = int(h * 0.12) + font.get_height() + 6
    pygame.draw.line(screen, (190, 178, 155), (cx - 140, rule_y), (cx + 140, rule_y), 1)

    # Trailing context window — show up to 3 recent lines, fading older ones
    visible = lines[max(0, idx - 2): idx + 1]
    base_y  = h // 2 - font.get_height() * len(visible) // 2
    for i, vline in enumerate(visible):
        is_current = (i == len(visible) - 1)
        alpha = 200 if is_current else 80
        if vline:
            col = (alpha // 2, alpha // 2 - 10, alpha // 2 - 20)
            col = (max(0, 60 - (len(visible) - 1 - i) * 40),) * 3
            col = (40, 35, 25) if is_current else (160, 152, 138)
            t = font.render(vline, True, col)
            screen.blit(t, (cx - t.get_width() // 2,
                            base_y + i * (font.get_height() + 14)))

    # Progress and hint
    is_last = idx >= len(lines) - 1
    prog = small.render(f"{idx + 1} / {len(lines)}", True, (180, 170, 150))
    screen.blit(prog, (cx - prog.get_width() // 2, int(h * 0.82)))

    hint_text = "[ Enter / Space: Finish ]" if is_last else "[ Enter / Space: Continue ]"
    hint = small.render(hint_text, True, (175, 163, 140))
    screen.blit(hint, (cx - hint.get_width() // 2, int(h * 0.88)))


# ── Familiar naming ───────────────────────────────────────────────────────────

def render_familiar_naming(screen, wState, pState):
    w, h = screen.get_size()
    font, small = _fonts(h)
    screen.fill((15, 12, 20))
    cx = w // 2
    cy = h // 2 - font.get_height() * 4

    hdr = font.render("A familiar has chosen you.", True, (200, 185, 150))
    screen.blit(hdr, (cx - hdr.get_width() // 2, cy)); cy += font.get_height() + 16

    sub = small.render("She watches you with ancient, steady eyes.", True, (140, 130, 110))
    screen.blit(sub, (cx - sub.get_width() // 2, cy)); cy += small.get_height() + 30

    prompt = font.render("Give her a name:", True, (220, 210, 180))
    screen.blit(prompt, (cx - prompt.get_width() // 2, cy)); cy += font.get_height() + 20

    cursor = "_" if (pygame.time.get_ticks() // 500) % 2 == 0 else " "
    buf_surf = font.render(wState.familiar_name_buffer + cursor, True, (255, 240, 180))
    screen.blit(buf_surf, (cx - buf_surf.get_width() // 2, cy)); cy += font.get_height() + 24

    hint = small.render("Enter to confirm   Backspace to delete", True, (90, 85, 75))
    screen.blit(hint, (cx - hint.get_width() // 2, cy))
