'''
adventure.py
Room entry, combat resolution, and adventure state helpers
'''

import random
import math
import state.gamestate as gamestate
import data.quests as quests
import data.monsters as monsters_module
import data.items as items_module
import data.passives as passives_data
import audio.sounds as sfx
from render.helpers import trigger_fade_in


def advance_day(wState, pState):
    '''Increment the day counter, check expired quests, and handle overnight events.'''
    wState.day += 1
    wState.adventured_today = False

    # Check for quests whose due date has passed
    expired_ids = [qid for qid, due in pState.quest_due_dates.items()
                   if wState.day > due and qid not in pState.quests_complete]
    for qid in expired_ids:
        quest = next((q for q in quests.QUESTS if q["id"] == qid), None)
        _is_dusk_quest = quest and quest.get("area") == "duskwall"
        if _is_dusk_quest:
            penalty = pState.marks // 2
            pState.marks -= penalty
        else:
            penalty = pState.gold // 2
            pState.gold -= penalty
        pState.active_quests.discard(qid)
        pState.quest_due_dates.pop(qid, None)
        pState.quest_snapshots.pop(qid, None)
        name = quest["name"] if quest else qid
        wState.quest_expired_popup.append((name, penalty))

    # Restholm debt deadline: day 14
    if wState.day == 14 and pState.debt > 0 and "second_debt" not in pState.active_quests:
        wState.game_over = "debt_expired"
    # Duskwall debt deadline: day 28
    elif wState.day == 28:
        if "second_debt" in pState.active_quests and pState.debt > 0:
            wState.game_over = "debt_expired"

    # Duskwall: 25% chance of overnight theft (5-10% of marks)
    _dusk_areas = {"duskwall", "duskwall_tavern", "duskwall_shop"}
    if wState.area in _dusk_areas and pState.marks > 0:
        if random.random() < 0.25:
            stolen = max(1, int(pState.marks * random.uniform(0.05, 0.10)))
            pState.marks -= stolen
            wState.night_theft_msg = f"You wake to find {stolen} marks lighter. Someone helped themselves overnight."


def _clear_combat_effects(pState):
    # Remove turn-limited combat effects (positive count).
    # Effects set to -1 (legacy permanent) stay until rest/cure.
    for e in ("poison", "weakened", "stunned", "cursed"):
        if pState.status_effects.get(e, 0) > 0:
            pState.status_effects.pop(e, None)


def _tick_status_effects(wState, pState):
    '''Tick per-round effects (poison damage, duration countdown). Returns True if player died.'''
    # Tick re-infliction cooldowns FIRST so a cooldown set this turn isn't immediately decremented
    for effect in list(pState.status_effect_cooldowns.keys()):
        pState.status_effect_cooldowns[effect] -= 1
        if pState.status_effect_cooldowns[effect] <= 0:
            del pState.status_effect_cooldowns[effect]
    for effect in ("poison", "weakened", "cursed"):
        if effect not in pState.status_effects:
            continue
        turns = pState.status_effects[effect]
        if turns == -1:
            continue   # legacy permanent effect — leave untouched
        if effect == "poison":
            died = pState.take_damage(2)
            wState.combat_log.append(
                f"Poison deals 2 dmg.  ({pState.health}/{pState.get_max_health()} HP)")
            if died:
                wState.combat_log.append("You succumb to poison!")
                return True
        pState.status_effects[effect] -= 1
        if pState.status_effects[effect] <= 0:
            del pState.status_effects[effect]
            pState.status_effect_cooldowns[effect] = 5   # can't re-apply for 5 turns
            wState.combat_log.append(f"The {effect} wears off.")
    return False


def _apply_monster_status(monster, wState, pState):
    '''Roll each monster status effect and apply to player on hit.'''
    for effect, chance, _dur in monster.status_effects:
        # Skip if the effect is still active OR in its post-expiry cooldown
        if pState.status_effects.get(effect, 0) > 0:
            continue
        if effect in pState.status_effect_cooldowns:
            continue
        if random.random() < chance:
            duration = random.randint(1, 5)
            pState.status_effects[effect] = duration
            wState.combat_log.append(f"You are afflicted with {effect}!")


