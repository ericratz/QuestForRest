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
import data.dialogue as dialogue
import data.intro as intro
import data.passives as passives_data
import state.save as save
import logic.adventure as adventure
import audio.sounds as sfx
from render.helpers import trigger_fade_in

_QUEST_START_NAMES = {
    "activate_quest_innkeeper":   "Into the Dark Forest",
    "activate_quest_guildmaster": "Cleanse the Outer Ruins",
    "activate_quest_mystic":      "The Mystic's Test",
}

def _append_quest_start_line(lines, post_action, pState):
    '''If the dialogue triggers a new quest, append a "Quest started" line.'''
    if post_action not in _QUEST_START_NAMES:
        return lines
    quest_id = post_action[len("activate_quest_"):] + "_quest"
    if quest_id in pState.active_quests or quest_id in pState.quests_complete:
        return lines
    return list(lines) + [f"[Quest started: {_QUEST_START_NAMES[post_action]}!]"]


def _group_items(items):
    """Collapse same-name items into (item, count) pairs, sorted by name."""
    groups = []
    for it in sorted(items, key=lambda i: i.name):
        if groups and groups[-1][0].name == it.name:
            groups[-1] = (groups[-1][0], groups[-1][1] + 1)
        else:
            groups.append((it, 1))
    return groups


