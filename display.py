'''
display.py
Handles the window and rendering things onto the screen
'''

import pygame
import gamestate
import save

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

_image_cache = {}

#set up the window
def init_display():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("QuestForRest")
    return screen

def _load_image(path):
    if path not in _image_cache:
        _image_cache[path] = pygame.image.load(path).convert()
    return _image_cache[path]

def _render_main_menu(screen, wState, area):
    width, height = screen.get_size()
    font = pygame.font.SysFont("Arial", max(int(height * 0.035), 18))
    small = pygame.font.SysFont("Arial", max(int(height * 0.025), 14))

    background = pygame.transform.scale(_load_image(area.image), (width, height))
    screen.blit(background, (0, 0))

    cx = width // 2
    y = int(height * 0.45)

    if wState.main_menu_confirm == "new_game_notify":
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))
        lines = ["You have existing save files.", "", "Enter: Start New Game    ESC: Back"]
        for line in lines:
            t = font.render(line, True, (255, 255, 255))
            screen.blit(t, (cx - t.get_width() // 2, y))
            y += font.get_height() + 8

    elif wState.main_menu_confirm == "load":
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))
        header = font.render("Select Save", True, (255, 255, 255))
        screen.blit(header, (cx - header.get_width() // 2, y))
        y += font.get_height() + 16
        for i, (slot, data) in enumerate(wState.available_saves):
            day = data.get("world", {}).get("day", "?")
            label = f"Save {slot}  —  Day {day}"
            color = (255, 255, 0) if i == wState.load_menu_index else (220, 220, 220)
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
            if unavailable:
                color = (80, 80, 80)
            elif i == wState.main_menu_index:
                color = (255, 255, 0)
            else:
                color = (220, 220, 220)
            prefix = "> " if i == wState.main_menu_index and not unavailable else "  "
            t = font.render(prefix + item, True, color)
            screen.blit(t, (cx - t.get_width() // 2, y))
            y += font.get_height() + 12

    pygame.display.flip()

def _render_shop(screen, wState, pState, area):
    width, height = screen.get_size()
    font  = pygame.font.SysFont("Arial", max(int(height * 0.035), 18))
    small = pygame.font.SysFont("Arial", max(int(height * 0.025), 14))

    background = pygame.transform.scale(_load_image(area.image), (width, height))
    screen.blit(background, (0, 0))
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 185))
    screen.blit(overlay, (0, 0))

    cx = width // 2
    col_name  = cx - 260
    col_stats = cx - 20
    col_price = cx + 160

    y = 40
    title = "Shop  —  Buy" if wState.shop_mode == "buy" else "Shop  —  Sell"
    t = font.render(title, True, (255, 255, 255))
    screen.blit(t, (cx - t.get_width() // 2, y))
    y += font.get_height() + 8

    gold_t = font.render(f"Gold: {pState.gold}", True, (255, 215, 50))
    screen.blit(gold_t, (cx - gold_t.get_width() // 2, y))
    y += font.get_height() + 24

    items_list = wState.shop_inventory if wState.shop_mode == "buy" else pState.inventory

    if not items_list:
        msg = "Nothing in stock." if wState.shop_mode == "buy" else "Nothing to sell."
        m = font.render(msg, True, (120, 120, 120))
        screen.blit(m, (cx - m.get_width() // 2, y))
    else:
        for i, item in enumerate(items_list):
            selected  = (i == wState.shop_index)
            price     = item.price if wState.shop_mode == "buy" else max(1, item.price // 2)
            can_afford = pState.gold >= item.price if wState.shop_mode == "buy" else True

            prefix     = "> " if selected else "  "
            name_color = (255, 255, 0) if selected else (215, 215, 215)
            price_color = (150, 150, 150) if not selected else ((220, 80, 80) if not can_afford else (255, 215, 50))

            stats_str = "  ".join(f"{k.capitalize()} +{v}" for k, v in item.stats.items())

            screen.blit(font.render(prefix + item.name, True, name_color),  (col_name,  y))
            screen.blit(small.render(stats_str,          True, (170, 170, 170)), (col_stats, y + 4))
            screen.blit(font.render(f"{price}g",         True, price_color),    (col_price, y))
            y += font.get_height() + 8

        if wState.shop_mode == "buy" and not can_afford:
            msg = small.render("Not enough gold.", True, (200, 80, 80))
            screen.blit(msg, (cx - msg.get_width() // 2, y + 8))

    hint_text = "Enter: Buy    ESC: Back" if wState.shop_mode == "buy" else "Enter: Sell    ESC: Back"
    hint = small.render(hint_text, True, (130, 130, 130))
    screen.blit(hint, (cx - hint.get_width() // 2, height - hint.get_height() - 15))

    pygame.display.flip()

_SLOT_POSITIONS = {
    "head":   (0.50, 0.12),
    "amulet": (0.50, 0.32),
    "weapon": (0.18, 0.32),
    "shield": (0.82, 0.32),
    "body":   (0.50, 0.52),
    "ring":   (0.18, 0.52),
    "legs":   (0.50, 0.72),
}

def _render_inventory(screen, wState, pState, area):
    width, height = screen.get_size()
    font  = pygame.font.SysFont("Arial", max(int(height * 0.028), 15))
    small = pygame.font.SysFont("Arial", max(int(height * 0.022), 12))

    background = pygame.transform.scale(_load_image(area.image), (width, height))
    screen.blit(background, (0, 0))
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 185))
    screen.blit(overlay, (0, 0))

    lp_w   = int(width * 0.40)   #paper doll column
    stat_x = lp_w + 15           #stats column start
    stat_w = int(width * 0.18)   #stats column width
    inv_x  = stat_x + stat_w + 15  #items column start

    #column dividers
    pygame.draw.line(screen, (80, 80, 100), (lp_w, 0), (lp_w, height), 1)
    pygame.draw.line(screen, (80, 80, 100), (stat_x + stat_w, 0), (stat_x + stat_w, height), 1)

    #paper doll
    slot_w = int(width * 0.09)
    slot_h = int(height * 0.09)
    doll_header = font.render("Equipment", True, (255, 255, 255))
    screen.blit(doll_header, (lp_w // 2 - doll_header.get_width() // 2, 18))

    selected_slot = (gamestate.EQUIPMENT_SLOTS[pState.equip_slot_index]
                     if pState.active_panel == "equipment" else None)

    for slot_name, (xf, yf) in _SLOT_POSITIONS.items():
        sx = int(lp_w * xf - slot_w // 2)
        sy = int(height * yf - slot_h // 2)
        is_selected = (slot_name == selected_slot)
        pygame.draw.rect(screen, (45, 45, 58), (sx, sy, slot_w, slot_h))
        pygame.draw.rect(screen, (255, 255, 0) if is_selected else (110, 110, 135),
                         (sx, sy, slot_w, slot_h), 2 if is_selected else 1)
        screen.blit(small.render(slot_name.capitalize(), True, (130, 130, 155)), (sx + 4, sy + 3))
        equipped = pState.equipment.get(slot_name)
        item_label = small.render(equipped.name if equipped else "Empty",
                                  True, (210, 210, 255) if equipped else (65, 65, 78))
        screen.blit(item_label, (sx + 4, sy + slot_h - small.get_height() - 4))

    #stats
    atk_bonus = sum(i.stats.get("attack",  0) for i in pState.equipment.values() if i)
    def_bonus = sum(i.stats.get("defense", 0) for i in pState.equipment.values() if i)

    sy = 18
    screen.blit(font.render("Stats", True, (255, 255, 255)), (stat_x, sy))
    sy += font.get_height() + 14

    screen.blit(small.render(f"HP:      {pState.health}", True, (220, 80, 80)), (stat_x, sy))
    sy += small.get_height() + 6
    screen.blit(small.render(f"Gold:    {pState.gold}", True, (255, 215, 50)), (stat_x, sy))
    sy += small.get_height() + 6
    screen.blit(small.render(f"Attack:  {pState.base_attack  + atk_bonus}", True, (220, 220, 220)), (stat_x, sy))
    sy += small.get_height() + 6
    screen.blit(small.render(f"Defense: {pState.base_defense + def_bonus}", True, (220, 220, 220)), (stat_x, sy))
    sy += small.get_height() + 6

    #inventory list
    ry = 18
    screen.blit(font.render("Inventory", True, (255, 255, 255)), (inv_x, ry))
    ry += font.get_height() + 12

    if not pState.inventory:
        screen.blit(font.render("No items", True, (110, 110, 110)), (inv_x, ry))
    else:
        for i, inv_item in enumerate(pState.inventory):
            selected = (i == pState.inventory_index and pState.active_panel == "inventory")
            color  = (255, 255, 0) if selected else (215, 215, 215)
            prefix = "> " if selected else "  "
            screen.blit(font.render(prefix + inv_item.name, True, color), (inv_x, ry))
            ry += font.get_height() + 4

        if 0 <= pState.inventory_index < len(pState.inventory):
            sel     = pState.inventory[pState.inventory_index]
            current = pState.equipment.get(sel.slot)
            ry += 10
            pygame.draw.line(screen, (80, 80, 100), (inv_x, ry), (width - 15, ry), 1)
            ry += 8
            screen.blit(small.render(f"Slot: {sel.slot.capitalize()}", True, (170, 170, 170)), (inv_x, ry))
            ry += small.get_height() + 4
            if current:
                screen.blit(small.render(f"Replacing: {current.name}", True, (190, 150, 150)), (inv_x, ry))
                ry += small.get_height() + 4
            all_stats = set(sel.stats) | (set(current.stats) if current else set())
            for stat in sorted(all_stats):
                new_val = sel.stats.get(stat, 0)
                cur_val = current.stats.get(stat, 0) if current else 0
                delta   = new_val - cur_val
                color   = (100, 230, 100) if delta > 0 else (230, 100, 100) if delta < 0 else (170, 170, 170)
                sign    = "+" if delta >= 0 else ""
                screen.blit(font.render(f"{stat.capitalize()}: {sign}{delta}", True, color), (inv_x, ry))
                ry += font.get_height() + 4

    if pState.active_panel == "equipment":
        hint_text = "→ Inventory  |  Enter: Unequip  |  ESC: Close"
    else:
        hint_text = "← Equipment  |  Enter: Equip  |  ESC: Close"
    hint = small.render(hint_text, True, (130, 130, 130))
    screen.blit(hint, (inv_x, height - hint.get_height() - 15))

    pygame.display.flip()

#render information on the screen
def render(screen, wState, pState, area):
    if wState.area == "start_screen":
        _render_main_menu(screen, wState, area)
        return

    if wState.shop_mode:
        _render_shop(screen, wState, pState, area)
        return

    if wState.inventory_open:
        _render_inventory(screen, wState, pState, area)
        return

    width, height = screen.get_size()
    #handle font
    font_size = max(int(height * 0.03), 16)  #3% of height, min 16
    font = pygame.font.SysFont("Arial", font_size)

    #load background image
    background = pygame.transform.scale(_load_image(area.image), (width, height))
    screen.blit(background, (0, 0))

    #HUD
    time_text = font.render(f"Day: {wState.day}", True, (255, 255, 255))
    screen.blit(time_text, (width - 200, 50))
    
    #bottom ui
    text_pad = 10
    opt_row_h = font.get_height() + text_pad * 2
    text_bar_h = font.get_height() + text_pad * 2
    opt_w = width // 2

    #text bar (area description) — top row
    text_bar_y = height - text_bar_h - opt_row_h * 2
    text_bar = pygame.Surface((width, text_bar_h), pygame.SRCALPHA)
    text_bar.fill((0, 0, 0, 150))
    screen.blit(text_bar, (0, text_bar_y))
    screen.blit(font.render(area.text, True, (255, 255, 255)), (text_pad, text_bar_y + text_pad))

    #2x2 options grid — rows below text
    choices = list(area.choices.values())
    for i in range(4):
        row = i // 2
        col = i % 2
        ox = col * opt_w
        oy = height - opt_row_h * (2 - row)
        has_option = i < len(choices)
        selected = has_option and (i == wState.nav_index)
        bg = pygame.Surface((opt_w, opt_row_h), pygame.SRCALPHA)
        bg.fill((100, 100, 140, 200) if selected else (20, 20, 30, 150))
        screen.blit(bg, (ox, oy))
        pygame.draw.rect(screen, (200, 200, 255) if selected else (50, 50, 70), (ox, oy, opt_w, opt_row_h), 1)
        if has_option:
            _, desc = choices[i]
            t = font.render(desc, True, (255, 255, 255) if selected else (150, 150, 160))
            screen.blit(t, (ox + opt_w // 2 - t.get_width() // 2, oy + text_pad))

    #confirmation dialogs for save and exit
    if wState.menu_confirm:
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        if wState.menu_confirm == "Saved":
            lines = ["Game saved!", "", "Press any key to continue"]
        else:
            lines = [f"{wState.menu_confirm} — are you sure?", "", "Enter: Yes    ESC: No"]
        y = height // 2 - font.get_height() * len(lines) // 2
        for line in lines:
            t = font.render(line, True, (255, 255, 255))
            screen.blit(t, (width // 2 - t.get_width() // 2, y))
            y += font.get_height() + 10

    #when open, render the menu
    elif wState.menu_open:
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        y = 50
        header = font.render("Menu", True, (255, 255, 255))
        screen.blit(header, (50, y))
        y += font.get_height() + 20
        stats = font.render(f"HP: {pState.health}   Gold: {pState.gold}", True, (180, 180, 180))
        screen.blit(stats, (50, y))
        y += font.get_height() + 20
        for i, item in enumerate(gamestate.MENU_ITEMS):
            color = (255, 255, 0) if i == wState.menu_index else (255, 255, 255)
            prefix = "> " if i == wState.menu_index else "  "
            t = font.render(prefix + item, True, color)
            screen.blit(t, (50, y))
            y += font.get_height() + 10

    pygame.display.flip()