def _do_counter_attack(monster, wState, pState):
    '''Apply monster counter-attack with block, reflect, status effects, and ticks.'''
    mdmg = monsters_module.calc_damage(monster.attack, pState.get_defense())
    # Block roll
    if random.randint(1, 100) <= pState.get_block_chance():
        mdmg = mdmg // 2
        if mdmg == 0:
            wState.combat_log.append(f"Completely blocked! {monster.name}'s attack deals no damage.")
        else:
            wState.combat_log.append(f"Blocked! {monster.name} hits you for {mdmg} dmg.")
    else:
        wState.combat_log.append(f"{monster.name} hits you for {mdmg} dmg.")
    had_second_wind = pState.second_wind_available
    died = pState.take_damage(mdmg)
    # Second Wind message — only when the passive actually triggered this hit
    if had_second_wind and not pState.second_wind_available and not died:
        wState.combat_log.append("Second Wind! You survive with 1 HP!")
    sfx.play_delayed('hit_player', 100)

    reflect = sum(i.stats.get("reflect", 0) for i in pState.equipment.values() if i)
    if reflect > 0:
        rdmg = max(1, int(mdmg * reflect))
        monster.hp -= rdmg
        wState.combat_log.append(f"Thorns reflect {rdmg} dmg!")
        if monster.hp <= 0 and not died:
            handle_victory(wState, pState)
            return

    if died:
        wState.combat_log.append("You have been slain!")
        handle_defeat(wState, pState)
        return

    _apply_monster_status(monster, wState, pState)
    if _tick_status_effects(wState, pState):
        handle_defeat(wState, pState)


def _spawn_for_loc(loc, tier):
    '''Spawn the right monster type based on location context.'''
    if loc.get("duskwall"):
        return monsters_module.duskwall_spawn(tier, loc["boss_index"])
    return monsters_module.spawn(tier, loc["boss_index"])


