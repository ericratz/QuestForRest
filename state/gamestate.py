'''
gamestate.py
World and player state
'''

import random
import data.items as items_module

MAIN_MENU_ITEMS  = ["New Game", "Load Game", "Exit"]
MENU_ITEMS       = ["Inventory", "Quests", "Save", "Options", "Exit"]
PERM_SHOP_ITEMS  = [items_module.ALL_ITEMS["Rations"],
                    items_module.ALL_ITEMS["Potion"],
                    items_module.ALL_ITEMS["Greater Potion"]]  # always stocked, never removed
DUSKWALL_PERM_SHOP_ITEMS = [items_module.ALL_ITEMS["MRE"],
                             items_module.ALL_ITEMS["Field Potion"],
                             items_module.ALL_ITEMS["Marked Tincture"]]
EQUIPMENT_SLOTS = ["head", "amulet", "weapon", "ring", "body", "shield", "legs"]

#          up        down      left       right
EQUIP_NAV = {
    "head":   ("legs",   "amulet", None,      "items"),
    "weapon": ("head",   "ring",   None,      "amulet"),
    "amulet": ("head",   "body",   "weapon",  "shield"),
    "shield": ("head",   None,     "amulet",  "items"),
    "ring":   ("weapon", "legs",   None,      "body"),
    "body":   ("amulet", "legs",   "ring",    "items"),
    "legs":   ("body",   "head",   None,      "items"),
}

ADVENTURE_LOCATIONS = [
    {
        "name":        "Dark Forest",
        "image":       "assets/images/Dark Forest.jpg",
        "desc":        "A dense, fog-filled forest teeming with beasts.",
        "music":       "dark_forest",
        "duskwall":    False,
        # rooms 0-8 (non-boss); room 9 is always the boss
        "boss_index":  1,                             # BOSS_POOL[1] = dark_wizard
        "total_rooms": 10,
        "monster_min": 3,
        "monster_max": 3,
        "monster_tier_split": 0.0,   # 0% tier 2 → all tier 1
        "room_dist":   ["campfire", "cursed", "item", "nothing", "shrine", "trapped_chest"],
    },
    {
        "name":        "Deep Caverns",
        "image":       "assets/images/Deep Cavern.jpeg",
        "desc":        "Ancient tunnels carved into cold black rock.",
        "music":       "deep_caverns",
        "duskwall":    False,
        # rooms 0-13 (non-boss); room 14 is always the boss
        "boss_index":  0,                             # BOSS_POOL[0] = hill_giant
        "total_rooms": 15,
        "monster_min": 3,
        "monster_max": 4,
        "monster_tier_split": 0.5,   # 50% tier 2
        "room_dist":   ["campfire", "cursed", "damage", "fairy", "food", "item",
                        "nothing", "shrine", "trapped_chest", "wanderer"],
    },
    {
        "name":        "Outer Ruins",
        "image":       "assets/images/Outer Ruins.jpeg",
        "desc":        "Crumbled walls and forgotten dead. Something still walks here.",
        "music":       "outer_ruins",
        "duskwall":    True,
        # rooms 0-18 (non-boss); room 19 is always the boss
        "boss_index":  0,                             # DUSKWALL_BOSS_POOL[0] = ruins_guardian
        "total_rooms": 20,
        "monster_min": 4,
        "monster_max": 5,
        "monster_tier_split": 0.0,   # 0% tier 2 → all tier 1
        "room_dist":   ["campfire", "cursed", "damage", "fairy", "food", "item",
                        "nothing", "shrine", "trapped_chest", "wanderer"],
    },
    {
        "name":        "Abandoned Castle",
        "image":       "assets/images/Abandoned Castle.jpeg",
        "desc":        "A noble seat, long forgotten. Whatever lives inside isn't noble.",
        "music":       "abandoned_castle",
        "duskwall":    True,
        # rooms 0-23 (non-boss); room 24 is always the boss
        "boss_index":  1,                                            # DUSKWALL_BOSS_POOL[1] = death_knight
        "total_rooms": 25,
        "monster_min": 5,
        "monster_max": 6,
        "monster_tier_split": 0.5,   # 50% tier 2
        "room_dist":   ["campfire", "cursed", "damage", "fairy", "food", "item",
                        "nothing", "shrine", "trapped_chest", "wanderer"],
    },
]

