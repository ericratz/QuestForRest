'''
adventure.py
Room entry, combat resolution, and adventure state helpers
'''

import random
import state.gamestate as gamestate
import data.quests as quests
import data.monsters as monsters_module
import data.items as items_module
import audio.sounds as sfx
from render.helpers import trigger_fade_in


def advance_day(wState, pState):
    '''Increment the day counter, check expired quests, trigger rent check every 14 days.'''
    wState.day += 1
    wState.adventured_today = False

    # Check for quests whose due date has passed
    expired_ids = [qid for qid, due in pState.quest_due_dates.items()
                   if wState.day > due and qid not in pState.quests_complete]
    for qid in expired_ids:
        quest = next((q for q in quests.QUESTS if q["id"] == qid), None)
        penalty = pState.gold // 2
        pState.gold -= penalty
        pState.active_quests.discard(qid)
        pState.quest_due_dates.pop(qid, None)
        pState.quest_snapshots.pop(qid, None)
        name = quest["name"] if quest else qid
        wState.quest_expired_popup.append((name, penalty))

    if wState.day == 14:
        if pState.debt > 0:
            wState.game_over = "debt_expired"
        else:
            pState.debt = 1000
            pState.active_quests.add("second_debt")
            wState.new_debt_popup = True
    elif wState.day == 28:
        if "second_debt" in pState.active_quests and pState.debt > 0:
            wState.game_over = "debt_expired"


def _clear_combat_effects(pState):
    # Only remove turn-limited combat effects (positive count).
    # Effects set to -1 (adventure-persistent, e.g. from cursed rooms) stay until adventure end.
    for e in ("poison", "weakened", "stunned"):
        if pState.status_effects.get(e, 0) > 0:
            pState.status_effects.pop(e, None)


def _tick_status_effects(wState, pState):
    '''Tick per-round effects (poison damage, duration countdown). Returns True if player died.'''
    for effect in ("poison", "weakened"):
        if effect not in pState.status_effects:
            continue
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
            wState.combat_log.append(f"The {effect} wears off.")
    return False


def _apply_monster_status(monster, wState, pState):
    '''Roll each monster status effect and apply to player on hit.'''
    for effect, chance, duration in monster.status_effects:
        if random.random() < chance:
            existing = pState.status_effects.get(effect, 0)
            pState.status_effects[effect] = max(existing, duration)
            if existing == 0:
                wState.combat_log.append(f"You are afflicted with {effect}!")


def _do_counter_attack(monster, wState, pState):
    '''Apply monster counter-attack with reflect, status effects, and ticks.'''
    mdmg = monsters_module.calc_damage(monster.attack, pState.get_defense())
    died = pState.take_damage(mdmg)
    wState.combat_log.append(f"{monster.name} hits you for {mdmg} dmg.")
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


