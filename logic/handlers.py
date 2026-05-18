'''
handlers.py
Keyboard event handling — called from the main loop in questforrest.py
Returns True when event is consumed, "exit" to quit the game.
'''

import pygame
import random
import data.areas as areas
import state.gamestate as gamestate
import data.quests as quests
import state.save as save
import logic.adventure as adventure


def handle_event(key, event, wState, pState):

    # ── Start screen ──────────────────────────────────────────────────────────
    if wState.area == "start_screen" and not wState.name_input_mode:
        if wState.main_menu_confirm == "new_game_notify":
            if key in (pygame.K_RETURN, pygame.K_ESCAPE):
                wState.main_menu_confirm = None
                if key == pygame.K_RETURN:
                    wState.reset(area="start_screen")
                    pState.reset()
                    wState.name_input_mode   = True
                    wState.name_input_buffer = ""

        elif wState.main_menu_confirm == "load":
            if key == pygame.K_ESCAPE:
                wState.main_menu_confirm = None
            elif key == pygame.K_UP:
                wState.load_menu_index = max(0, wState.load_menu_index - 1)
            elif key == pygame.K_DOWN:
                wState.load_menu_index = min(len(wState.available_saves) - 1,
                                              wState.load_menu_index + 1)
            elif key == pygame.K_RETURN and wState.available_saves:
                slot, _ = wState.available_saves[wState.load_menu_index]
                save.load_game(wState, pState, slot)

        else:
            has_save = save.save_exists()

            def _skip(idx, step):
                idx = (idx + step) % len(gamestate.MAIN_MENU_ITEMS)
                if gamestate.MAIN_MENU_ITEMS[idx] == "Load Game" and not has_save:
                    idx = (idx + step) % len(gamestate.MAIN_MENU_ITEMS)
                return idx

            if key == pygame.K_UP:
                wState.main_menu_index = _skip(wState.main_menu_index, -1)
            elif key == pygame.K_DOWN:
                wState.main_menu_index = _skip(wState.main_menu_index, 1)
            elif key == pygame.K_RETURN:
                selected = gamestate.MAIN_MENU_ITEMS[wState.main_menu_index]
                if selected == "New Game":
                    if save.save_exists():
                        wState.main_menu_confirm = "new_game_notify"
                    else:
                        wState.reset(area="start_screen")
                        pState.reset()
                        wState.name_input_mode   = True
                        wState.name_input_buffer = ""
                elif selected == "Load Game":
                    saves = save.list_saves()
                    if saves:
                        wState.available_saves   = saves
                        wState.load_menu_index   = 0
                        wState.main_menu_confirm = "load"
                elif selected == "Exit":
                    return "exit"
        return True

    # ── Name input ────────────────────────────────────────────────────────────
    if wState.name_input_mode:
        if key == pygame.K_RETURN:
            if wState.name_input_buffer.strip():
                pState.name            = wState.name_input_buffer.strip()
                wState.name_input_mode = False
                wState.area            = "village"
        elif key == pygame.K_BACKSPACE:
            wState.name_input_buffer = wState.name_input_buffer[:-1]
        elif event.unicode and event.unicode.isprintable():
            if len(wState.name_input_buffer) < 20:
                wState.name_input_buffer += event.unicode
        return True

    # ── Adventure location select ─────────────────────────────────────────────
    if wState.adventure_select_mode:
        if key == pygame.K_ESCAPE:
            wState.adventure_select_mode = False
            wState.adventure_select_msg  = ""
        elif key == pygame.K_UP:
            wState.adventure_select_index = max(0, wState.adventure_select_index - 1)
            wState.adventure_select_msg   = ""
        elif key == pygame.K_DOWN:
            wState.adventure_select_index = min(
                wState.adventure_locations_unlocked - 1,
                wState.adventure_select_index + 1)
            wState.adventure_select_msg = ""
        elif key == pygame.K_RETURN:
            idx = wState.adventure_select_index
            if idx < wState.adventure_locations_unlocked:
                if pState.food < 1:
                    wState.adventure_select_msg = "Not enough food! You need at least 1."
                else:
                    pState.food                 -= 1
                    wState.in_adventure          = True
                    wState.adventure_loc_index   = idx
                    wState.adventure_room        = 0
                    wState.adventure_select_mode = False
                    wState.adventure_select_msg  = ""
                    wState.adventured_today      = True
                    adventure.enter_room(idx, 0, wState, pState)
        return True

    # ── Inventory screen ──────────────────────────────────────────────────────
    if wState.inventory_open:
        if key == pygame.K_ESCAPE:
            wState.inventory_open = False
            pState.active_panel   = "inventory"
        elif pState.active_panel == "inventory":
            if key == pygame.K_UP:
                pState.inventory_index = max(0, pState.inventory_index - 1)
            elif key == pygame.K_DOWN:
                pState.inventory_index = min(len(pState.inventory) - 1,
                                              pState.inventory_index + 1)
            elif key == pygame.K_LEFT:
                pState.active_panel = "equipment"
            elif key == pygame.K_RETURN and pState.inventory:
                item = pState.inventory[pState.inventory_index]
                if item.consumable:
                    pState.use_item(pState.inventory_index)
                else:
                    pState.equip_item(pState.inventory_index)
                    newly_done = quests.check_new_completions(pState)
                    if newly_done:
                        wState.quest_completion_popup = newly_done
        else:
            _dir = {pygame.K_UP: 0, pygame.K_DOWN: 1, pygame.K_LEFT: 2, pygame.K_RIGHT: 3}
            if key in _dir:
                slot = gamestate.EQUIPMENT_SLOTS[pState.equip_slot_index]
                dest = gamestate.EQUIP_NAV[slot][_dir[key]]
                if dest == "items":
                    pState.active_panel = "inventory"
                elif dest is not None:
                    pState.equip_slot_index = gamestate.EQUIPMENT_SLOTS.index(dest)
            elif key == pygame.K_RETURN:
                pState.unequip_item(pState.equip_slot_index)
        return True

    # ── In combat ─────────────────────────────────────────────────────────────
    if wState.in_combat:
        col = wState.combat_nav_index % 2
        row = wState.combat_nav_index // 2
        if key == pygame.K_LEFT:
            if col > 0:
                wState.combat_nav_index -= 1
        elif key == pygame.K_RIGHT:
            if col < 1:
                wState.combat_nav_index += 1
        elif key == pygame.K_UP:
            if row > 0:
                wState.combat_nav_index -= 2
        elif key == pygame.K_DOWN:
            if row < 1:
                wState.combat_nav_index += 2
        elif key == pygame.K_RETURN:
            adventure.do_combat_action(wState.combat_nav_index, wState, pState)
        return True

    # ── Post-combat ───────────────────────────────────────────────────────────
    if wState.post_combat_mode:
        if key == pygame.K_i:
            wState.inventory_open  = True
            pState.inventory_index = 0
            pState.active_panel    = "inventory"
        elif key == pygame.K_RETURN:
            if (wState.combat_result == "victory"
                    and wState.in_adventure
                    and not wState.adventure_complete):
                wState.post_combat_mode              = False
                wState.adventure_complete            = False
                wState.post_combat_levelups          = []
                wState.post_combat_quest_completions = []
                wState.adventure_room               += 1
                adventure.enter_room(wState.adventure_loc_index, wState.adventure_room,
                                     wState, pState)
            else:
                adventure.return_to_village(wState)
        elif key == pygame.K_ESCAPE:
            if (wState.combat_result == "victory"
                    and wState.in_adventure
                    and not wState.adventure_complete):
                adventure.return_to_village(wState)
        return True

    # ── Adventure trade (wanderer) ────────────────────────────────────────────
    if wState.adventure_trade_mode:
        item = wState.adventure_trade_item
        if key == pygame.K_ESCAPE:
            wState.adventure_trade_mode = False
            wState.adventure_trade_item = None
            wState.post_room_lines = ["You decline the offer.",
                                      "The wanderer sadly wanders away."]
            wState.post_room_mode  = True
        elif key == pygame.K_RETURN and item:
            if pState.gold >= item.price:
                pState.gold -= item.price
                pState.inventory.append(item)
                wState.post_room_lines = [f"You bought {item.name} for {item.price}g!",
                                          "The wanderer happily wanders away."]
            else:
                wState.post_room_lines = ["Not enough gold to buy that.",
                                          "The wanderer angrily wanders away."]
            wState.adventure_trade_mode = False
            wState.adventure_trade_item = None
            wState.post_room_mode       = True
        return True

    # ── Post-room (non-combat) ────────────────────────────────────────────────
    if wState.post_room_mode:
        if key == pygame.K_i:
            wState.inventory_open  = True
            pState.inventory_index = 0
            pState.active_panel    = "inventory"
        elif key == pygame.K_RETURN:
            wState.post_room_mode  = False
            wState.post_room_lines = []
            if wState.in_adventure:
                wState.adventure_room += 1
                adventure.enter_room(wState.adventure_loc_index, wState.adventure_room,
                                     wState, pState)
            else:
                adventure.return_to_village(wState)
        elif key == pygame.K_ESCAPE:
            wState.post_room_mode  = False
            wState.post_room_lines = []
            adventure.return_to_village(wState)
        return True

    # ── Stash ─────────────────────────────────────────────────────────────────
    if wState.stash_open:
        if key == pygame.K_ESCAPE:
            wState.stash_open = False
        elif key in (pygame.K_LEFT, pygame.K_RIGHT):
            wState.stash_panel = "stash" if wState.stash_panel == "inventory" else "inventory"
        elif key == pygame.K_UP:
            if wState.stash_panel == "inventory":
                wState.stash_inv_index = max(0, wState.stash_inv_index - 1)
            else:
                wState.stash_stash_index = max(0, wState.stash_stash_index - 1)
        elif key == pygame.K_DOWN:
            if wState.stash_panel == "inventory":
                wState.stash_inv_index = min(len(pState.inventory) - 1, wState.stash_inv_index + 1)
            else:
                wState.stash_stash_index = min(len(pState.stash) - 1, wState.stash_stash_index + 1)
        elif key == pygame.K_RETURN:
            if wState.stash_panel == "inventory" and pState.inventory:
                idx  = wState.stash_inv_index
                item = pState.inventory.pop(idx)
                pState.stash.append(item)
                wState.stash_inv_index = min(idx, max(0, len(pState.inventory) - 1))
            elif wState.stash_panel == "stash" and pState.stash:
                idx  = wState.stash_stash_index
                item = pState.stash.pop(idx)
                if item.consumable and "food" in item.use_effect:
                    pState.food += item.use_effect["food"]
                else:
                    pState.inventory.append(item)
                wState.stash_stash_index = min(idx, max(0, len(pState.stash) - 1))
        return True

    # ── Quest log ─────────────────────────────────────────────────────────────
    if wState.quests_open:
        if key == pygame.K_ESCAPE:
            wState.quests_open = False
        return True

    # ── Innkeeper ─────────────────────────────────────────────────────────────
    if wState.innkeeper_open:
        if key == pygame.K_ESCAPE:
            wState.innkeeper_open = False
        elif key == pygame.K_RETURN and pState.debt > 0:
            pay = min(10, pState.gold, pState.debt)
            if pay > 0:
                pState.gold -= pay
                pState.debt -= pay
                newly_done = quests.check_new_completions(pState)
                if newly_done:
                    wState.quest_completion_popup = newly_done
        return True

    # ── Quest board ───────────────────────────────────────────────────────────
    if wState.questboard_open:
        board_items = ["odd_jobs"]
        if wState.questboard_quest_id:
            board_items.append("quest")
        n_board = len(board_items)

        if wState.questboard_confirm == "odd_jobs":
            if key == pygame.K_RETURN:
                gold = random.randint(3, 15)
                pState.gold              += gold
                pState.food              += 1
                pState.health             = pState.get_max_health()
                wState.day              += 1
                wState.adventured_today  = False
                wState.questboard_open   = False
                wState.questboard_index  = 0
                wState.questboard_confirm = None
                wState.work_result = ("You worked odd jobs around town.", gold, 1)
            elif key == pygame.K_ESCAPE:
                wState.questboard_confirm = None
            return True

        if key == pygame.K_ESCAPE:
            wState.questboard_open  = False
            wState.questboard_index = 0
        elif key == pygame.K_UP:
            wState.questboard_index = max(0, wState.questboard_index - 1)
        elif key == pygame.K_DOWN:
            wState.questboard_index = min(n_board - 1, wState.questboard_index + 1)
        elif key == pygame.K_RETURN:
            sel = board_items[min(wState.questboard_index, n_board - 1)]
            if sel == "odd_jobs":
                if wState.adventured_today:
                    wState.questboard_open  = False
                    wState.questboard_index = 0
                    wState.work_result = (
                        "You are too tired from your adventure to work today.", 0, 0)
                else:
                    wState.questboard_confirm = "odd_jobs"
            elif sel == "quest" and wState.questboard_quest_id:
                qid   = wState.questboard_quest_id
                quest = next((q for q in quests.QUESTS if q["id"] == qid), None)
                pState.active_quests.add(qid)
                if quest:
                    if quest["type"] == "kills":
                        pState.quest_snapshots[qid] = pState.kills
                    elif quest["type"] == "bosses":
                        pState.quest_snapshots[qid] = pState.boss_kills
                wState.questboard_quest_id = None
                wState.questboard_open     = False
                wState.questboard_index    = 0
        return True

    # ── Quest completion popup dismiss ────────────────────────────────────────
    if wState.quest_completion_popup:
        wState.quest_completion_popup = []
        return True

    # ── Work result dismiss ───────────────────────────────────────────────────
    if wState.work_result is not None:
        wState.work_result = None
        return True

    # ── ESC key ───────────────────────────────────────────────────────────────
    if key == pygame.K_ESCAPE:
        if wState.shop_mode:
            wState.shop_mode  = None
            wState.shop_index = 0
            wState.shop_msg   = ""
        elif wState.menu_confirm:
            wState.menu_confirm = None
        else:
            wState.menu_open  = not wState.menu_open
            wState.menu_index = 0
        return True

    # ── Shop ──────────────────────────────────────────────────────────────────
    if wState.shop_mode:
        items_list = (wState.shop_inventory + gamestate.PERM_SHOP_ITEMS
                      if wState.shop_mode == "buy" else pState.inventory)
        if key == pygame.K_UP:
            wState.shop_index = max(0, wState.shop_index - 1)
        elif key == pygame.K_DOWN:
            wState.shop_index = min(len(items_list) - 1, wState.shop_index + 1)
        elif key == pygame.K_RETURN and items_list:
            item = items_list[wState.shop_index]
            if wState.shop_mode == "buy":
                if pState.gold >= item.price:
                    pState.gold -= item.price
                    if item.consumable and "food" in item.use_effect:
                        pState.food += item.use_effect["food"]
                        wState.shop_msg = f"+{item.use_effect['food']} food."
                    elif not item.consumable and pState.equipment.get(item.slot) is None:
                        pState.equipment[item.slot] = item
                        pState.health = min(pState.health, pState.get_max_health())
                        wState.shop_msg = f"{item.name} auto-equipped!"
                        newly_done = quests.check_new_completions(pState)
                        if newly_done:
                            wState.quest_completion_popup = newly_done
                    else:
                        pState.inventory.append(item)
                        wState.shop_msg = f"Purchased {item.name}."
                    if wState.shop_index < len(wState.shop_inventory):
                        wState.shop_inventory.pop(wState.shop_index)
                    wState.shop_index = min(
                        wState.shop_index,
                        max(0, len(wState.shop_inventory + gamestate.PERM_SHOP_ITEMS) - 1))
            else:
                sell_price = max(1, item.price // 2)
                pState.gold += sell_price
                pState.inventory.pop(wState.shop_index)
                wState.shop_index = min(wState.shop_index, max(0, len(pState.inventory) - 1))
        return True

    # ── Menu confirm dialogs ──────────────────────────────────────────────────
    if wState.menu_confirm == "Saved":
        wState.menu_confirm = None
        return True

    if wState.menu_confirm:
        if key == pygame.K_RETURN:
            if wState.menu_confirm == "Exit":
                wState.reset(area="start_screen")
                pState.reset()
            elif wState.menu_confirm == "Save":
                save.save_game(wState, pState)
                wState.menu_confirm = "Saved"
        return True

    # ── ESC menu navigation ───────────────────────────────────────────────────
    if wState.menu_open:
        if key == pygame.K_UP:
            wState.menu_index = (wState.menu_index - 1) % len(gamestate.MENU_ITEMS)
        elif key == pygame.K_DOWN:
            wState.menu_index = (wState.menu_index + 1) % len(gamestate.MENU_ITEMS)
        elif key == pygame.K_RETURN:
            selected = gamestate.MENU_ITEMS[wState.menu_index]
            if selected in ("Save", "Exit"):
                wState.menu_confirm = selected
            elif selected == "Inventory":
                wState.menu_open       = False
                wState.inventory_open  = True
                pState.inventory_index = 0
            elif selected == "Quests":
                wState.menu_open   = False
                wState.quests_open = True
        return True

    # ── Area navigation ───────────────────────────────────────────────────────
    choices = list(areas.areas[wState.getArea()].choices.values())
    n    = len(choices)
    col  = wState.nav_index % 2
    row  = wState.nav_index // 2

    if key == pygame.K_LEFT:
        if col > 0:
            wState.nav_index -= 1
    elif key == pygame.K_RIGHT:
        if col < 1 and wState.nav_index + 1 < n:
            wState.nav_index += 1
    elif key == pygame.K_UP:
        if row > 0:
            wState.nav_index -= 2
    elif key == pygame.K_DOWN:
        if wState.nav_index + 2 < n:
            wState.nav_index += 2
    elif key == pygame.K_RETURN and choices:
        dest = choices[wState.nav_index][0]

        if dest in ("buy", "sell"):
            wState.shop_mode  = dest
            wState.shop_index = 0

        elif dest == "adventure":
            wState.adventure_select_mode  = True
            wState.adventure_select_msg   = ""
            wState.adventure_select_index = min(
                wState.adventure_select_index,
                wState.adventure_locations_unlocked - 1)

        elif dest == "questboard":
            quests.refresh_questboard(wState, pState)
            wState.questboard_open = True

        elif dest == "rest":
            wState.day             += 1
            wState.adventured_today = False
            pState.health           = pState.get_max_health()
            wState.work_result      = ("You rested until morning.", 0, 0)

        elif dest == "stash":
            wState.stash_open        = True
            wState.stash_panel       = "inventory"
            wState.stash_inv_index   = 0
            wState.stash_stash_index = 0

        elif dest == "innkeeper":
            wState.innkeeper_open = True

        elif dest == "work":
            text   = random.choice(gamestate.WORK_TEXTS)
            gold   = random.randint(1, 10)
            food   = random.randint(1, 2) if random.random() < 0.4 else 0
            pState.gold += gold
            pState.food += food
            wState.work_result = (text, gold, food)

        else:
            wState.updateArea(dest)

    return True
