'''
items.py
Item definitions
'''

class Item:
    def __init__(self, name, slot, stats, price, tier=1, consumable=False, use_effect=None):
        self.name       = name
        self.slot       = slot        # equipment slot name, or None for consumables
        self.stats      = stats       # passive bonuses when equipped {"attack":2, "hp":5, "defense":3}
        self.price      = price       # buy price; sell = price // 2
        self.tier       = tier        # 1=common, 2=rare
        self.consumable = consumable
        self.use_effect = use_effect or {}  # {"heal": 20} or {"food": 3}

# ── Equipment Tier 1 ─────────────────────────────────────────────────────────
rusty_sword   = Item("Rusty Sword",   "weapon", {"attack": 2},  price=3)
leather_helm  = Item("Leather Helm",  "head",   {"hp": 2},      price=4)
leather_body  = Item("Leather Armor", "body",   {"defense": 2}, price=5)
leather_chaps = Item("Leather Chaps", "legs",   {"defense": 1}, price=3)
iron_ring     = Item("Iron Ring",     "ring",   {"hp": 2},      price=3)
wood_shield   = Item("Wood Shield",   "shield", {"defense": 1}, price=3)
copper_amulet = Item("Copper Amulet", "amulet", {"attack": 1},  price=4)

# ── Equipment Tier 2 ─────────────────────────────────────────────────────────
iron_sword    = Item("Iron Sword",    "weapon", {"attack": 4},               price=10, tier=2)
iron_helm     = Item("Iron Helm",     "head",   {"hp": 5},                   price=12, tier=2)
iron_body     = Item("Iron Armor",    "body",   {"defense": 4},              price=14, tier=2)
iron_chaps    = Item("Iron Chaps",    "legs",   {"defense": 3},              price=12, tier=2)
life_ring     = Item("Life Ring",     "ring",   {"hp": 4},                   price=10, tier=2)
iron_shield   = Item("Iron Shield",   "shield", {"defense": 5},              price=16, tier=2)
gold_amulet   = Item("Gold Amulet",   "amulet", {"attack": 2, "defense": 1}, price=18, tier=2)

# ── Equipment Tier 3 ─────────────────────────────────────────────────────────
boots_of_speed  = Item("Boots of Speed",  "legs",   {"flee_bonus": 0.20},         price=30, tier=3)
thorn_ring      = Item("Thorn Ring",      "ring",   {"reflect": 0.25},            price=35, tier=3)
berserker_helm  = Item("Berserker Helm",  "head",   {"attack": 3, "defense": -2}, price=28, tier=3)
mage_robe       = Item("Mage Robe",       "body",   {"hp": 8},                    price=32, tier=3)

# ── Consumables ───────────────────────────────────────────────────────────────
rations          = Item("Rations",          None, {}, 4,  consumable=True, use_effect={"food": 1})
potion           = Item("Potion",           None, {}, 15, consumable=True, use_effect={"heal": 20})
greater_potion   = Item("Greater Potion",   None, {}, 40, consumable=True, use_effect={"heal": 50})
antidote         = Item("Antidote",         None, {}, 20, consumable=True, use_effect={"cure": True})
smoke_bomb       = Item("Smoke Bomb",       None, {}, 25, consumable=True, use_effect={"flee": True})
sharpening_stone = Item("Sharpening Stone", None, {}, 30, consumable=True, use_effect={"buff_attack": 1})
iron_ration      = Item("MRE",              None, {}, 8,  consumable=True, use_effect={"food": 3})

_equipment   = [rusty_sword, leather_helm, leather_body, leather_chaps, iron_ring,
                wood_shield, copper_amulet,
                iron_sword, iron_helm, iron_body, iron_chaps, life_ring, iron_shield, gold_amulet,
                boots_of_speed, thorn_ring, berserker_helm, mage_robe]
_consumables = [rations, potion, greater_potion, antidote, smoke_bomb, sharpening_stone, iron_ration]
_all         = _equipment + _consumables

ALL_ITEMS            = {item.name: item for item in _all}
SHOP_POOL            = _equipment   # random equipment rotation
SHOP_CONSUMABLE_POOL = [antidote, smoke_bomb, sharpening_stone]  # random consumable rotation
