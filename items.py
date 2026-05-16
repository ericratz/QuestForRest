'''
items.py
Item definitions
'''

class Item:
    def __init__(self, name, slot, stats, price):
        self.name  = name
        self.slot  = slot   #must match a key in EQUIPMENT_SLOTS
        self.stats = stats  #e.g. {"attack": 5, "defense": 2}
        self.price = price  #buy price; sell price = price // 2

rusty_sword  = Item("Rusty Sword",   "weapon", {"attack": 2},            5)
iron_sword   = Item("Iron Sword",    "weapon", {"attack": 6},           20)
leather_helm = Item("Leather Helm",  "head",   {"defense": 2},           8)
iron_helm    = Item("Iron Helm",     "head",   {"defense": 5},          18)
leather_body = Item("Leather Armor", "body",   {"defense": 3},          12)
leather_chaps = Item("Leather Chaps", "legs",   {"defense": 2},           10)
wood_shield  = Item("Wood Shield",   "shield", {"defense": 3},           8)
iron_shield  = Item("Iron Shield",   "shield", {"defense": 7},          22)
gold_amulet  = Item("Gold Amulet",   "amulet", {"defense": 1, "attack": 1}, 25)
iron_ring    = Item("Iron Ring",     "ring",   {"attack": 2},           15)

_all = [rusty_sword, iron_sword, leather_helm, iron_helm, leather_body, leather_chaps,
        wood_shield, iron_shield, gold_amulet, iron_ring]
ALL_ITEMS = {item.name: item for item in _all}