def enter_room(loc_index, room_index, wState, pState):
    loc = gamestate.ADVENTURE_LOCATIONS[loc_index]

    if room_index == loc["total_rooms"] - 1:
        m = monsters_module.spawn(3, loc["boss_index"])
        wState.start_combat(m)
        sfx.set_music('boss')
        trigger_fade_in()
        return

    room_type = (wState.adventure_room_sequence[room_index]
                 if wState.adventure_room_sequence and room_index < len(wState.adventure_room_sequence)
                 else random.choice(["monster"] * 3 + ["item", "nothing", "damage", "fairy", "food", "wanderer"]))

    if room_type == "monster":
        pState.consecutive_peaceful_rooms = 0
        tier = loc["tiers"][room_index]
        m = monsters_module.spawn(tier, loc["boss_index"])
        wState.start_combat(m)
        sfx.set_music('battle')
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
            pool = [i for i in items_module.ALL_ITEMS.values()
                    if not i.consumable and i.tier == 1]
            item = random.choice(pool)
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
        pState.food += 1
        lines = ["You found food!",
                 f"You pocket it for later.  Food: {pState.food}"]
        sfx.play('pickup')

    elif room_type == "wanderer":
        sub = random.randint(1, 7)
        if sub == 1:
            if pState.gold > 1:
                stolen = random.randint(1, max(1, pState.gold // 2))
                pState.gold -= stolen
                lines = ["You've encountered a greedy wanderer!",
                         f"He steals {stolen} gold from you!",
                         "The wanderer quickly wanders away."]
            else:
                lines = ["You've encountered a greedy wanderer!",
                         "He tries to steal your gold, but you're broke.",
                         "The wanderer wanders away."]
        elif sub == 2:
            gained = random.randint(1, 20) if pState.gold == 0 else random.randint(1, pState.gold)
            pState.gold += gained
            lines = ["You've encountered a generous wanderer!",
                     f"He gives you {gained} gold!",
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
            trade_item = random.choice(items_module.SHOP_POOL)
            wState.adventure_trade_item = trade_item
            wState.adventure_trade_mode = True
            return
        elif sub == 7:
            pState.consecutive_peaceful_rooms = 0
            m = monsters_module.spawn(2, 0)
            wState.start_combat(m)
            return

    elif room_type == "shrine":
        buff = random.choice(["atk", "def", "hp"])
        if buff == "atk":
            pState.base_attack += 1
            lines = ["You discover an ancient shrine.",
                     "A warm light fills you.  Attack +1!"]
        elif buff == "def":
            pState.base_defense += 1
            lines = ["You discover an ancient shrine.",
                     "A warm light fills you.  Defense +1!"]
        else:
            pState.base_max_health += 3
            pState.health = min(pState.health + 3, pState.get_max_health())
            lines = ["You discover an ancient shrine.",
                     "A warm light fills you.  Max HP +3!"]
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
            pState.status_effects["weakened"] = -1
            lines = ["You enter a cursed room!",
                     "Dark energy saps your strength.  Weakened!  (-50% ATK until cured or rested)"]
        elif curse_type == 2:
            pState.status_effects["cursed"] = -1
            lines = ["You enter a cursed room!",
                     "Dark energy twists around you.  Cursed!  (-2 ATK, -2 DEF until cured or rested)"]
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
        dmg  = random.randint(3, 8)
        died = pState.take_damage(dmg)
        lines.append(
            f"It was trapped — you take {dmg} damage!  ({pState.health}/{pState.get_max_health()} HP)")
        sfx.play('hit')
        if died:
            handle_defeat(wState, pState)
            return

    if give_item:
        pool = [i for i in items_module.ALL_ITEMS.values() if not i.consumable and i.tier <= 2]
        item = random.choice(pool)
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
    gold, item = monster.roll_loot()
    pState.gold += gold
    loot_label = None
    if item:
        if item.consumable and "food" in item.use_effect:
            pState.food += item.use_effect["food"]
            loot_label = f"+{item.use_effect['food']} food"
        else:
            pState.inventory.append(item)
            if pState.equipment.get(item.slot) is None:
                pState.equip_item(len(pState.inventory) - 1)
                loot_label = f"{item.name} (auto-equipped)"
            else:
                loot_label = item.name
    leveled = pState.gain_xp(monster.xp)
    if leveled:
        sfx.play_delayed('levelup', 100, exclusive=True)
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
    # Restore zone music after non-boss fight; boss/adventure-complete stays silent until village
    if wState.in_adventure:
        loc = gamestate.ADVENTURE_LOCATIONS[wState.adventure_loc_index]
        sfx.set_music(loc.get("music", "dark_forest"))

    boss_room = gamestate.ADVENTURE_LOCATIONS[wState.adventure_loc_index]["total_rooms"] - 1
    if wState.in_adventure and wState.adventure_room == boss_room:
        wState.adventure_complete = True
        wState.in_adventure       = False
        if wState.adventure_loc_index not in wState.adventure_locations_complete:
            wState.adventure_locations_complete.append(wState.adventure_loc_index)
            next_unlock = wState.adventure_loc_index + 2
            wState.adventure_locations_unlocked = min(
                len(gamestate.ADVENTURE_LOCATIONS),
                max(wState.adventure_locations_unlocked, next_unlock))
        # Survivalist: complete without potion
        if not pState.used_potion_this_run:
            pState.survivalist_completions += 1
        # Iron Will: survived at <= 10% HP
        if pState.health > 0 and pState.health <= 5:
            quests.unlock_achievement("iron_will", wState, pState)
        # Speed Run: Dark Forest completed on Day 1 (before advance_day increments)
        if wState.adventure_loc_index == 0 and wState.day == 1:
            quests.unlock_achievement("speed_run", wState, pState)
        quests.check_achievements(wState, pState)
        pState.temp_attack_bonus          = 0
        pState.consecutive_peaceful_rooms = 0
        pState.status_effects             = {}
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
    sfx.set_music('village')
    wState.in_adventure                  = False
    wState.adventure_complete            = False
    wState.post_combat_mode              = False
    wState.post_room_mode                = False
    wState.post_room_lines               = []
    wState.adventure_trade_mode          = False
    wState.adventure_trade_item          = None
    wState.combat_result                 = None
    wState.post_combat_quest_completions = []
    wState.area                          = "village"
    wState.nav_index                     = 0
    pState.temp_attack_bonus             = 0
    pState.consecutive_peaceful_rooms    = 0
    pState.status_effects                = {}


def do_combat_action(action_index, wState, pState):
    monster = wState.combat_monster

    # ── Stunned: skip player action, monster still attacks ────────────────────
    if "stunned" in pState.status_effects:
        pState.status_effects["stunned"] -= 1
        if pState.status_effects["stunned"] <= 0:
            del pState.status_effects["stunned"]
            wState.combat_log.append("You were stunned and couldn't act! (Stun fades.)")
        else:
            wState.combat_log.append("You are stunned and cannot act!")
        if wState.in_combat:
            _do_counter_attack(monster, wState, pState)
        return

    if action_index == 0:   # Attack
        dmg = monsters_module.calc_damage(pState.get_attack(), monster.defense)
        monster.hp -= dmg
        wState.combat_log.append(f"You deal {dmg} dmg to the {monster.name}.")
        sfx.play('hit')
        if monster.hp <= 0:
            handle_victory(wState, pState)
            return

    elif action_index == 1:  # Use Item (smoke bomb → guaranteed flee; else heal potion)
        smoke = next((i for i, it in enumerate(pState.inventory)
                      if it.consumable and "flee" in it.use_effect), None)
        if smoke is not None:
            pState.inventory.pop(smoke)
            wState.combat_log.append("You throw a smoke bomb and escape!")
            handle_flee(wState, pState)
            return
        potion_idx = next((i for i, it in enumerate(pState.inventory)
                           if it.consumable and "heal" in it.use_effect), None)
        if potion_idx is None:
            wState.combat_log.append("No potions or smoke bombs available!")
            sfx.play('error')
            return
        msg = pState.use_item(potion_idx)
        wState.combat_log.append(msg or "Used a potion.")
        sfx.play('potion')

    elif action_index == 2:  # Examine
        m = monster
        wState.combat_log.append(
            f"{m.name}: HP {m.hp}/{m.max_hp}  ATK {m.attack}  DEF {m.defense}")
        wState.combat_examined = True
        return  # free action — no counter-attack

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
