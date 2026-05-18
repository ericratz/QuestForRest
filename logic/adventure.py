'''
adventure.py
Room entry, combat resolution, and adventure state helpers
'''

import random
import state.gamestate as gamestate
import data.quests as quests
import data.monsters as monsters_module
import data.items as items_module


def enter_room(loc_index, room_index, wState, pState):
    loc = gamestate.ADVENTURE_LOCATIONS[loc_index]

    if room_index == 9:
        m = monsters_module.spawn(3, loc["boss_index"])
        wState.start_combat(m)
        return

    room_pool = ["monster"] * 3 + ["item", "nothing", "damage", "fairy", "food", "wanderer"]
    room_type = random.choice(room_pool)

    if room_type == "monster":
        tier = loc["tiers"][room_index]
        m = monsters_module.spawn(tier, loc["boss_index"])
        wState.start_combat(m)
        return

    lines = []

    if room_type == "item":
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
        else:
            lines = ["You found a fairy!",
                     "She tries to heal you, but you're already at full health."]

    elif room_type == "food":
        pState.food += 1
        lines = ["You found food!",
                 f"You pocket it for later.  Food: {pState.food}"]

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
            m = monsters_module.spawn(2, 0)
            wState.start_combat(m)
            return

    wState.post_room_lines = lines
    wState.post_room_mode  = True


def handle_victory(wState, pState):
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
            loot_label = item.name
    leveled = pState.gain_xp(monster.xp)
    pState.kills += 1
    if monster.tier == 3:
        pState.boss_kills += 1
    newly_done = quests.check_new_completions(pState)

    wState.post_combat_loot              = (gold, loot_label)
    wState.post_combat_levelups          = leveled
    wState.post_combat_quest_completions = newly_done
    wState.combat_result                 = "victory"
    wState.in_combat                     = False
    wState.post_combat_mode              = True

    if wState.in_adventure and wState.adventure_room == 9:
        wState.adventure_complete = True
        wState.in_adventure       = False
        if wState.adventure_loc_index not in wState.adventure_locations_complete:
            wState.adventure_locations_complete.append(wState.adventure_loc_index)
            next_unlock = wState.adventure_loc_index + 2
            wState.adventure_locations_unlocked = min(
                len(gamestate.ADVENTURE_LOCATIONS),
                max(wState.adventure_locations_unlocked, next_unlock))
        wState.day             += 1
        wState.adventured_today = False


def handle_defeat(wState, pState):
    pState.die()
    wState.combat_result                 = "defeat"
    wState.in_combat                     = False
    wState.in_adventure                  = False
    wState.post_combat_mode              = True
    wState.post_combat_loot              = (0, None)
    wState.post_combat_levelups          = []
    wState.post_combat_quest_completions = []
    wState.day                          += 1
    wState.adventured_today              = False


def handle_flee(wState, pState):
    pState.food            -= 1
    wState.combat_result    = "fled"
    wState.in_combat        = False
    wState.in_adventure     = False
    wState.post_combat_mode = True
    wState.post_combat_loot = (0, None)
    wState.post_combat_levelups = []


def return_to_village(wState):
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


def do_combat_action(action_index, wState, pState):
    monster = wState.combat_monster

    if action_index == 0:   # Attack
        dmg = monsters_module.calc_damage(pState.get_attack(), monster.defense)
        monster.hp -= dmg
        wState.combat_log.append(f"You deal {dmg} dmg to the {monster.name}.")
        if monster.hp <= 0:
            handle_victory(wState, pState)
            return

    elif action_index == 1:  # Use Potion
        potions = [(i, it) for i, it in enumerate(pState.inventory)
                   if it.consumable and "heal" in it.use_effect]
        if not potions:
            wState.combat_log.append("No potions available!")
            return
        idx, _ = potions[0]
        msg = pState.use_item(idx)
        wState.combat_log.append(msg or "Used a potion.")

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
        handle_flee(wState, pState)
        return

    # Monster counter-attack (after Attack or Use Potion)
    if wState.in_combat:
        mdmg = monsters_module.calc_damage(monster.attack, pState.get_defense())
        died = pState.take_damage(mdmg)
        wState.combat_log.append(f"{monster.name} hits you for {mdmg} dmg.")
        if died:
            wState.combat_log.append("You have been slain!")
            handle_defeat(wState, pState)