COMBAT_ACTIONS = ["Attack", "Use Item", "Examine", "Flee"]

WORK_TEXTS = [
    "You chopped wood at the mill.",
    "You helped harvest the crops.",
    "You worked as a stable hand.",
    "You ran errands for the elder.",
    "You repaired the town walls.",
    "You caught fish at the river.",
    "You worked the blacksmith's forge.",
    "You guarded a merchant's cart.",
]


class FamiliarState:
    '''A companion creature found in Duskwall. No HP — it cannot die.'''
    def __init__(self):
        self.found       = False
        self.name        = ""
        self.level       = 1
        self.xp          = 0
        self.base_attack = 2
        self.equipment   = None   # one Item or None (slot == "familiar")

    def get_attack(self):
        equip_bonus = self.equipment.stats.get("attack", 0) if self.equipment else 0
        return self.base_attack + equip_bonus

    def xp_to_next(self):
        return int(8 * self.level ** 2 + 10)

    def gain_xp(self, amount):
        '''Returns list of new levels reached.'''
        self.xp += amount
        leveled = []
        while self.xp >= self.xp_to_next():
            self.xp -= self.xp_to_next()
            self.level       += 1
            self.base_attack += 1
            leveled.append(self.level)
        return leveled

    def reset(self):
        self.__init__()


