'''
gamestate.py
World and player state
'''

import random
import data.items as items_module

MAIN_MENU_ITEMS  = ["New Game", "Load Game", "Exit"]
MENU_ITEMS       = ["Inventory", "Quests", "Save", "Exit"]
PERM_SHOP_ITEMS  = [items_module.ALL_ITEMS["Rations"]]  # always stocked, never removed
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
        "name":       "Dark Forest",
        "image":      "assets/forest.jpg",
        "desc":       "A dense, fog-filled forest teeming with beasts.",
        "tiers":      [1, 1, 1, 1, 2, 1, 1, 2, 2],  # rooms 0-8; room 9 always boss
        "boss_index": 0,
    },
    {
        "name":       "Deep Caverns",
        "image":      "assets/cave.jpeg",
        "desc":       "Ancient tunnels carved into cold black rock.",
        "tiers":      [1, 2, 1, 2, 2, 1, 2, 2, 2],  # rooms 0-8; room 9 always boss
        "boss_index": 1,
    },
]

COMBAT_ACTIONS = ["Attack", "Use Potion", "Examine", "Flee"]

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
        self.shop_mode            = None  # "buy" | "sell"
        self.shop_msg             = ""    # transient feedback line shown in shop

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
        self.combat_nav_index = 0
        self.combat_result   = None   # "victory" | "defeat" | "fled"
        self.combat_examined = False

        # post-combat result screen
        self.post_combat_mode  = False
        self.post_combat_loot  = (0, None)
        self.adventure_complete = False
        self.post_combat_levelups = []

        # non-combat adventure rooms
        self.post_room_mode  = False
        self.post_room_lines = []

        # wanderer trade
        self.adventure_trade_mode = False
        self.adventure_trade_item = None

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

        # adventure no-food message
        self.adventure_select_msg = ""

        # post-combat quest completions
        self.post_combat_quest_completions = []

        # equipment quest completion popup
        self.quest_completion_popup = []

        # other UI
        self.quests_open    = False
        self.innkeeper_open = False
        self.work_result    = None   # (text, gold, food) or None
        self.rest_confirm   = False

    # ── shop ──────────────────────────────────────────────────────────────────
    def restock_shop(self):
        equip_pool = [i for i in items_module.SHOP_POOL if not i.consumable]
        cons_pool  = [i for i in items_module.SHOP_POOL if i.consumable]
        picks  = random.sample(equip_pool, min(2, len(equip_pool)))
        picks += random.sample(cons_pool,  min(2, len(cons_pool)))
        self.shop_inventory        = picks
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
        if new_area == "shop" and self.day > self.shop_last_stocked_day:
            self.restock_shop()

    # ── combat ────────────────────────────────────────────────────────────────
    def start_combat(self, monster):
        self.in_combat        = True
        self.combat_monster   = monster
        self.combat_log       = [f"A {monster.name} appears!"]
        self.combat_nav_index = 0
        self.combat_result    = None
        self.combat_examined  = False


class PlayerState:
    def __init__(self):
        self.name            = ""
        self.health          = 20
        self.base_max_health = 20
        self.gold            = 0
        self.base_attack     = 1
        self.base_defense    = 1
        self.level           = 1
        self.xp              = 0
        self.food            = 0
        self.debt            = 100
        self.kills           = 0
        self.boss_kills      = 0
        self.quests_complete  = set()
        self.active_quests    = {"debt"}
        self.quest_snapshots  = {}  # quest_id -> stat value at time of acceptance

        self.inventory = []
        self.stash     = [items_module.ALL_ITEMS["Rations"]]
        self.equipment = {slot: None for slot in EQUIPMENT_SLOTS}

        # UI cursors
        self.inventory_index  = 0
        self.active_panel     = "inventory"
        self.equip_slot_index = 0

    # ── derived stats ─────────────────────────────────────────────────────────
    def get_max_health(self):
        bonus = sum(i.stats.get("hp", 0) for i in self.equipment.values() if i)
        return self.base_max_health + bonus

    def get_attack(self):
        bonus = sum(i.stats.get("attack", 0) for i in self.equipment.values() if i)
        return self.base_attack + bonus

    def get_defense(self):
        bonus = sum(i.stats.get("defense", 0) for i in self.equipment.values() if i)
        return self.base_defense + bonus

    # ── levelling ─────────────────────────────────────────────────────────────
    def xp_to_next(self):
        return int(5 * self.level ** 2.2 + 5)

    def gain_xp(self, amount):
        '''Add XP. Returns list of new levels gained.'''
        self.xp += amount
        leveled = []
        while self.xp >= self.xp_to_next():
            self.xp -= self.xp_to_next()
            self.level          += 1
            self.base_max_health += 5
            self.base_attack    += 1
            self.base_defense   += 1
            self.health          = self.get_max_health()
            leveled.append(self.level)
        return leveled

    # ── HP ────────────────────────────────────────────────────────────────────
    def heal(self, amount):
        self.health = min(self.get_max_health(), self.health + amount)

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)
        return self.health <= 0

    def die(self):
        self.inventory = []
        self.equipment = {slot: None for slot in EQUIPMENT_SLOTS}
        self.gold      = self.gold // 2
        self.food      = max(0, self.food - 2)
        self.health    = self.get_max_health()

    # ── items ─────────────────────────────────────────────────────────────────
    def use_item(self, index):
        '''Use a consumable from inventory. Returns description string or None if invalid.'''
        if not (0 <= index < len(self.inventory)):
            return None
        item = self.inventory[index]
        if not item.consumable:
            return None
        effect = item.use_effect
        if "heal" in effect:
            before = self.health
            self.heal(effect["heal"])
            healed = self.health - before
            msg = f"Used {item.name}. Restored {healed} HP."
        elif "food" in effect:
            self.food += effect["food"]
            msg = f"Used {item.name}. Gained {effect['food']} food."
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
        current = self.equipment[item.slot]
        self.equipment[item.slot] = item
        self.inventory.pop(index)
        if current:
            self.inventory.insert(index, current)
        self.inventory_index = min(self.inventory_index, max(0, len(self.inventory) - 1))
        self.health = min(self.health, self.get_max_health())

    def unequip_item(self, slot_index):
        slot = EQUIPMENT_SLOTS[slot_index]
        item = self.equipment.get(slot)
        if item:
            self.equipment[slot] = None
            self.inventory.append(item)
            self.health = min(self.health, self.get_max_health())

    # ── compat helpers ────────────────────────────────────────────────────────
    def getHealth(self): return self.health
    def getGold(self):   return self.gold

    def reset(self):
        self.__init__()