def enter_room(loc_index, room_index, wState, pState):
    loc = gamestate.ADVENTURE_LOCATIONS[loc_index]

    if room_index == loc["total_rooms"] - 1:
        m = _spawn_for_loc(loc, 3)
        wState.start_combat(m)
        sfx.set_music('boss')
        trigger_fade_in()
        return

    room_type = (wState.adventure_room_sequence[room_index]
                 if wState.adventure_room_sequence and room_index < len(wState.adventure_room_sequence)
                 else random.choice(["monster"] * 3 + ["campfire", "cursed", "damage", "fairy",
                                                        "food", "item", "nothing", "shrine",
                                                        "trapped_chest", "wanderer"]))

    if room_type in ("monster", "monster_1", "monster_2"):
        pState.consecutive_peaceful_rooms = 0
        tier = 2 if room_type == "monster_2" else 1
        m = _spawn_for_loc(loc, tier)
        wState.start_combat(m)
        sfx.set_music('dusk_battle' if loc.get("duskwall") else 'battle')
        trigger_fade_in()
        return

    sfx.set_music(loc.get("music", "dark_forest"))

    lines = []

    if room_type == "item":
        roll = random.randint(1, 4)
        if roll == 1:
            gold = random.randint(1, 10)
            pState.gold += gold
            lines = ["You see a corpse lying under a tree.",
                     f"You search it and find {gold} gold!"]
            sfx.play('gold')
        elif roll == 2:
            base_pool = items_module.DUSKWALL_SHOP_POOL if loc.get("duskwall") else items_module.SHOP_POOL
            # Tier scales with dungeon depth:
            # loc 0 Dark Forest → t1; loc 1 Deep Caverns → t1/t2 (50/50)
            # loc 2 Outer Ruins → t2; loc 3 Abandoned Castle → t2/t3 (50/50)
            loc_idx   = wState.adventure_loc_index
            if loc.get("duskwall"):
                item_tier = 3 if (loc_idx >= 3 and random.random() < 0.5) else 2
            else:
                item_tier = 2 if (loc_idx >= 1 and random.random() < 0.5) else 1
            pool = [i for i in base_pool if i.tier == item_tier]
            if not pool:
                pool = list(base_pool)
            item      = random.choice(pool)
            pState.inventory.append(item)
            if pState.equipment.get(item.slot) is None:
                pState.equip_item(len(pState.inventory) - 1)
                found_msg = f"You search it and find a {item.name}! (auto-equipped)"
            else:
                found_msg = f"You search it and find a {item.name}!"
            lines = ["You see a corpse lying under a tree.", found_msg]
            sfx.play('pickup')
        elif roll == 3:
            potion = items_module.ALL_ITEMS["Potion"]
            pState.inventory.append(potion)
            lines = ["You see a corpse lying under a tree.",
                     "You search it and find a Potion!"]
            sfx.play('pickup')
        else:
            lines = ["You see a corpse lying under a tree.",
                     "You search it... but find nothing."]

    elif room_type == "nothing":
        lines = ["You found an empty field. Great."]

    elif room_type == "damage":
        pct = random.randint(1, 15)
        dmg = max(1, int(pState.get_max_health() * pct / 100))
        died = pState.take_damage(dmg)
        if died:
            handle_defeat(wState, pState)
            return
        lines = ["You accidentally trip and scrape your knees!",
                 f"You lose {dmg} HP.  ({pState.health}/{pState.get_max_health()} HP remaining)"]

    elif room_type == "fairy":
        if pState.health < pState.get_max_health():
            healed = pState.get_max_health() - pState.health
            pState.health = pState.get_max_health()
            lines = ["You found a fairy!",
                     f"She restores your health to full.  (+{healed} HP)"]
            sfx.play('heal')
        else:
            lines = ["You found a fairy!",
                     "She tries to heal you, but you're already at full health."]

    elif room_type == "food":
        food_gain = 1 + pState.passive_effect("food_bonus")
        pState.food += food_gain
        lines = ["You found food!",
                 f"You pocket it for later.  Food: {pState.food}"]
        sfx.play('pickup')

    elif room_type == "wanderer":
        _is_dusk = loc.get("duskwall", False)
        sub = random.randint(1, 7)
        if sub == 1:
            wallet = pState.marks if _is_dusk else pState.gold
            currency = "marks" if _is_dusk else "gold"
            if wallet > 1:
                stolen = random.randint(1, max(1, wallet // 2))
                if _is_dusk:
                    pState.marks -= stolen
                else:
                    pState.gold -= stolen
                lines = ["You've encountered a greedy wanderer!",
                         f"He steals {stolen} {currency} from you!",
                         "The wanderer quickly wanders away."]
            else:
                lines = ["You've encountered a greedy wanderer!",
                         f"He tries to steal your {currency}, but you're broke.",
                         "The wanderer wanders away."]
        elif sub == 2:
            wallet = pState.marks if _is_dusk else pState.gold
            currency = "marks" if _is_dusk else "gold"
            gained = random.randint(1, 20) if wallet == 0 else random.randint(1, wallet)
            if _is_dusk:
                pState.marks += gained
            else:
                pState.gold += gained
            lines = ["You've encountered a generous wanderer!",
                     f"He gives you {gained} {currency}!",
                     "The wanderer happily wanders away."]
        elif sub == 3:
            lines = ["You've encountered a scary wanderer!",
                     "He's just standing there... menacingly!",
                     "You continue on. You hope not to see him again."]
        elif sub == 4:
            if pState.food > 0:
                pState.food -= 1
                lines = ["You've encountered a hungry wanderer!",
                         "He steals some food from you!",
                         "The wanderer quickly wanders away."]
            else:
                lines = ["You've encountered a hungry wanderer!",
                         "He tries to steal your food, but you have none.",
                         "The wanderer wanders away."]
        elif sub == 5:
            if pState.inventory:
                idx = random.randrange(len(pState.inventory))
                stolen_item = pState.inventory.pop(idx)
                lines = ["You've encountered a thief wanderer!",
                         f"He steals your {stolen_item.name}!",
                         "The wanderer quickly wanders away."]
            else:
                lines = ["You've encountered a thief wanderer!",
                         "He tries to steal from your inventory, but you have nothing.",
                         "The wanderer wanders away."]
        elif sub == 6:
            _pool = (items_module.DUSKWALL_SHOP_POOL
                     if loc.get("duskwall") else items_module.SHOP_POOL)
            trade_item = random.choice(_pool)
            wState.adventure_trade_item = trade_item
            wState.adventure_trade_dusk = bool(loc.get("duskwall"))
            wState.adventure_trade_mode = True
            return
        elif sub == 7:
            pState.consecutive_peaceful_rooms = 0
            if loc.get("duskwall"):
                m = monsters_module.duskwall_spawn(2, 0)
            else:
                m = monsters_module.spawn(2, 0)
            wState.start_combat(m)
            return

    elif room_type == "shrine":
        buff = random.choice(["atk", "def", "hp"])
        if buff == "atk":
            bonus = random.randint(1, 2)
            pState.temp_attack_bonus += bonus
            lines = ["You discover an ancient shrine.",
                     f"A warm light fills you.  Attack +{bonus}! (until adventure ends)"]
        elif buff == "def":
            bonus = random.randint(1, 2)
            pState.temp_defense_bonus += bonus
            lines = ["You discover an ancient shrine.",
                     f"A warm light fills you.  Defense +{bonus}! (until adventure ends)"]
        else:
            bonus = random.randint(2, 3)
            pState.temp_max_health_bonus += bonus
            pState.health = min(pState.health + bonus, pState.get_max_health())
            lines = ["You discover an ancient shrine.",
                     f"A warm light fills you.  Max HP +{bonus}! (until adventure ends)"]
        sfx.play('shrine')
        cleansed = [e for e in ("cursed", "weakened", "poison") if e in pState.status_effects]
        if cleansed:
            for e in cleansed:
                del pState.status_effects[e]
            lines.append("The shrine's light cleanses your afflictions!")

    elif room_type == "campfire":
        wState.campfire_pending_heal = max(1, pState.get_max_health() // 4)
        wState.campfire_prompt = True
        return

    elif room_type == "cursed":
        sfx.play('curse')
        curse_type = random.randint(1, 3)
        if curse_type == 1:
            pState.status_effects["weakened"] = random.randint(3, 5)
            lines = ["You enter a cursed room!",
                     "Dark energy saps your strength.  Weakened!  (-50% ATK for your next battle)"]
        elif curse_type == 2:
            pState.status_effects["cursed"] = random.randint(3, 5)
            lines = ["You enter a cursed room!",
                     "Dark energy twists around you.  Cursed!  (-2 ATK, -2 DEF for your next battle)"]
        else:
            died = pState.take_damage(3)
            lines = ["You enter a cursed room!",
                     f"Dark energy scorches you for 3 damage!  ({pState.health}/{pState.get_max_health()} HP)"]
            if died:
                handle_defeat(wState, pState)
                return

    elif room_type == "trapped_chest":
        wState.trapped_chest_mode = True
        return

    pState.consecutive_peaceful_rooms += 1
    quests.check_achievements(wState, pState)
    wState.post_room_lines = lines
    wState.post_room_mode  = True


def handle_trapped_chest_open(wState, pState):
    '''Player chose to open the trapped chest.
    40% item only, 40% damage only, 20% both.'''
    roll      = random.random()
    give_item = roll < 0.60   # item in [0, 0.40) and [0.40, 0.60)
    take_dmg  = roll >= 0.40  # damage in [0.40, 0.60) and [0.60, 1.0)

    lines = ["You open the chest!"]
    wState.trapped_chest_mode = False
    sfx.play('chest')

    if take_dmg:
        # 10–25% of max HP, rounded up, minimum 1
        dmg  = max(1, math.ceil(pState.get_max_health() * random.uniform(0.10, 0.25)))
        died = pState.take_damage(dmg)
        lines.append(
            f"It was trapped — you take {dmg} damage!  ({pState.health}/{pState.get_max_health()} HP)")
        sfx.play('hit')
        if died:
            handle_defeat(wState, pState)
            return

    if give_item:
        loc       = gamestate.ADVENTURE_LOCATIONS[wState.adventure_loc_index]
        base_pool = items_module.DUSKWALL_SHOP_POOL if loc.get("duskwall") else items_module.SHOP_POOL
        pool      = [i for i in base_pool if i.tier <= 2]
        item      = random.choice(pool)
        pState.inventory.append(item)
        if pState.equipment.get(item.slot) is None:
            pState.equip_item(len(pState.inventory) - 1)
            lines.append(f"Inside you find: {item.name}!  (Auto-equipped)")
        else:
            lines.append(f"Inside you find: {item.name}!")
    else:
        lines.append("The chest is empty — it was only a trap.")

    pState.consecutive_peaceful_rooms += 1
    quests.check_achievements(wState, pState)
    wState.post_room_lines = lines
    wState.post_room_mode  = True


def handle_trapped_chest_leave(wState, pState):
    '''Player chose to leave the trapped chest alone.'''
    wState.trapped_chest_mode = False
    pState.consecutive_peaceful_rooms += 1
    quests.check_achievements(wState, pState)
    wState.post_room_lines = ["You decide not to risk it.",
                               "You leave the chest behind."]
    wState.post_room_mode  = True


def handle_victory(wState, pState):
    _clear_combat_effects(pState)
    monster = wState.combat_monster
    loc     = gamestate.ADVENTURE_LOCATIONS[wState.adventure_loc_index]

    # Roll loot — bosses use tiered 3-way roll; normal/wanderer use per-area roll
    if monster.tier == 3:
        if loc.get("duskwall"):
            loot_tier = 3
            loot_pool = items_module.DUSKWALL_SHOP_POOL
        else:
            # Dark Forest (loc 0) → tier-2 items; all later dungeons → tier-3 items
            loot_tier = 2 if wState.adventure_loc_index == 0 else 3
            loot_pool = items_module.SHOP_POOL
        gold, items = monster.roll_boss_loot(loot_tier, loot_pool)
    else:
        if loc.get("duskwall"):
            gold, _item = monster.roll_duskwall_loot()
        else:
            gold, _item = monster.roll_loot()
        items = [_item] if _item is not None else []

    # Prospector: bonus gold/marks
    gold_bonus = pState.passive_effect("gold_mult")
    if gold_bonus and gold > 0:
        gold = max(gold, int(gold * (1 + gold_bonus)))
    if loc.get("duskwall"):
        pState.marks += gold
    else:
        pState.gold += gold

    # Award items (list; bosses may give 0, 1, or 2)
    loot_label  = None
    item_labels = []
    for item in items:
        if item.consumable and "food" in item.use_effect:
            pState.food += item.use_effect["food"]
            item_labels.append(f"+{item.use_effect['food']} food")
        else:
            pState.inventory.append(item)
            # Auto-equip: check the right slot (familiar vs normal)
            if item.slot == "familiar":
                can_auto = pState.familiar.equipment is None
            else:
                can_auto = pState.equipment.get(item.slot) is None
            if can_auto:
                pState.equip_item(len(pState.inventory) - 1)
                item_labels.append(f"{item.name} (auto-equipped)")
            else:
                item_labels.append(item.name)
    if item_labels:
        loot_label = ", ".join(item_labels)

    # Loot drop sounds
    _has_gold      = gold > 0
    _has_item      = bool(items)
    _is_equip      = _has_item and any(not i.consumable for i in items)
    _is_consumable = _has_item and not _is_equip
    if _has_gold and _is_equip:
        sfx.play('gold')
        sfx.play_delayed('equip', 200)
    elif _has_gold and _is_consumable:
        sfx.play('gold')
        sfx.play_delayed('pickup', 200)
    elif _has_gold:
        sfx.play('gold')
    elif _is_equip:
        sfx.play('equip')
    elif _is_consumable:
        sfx.play('pickup')

    xp_earned = monster.roll_xp()
    leveled = pState.gain_xp(xp_earned)
    if leveled:
        sfx.play_delayed('levelup', 100, exclusive=True)
        # Check for passive milestone
        for new_level, _, _, _ in leveled:
            if (new_level in passives_data.MILESTONES
                    and new_level not in pState.passive_milestones_done):
                wState.passive_pending_milestone = new_level
                break

    # Familiar gains XP (half of monster XP)
    if pState.familiar.found:
        fam_xp = max(1, xp_earned // 2)
        fam_leveled = pState.familiar.gain_xp(fam_xp)
        if fam_leveled:
            sfx.play_delayed('levelup', 200)
            wState.combat_log.append(
                f"{pState.familiar.name} reached level {fam_leveled[-1]}!")

    pState.kills += 1
    pState.kill_counts[monster.name] = pState.kill_counts.get(monster.name, 0) + 1
    if monster.tier == 3:
        pState.boss_kills += 1
    newly_done = quests.check_new_completions(pState)

    wState.post_combat_loot              = (gold, loot_label)
    wState.post_combat_levelups          = leveled
    wState.post_combat_quest_completions = newly_done
    wState.combat_result                 = "victory"
    wState.in_combat                     = False
    wState.post_combat_mode              = True

    boss_room        = loc["total_rooms"] - 1
    is_boss_victory  = wState.in_adventure and wState.adventure_room == boss_room
    if wState.in_adventure:
        sfx.set_music("victory" if is_boss_victory else loc.get("music", "dark_forest"))

    if is_boss_victory:
        wState.adventure_complete = True
        wState.in_adventure       = False
        loc_idx = wState.adventure_loc_index
        if loc_idx not in wState.adventure_locations_complete:
            wState.adventure_locations_complete.append(loc_idx)
        pState.locations_complete.add(loc_idx)
        if loc_idx <= 1:
            # Restholm dungeon: unlock next Restholm dungeon
            next_unlock = loc_idx + 2
            wState.adventure_locations_unlocked = min(
                2,   # cap at 2 Restholm dungeons
                max(wState.adventure_locations_unlocked, next_unlock))
            # Beating Deep Caverns unlocks Duskwall travel + Outer Ruins
            if loc_idx == 1:
                wState.duskwall_unlocked           = True
                wState.duskwall_just_unlocked      = True
                if wState.duskwall_locations_unlocked < 1:
                    wState.duskwall_locations_unlocked = 1
        elif loc_idx == 2:
            # Outer Ruins beaten: unlock Abandoned Castle
            if wState.duskwall_locations_unlocked < 2:
                wState.duskwall_locations_unlocked = 2
        # Survivalist: complete without potion
        if not pState.used_potion_this_run:
            pState.survivalist_completions += 1
        # Iron Will: left the dungeon with exactly 1 HP
        if pState.health == 1:
            quests.unlock_achievement("iron_will", wState, pState)
        # Speed Run: Dark Forest completed on Day 1
        if loc_idx == 0 and wState.day == 1:
            quests.unlock_achievement("speed_run", wState, pState)
        quests.check_achievements(wState, pState)
        pState.temp_attack_bonus          = 0
        pState.temp_defense_bonus         = 0
        pState.temp_max_health_bonus      = 0
        pState.consecutive_peaceful_rooms = 0
        pState.status_effects             = {}
        pState.status_effect_cooldowns    = {}
        advance_day(wState, pState)


def handle_defeat(wState, pState):
    _clear_combat_effects(pState)
    sfx.play_exclusive('defeat')
    pState.die()
    wState.combat_result                 = "defeat"
    wState.in_combat                     = False
    wState.in_adventure                  = False
    wState.post_combat_mode              = True
    wState.post_combat_loot              = (0, None)
    wState.post_combat_levelups          = []
    wState.post_combat_quest_completions = []
    advance_day(wState, pState)


def handle_flee(wState, pState):
    _clear_combat_effects(pState)
    sfx.play('flee')
    wState.combat_result    = "fled"
    wState.in_combat        = False
    wState.in_adventure     = False
    wState.post_combat_mode = True
    wState.post_combat_loot = (0, None)
    wState.post_combat_levelups = []


def return_to_village(wState, pState):
    trigger_fade_in()
    origin = wState.adventure_origin
    sfx.set_music("duskwall" if origin == "duskwall" else "village")
    wState.in_adventure                  = False
    wState.adventure_complete            = False
    wState.post_combat_mode              = False
    wState.post_room_mode                = False
    wState.post_room_lines               = []
    wState.adventure_trade_mode          = False
    wState.adventure_trade_item          = None
    wState.combat_result                 = None
    wState.post_combat_quest_completions = []
    wState.area                          = origin
    wState.nav_index                     = 0
    pState.temp_attack_bonus             = 0
    pState.temp_defense_bonus            = 0
    pState.temp_max_health_bonus         = 0
    pState.consecutive_peaceful_rooms    = 0
    pState.status_effects                = {}
    pState.status_effect_cooldowns       = {}


def do_combat_action(action_index, wState, pState):
    monster = wState.combat_monster

    # ── Stunned: skip non-item actions; items are still usable ──────────────
    if "stunned" in pState.status_effects:
        if action_index != 1:   # 1 = Use Item — allowed while stunned
            pState.status_effects["stunned"] -= 1
            if pState.status_effects["stunned"] <= 0:
                del pState.status_effects["stunned"]
                pState.status_effect_cooldowns["stunned"] = 5
                wState.combat_log.append("You were stunned and couldn't act! (Stun fades.)")
            else:
                wState.combat_log.append("You are stunned and cannot act!")
            if wState.in_combat:
                _do_counter_attack(monster, wState, pState)
            return
        # Potion while stunned: tick stun down, log it, then fall through to potion logic
        pState.status_effects["stunned"] -= 1
        if pState.status_effects["stunned"] <= 0:
            del pState.status_effects["stunned"]
            pState.status_effect_cooldowns["stunned"] = 5
            wState.combat_log.append("Stunned — but you force down a potion. (Stun fades.)")
        else:
            wState.combat_log.append("Stunned — but you force down a potion!")

    if action_index == 0:   # Attack
        dmg = monsters_module.calc_damage(pState.get_attack(), monster.defense)
        # Crit roll
        crit = random.randint(1, 100) <= pState.get_crit_chance()
        if crit:
            dmg = max(1, dmg * 2)
        monster.hp -= dmg
        if crit:
            wState.combat_log.append(f"Critical hit! You deal {dmg} dmg to the {monster.name}.")
        else:
            wState.combat_log.append(f"You deal {dmg} dmg to the {monster.name}.")
        sfx.play('hit')
        # Lifesteal
        steal = pState.passive_effect("lifesteal")
        if steal:
            pState.heal(steal)
            wState.combat_log.append(f"Lifesteal: +{steal} HP.  ({pState.health}/{pState.get_max_health()} HP)")
        if monster.hp <= 0:
            handle_victory(wState, pState)
            return
        # Familiar attacks after player
        if pState.familiar.found and wState.in_combat:
            fdmg = max(1, monsters_module.calc_damage(pState.familiar.get_attack(), monster.defense))
            monster.hp -= fdmg
            wState.combat_log.append(f"{pState.familiar.name} strikes for {fdmg} dmg!")
            if monster.hp <= 0:
                handle_victory(wState, pState)
                return

    elif action_index == 1:  # Use Item (fallback: smoke bomb or best heal while stunned)
        smoke = next((i for i, it in enumerate(pState.inventory)
                      if it.consumable and "flee" in it.use_effect), None)
        if smoke is not None:
            pState.inventory.pop(smoke)
            wState.combat_log.append("You throw a smoke bomb and escape!")
            handle_flee(wState, pState)
            return
        item_idx = next((i for i, it in enumerate(pState.inventory) if it.consumable), None)
        if item_idx is None:
            wState.combat_log.append("No usable items!")
            sfx.play('error')
            return
        msg = pState.use_item(item_idx)
        wState.combat_log.append(msg or "Used item.")
        sfx.play('potion')

    elif action_index == 2:  # Examine
        if wState.combat_examined:
            return   # already examined — button is disabled; do nothing
        m = monster
        wState.combat_log.append(
            f"{m.name}: HP {m.hp}/{m.max_hp}  ATK {m.attack}  DEF {m.defense}")
        if m.description:
            wState.combat_log.append(m.description)
        wState.combat_examined = True
        # Falls through to counter-attack — examine costs a turn

    elif action_index == 3:  # Flee
        if pState.food <= 0:
            wState.combat_log.append("No food! Cannot flee.")
            return
        pState.food -= 1
        flee_bonus = sum(i.stats.get("flee_bonus", 0) for i in pState.equipment.values() if i)
        thresholds = {1: 0.80, 2: 0.66, 3: 0.50}
        chance = min(0.95, thresholds.get(monster.tier, 0.50) + flee_bonus)
        if random.random() < chance:
            wState.combat_log.append(
                f"You throw food as a distraction and escape from {monster.name}!")
            handle_flee(wState, pState)
        else:
            wState.combat_log.append(
                f"You throw food but {monster.name} won't be distracted — you fail to escape!")
            if wState.in_combat:
                _do_counter_attack(monster, wState, pState)
        return

    # Monster counter-attack (after Attack or Use Item)
    if wState.in_combat:
        _do_counter_attack(monster, wState, pState)
