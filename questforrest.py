'''
QuestforRest
A rebuild of my untitled c++ text-rpg, now with simple graphics
'''

import pygame
import gameareas
import gamestate
import display
import save

#window and state initialization
screen = display.init_display()
wState = gamestate.WorldState()
pState = gamestate.PlayerState()

#main loop
running = True
while running:
    try:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:

                #main menu (title screen)
                if wState.area == "start_screen":
                    if wState.main_menu_confirm == "new_game_notify":
                        if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                            wState.main_menu_confirm = None
                            if event.key == pygame.K_RETURN:
                                wState.reset()
                                pState.reset()

                    elif wState.main_menu_confirm == "load":
                        if event.key == pygame.K_ESCAPE:
                            wState.main_menu_confirm = None
                        elif event.key == pygame.K_UP:
                            wState.load_menu_index = max(0, wState.load_menu_index - 1)
                        elif event.key == pygame.K_DOWN:
                            wState.load_menu_index = min(len(wState.available_saves) - 1, wState.load_menu_index + 1)
                        elif event.key == pygame.K_RETURN and wState.available_saves:
                            slot, _ = wState.available_saves[wState.load_menu_index]
                            save.load_game(wState, pState, slot)

                    else:
                        has_save = save.save_exists()
                        def _skip(idx, step):
                            idx = (idx + step) % len(gamestate.MAIN_MENU_ITEMS)
                            if gamestate.MAIN_MENU_ITEMS[idx] == "Load Game" and not has_save:
                                idx = (idx + step) % len(gamestate.MAIN_MENU_ITEMS)
                            return idx
                        if event.key == pygame.K_UP:
                            wState.main_menu_index = _skip(wState.main_menu_index, -1)
                        elif event.key == pygame.K_DOWN:
                            wState.main_menu_index = _skip(wState.main_menu_index, 1)
                        elif event.key == pygame.K_RETURN:
                            selected = gamestate.MAIN_MENU_ITEMS[wState.main_menu_index]
                            if selected == "New Game":
                                if save.save_exists():
                                    wState.main_menu_confirm = "new_game_notify"
                                else:
                                    wState.reset()
                                    pState.reset()
                            elif selected == "Load Game":
                                saves = save.list_saves()
                                if saves:
                                    wState.available_saves = saves
                                    wState.load_menu_index = 0
                                    wState.main_menu_confirm = "load"
                            elif selected == "Exit":
                                running = False

                #in-game screens
                elif event.key == pygame.K_ESCAPE:
                    if wState.shop_mode:
                        wState.shop_mode = None
                        wState.shop_index = 0
                    elif wState.inventory_open:
                        wState.inventory_open = False
                        pState.active_panel = "inventory"
                    elif wState.menu_confirm:
                        wState.menu_confirm = None
                    else:
                        wState.menu_open = not wState.menu_open
                        wState.menu_index = 0

                elif wState.inventory_open:
                    _dir = {pygame.K_UP: 0, pygame.K_DOWN: 1,
                            pygame.K_LEFT: 2, pygame.K_RIGHT: 3}
                    if pState.active_panel == "inventory":
                        if event.key == pygame.K_UP:
                            pState.inventory_index = max(0, pState.inventory_index - 1)
                        elif event.key == pygame.K_DOWN:
                            pState.inventory_index = min(len(pState.inventory) - 1, pState.inventory_index + 1)
                        elif event.key == pygame.K_LEFT:
                            pState.active_panel = "equipment"
                        elif event.key == pygame.K_RETURN and pState.inventory:
                            pState.equip_item(pState.inventory_index)
                    else:
                        if event.key in _dir:
                            slot = gamestate.EQUIPMENT_SLOTS[pState.equip_slot_index]
                            dest = gamestate.EQUIP_NAV[slot][_dir[event.key]]
                            if dest == "items":
                                pState.active_panel = "inventory"
                            elif dest is not None:
                                pState.equip_slot_index = gamestate.EQUIPMENT_SLOTS.index(dest)
                        elif event.key == pygame.K_RETURN:
                            pState.unequip_item(pState.equip_slot_index)

                elif wState.shop_mode:
                    items_list = (wState.shop_inventory if wState.shop_mode == "buy"
                                  else pState.inventory)
                    if event.key == pygame.K_UP:
                        wState.shop_index = max(0, wState.shop_index - 1)
                    elif event.key == pygame.K_DOWN:
                        wState.shop_index = min(len(items_list) - 1, wState.shop_index + 1)
                    elif event.key == pygame.K_RETURN and items_list:
                        item = items_list[wState.shop_index]
                        if wState.shop_mode == "buy":
                            if pState.gold >= item.price:
                                pState.gold -= item.price
                                pState.inventory.append(item)
                                wState.shop_inventory.pop(wState.shop_index)
                                wState.shop_index = min(wState.shop_index,
                                                        max(0, len(wState.shop_inventory) - 1))
                        else:
                            sell_price = max(1, item.price // 2)
                            pState.gold += sell_price
                            pState.inventory.pop(wState.shop_index)
                            wState.shop_index = min(wState.shop_index,
                                                    max(0, len(pState.inventory) - 1))

                elif wState.menu_confirm == "Saved":
                    wState.menu_confirm = None

                elif wState.menu_confirm:
                    if event.key == pygame.K_RETURN:
                        if wState.menu_confirm == "Exit":
                            wState.reset(area="start_screen")
                            pState.reset()
                        elif wState.menu_confirm == "Save":
                            save.save_game(wState, pState)
                            wState.menu_confirm = "Saved"

                elif wState.menu_open:
                    if event.key == pygame.K_UP:
                        wState.menu_index = (wState.menu_index - 1) % len(gamestate.MENU_ITEMS)
                    elif event.key == pygame.K_DOWN:
                        wState.menu_index = (wState.menu_index + 1) % len(gamestate.MENU_ITEMS)
                    elif event.key == pygame.K_RETURN:
                        selected = gamestate.MENU_ITEMS[wState.menu_index]
                        if selected in ("Save", "Exit"):
                            wState.menu_confirm = selected
                        elif selected == "Inventory":
                            wState.menu_open = False
                            wState.inventory_open = True
                            pState.inventory_index = 0

                elif not wState.menu_open:
                    choices = list(gameareas.areas[wState.getArea()].choices.values())
                    n = len(choices)
                    col = wState.nav_index % 2
                    row = wState.nav_index // 2
                    if event.key == pygame.K_LEFT:
                        if col > 0:
                            wState.nav_index -= 1
                    elif event.key == pygame.K_RIGHT:
                        if col < 1 and wState.nav_index + 1 < n:
                            wState.nav_index += 1
                    elif event.key == pygame.K_UP:
                        if row > 0:
                            wState.nav_index -= 2
                    elif event.key == pygame.K_DOWN:
                        if wState.nav_index + 2 < n:
                            wState.nav_index += 2
                    elif event.key == pygame.K_RETURN and choices:
                        dest = choices[wState.nav_index][0]
                        if dest in ("buy", "sell"):
                            wState.shop_mode = dest
                            wState.shop_index = 0
                        else:
                            wState.updateArea(dest)
    
        #render current area
        area = gameareas.areas[wState.getArea()]
        display.render(screen, wState, pState, area)
    except Exception:
        import traceback
        traceback.print_exc()
        running = False
        pygame.event.pump()
    
pygame.quit()