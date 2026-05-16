'''
gamestate.py
Handles the world state
'''

import random
import items as items_module

MAIN_MENU_ITEMS = ["New Game", "Load Game", "Options", "Exit"]
MENU_ITEMS = ["Inventory", "Options", "Save", "Exit"]
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

class WorldState:
    def __init__(self):
        self.day = 1
        self.area = "start_screen"
        self.menu_open = False
        self.menu_index = 0
        self.menu_confirm = None  # "Save", "Exit", or "Saved"
        self.inventory_open = False
        self.main_menu_index = 0
        self.main_menu_confirm = None  # "new_game_notify" or "load"
        self.available_saves = []
        self.load_menu_index = 0
        self.save_slot = None
        self.nav_index = 0
        self.shop_inventory = []
        self.shop_last_stocked_day = -1
        self.shop_index = 0
        self.shop_mode = None  # "buy" or "sell"

    def restock_shop(self):
        pool = list(items_module.ALL_ITEMS.values())
        self.shop_inventory = random.sample(pool, min(2, len(pool)))
        self.shop_last_stocked_day = self.day

    def reset(self, area="village"):
        self.day = 1
        self.area = area
        self.menu_open = False
        self.menu_index = 0
        self.menu_confirm = None
        self.inventory_open = False
        self.main_menu_index = 0
        self.main_menu_confirm = None
        self.available_saves = []
        self.load_menu_index = 0
        self.save_slot = None
        self.nav_index = 0
        self.shop_inventory = []
        self.shop_last_stocked_day = -1
        self.shop_index = 0
        self.shop_mode = None

    def getDay(self):
        return self.day

    def getArea(self):
        return self.area

    def updateDay(self):
        self.day += 1

    def updateArea(self, new_area):
        self.area = new_area
        self.nav_index = 0
        if new_area == "shop" and self.day > self.shop_last_stocked_day:
            self.restock_shop()

class PlayerState:
    def __init__(self):
        self.health = 10
        self.gold = 10
        self.base_attack = 1
        self.base_defense = 1
        self.inventory = []
        self.equipment = {slot: None for slot in EQUIPMENT_SLOTS}
        self.inventory_index = 0
        self.active_panel = "inventory"
        self.equip_slot_index = 0

    def get_attack(self):
        bonus = sum(item.stats.get("attack", 0) for item in self.equipment.values() if item)
        return self.base_attack + bonus

    def get_defense(self):
        bonus = sum(item.stats.get("defense", 0) for item in self.equipment.values() if item)
        return self.base_defense + bonus

    def unequip_item(self, slot_index):
        slot = EQUIPMENT_SLOTS[slot_index]
        item = self.equipment.get(slot)
        if item:
            self.equipment[slot] = None
            self.inventory.append(item)

    def equip_item(self, index):
        if not (0 <= index < len(self.inventory)):
            return
        item = self.inventory[index]
        current = self.equipment[item.slot]
        self.equipment[item.slot] = item
        self.inventory.pop(index)
        if current:
            self.inventory.insert(index, current)
        self.inventory_index = min(self.inventory_index, max(0, len(self.inventory) - 1))

    def getHealth(self):
        return self.health

    def getGold(self):
        return self.gold

    def updateHealth(self, new_health):
        self.health = max(0, new_health)

    def updateGold(self, new_gold):
        self.gold = new_gold

    def reset(self):
        self.__init__()