class WorldState:
    def __init__(self):
        self.day  = 1
        self.area = "start_screen"

        # menus
        self.menu_open    = False
        self.menu_index   = 0
        self.menu_confirm = None

        # inventory screen
        self.inventory_open = False

        # main menu
        self.main_menu_index   = 0
        self.main_menu_confirm = None
        self.available_saves   = []
        self.load_menu_index   = 0
        self.save_slot         = None

        # area navigation grid
        self.nav_index = 0

        # shop
        self.shop_inventory       = []
        self.shop_last_stocked_day = -1
        self.shop_index           = 0
        self.shop_col             = 0    # 0=equipment column, 1=supplies column (buy mode only)
        self.shop_mode            = None  # "buy" | "sell"
        self.shop_msg             = ""    # transient feedback line shown in shop

        # intro sequence (new game)
        self.intro_mode        = False
        self.intro_phase       = "opening"   # "opening"|"name"|"qa"|"qa_response"|"closing"
        self.intro_line_index  = 0
        self.intro_qa_index    = 0
        self.intro_qa_response = []
        self.intro_skipped     = False       # True when opening was ESC-skipped

        # character name input
        self.name_input_mode   = False
        self.name_input_buffer = ""

        # adventure location select
        self.adventure_select_mode  = False
        self.adventure_select_index = 0

        # adventure run
        self.in_adventure               = False
        self.adventure_loc_index        = 0
        self.adventure_room             = 0
        self.adventure_locations_unlocked = 1
        self.adventure_locations_complete = []
        self.adventured_today           = False

        # combat
        self.in_combat       = False
        self.combat_monster  = None
        self.combat_log      = []
        self.combat_nav_index  = 0
        self.combat_result     = None   # "victory" | "defeat" | "fled"
        self.combat_examined   = False
        self.combat_item_mode  = False  # item selection overlay open
        self.combat_item_index = 0

        # post-combat result screen
        self.post_combat_mode  = False
        self.post_combat_loot  = (0, None)
        self.adventure_complete = False
        self.post_combat_levelups = []  # list of (level, hp_gain, atk_gain, def_gain)

        # non-combat adventure rooms
        self.post_room_mode  = False
        self.post_room_lines = []

        # wanderer trade
        self.adventure_trade_mode = False
        self.adventure_trade_item = None
        self.adventure_trade_dusk = False  # True when trade is in a Duskwall location

        # trapped chest
        self.trapped_chest_mode = False

        # pre-generated room sequence for current adventure
        self.adventure_room_sequence = []

        # stash
        self.stash_open       = False
        self.stash_panel      = "inventory"  # "inventory" | "stash"
        self.stash_inv_index  = 0
        self.stash_stash_index = 0

        # questboard
        self.questboard_open     = False
        self.questboard_quest_id = None
        self.questboard_day      = -1
        self.questboard_index    = 0
        self.questboard_confirm  = None   # "odd_jobs" while confirm popup is open

        # map screen
        self.map_open              = False
        self.map_cursor            = 0    # 0 = Restholm, 1 = Duskwall

        # Duskwall unlock
        self.duskwall_unlocked           = False
        self.duskwall_just_unlocked      = False   # True only for the arrival cutscene turn
        self.duskwall_arrival_pending    = False   # True while showing arrival post_room text
        self.duskwall_currency_converted = False   # gold 25:1 conversion done once
        self.duskwall_locations_unlocked = 0       # 0=none, 1=Outer Ruins, 2=Abandoned Castle

        # adventure origin — area to return to after any adventure/defeat/flee
        self.adventure_origin = "village"

        # adventure location select context
        self.adventure_select_context = "restholm"  # "restholm" | "duskwall"

        # familiar naming
        self.familiar_naming_mode  = False
        self.familiar_name_buffer  = ""

        # post-dialogue trigger (e.g. "give_familiar")
        self.post_dialogue_action  = None

        # passive skill selection
        self.passive_select_mode      = False
        self.passive_select_options   = []   # list of 3 passive IDs
        self.passive_select_index     = 0
        self.passive_pending_milestone = None  # level int (5/10/15) while selecting

        # adventure no-food message
        self.adventure_select_msg = ""

        # post-combat quest completions
        self.post_combat_quest_completions = []

        # equipment quest completion popup
        self.quest_completion_popup = []

        # quest expired popup — list of (quest_name, gold_lost)
        self.quest_expired_popup = []

        # new debt introduced popup
        self.new_debt_popup = False

        # achievement unlock popup — list of achievement names
        self.achievement_popup = []

        # other UI
        self.quests_open           = False
        self.innkeeper_open        = False
        self.innkeeper_option      = 0   # 0 = pay debt, 1 = talk
        self.work_result           = None   # (text, gold, food) or None
        self.rest_confirm          = False
        self.currency_exchange_open = False
        self.exchange_index        = 0
        self.night_theft_msg       = None  # set when gold is stolen overnight in Duskwall

        # ending sequence (plays before the win game_over screen)
        self.ending_mode       = False
        self.ending_line_index = 0

        # game over / win state
        self.game_over = None  # None | "debt_paid" | "debt_expired"

        # boss room warning
        self.boss_warning_mode = False

        # campfire prompt
        self.campfire_prompt       = False
        self.campfire_pending_heal = 0

        # npc dialogue
        self.dialogue_open       = False
        self.dialogue_npc_id     = None
        self.dialogue_lines      = []
        self.dialogue_line_index = 0

        # options menu
        self.options_open   = False
        self.options_bar    = 0     # 0 = music, 1 = sfx
        self.music_volume   = 0.5   # 0.0 – 1.0 in 0.1 steps
        self.sfx_volume     = 0.5   # 0.0 – 1.0 in 0.1 steps

    # ── shop ──────────────────────────────────────────────────────────────────
    def restock_shop(self):
        if self.area == "duskwall_shop":
            # Duskwall shop stocks Duskwall equipment
            if 2 in self.adventure_locations_complete:
                pool_a = [i for i in items_module.DUSKWALL_SHOP_POOL if i.tier == 3]
                pool_b = [i for i in items_module.DUSKWALL_SHOP_POOL if i.tier == 2]
            else:
                pool_a = [i for i in items_module.DUSKWALL_SHOP_POOL if i.tier == 2]
                pool_b = [i for i in items_module.DUSKWALL_SHOP_POOL if i.tier == 3]
            equip_picks = (random.sample(pool_a, min(2, len(pool_a))) +
                           random.sample(pool_b, min(1, len(pool_b))))
            self.shop_inventory        = equip_picks
            self.shop_last_stocked_day = self.day
            return
        # Restholm shop
        if 0 in self.adventure_locations_complete:
            pool_a = [i for i in items_module.SHOP_POOL if i.tier == 2]
            pool_b = [i for i in items_module.SHOP_POOL if i.tier == 3]
        else:
            pool_a = [i for i in items_module.SHOP_POOL if i.tier == 1]
            pool_b = [i for i in items_module.SHOP_POOL if i.tier == 2]
        equip_picks = (random.sample(pool_a, min(2, len(pool_a))) +
                       random.sample(pool_b, min(1, len(pool_b))))
        cons_picks  = random.sample(items_module.SHOP_CONSUMABLE_POOL,
                                    min(1, len(items_module.SHOP_CONSUMABLE_POOL)))
        self.shop_inventory        = equip_picks + cons_picks
        self.shop_last_stocked_day = self.day

    # ── reset ─────────────────────────────────────────────────────────────────
    def reset(self, area="village"):
        self.__init__()
        self.area = area
        if area != "start_screen":
            self.restock_shop()

    # ── helpers ───────────────────────────────────────────────────────────────
    def getDay(self):  return self.day
    def getArea(self): return self.area
    def updateDay(self): self.day += 1

    def updateArea(self, new_area):
        self.area      = new_area
        self.nav_index = 0
        if new_area in ("shop", "duskwall_shop") and self.day > self.shop_last_stocked_day:
            self.restock_shop()

    # ── combat ────────────────────────────────────────────────────────────────
    def start_combat(self, monster):
        self.in_combat        = True
        self.combat_monster   = monster
        self.combat_log       = [f"A {monster.name} appears!"]
        self.combat_nav_index  = 0
        self.combat_result     = None
        self.combat_examined   = False
        self.combat_item_mode  = False
        self.combat_item_index = 0