def handle_event(key, event, wState, pState):

    # ── Ending sequence ───────────────────────────────────────────────────────
    if wState.ending_mode:
        if key in (pygame.K_RETURN, pygame.K_SPACE):
            wState.ending_line_index += 1
            sfx.play('menu')
            if wState.ending_line_index >= len(intro.ENDING_LINES):
                wState.ending_mode = False
                wState.game_over   = "debt_paid"
                trigger_fade_in()
        return True

    # ── Game over / debt win screen ───────────────────────────────────────────
    if wState.game_over:
        if key in (pygame.K_RETURN, pygame.K_ESCAPE):
            wState.reset(area="start_screen")
            pState.reset()
            sfx.stop_music()
        return True

    # ── Start screen ──────────────────────────────────────────────────────────
    if wState.area == "start_screen" and not wState.name_input_mode and not wState.intro_mode:
        if wState.main_menu_confirm == "new_game_notify":
            if key in (pygame.K_RETURN, pygame.K_ESCAPE):
                wState.main_menu_confirm = None
                if key == pygame.K_RETURN:
                    wState.reset(area="start_screen")
                    pState.reset()
                    wState.intro_mode       = True
                    wState.intro_phase      = "opening"
                    wState.intro_line_index = 0
                    wState.name_input_buffer = ""
                    trigger_fade_in()

        elif wState.main_menu_confirm == "load":
            if key == pygame.K_ESCAPE:
                wState.main_menu_confirm = None
            elif key == pygame.K_UP:
                wState.load_menu_index = max(0, wState.load_menu_index - 1)
                sfx.play('menu')
            elif key == pygame.K_DOWN:
                wState.load_menu_index = min(len(wState.available_saves) - 1,
                                              wState.load_menu_index + 1)
                sfx.play('menu')
            elif key == pygame.K_RETURN and wState.available_saves:
                slot, _ = wState.available_saves[wState.load_menu_index]
                save.load_game(wState, pState, slot)
                sfx.set_sfx_volume(wState.sfx_volume)
                sfx.set_music_volume(wState.music_volume)
                sfx.set_music('village')
                trigger_fade_in()

        else:
            has_save = save.save_exists()

            def _skip(idx, step):
                idx = (idx + step) % len(gamestate.MAIN_MENU_ITEMS)
                if gamestate.MAIN_MENU_ITEMS[idx] == "Load Game" and not has_save:
                    idx = (idx + step) % len(gamestate.MAIN_MENU_ITEMS)
                return idx

            if key == pygame.K_UP:
                wState.main_menu_index = _skip(wState.main_menu_index, -1)
                sfx.play('menu')
            elif key == pygame.K_DOWN:
                wState.main_menu_index = _skip(wState.main_menu_index, 1)
                sfx.play('menu')
            elif key == pygame.K_RETURN:
                selected = gamestate.MAIN_MENU_ITEMS[wState.main_menu_index]
                if selected == "New Game":
                    if save.save_exists():
                        wState.main_menu_confirm = "new_game_notify"
                    else:
                        wState.reset(area="start_screen")
                        pState.reset()
                        wState.intro_mode       = True
                        wState.intro_phase      = "opening"
                        wState.intro_line_index = 0
                        wState.name_input_buffer = ""
                        trigger_fade_in()
                elif selected == "Load Game":
                    saves = save.list_saves()
                    if saves:
                        wState.available_saves   = saves
                        wState.load_menu_index   = 0
                        wState.main_menu_confirm = "load"
                elif selected == "Exit":
                    return "exit"
        return True

    # ── Intro sequence ────────────────────────────────────────────────────────
    if wState.intro_mode:
        phase = wState.intro_phase

        if phase == "opening":
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                wState.intro_line_index += 1
                sfx.play('menu')
                if wState.intro_line_index >= len(intro.OPENING_LINES):
                    wState.intro_phase      = "name"
                    wState.intro_line_index = 0
                    wState.name_input_buffer = ""
            elif key == pygame.K_ESCAPE:
                wState.intro_phase       = "name"
                wState.intro_line_index  = 0
                wState.name_input_buffer = ""
                wState.intro_skipped     = True

        elif phase == "name":
            if key == pygame.K_RETURN:
                if wState.name_input_buffer.strip():
                    pState.name = wState.name_input_buffer.strip()
                    if wState.intro_skipped:
                        # Intro was skipped — go straight to game
                        wState.intro_mode    = False
                        wState.intro_phase   = "opening"
                        wState.intro_skipped = False
                        wState.area          = "village"
                        sfx.set_music('village')
                        trigger_fade_in()
                    else:
                        wState.intro_phase    = "qa"
                        wState.intro_qa_index = 0
            elif key == pygame.K_BACKSPACE:
                wState.name_input_buffer = wState.name_input_buffer[:-1]
            elif event.unicode and event.unicode.isprintable():
                if len(wState.name_input_buffer) < 20:
                    wState.name_input_buffer += event.unicode

        elif phase == "qa":
            n = len(intro.QA_OPTIONS)
            if key == pygame.K_UP:
                wState.intro_qa_index = max(0, wState.intro_qa_index - 1)
                sfx.play('menu')
            elif key == pygame.K_DOWN:
                wState.intro_qa_index = min(n - 1, wState.intro_qa_index + 1)
                sfx.play('menu')
            elif key == pygame.K_RETURN:
                _, qa_key = intro.QA_OPTIONS[wState.intro_qa_index]
                sfx.play('menu')
                if qa_key == "qa_done":
                    wState.intro_phase      = "closing"
                    wState.intro_line_index = 0
                else:
                    wState.intro_qa_response = list(intro.QA_RESPONSES[qa_key])
                    wState.intro_line_index  = 0
                    wState.intro_phase       = "qa_response"

        elif phase == "qa_response":
            if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                wState.intro_line_index += 1
                sfx.play('menu')
                if wState.intro_line_index >= len(wState.intro_qa_response):
                    wState.intro_phase       = "qa"
                    wState.intro_line_index  = 0
                    wState.intro_qa_response = []

        elif phase == "closing":
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                wState.intro_line_index += 1
                sfx.play('menu')
                if wState.intro_line_index >= len(intro.CLOSING_LINES):
                    wState.intro_mode       = False
                    wState.intro_phase      = "opening"
                    wState.intro_line_index = 0
                    wState.area             = "village"
                    sfx.set_music('village')
                    trigger_fade_in()

        return True

    # ── Familiar naming ───────────────────────────────────────────────────────
    if wState.familiar_naming_mode:
        if key == pygame.K_RETURN:
            name = wState.familiar_name_buffer.strip()
            if name:
                pState.familiar.name        = name
                pState.familiar.found       = True
                wState.familiar_naming_mode = False
                wState.familiar_name_buffer = ""
                sfx.play('pickup')
        elif key == pygame.K_BACKSPACE:
            wState.familiar_name_buffer = wState.familiar_name_buffer[:-1]
        elif event.unicode and event.unicode.isprintable():
            if len(wState.familiar_name_buffer) < 20:
                wState.familiar_name_buffer += event.unicode
        return True

    # ── Name input ────────────────────────────────────────────────────────────
    if wState.name_input_mode:
        if key == pygame.K_RETURN:
            if wState.name_input_buffer.strip():
                pState.name            = wState.name_input_buffer.strip()
                wState.name_input_mode = False
                wState.area            = "village"
                sfx.set_music('village')
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
            sfx.play('menu')
        elif key == pygame.K_DOWN:
            _ctx_unlocked = (wState.duskwall_locations_unlocked
                             if wState.adventure_select_context == "duskwall"
                             else wState.adventure_locations_unlocked)
            wState.adventure_select_index = min(
                _ctx_unlocked - 1,
                wState.adventure_select_index + 1)
            wState.adventure_select_msg = ""
            sfx.play('menu')
        elif key == pygame.K_RETURN:
            context    = wState.adventure_select_context
            rel_idx    = wState.adventure_select_index
            offset     = 2 if context == "duskwall" else 0
            actual_idx = offset + rel_idx
            max_unlocked = (wState.duskwall_locations_unlocked
                            if context == "duskwall"
                            else wState.adventure_locations_unlocked)
            if rel_idx < max_unlocked:
                is_dusk       = (context == "duskwall")
                if is_dusk:
                    base_food_req = 5 if rel_idx >= 1 else 4
                elif rel_idx >= 1:
                    base_food_req = 3
                else:
                    base_food_req = 1
                required_food = max(1, base_food_req - pState.passive_effect("food_bonus"))
                if pState.food < required_food:
                    wState.adventure_select_msg = f"Not enough food! You need at least {required_food}."
                    sfx.play('error')
                else:
                    pState.food                      -= required_food
                    pState.used_potion_this_run       = False
                    pState.consecutive_peaceful_rooms = 0
                    pState.second_wind_available      = bool(pState.passive_effect("second_wind"))
                    wState.in_adventure               = True
                    wState.adventure_loc_index        = actual_idx
                    wState.adventure_room             = 0
                    wState.adventure_select_mode      = False
                    wState.adventure_select_msg       = ""
                    wState.adventured_today           = True
                    loc        = gamestate.ADVENTURE_LOCATIONS[actual_idx]
                    n_monsters = random.randint(loc["monster_min"], loc["monster_max"])
                    split      = loc.get("monster_tier_split", 0.0)
                    n_tier2    = round(n_monsters * split)
                    n_tier1    = n_monsters - n_tier2
                    n_other    = (loc["total_rooms"] - 1) - n_monsters
                    other_rooms = random.choices(loc["room_dist"], k=n_other)
                    dist = (["monster_1"] * n_tier1 +
                            ["monster_2"] * n_tier2 +
                            other_rooms)
                    random.shuffle(dist)
                    wState.adventure_room_sequence = dist
                    sfx.set_music(loc.get("music", "dark_forest"))
                    trigger_fade_in()
                    adventure.enter_room(actual_idx, 0, wState, pState)
        return True

    # ── Global popup dismissals (must be above any screen handler) ───────────
    if wState.quest_completion_popup:
        wState.quest_completion_popup = []
        return True

    if wState.quest_expired_popup:
        wState.quest_expired_popup = []
        return True

    if wState.new_debt_popup:
        wState.new_debt_popup = False
        return True

    if wState.achievement_popup:
        wState.achievement_popup = []
        return True

    # ── Inventory screen ──────────────────────────────────────────────────────
    if wState.inventory_open:
        if key in (pygame.K_ESCAPE, pygame.K_i):
            wState.inventory_open = False
            pState.active_panel   = "inventory"
        elif pState.active_panel == "inventory":
            group_names = sorted({it.name for it in pState.inventory})
            n_groups    = len(group_names)
            if key == pygame.K_UP:
                pState.inventory_index = max(0, pState.inventory_index - 1)
                sfx.play('menu')
            elif key == pygame.K_DOWN:
                pState.inventory_index = min(n_groups - 1, pState.inventory_index + 1)
                sfx.play('menu')
            elif key == pygame.K_LEFT:
                pState.active_panel = "equipment"
                sfx.play('menu')
            elif key == pygame.K_RETURN and pState.inventory and pState.inventory_index < n_groups:
                target_name = group_names[pState.inventory_index]
                raw_idx = next(i for i, it in enumerate(pState.inventory) if it.name == target_name)
                item = pState.inventory[raw_idx]
                if item.consumable:
                    pState.use_item(raw_idx)
                else:
                    pState.equip_item(raw_idx)
                    sfx.play('equip')
                    newly_done = quests.check_new_completions(pState)
                    if newly_done:
                        wState.quest_completion_popup = newly_done
                # re-clamp to group count after the operation
                n_groups_after = len({it.name for it in pState.inventory})
                pState.inventory_index = min(pState.inventory_index, max(0, n_groups_after - 1))
            elif key == pygame.K_f and pState.familiar.found and pState.familiar.equipment:
                # F — unequip familiar charm to inventory
                pState.inventory.append(pState.familiar.equipment)
                pState.familiar.equipment = None
                sfx.play('equip')
        else:
            _dir = {pygame.K_UP: 0, pygame.K_DOWN: 1, pygame.K_LEFT: 2, pygame.K_RIGHT: 3}
            if key in _dir:
                slot = gamestate.EQUIPMENT_SLOTS[pState.equip_slot_index]
                dest = gamestate.EQUIP_NAV[slot][_dir[key]]
                if dest == "items":
                    pState.active_panel = "inventory"
                    sfx.play('menu')
                elif dest is not None:
                    pState.equip_slot_index = gamestate.EQUIPMENT_SLOTS.index(dest)
                    sfx.play('menu')
            elif key == pygame.K_RETURN:
                slot = gamestate.EQUIPMENT_SLOTS[pState.equip_slot_index]
                if pState.equipment.get(slot):
                    pState.unequip_item(pState.equip_slot_index)
                    sfx.play('equip')
        return True

    # ── In combat ─────────────────────────────────────────────────────────────
    if wState.in_combat:
        # Item selection overlay takes priority
        if wState.combat_item_mode:
            consumables = [(i, it) for i, it in enumerate(pState.inventory) if it.consumable]
            n = len(consumables)
            if key == pygame.K_ESCAPE:
                wState.combat_item_mode = False
            elif key == pygame.K_UP:
                wState.combat_item_index = max(0, wState.combat_item_index - 1)
                sfx.play('menu')
            elif key == pygame.K_DOWN:
                wState.combat_item_index = min(max(0, n - 1), wState.combat_item_index + 1)
                sfx.play('menu')
            elif key == pygame.K_RETURN and n > 0:
                raw_idx = consumables[wState.combat_item_index][0]
                msg = pState.use_item(raw_idx)
                wState.combat_log.append(msg or "Used item.")
                sfx.play('potion')
                wState.combat_item_mode = False
                # Monster counter-attacks after item use
                if wState.in_combat:
                    from logic.adventure import _do_counter_attack
                    _do_counter_attack(wState.combat_monster, wState, pState)
            return True

        col = wState.combat_nav_index % 2
        row = wState.combat_nav_index // 2
        if key == pygame.K_LEFT:
            if col > 0:
                wState.combat_nav_index -= 1
                sfx.play('menu')
        elif key == pygame.K_RIGHT:
            if col < 1:
                wState.combat_nav_index += 1
                sfx.play('menu')
        elif key == pygame.K_UP:
            if row > 0:
                wState.combat_nav_index -= 2
                sfx.play('menu')
        elif key == pygame.K_DOWN:
            if row < 1:
                wState.combat_nav_index += 2
                sfx.play('menu')
        elif key == pygame.K_RETURN:
            if wState.combat_nav_index == 1:  # Use Item — open item list
                consumables = [it for it in pState.inventory if it.consumable]
                if consumables:
                    wState.combat_item_mode  = True
                    wState.combat_item_index = 0
                else:
                    wState.combat_log.append("No usable items!")
                    sfx.play('error')
            else:
                adventure.do_combat_action(wState.combat_nav_index, wState, pState)
        return True

    # ── Boss room warning ─────────────────────────────────────────────────────
    if wState.boss_warning_mode:
        if key == pygame.K_RETURN:
            wState.boss_warning_mode = False
            adventure.enter_room(wState.adventure_loc_index, wState.adventure_room,
                                 wState, pState)
        elif key == pygame.K_ESCAPE:
            wState.boss_warning_mode = False
            adventure.return_to_village(wState, pState)
        return True

    # ── Passive skill selection ───────────────────────────────────────────────
    if wState.passive_select_mode:
        n = len(wState.passive_select_options)
        if key == pygame.K_UP:
            wState.passive_select_index = max(0, wState.passive_select_index - 1)
            sfx.play('menu')
        elif key == pygame.K_DOWN:
            wState.passive_select_index = min(n - 1, wState.passive_select_index + 1)
            sfx.play('menu')
        elif key == pygame.K_RETURN:
            chosen_id = wState.passive_select_options[wState.passive_select_index]
            pState.chosen_passives.append(chosen_id)
            pState.passive_milestones_done.add(wState.passive_pending_milestone)
            wState.passive_select_mode      = False
            wState.passive_select_options   = []
            wState.passive_pending_milestone = None
            sfx.play('pickup')
            # Continue adventure after selection
            if wState.adventure_complete or not wState.in_adventure:
                adventure.return_to_village(wState, pState)
            else:
                wState.adventure_room += 1
                boss_room = gamestate.ADVENTURE_LOCATIONS[wState.adventure_loc_index]["total_rooms"] - 1
                if wState.adventure_room == boss_room:
                    wState.boss_warning_mode = True
                else:
                    adventure.enter_room(wState.adventure_loc_index, wState.adventure_room,
                                         wState, pState)
        return True

    # ── Post-combat ───────────────────────────────────────────────────────────
    if wState.post_combat_mode:
        if key == pygame.K_i:
            wState.inventory_open  = True
            pState.inventory_index = 0
            pState.active_panel    = "inventory"
        elif key == pygame.K_q:
            wState.quests_open = True
        elif key == pygame.K_RETURN:
            if (wState.combat_result == "victory"
                    and wState.in_adventure
                    and not wState.adventure_complete):
                wState.post_combat_mode              = False
                wState.post_combat_levelups          = []
                wState.post_combat_quest_completions = []
                # Passive milestone takes priority — defer room advance
                if wState.passive_pending_milestone:
                    m = wState.passive_pending_milestone
                    wState.passive_select_options = list(passives_data.MILESTONE_OPTIONS[m])
                    wState.passive_select_index   = 0
                    wState.passive_select_mode    = True
                else:
                    wState.adventure_room += 1
                    boss_room = gamestate.ADVENTURE_LOCATIONS[wState.adventure_loc_index]["total_rooms"] - 1
                    if wState.adventure_room == boss_room:
                        wState.boss_warning_mode = True
                    else:
                        adventure.enter_room(wState.adventure_loc_index, wState.adventure_room,
                                             wState, pState)
            else:
                # Defeat, fled, or adventure complete
                if wState.passive_pending_milestone:
                    m = wState.passive_pending_milestone
                    wState.passive_select_options = list(passives_data.MILESTONE_OPTIONS[m])
                    wState.passive_select_index   = 0
                    wState.passive_select_mode    = True
                    wState.post_combat_mode       = False
                    wState.post_combat_levelups   = []
                    wState.post_combat_quest_completions = []
                elif wState.duskwall_just_unlocked:
                    # Show Duskwall arrival story, then drop the player in Duskwall
                    wState.duskwall_just_unlocked = False
                    wState.post_combat_mode       = False
                    wState.post_combat_levelups   = []
                    wState.post_combat_quest_completions = []
                    # Set Duskwall debt on first arrival
                    if not wState.duskwall_currency_converted:
                        wState.duskwall_currency_converted = True
                        wState.duskwall_locations_unlocked = 1
                        pState.debt = 200
                        pState.active_quests.add("second_debt")
                        wState.new_debt_popup = False  # suppress generic popup; story text explains it
                    wState.post_room_lines = [
                        "You step over the fallen creature.",
                        "Ahead - a faint glow. A crack in the cave wall.",
                        "",
                        "You squeeze through.",
                        "",
                        "Cold air. Stars. Ground beneath your boots.",
                        "You're outside.",
                        "",
                        "Down in the valley - lights. Smoke curling from chimneys.",
                        "Another settlement.",
                        "",
                        "Duskwall.",
                        "",
                        "Economy here runs on marks, not gold.",
                        "Earn them from the ruins, or exchange at the Currency Exchange.",
                        "",
                        "A Guildmaster's debt has already been logged: 200 marks.",
                        "Press M at any time to open the travel map.",
                    ]
                    wState.duskwall_arrival_pending = True
                    wState.post_room_mode = True
                else:
                    adventure.return_to_village(wState, pState)
        elif key == pygame.K_ESCAPE:
            if (wState.combat_result == "victory"
                    and wState.in_adventure
                    and not wState.adventure_complete):
                adventure.return_to_village(wState, pState)
        return True

    # ── Adventure trade (wanderer) ────────────────────────────────────────────
    if wState.adventure_trade_mode:
        item      = wState.adventure_trade_item
        _is_dusk  = wState.adventure_trade_dusk
        _currency = "marks" if _is_dusk else "gold"
        _wallet   = pState.marks if _is_dusk else pState.gold
        if key == pygame.K_ESCAPE:
            wState.adventure_trade_mode = False
            wState.adventure_trade_item = None
            wState.post_room_lines = ["You decline the offer.",
                                      "The wanderer sadly wanders away."]
            wState.post_room_mode  = True
        elif key == pygame.K_RETURN and item:
            if _wallet >= item.price:
                if _is_dusk:
                    pState.marks -= item.price
                else:
                    pState.gold -= item.price
                pState.inventory.append(item)
                if not item.consumable and pState.equipment.get(item.slot) is None:
                    pState.equip_item(len(pState.inventory) - 1)
                    bought_msg = f"You bought {item.name} for {item.price} {_currency}! (auto-equipped)"
                else:
                    bought_msg = f"You bought {item.name} for {item.price} {_currency}!"
                wState.post_room_lines = [bought_msg, "The wanderer happily wanders away."]
            else:
                wState.post_room_lines = [f"Not enough {_currency} to buy that.",
                                          "The wanderer angrily wanders away."]
            wState.adventure_trade_mode = False
            wState.adventure_trade_item = None
            pState.consecutive_peaceful_rooms += 1
            quests.check_achievements(wState, pState)
            wState.post_room_mode       = True
        return True

    # ── Trapped chest ─────────────────────────────────────────────────────────
    if wState.trapped_chest_mode:
        if key == pygame.K_RETURN:
            adventure.handle_trapped_chest_open(wState, pState)
        elif key == pygame.K_ESCAPE:
            adventure.handle_trapped_chest_leave(wState, pState)
        return True

    # ── NPC dialogue ─────────────────────────────────────────────────────────
    if wState.dialogue_open:
        if key in (pygame.K_RETURN, pygame.K_SPACE):
            if wState.dialogue_line_index < len(wState.dialogue_lines) - 1:
                wState.dialogue_line_index += 1
                sfx.play('menu')
            else:
                wState.dialogue_open       = False
                wState.dialogue_npc_id     = None
                wState.dialogue_lines      = []
                wState.dialogue_line_index = 0
                action = wState.post_dialogue_action
                wState.post_dialogue_action = None
                if action == "give_familiar":
                    wState.familiar_naming_mode = True
                    wState.familiar_name_buffer = ""
                    # Complete mystic quest if active
                    if "mystic_quest" in pState.active_quests:
                        newly = quests.check_new_completions(pState)
                        if newly:
                            wState.quest_completion_popup = newly
                elif action == "activate_quest_innkeeper":
                    if "innkeeper_quest" not in pState.active_quests and "innkeeper_quest" not in pState.quests_complete:
                        pState.active_quests.add("innkeeper_quest")
                elif action == "activate_quest_guildmaster":
                    if "guildmaster_quest" not in pState.active_quests and "guildmaster_quest" not in pState.quests_complete:
                        pState.active_quests.add("guildmaster_quest")
                elif action == "activate_quest_mystic":
                    if "mystic_quest" not in pState.active_quests and "mystic_quest" not in pState.quests_complete:
                        pState.active_quests.add("mystic_quest")
                elif action == "open_exchange":
                    wState.currency_exchange_open = True
                    wState.exchange_index = 0
        elif key == pygame.K_ESCAPE:
            wState.dialogue_open        = False
            wState.dialogue_npc_id      = None
            wState.dialogue_lines       = []
            wState.dialogue_line_index  = 0
            wState.post_dialogue_action = None
        return True

    # ── Campfire prompt ───────────────────────────────────────────────────────
    if wState.campfire_prompt:
        def _campfire_advance():
            wState.campfire_prompt = False
            wState.campfire_pending_heal = 0
            if wState.in_adventure:
                wState.adventure_room += 1
                boss_room = gamestate.ADVENTURE_LOCATIONS[wState.adventure_loc_index]["total_rooms"] - 1
                if wState.adventure_room == boss_room:
                    wState.boss_warning_mode = True
                else:
                    adventure.enter_room(wState.adventure_loc_index, wState.adventure_room, wState, pState)
            else:
                adventure.return_to_village(wState, pState)

        if key == pygame.K_RETURN and pState.food > 0:
            pState.food -= 1
            heal_amt = wState.campfire_pending_heal
            before = pState.health
            pState.health = min(pState.get_max_health(), pState.health + heal_amt)
            actual = pState.health - before
            sfx.play('heal')
            wState.post_room_lines = ["You build a fire and rest for a while.",
                                      f"You eat some food and recover.  +{actual} HP  (-1 food)"]
            wState.campfire_prompt = False
            wState.campfire_pending_heal = 0
            wState.post_room_mode = True
        elif key in (pygame.K_RETURN, pygame.K_ESCAPE):
            wState.post_room_lines = ["You pass by the cold campfire without stopping."]
            wState.campfire_prompt = False
            wState.campfire_pending_heal = 0
            wState.post_room_mode = True
        return True

    # ── Post-room (non-combat) ────────────────────────────────────────────────
    if wState.post_room_mode:
        if key == pygame.K_i:
            wState.inventory_open  = True
            pState.inventory_index = 0
            pState.active_panel    = "inventory"
        elif key == pygame.K_q:
            wState.quests_open = True
        elif key == pygame.K_RETURN:
            wState.post_room_mode  = False
            wState.post_room_lines = []
            if wState.duskwall_arrival_pending:
                # Player just arrived in Duskwall — land them there directly
                wState.duskwall_arrival_pending = False
                adventure.return_to_village(wState, pState)
                wState.area      = "duskwall"
                wState.nav_index = 0
                sfx.set_music("duskwall")
            elif wState.in_adventure:
                wState.adventure_room += 1
                boss_room = gamestate.ADVENTURE_LOCATIONS[wState.adventure_loc_index]["total_rooms"] - 1
                if wState.adventure_room == boss_room:
                    wState.boss_warning_mode = True
                else:
                    adventure.enter_room(wState.adventure_loc_index, wState.adventure_room,
                                         wState, pState)
            else:
                adventure.return_to_village(wState, pState)
        elif key == pygame.K_ESCAPE:
            wState.post_room_mode  = False
            wState.post_room_lines = []
            if wState.duskwall_arrival_pending:
                wState.duskwall_arrival_pending = False
                adventure.return_to_village(wState, pState)
                wState.area      = "duskwall"
                wState.nav_index = 0
                sfx.set_music("duskwall")
            else:
                adventure.return_to_village(wState, pState)
        return True

    # ── Stash ─────────────────────────────────────────────────────────────────
    if wState.stash_open:
        if key == pygame.K_ESCAPE:
            wState.stash_open = False
        elif key in (pygame.K_LEFT, pygame.K_RIGHT):
            wState.stash_panel = "stash" if wState.stash_panel == "inventory" else "inventory"
            sfx.play('menu')
        elif key == pygame.K_UP:
            if wState.stash_panel == "inventory":
                wState.stash_inv_index = max(0, wState.stash_inv_index - 1)
            else:
                wState.stash_stash_index = max(0, wState.stash_stash_index - 1)
            sfx.play('menu')
        elif key == pygame.K_DOWN:
            if wState.stash_panel == "inventory":
                wState.stash_inv_index = min(len(_group_items(pState.inventory)) - 1,
                                             wState.stash_inv_index + 1)
            else:
                wState.stash_stash_index = min(len(_group_items(pState.stash)) - 1,
                                               wState.stash_stash_index + 1)
            sfx.play('menu')
        elif key == pygame.K_RETURN:
            if wState.stash_panel == "inventory" and pState.inventory:
                inv_groups = _group_items(pState.inventory)
                item = inv_groups[wState.stash_inv_index][0]
                pState.inventory.remove(item)
                pState.stash.append(item)
                wState.stash_inv_index = min(wState.stash_inv_index,
                                             max(0, len(_group_items(pState.inventory)) - 1))
                newly_done = quests.check_new_completions(pState)
                if newly_done:
                    wState.quest_completion_popup = newly_done
            elif wState.stash_panel == "stash" and pState.stash:
                stash_groups = _group_items(pState.stash)
                item = stash_groups[wState.stash_stash_index][0]
                pState.stash.remove(item)
                if item.consumable and "food" in item.use_effect:
                    pState.food += item.use_effect["food"]
                else:
                    pState.inventory.append(item)
                wState.stash_stash_index = min(wState.stash_stash_index,
                                               max(0, len(_group_items(pState.stash)) - 1))
        return True

    # ── Quest log ─────────────────────────────────────────────────────────────
    if wState.quests_open:
        if key in (pygame.K_ESCAPE, pygame.K_q):
            wState.quests_open = False
        return True

    # ── Innkeeper ─────────────────────────────────────────────────────────────
    if wState.innkeeper_open:
        if key == pygame.K_ESCAPE:
            wState.innkeeper_open   = False
            wState.innkeeper_option = 0
        elif key in (pygame.K_UP, pygame.K_DOWN):
            wState.innkeeper_option = 1 - wState.innkeeper_option
            sfx.play('menu')
        elif key == pygame.K_RETURN:
            _dusk  = wState.area == "duskwall"
            npc_id = "duskwall_guild" if _dusk else "restholm_innkeeper"
            if wState.innkeeper_option == 1:
                # Talk option
                lines, post_action = dialogue.get_lines(npc_id, wState, pState)
                lines = _append_quest_start_line(lines, post_action, pState)
                wState.dialogue_npc_id      = npc_id
                wState.dialogue_lines       = lines
                wState.dialogue_line_index  = 0
                wState.dialogue_open        = True
                wState.post_dialogue_action = post_action
                wState.innkeeper_open       = False
                wState.innkeeper_option     = 0
            else:
                # Pay option — marks in Duskwall, gold in Restholm
                if pState.debt > 0:
                    wallet = pState.marks if _dusk else pState.gold
                    pay    = min(10, wallet, pState.debt)
                    if pay > 0:
                        if _dusk:
                            pState.marks -= pay
                        else:
                            pState.gold -= pay
                        pState.debt -= pay
                        sfx.play('gold')
                        newly_done = quests.check_new_completions(pState)
                        # Win condition: second debt just cleared
                        if pState.debt == 0 and "second_debt" in newly_done:
                            wState.quest_completion_popup = []
                            wState.innkeeper_open          = False
                            wState.innkeeper_option        = 0
                            wState.ending_mode             = True
                            wState.ending_line_index       = 0
                            sfx.stop_music()
                        elif newly_done:
                            wState.quest_completion_popup = newly_done
                    else:
                        sfx.play('error')
        return True

    # ── Currency exchange ─────────────────────────────────────────────────────
    if wState.currency_exchange_open:
        _BUY_RATE  = 25   # gold cost to buy 1 mark
        _SELL_RATE = 10   # gold received when selling 1 mark
        if key == pygame.K_ESCAPE:
            wState.currency_exchange_open = False
            wState.shop_msg = None
        elif key == pygame.K_UP:
            wState.exchange_index = max(0, wState.exchange_index - 1)
            sfx.play('menu')
        elif key == pygame.K_DOWN:
            wState.exchange_index = min(1, wState.exchange_index + 1)
            sfx.play('menu')
        elif key == pygame.K_RETURN:
            idx = wState.exchange_index
            if idx == 0:  # Buy 1 mark for 25g
                if pState.gold >= _BUY_RATE:
                    pState.gold  -= _BUY_RATE
                    pState.marks += 1
                    wState.shop_msg = f"Spent {_BUY_RATE}g. Received 1 mark."
                    sfx.play('gold')
                else:
                    wState.shop_msg = f"Not enough gold. Need {_BUY_RATE}g."
                    sfx.play('error')
            else:  # Sell 1 mark for 10g
                if pState.marks >= 1:
                    pState.marks -= 1
                    pState.gold  += _SELL_RATE
                    wState.shop_msg = f"Sold 1 mark. Received {_SELL_RATE}g."
                    sfx.play('gold')
                else:
                    wState.shop_msg = "No marks to sell."
                    sfx.play('error')
        return True

    # ── Quest board ───────────────────────────────────────────────────────────
    if wState.questboard_open:
        _dusk_areas = {"duskwall", "duskwall_tavern", "duskwall_shop"}
        _in_dusk    = wState.area in _dusk_areas
        fixed_job   = "smuggle" if _in_dusk else "odd_jobs"
        board_items = [fixed_job]
        if wState.questboard_quest_id:
            board_items.append("quest")
        n_board = len(board_items)

        if wState.questboard_confirm == "odd_jobs":
            if key == pygame.K_RETURN:
                gold = random.randint(3, 10)
                pState.gold              += gold
                pState.food              += 1
                pState.health             = pState.get_max_health()
                adventure.advance_day(wState, pState)
                wState.questboard_open   = False
                wState.questboard_index  = 0
                wState.questboard_confirm = None
                wState.work_result = ("You worked odd jobs around town.", gold, 1)
                sfx.play('gold')
            elif key == pygame.K_ESCAPE:
                wState.questboard_confirm = None
            return True

        if wState.questboard_confirm == "smuggle":
            if key == pygame.K_RETURN:
                marks_earned = random.randint(5, 18)
                result_lines = [f"You ran contraband through Duskwall's back alleys.",
                               f"Earned {marks_earned} marks."]
                # Risk events
                risk = random.random()
                if risk < 0.20:
                    dmg = random.randint(5, 20)
                    pState.health = max(1, pState.health - dmg)
                    result_lines.append(f"Ambushed! Lost {dmg} HP.")
                elif risk < 0.35:
                    lost = marks_earned + random.randint(3, 12)
                    lost = min(lost, pState.marks)
                    pState.marks = max(0, pState.marks - lost)
                    result_lines.append(f"Shaken down. Lost {lost} marks.")
                elif risk < 0.45 and pState.inventory:
                    stolen = random.choice(pState.inventory)
                    pState.inventory.remove(stolen)
                    result_lines.append(f"A thief took your {stolen.name}!")
                pState.marks += marks_earned
                adventure.advance_day(wState, pState)
                wState.questboard_open    = False
                wState.questboard_index   = 0
                wState.questboard_confirm = None
                wState.work_result = ("\n".join(result_lines), 0, 0)
                wState.night_theft_msg = None  # clear so it doesn't double-show
                sfx.play('gold')
            elif key == pygame.K_ESCAPE:
                wState.questboard_confirm = None
            return True

        if wState.questboard_confirm == "quest_accept":
            if key == pygame.K_RETURN:
                qid   = wState.questboard_quest_id
                quest = next((q for q in quests.QUESTS if q["id"] == qid), None)
                pState.active_quests.add(qid)
                sfx.play('pickup')
                if quest:
                    if quest["type"] == "kills":
                        pState.quest_snapshots[qid] = pState.kills
                    elif quest["type"] == "bosses":
                        pState.quest_snapshots[qid] = pState.boss_kills
                    elif quest["type"] == "survivalist":
                        pState.quest_snapshots[qid] = pState.survivalist_completions
                    elif quest["type"] == "exterminator":
                        pState.quest_snapshots[qid] = dict(pState.kill_counts)
                    if quest.get("days"):
                        pState.quest_due_dates[qid] = wState.day + quest["days"]
                wState.questboard_quest_id = None
                wState.questboard_open     = False
                wState.questboard_index    = 0
                wState.questboard_confirm  = None
            elif key == pygame.K_ESCAPE:
                wState.questboard_confirm = None
            return True

        if key == pygame.K_ESCAPE:
            wState.questboard_open  = False
            wState.questboard_index = 0
        elif key == pygame.K_UP:
            wState.questboard_index = max(0, wState.questboard_index - 1)
            sfx.play('menu')
        elif key == pygame.K_DOWN:
            wState.questboard_index = min(n_board - 1, wState.questboard_index + 1)
            sfx.play('menu')
        elif key == pygame.K_RETURN:
            sel = board_items[min(wState.questboard_index, n_board - 1)]
            if sel in ("odd_jobs", "smuggle"):
                if wState.adventured_today:
                    wState.questboard_open  = False
                    wState.questboard_index = 0
                    wState.work_result = (
                        "You are too tired from your adventure to work today.", 0, 0)
                else:
                    wState.questboard_confirm = sel
            elif sel == "quest" and wState.questboard_quest_id:
                wState.questboard_confirm = "quest_accept"
        return True

    # ── Work result dismiss ───────────────────────────────────────────────────
    if wState.work_result is not None:
        wState.work_result = None
        return True

    # ── Rest confirmation ─────────────────────────────────────────────────────
    if wState.rest_confirm:
        if key == pygame.K_RETURN:
            wState.rest_confirm = False
            adventure.advance_day(wState, pState)
            pState.health = pState.get_max_health()
            rest_text = f"You rested until morning.\nDay {wState.day}"
            if wState.night_theft_msg:
                rest_text += f"\n{wState.night_theft_msg}"
                wState.night_theft_msg = None
            wState.work_result = (rest_text, 0, 0)
            sfx.play('heal')
        elif key == pygame.K_ESCAPE:
            wState.rest_confirm = False
        return True

    # ── Map screen (must be above the generic ESC handler) ───────────────────
    if wState.map_open:
        if key in (pygame.K_ESCAPE, pygame.K_m):
            wState.map_open = False
        elif key in (pygame.K_LEFT, pygame.K_UP):
            wState.map_cursor = 0
            sfx.play('menu')
        elif key in (pygame.K_RIGHT, pygame.K_DOWN):
            wState.map_cursor = 1
            sfx.play('menu')
        elif key == pygame.K_RETURN:
            towns = ["village", "duskwall"]
            dest_town = towns[wState.map_cursor]
            wState.map_open = False
            if dest_town != wState.area:
                wState.area      = dest_town
                wState.nav_index = 0
                sfx.set_music("duskwall" if dest_town == "duskwall" else "village")
                trigger_fade_in()
        return True

    # ── M key — open map ─────────────────────────────────────────────────────
    if key == pygame.K_m and wState.duskwall_unlocked and wState.area in ("village", "duskwall"):
        wState.map_open   = True
        wState.map_cursor = 0 if wState.area == "village" else 1
        sfx.play('menu')
        return True

    # ── ESC key ───────────────────────────────────────────────────────────────
    if key == pygame.K_ESCAPE:
        if wState.options_open:
            wState.options_open  = False
            wState.options_bar   = 0
            wState.menu_open     = True
            return True
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
        if wState.shop_mode == "buy":
            _perm_items = (gamestate.DUSKWALL_PERM_SHOP_ITEMS
                           if wState.area == "duskwall_shop"
                           else gamestate.PERM_SHOP_ITEMS)
            equip_list  = sorted([i for i in wState.shop_inventory if not i.consumable],
                                 key=lambda i: i.price)
            supply_list = sorted([i for i in wState.shop_inventory if i.consumable]
                                 + _perm_items, key=lambda i: i.price)
            active_list = equip_list if wState.shop_col == 0 else supply_list
            if key == pygame.K_LEFT:
                if wState.shop_col == 1:
                    wState.shop_col   = 0
                    wState.shop_index = min(wState.shop_index, max(0, len(equip_list) - 1))
                    sfx.play('menu')
            elif key == pygame.K_RIGHT:
                if wState.shop_col == 0:
                    wState.shop_col   = 1
                    wState.shop_index = min(wState.shop_index, max(0, len(supply_list) - 1))
                    sfx.play('menu')
            elif key == pygame.K_UP:
                wState.shop_index = max(0, wState.shop_index - 1)
                sfx.play('menu')
            elif key == pygame.K_DOWN:
                wState.shop_index = min(len(active_list) - 1, wState.shop_index + 1)
                sfx.play('menu')
            elif key == pygame.K_RETURN and active_list:
                item     = active_list[wState.shop_index]
                _in_dusk = (wState.area == "duskwall_shop")
                wallet   = pState.marks if _in_dusk else pState.gold
                if wallet >= item.price:
                    if _in_dusk:
                        pState.marks -= item.price
                    else:
                        pState.gold             -= item.price
                        pState.total_spent_gold += item.price
                    quests.check_achievements(wState, pState)
                    if item.consumable and "food" in item.use_effect:
                        pState.food     += item.use_effect["food"]
                        wState.shop_msg  = f"+{item.use_effect['food']} food."
                    elif not item.consumable and pState.equipment.get(item.slot) is None:
                        pState.equipment[item.slot] = item
                        pState.health   = min(pState.health, pState.get_max_health())
                        wState.shop_msg = f"{item.name} auto-equipped!"
                        newly_done = quests.check_new_completions(pState)
                        if newly_done:
                            wState.quest_completion_popup = newly_done
                    else:
                        pState.inventory.append(item)
                        wState.shop_msg = f"Purchased {item.name}."
                    sfx.play('purchase')
                    if item in wState.shop_inventory:
                        wState.shop_inventory.remove(item)
                    new_equip  = sorted([i for i in wState.shop_inventory if not i.consumable],
                                        key=lambda i: i.price)
                    new_supply = sorted([i for i in wState.shop_inventory if i.consumable]
                                        + _perm_items, key=lambda i: i.price)
                    new_active = new_equip if wState.shop_col == 0 else new_supply
                    wState.shop_index = min(wState.shop_index, max(0, len(new_active) - 1))
                else:
                    wState.shop_msg = "Not enough marks." if _in_dusk else "Not enough gold."
                    sfx.play('error')
        else:
            _in_dusk    = (wState.area == "duskwall_shop")
            sell_groups = _group_items(pState.inventory)
            if key == pygame.K_UP:
                wState.shop_index = max(0, wState.shop_index - 1)
                sfx.play('menu')
            elif key == pygame.K_DOWN:
                wState.shop_index = min(len(sell_groups) - 1, wState.shop_index + 1)
                sfx.play('menu')
            elif key == pygame.K_RETURN and sell_groups:
                item = sell_groups[wState.shop_index][0]
                if _in_dusk:
                    sell_price = max(1, item.price // 4)
                    pState.marks += sell_price
                else:
                    sell_price = max(1, item.price // 2)
                    pState.gold += sell_price
                pState.inventory.remove(item)
                sfx.play('gold')
                wState.shop_index = min(wState.shop_index,
                                        max(0, len(_group_items(pState.inventory)) - 1))
        return True

    # ── Options overlay ───────────────────────────────────────────────────────
    if wState.options_open:
        step = 0.1
        if key in (pygame.K_UP, pygame.K_DOWN):
            wState.options_bar = 1 - wState.options_bar   # toggle 0 ↔ 1
            sfx.play('menu')
        elif key in (pygame.K_LEFT, pygame.K_COMMA):
            if wState.options_bar == 0:
                wState.music_volume = round(max(0.0, wState.music_volume - step), 1)
                sfx.set_music_volume(wState.music_volume)
            else:
                wState.sfx_volume = round(max(0.0, wState.sfx_volume - step), 1)
                sfx.set_sfx_volume(wState.sfx_volume)
                sfx.play('vol_sfx')
        elif key in (pygame.K_RIGHT, pygame.K_PERIOD):
            if wState.options_bar == 0:
                wState.music_volume = round(min(1.0, wState.music_volume + step), 1)
                sfx.set_music_volume(wState.music_volume)
            else:
                wState.sfx_volume = round(min(1.0, wState.sfx_volume + step), 1)
                sfx.set_sfx_volume(wState.sfx_volume)
                sfx.play('vol_sfx')
        elif key == pygame.K_ESCAPE:
            wState.options_open = False
            wState.menu_open    = True
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
            sfx.play('menu')
        elif key == pygame.K_DOWN:
            wState.menu_index = (wState.menu_index + 1) % len(gamestate.MENU_ITEMS)
            sfx.play('menu')
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
            elif selected == "Options":
                wState.menu_open    = False
                wState.options_open = True
        return True

    # ── Hotkeys ───────────────────────────────────────────────────────────────
    if key == pygame.K_i:
        wState.inventory_open  = True
        pState.inventory_index = 0
        pState.active_panel    = "inventory"
        return True

    if key == pygame.K_q:
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
            sfx.play('menu')
    elif key == pygame.K_RIGHT:
        if col < 1 and wState.nav_index + 1 < n:
            wState.nav_index += 1
            sfx.play('menu')
    elif key == pygame.K_UP:
        if row > 0:
            wState.nav_index -= 2
            sfx.play('menu')
    elif key == pygame.K_DOWN:
        if wState.nav_index + 2 < n:
            wState.nav_index += 2
            sfx.play('menu')
    elif key == pygame.K_RETURN and choices:
        dest = choices[wState.nav_index][0]

        if dest in ("buy", "sell"):
            wState.shop_mode  = dest
            wState.shop_index = 0
            wState.shop_col   = 0
            trigger_fade_in()

        elif dest == "adventure":
            wState.adventure_origin         = wState.area
            wState.adventure_select_context = "restholm"
            wState.adventure_select_mode    = True
            wState.adventure_select_msg     = ""
            wState.adventure_select_index   = min(
                wState.adventure_select_index,
                wState.adventure_locations_unlocked - 1)

        elif dest == "duskwall_adventure":
            wState.adventure_origin = wState.area
            if wState.duskwall_locations_unlocked > 0:
                wState.adventure_select_context = "duskwall"
                wState.adventure_select_index   = 0
                wState.adventure_select_mode    = True
                wState.adventure_select_msg     = ""
            else:
                wState.post_room_lines = [
                    "You scan the horizon beyond Duskwall's walls.",
                    "Crumbled towers. Overgrown paths. Something old.",
                    "",
                    "Not yet. Clear the Deep Caverns first.",
                ]
                wState.post_room_mode = True

        elif dest == "questboard":
            quests.refresh_questboard(wState, pState)
            wState.questboard_open = True

        elif dest == "rest":
            wState.rest_confirm = True

        elif dest == "stash":
            wState.stash_open        = True
            wState.stash_panel       = "inventory"
            wState.stash_inv_index   = 0
            wState.stash_stash_index = 0

        elif dest == "innkeeper":
            wState.innkeeper_open   = True
            wState.innkeeper_option = 0

        elif dest == "currency_exchange":
            wState.currency_exchange_open = True

        elif dest.startswith("talk:"):
            npc_id = dest[5:]
            lines, post_action = dialogue.get_lines(npc_id, wState, pState)
            lines = _append_quest_start_line(lines, post_action, pState)
            wState.dialogue_npc_id     = npc_id
            wState.dialogue_lines      = lines
            wState.dialogue_line_index = 0
            wState.dialogue_open       = True
            wState.post_dialogue_action = post_action

        elif dest == "work":
            text   = random.choice(gamestate.WORK_TEXTS)
            gold   = random.randint(1, 10)
            food   = random.randint(1, 2) if random.random() < 0.4 else 0
            pState.gold += gold
            pState.food += food
            wState.work_result = (text, gold, food)

        else:
            # Music changes on area transitions
            if dest in ("inn", "duskwall_tavern"):
                sfx.set_music("inn")
            elif dest in ("village", "shop"):
                sfx.set_music("village")
            elif dest in ("duskwall", "duskwall_shop"):
                sfx.set_music("duskwall")
            wState.updateArea(dest)
            trigger_fade_in()

    return True
