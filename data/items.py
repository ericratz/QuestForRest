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
        self.tier       = tier        # 1=common, 2=rare, 3=epic
        self.consumable = consumable
        self.use_effect = use_effect or {}  # {"heal": 20} or {"food": 3}

# ── Restholm Equipment Tier 1 ─────────────────────────────────────────────────
rusty_sword   = Item("Rusty Sword",   "weapon", {"attack": 2},  price=3)
leather_helm  = Item("Leather Helm",  "head",   {"hp": 2},      price=4)
leather_body  = Item("Leather Armor", "body",   {"defense": 2}, price=5)
leather_chaps = Item("Leather Chaps", "legs",   {"defense": 1}, price=3)
iron_ring     = Item("Iron Ring",     "ring",   {"hp": 2},      price=3)
wood_shield   = Item("Wood Shield",   "shield", {"block_chance": 5}, price=3)
copper_amulet = Item("Copper Amulet", "amulet", {"attack": 1},  price=4)

# ── Restholm Equipment Tier 2 ─────────────────────────────────────────────────
iron_sword    = Item("Iron Sword",    "weapon", {"attack": 4},               price=10, tier=2)
iron_helm     = Item("Iron Helm",     "head",   {"hp": 5},                   price=12, tier=2)
iron_body     = Item("Iron Armor",    "body",   {"defense": 4},              price=14, tier=2)
iron_chaps    = Item("Iron Chaps",    "legs",   {"defense": 3},              price=12, tier=2)
life_ring     = Item("Life Ring",     "ring",   {"hp": 4},                   price=10, tier=2)
iron_shield   = Item("Iron Shield",   "shield", {"defense": 5, "block_chance": 10}, price=16, tier=2)
gold_amulet   = Item("Gold Amulet",   "amulet", {"attack": 2, "defense": 1}, price=18, tier=2)

# ── Restholm Equipment Tier 3 ─────────────────────────────────────────────────
boots_of_speed  = Item("Boots of Speed",  "legs",   {"flee_bonus": 0.20},         price=30, tier=3)
thorn_ring      = Item("Thorn Ring",      "ring",   {"reflect": 0.25},            price=35, tier=3)
berserker_helm  = Item("Berserker Helm",  "head",   {"attack": 3, "defense": -2}, price=28, tier=3)
mage_robe       = Item("Mage Robe",       "body",   {"hp": 8},                    price=32, tier=3)
dragon_sword    = Item("Dragon Sword",    "weapon", {"attack": 6},                price=40, tier=3)
tower_shield    = Item("Tower Shield",    "shield", {"defense": 6, "block_chance": 10}, price=38, tier=3)
ancient_amulet  = Item("Ancient Amulet",  "amulet", {"attack": 2, "defense": 2},  price=36, tier=3)

# ── Duskwall Equipment Tier 2 ─────────────────────────────────────────────────
mercenary_blade  = Item("Mercenary's Blade", "weapon", {"attack": 3},              price=8,  tier=2)
iron_mask        = Item("Iron Mask",         "head",   {"defense": 3, "hp": 2},    price=10, tier=2)
chain_vest       = Item("Chain Vest",        "body",   {"defense": 5},             price=12, tier=2)
studded_greaves  = Item("Studded Greaves",   "legs",   {"defense": 2},             price=7,  tier=2)
spiked_ring      = Item("Spiked Ring",       "ring",   {"attack": 1, "hp": 2},     price=8,  tier=2)
rusted_buckler   = Item("Rusted Buckler",    "shield", {"defense": 3, "block_chance": 10}, price=6,  tier=2)
bone_amulet      = Item("Bone Amulet",       "amulet", {"hp": 5},                  price=9,  tier=2)

# ── Duskwall Equipment Tier 3 ─────────────────────────────────────────────────
shadow_cloak       = Item("Shadow Cloak",        "body",   {"defense": 4, "flee_bonus": 0.15}, price=22, tier=3)
executioners_blade = Item("Executioner's Blade", "weapon", {"attack": 6},                      price=28, tier=3)
wardens_shield     = Item("Warden's Shield",     "shield", {"defense": 7, "block_chance": 10}, price=30, tier=3)
dead_mans_ring     = Item("Dead Man's Ring",      "ring",   {"hp": 6, "reflect": 0.15},         price=25, tier=3)
skull_helm         = Item("Skull Helm",           "head",   {"defense": 4, "hp": 5},            price=26, tier=3)
grave_walkers      = Item("Grave Walkers",        "legs",   {"defense": 3, "flee_bonus": 0.10}, price=24, tier=3)
cursed_pendant     = Item("Cursed Pendant",       "amulet", {"attack": 3, "defense": -1},       price=22, tier=3)