class PlayerState:
    def __init__(self):
        self.name            = ""
        self.health          = 20
        self.base_max_health = 20
        self.gold            = 0
        self.marks           = 0   # Duskwall currency; separate from Restholm gold
        self.base_attack     = 1
        self.base_defense    = 1
        self.level           = 1
        self.xp              = 0
        self.food            = 0
        self.debt            = 100
        self.kills           = 0
        self.boss_kills      = 0
        self.kill_counts     = {}   # {monster_name: count} for Exterminator quest
        self.quests_complete  = set()
        self.active_quests    = {"debt"}
        self.quest_snapshots  = {}  # quest_id -> stat value at time of acceptance
        self.quest_due_dates  = {}  # quest_id -> day the quest expires

        # achievement tracking
        self.achievements_unlocked       = set()
        self.used_potion_this_run        = False  # reset each adventure start
        self.survivalist_completions     = 0      # incremented on dungeon clear without potion
        self.consecutive_peaceful_rooms  = 0      # resets on combat or adventure start
        self.total_spent_gold            = 0      # cumulative gold spent at shop

        # passive skills
        self.chosen_passives        = []    # list of passive IDs in selection order
        self.passive_milestones_done = set()  # {5, 10, 15} as milestones are picked
        self.second_wind_available  = False # reset True at each adventure start

        # familiar companion
        self.familiar = FamiliarState()

        # temporary in-adventure buffs (cleared on leaving adventure)
        self.temp_attack_bonus   = 0
        self.temp_defense_bonus  = 0
        self.temp_max_health_bonus = 0

        self.inventory = []
        self.stash     = [items_module.ALL_ITEMS["Rations"]]
        self.equipment = {slot: None for slot in EQUIPMENT_SLOTS}

        # status effects: name -> turns remaining (-1 = permanent/legacy)
        self.status_effects          = {}
        # per-effect cooldown after clearing: name -> turns until re-inflictable
        self.status_effect_cooldowns = {}

        # locations cleared — mirrored here for quest_progress checks
        self.locations_complete = set()

        # UI cursors
        self.inventory_index  = 0
        self.active_panel     = "inventory"
        self.equip_slot_index = 0

    # ── passive helper ────────────────────────────────────────────────────────
    def passive_effect(self, key, default=0):
        '''Sum a named effect across all chosen passives.'''
        import data.passives as passives_data
        total = default
        for pid in self.chosen_passives:
            total += passives_data.PASSIVES.get(pid, {}).get("effect", {}).get(key, 0)
        return total

    # ── derived stats ─────────────────────────────────────────────────────────
    def get_max_health(self):
        bonus = sum(i.stats.get("hp", 0) for i in self.equipment.values() if i)
        return self.base_max_health + bonus + self.passive_effect("hp_bonus") + self.temp_max_health_bonus

    def get_attack(self):
        bonus = sum(i.stats.get("attack", 0) for i in self.equipment.values() if i)
        atk = self.base_attack + bonus + self.temp_attack_bonus + self.passive_effect("atk_bonus")
        if self.passive_effect("berserker_atk") and self.health < self.get_max_health() / 2:
            atk += self.passive_effect("berserker_atk")
        if "cursed" in self.status_effects:
            atk = max(1, atk - 2)
        if "weakened" in self.status_effects:
            atk = max(1, atk // 2)
        return max(1, atk)

    def get_defense(self):
        bonus = sum(i.stats.get("defense", 0) for i in self.equipment.values() if i)
        def_ = self.base_defense + bonus + self.passive_effect("def_bonus") + self.temp_defense_bonus
        if "cursed" in self.status_effects:
            def_ = max(1, def_ - 2)
        return max(1, def_)

    def get_crit_chance(self):
        '''Return crit chance as a percent integer (e.g. 13 = 13%).'''
        import data.passives as passives_data
        return passives_data.BASE_CRIT_CHANCE + self.passive_effect("crit_bonus")

    def get_block_chance(self):
        '''Return block chance as a percent integer. Shield contributes its block_chance stat.'''
        import data.passives as passives_data
        shield = self.equipment.get("shield")
        shield_bonus = shield.stats.get("block_chance", 0) if shield else 0
        return passives_data.BASE_BLOCK_CHANCE + shield_bonus + self.passive_effect("block_bonus")

    # ── levelling ─────────────────────────────────────────────────────────────
    def xp_to_next(self):
        return int(5 * self.level ** 2.2 + 5)

    def gain_xp(self, amount):
        '''Add XP. Returns list of (level, hp_gain, atk_gain, def_gain) tuples.'''
        import random
        self.xp += amount
        leveled = []
        while self.xp >= self.xp_to_next():
            self.xp -= self.xp_to_next()
            self.level          += 1
            hp_gain  = random.randint(0, 2)
            atk_gain = random.randint(0, 2)
            def_gain = random.randint(0, 2)
            self.base_max_health += hp_gain
            self.base_attack     += atk_gain
            self.base_defense    += def_gain
            self.health           = self.get_max_health()
            leveled.append((self.level, hp_gain, atk_gain, def_gain))
        return leveled

    # ── HP ────────────────────────────────────────────────────────────────────
    def heal(self, amount):
        self.health = min(self.get_max_health(), self.health + amount)

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)
        if self.health <= 0 and self.second_wind_available and self.passive_effect("second_wind"):
            self.health = 1
            self.second_wind_available = False
            return False   # survived via Second Wind
        return self.health <= 0

    def die(self):
        self.inventory         = []
        self.equipment         = {slot: None for slot in EQUIPMENT_SLOTS}
        self.gold              = self.gold // 2
        self.food              = max(0, self.food - 2)
        self.status_effects    = {}
        self.temp_attack_bonus = 0
        self.health            = self.get_max_health()

    # ── items ─────────────────────────────────────────────────────────────────
    def use_item(self, index):
        '''Use a consumable from inventory. Returns description string or None if invalid.'''
        if not (0 <= index < len(self.inventory)):
            return None
        item = self.inventory[index]
        if not item.consumable:
            return None
        effect = item.use_effect
        if "cure_all" in effect:
            all_effects = ("poison", "cursed", "weakened", "stunned")
            before = self.health
            self.heal(effect.get("heal", 9999))
            healed = self.health - before
            cured = [e for e in all_effects if e in self.status_effects]
            for e in cured:
                del self.status_effects[e]
            parts = [f"Restored {healed} HP"]
            if cured:
                parts.append(f"cured {', '.join(cured)}")
            msg = f"Used {item.name}. " + ", ".join(parts) + "."
            self.used_potion_this_run = True
        elif "heal" in effect:
            before = self.health
            self.heal(effect["heal"])
            healed = self.health - before
            msg = f"Used {item.name}. Restored {healed} HP."
            self.used_potion_this_run = True
        elif "food" in effect:
            self.food += effect["food"]
            msg = f"Used {item.name}. Gained {effect['food']} food."
        elif "cure_poison" in effect:
            if "poison" in self.status_effects:
                del self.status_effects["poison"]
                msg = f"Used {item.name}. Cured poison."
            else:
                msg = f"Used {item.name}. (Not poisoned.)"
        elif "cure_stun" in effect:
            if "stunned" in self.status_effects:
                del self.status_effects["stunned"]
                msg = f"Used {item.name}. Cured stun."
            else:
                msg = f"Used {item.name}. (Not stunned.)"
        elif "cure_hex" in effect:
            cured = [e for e in ("cursed", "weakened") if e in self.status_effects]
            for e in cured:
                del self.status_effects[e]
            msg = (f"Used {item.name}. Cured: {', '.join(cured)}."
                   if cured else f"Used {item.name}. (No hex active.)")
        elif "cure" in effect:
            cured = [e for e in ("poison", "cursed", "weakened") if e in self.status_effects]
            for e in cured:
                del self.status_effects[e]
            msg = (f"Used {item.name}. Cured: {', '.join(cured)}."
                   if cured else f"Used {item.name}. (Nothing to cure.)")
        elif "buff_attack" in effect:
            self.temp_attack_bonus += effect["buff_attack"]
            msg = f"Used {item.name}. Attack +{effect['buff_attack']} until you leave!  (ATK: {self.get_attack()})"
        else:
            msg = f"Used {item.name}."
        self.inventory.pop(index)
        self.inventory_index = min(self.inventory_index, max(0, len(self.inventory) - 1))
        return msg

    def equip_item(self, index):
        if not (0 <= index < len(self.inventory)):
            return
        item = self.inventory[index]
        if item.consumable:
            self.use_item(index)
            return
        # Familiar charm: route to familiar equipment slot
        if item.slot == "familiar":
            old = self.familiar.equipment
            self.familiar.equipment = item
            self.inventory.pop(index)
            if old:
                self.inventory.insert(index, old)
            self.inventory_index = min(self.inventory_index, max(0, len(self.inventory) - 1))
            return
        # Normal equipment
        old_max = self.get_max_health()
        current = self.equipment[item.slot]
        self.equipment[item.slot] = item
        self.inventory.pop(index)
        if current:
            self.inventory.insert(index, current)
        self.inventory_index = min(self.inventory_index, max(0, len(self.inventory) - 1))
        new_max = self.get_max_health()
        hp_delta = new_max - old_max
        if hp_delta > 0:
            self.health = min(new_max, self.health + hp_delta)
        else:
            self.health = max(1, min(self.health, new_max))

    def unequip_item(self, slot_index):
        slot = EQUIPMENT_SLOTS[slot_index]
        item = self.equipment.get(slot)
        if item:
            self.equipment[slot] = None
            self.inventory.append(item)
            new_max = self.get_max_health()
            self.health = max(1, min(self.health, new_max))

    # ── compat helpers ────────────────────────────────────────────────────────
    def getHealth(self): return self.health
    def getGold(self):   return self.gold

    def reset(self):
        self.__init__()   # FamiliarState is recreated inside __init__