# ── Familiar Charms (slot="familiar", equip on familiar only) ─────────────────
worn_collar   = Item("Worn Collar",   "familiar", {"attack": 1},            price=4,  tier=1)
silver_charm  = Item("Silver Charm",  "familiar", {"attack": 2},            price=10, tier=2)
arcane_collar = Item("Arcane Collar", "familiar", {"attack": 3, "hp": 3},   price=18, tier=3)

# ── Consumables ───────────────────────────────────────────────────────────────
rations          = Item("Rations",          None, {}, 4,  consumable=True, use_effect={"food": 1})
potion           = Item("Potion",           None, {}, 15, consumable=True, use_effect={"heal": 10})
greater_potion   = Item("Greater Potion",   None, {}, 40, consumable=True, use_effect={"heal": 20})
antidote         = Item("Antidote",         None, {}, 20, consumable=True, use_effect={"cure": True})
smoke_bomb       = Item("Smoke Bomb",       None, {}, 25, consumable=True, use_effect={"flee": True})
sharpening_stone = Item("Sharpening Stone", None, {}, 30, consumable=True, use_effect={"buff_attack": 1})
iron_ration      = Item("Combat Rations",   None, {}, 8,  consumable=True, use_effect={"food": 3})

# ── Duskwall Consumables (cheaper scale for post-conversion economy) ───────────
field_potion    = Item("Field Potion",    None, {}, 3,  consumable=True, use_effect={"heal": 25})
field_ration    = Item("MRE",            None, {}, 1,  consumable=True, use_effect={"food": 1})
marked_tincture = Item("Marked Tincture",None, {}, 8,  consumable=True, use_effect={"heal": 9999, "cure_all": True})
bitter_root     = Item("Bitter Root",    None, {}, 2,  consumable=True, use_effect={"cure_poison": True})
smelling_salts  = Item("Smelling Salts", None, {}, 2,  consumable=True, use_effect={"cure_stun": True})
hex_ward        = Item("Hex Ward",       None, {}, 3,  consumable=True, use_effect={"cure_hex": True})

# ── Item registries ───────────────────────────────────────────────────────────
_restholm_equip = [
    rusty_sword, leather_helm, leather_body, leather_chaps, iron_ring, wood_shield, copper_amulet,
    iron_sword, iron_helm, iron_body, iron_chaps, life_ring, iron_shield, gold_amulet,
    boots_of_speed, thorn_ring, berserker_helm, mage_robe, dragon_sword, tower_shield, ancient_amulet,
]
_duskwall_equip = [
    mercenary_blade, iron_mask, chain_vest, studded_greaves, spiked_ring, rusted_buckler, bone_amulet,
    shadow_cloak, executioners_blade, wardens_shield, dead_mans_ring, skull_helm, grave_walkers, cursed_pendant,
]
_familiar_charms = [worn_collar, silver_charm, arcane_collar]
_consumables = [
    rations, potion, greater_potion, antidote, smoke_bomb, sharpening_stone, iron_ration,
    field_potion, field_ration, marked_tincture,
    bitter_root, smelling_salts, hex_ward,
]

_all = _restholm_equip + _duskwall_equip + _familiar_charms + _consumables

ALL_ITEMS             = {item.name: item for item in _all}
SHOP_POOL             = _restholm_equip          # Restholm shop equipment rotation
SHOP_CONSUMABLE_POOL  = [antidote, smoke_bomb, sharpening_stone]
DUSKWALL_SHOP_POOL    = _duskwall_equip          # Duskwall shop equipment rotation
DUSKWALL_PERM_SHOP_ITEMS = [field_ration, field_potion, marked_tincture,
                             bitter_root, smelling_salts, hex_ward]
FAMILIAR_ITEM_POOL    = _familiar_charms
