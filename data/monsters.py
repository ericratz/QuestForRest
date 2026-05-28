'''
monsters.py
Monster definitions and combat math
'''

import random
import data.items as items_module


class Monster:
    def __init__(self, name, tier, hp, attack, defense, xp, gold_min, gold_max,
                 item_chance=0.25, status_effects=None):
        self.name           = name
        self.tier           = tier      # 1=normal, 2=wanderer, 3=boss
        self.max_hp         = hp
        self.hp             = hp
        self.attack         = attack
        self.defense        = defense
        self.xp             = xp
        self.gold_min       = gold_min
        self.gold_max       = gold_max
        self.item_chance    = item_chance
        # list of (effect_name, chance, duration); duration -1 = permanent
        self.status_effects = status_effects or []

    def copy(self):
        m = Monster(self.name, self.tier, self.max_hp, self.attack, self.defense,
                    self.xp, self.gold_min, self.gold_max, self.item_chance,
                    list(self.status_effects))
        return m

    def roll_loot(self):
        gold = random.randint(self.gold_min, self.gold_max)
        item = None
        if random.random() < self.item_chance:
            loot_tier = 2 if self.tier == 3 else 1
            pool = [i for i in items_module.ALL_ITEMS.values()
                    if not i.consumable and i.tier == loot_tier]
            if pool:
                item = random.choice(pool)
        return gold, item


# ── Tier 1: Normal ────────────────────────────────────────────────────────────
goblin   = Monster("Goblin",   1,  8,  3, 1,  5,  1,  5, 0.20,
                   status_effects=[("weakened", 0.25, 3)])
imp      = Monster("Imp",      1,  6,  4, 0,  5,  1,  3, 0.15,
                   status_effects=[("poison", 0.30, 3)])
skeleton = Monster("Skeleton", 1, 10,  2, 3,  6,  1,  5, 0.25)
cow      = Monster("Cow",      1, 15,  1, 2,  4,  2,  8, 0.10)
unicorn  = Monster("Unicorn",  1, 12,  3, 3,  8,  5, 10, 0.35)

# ── Tier 2: Wanderers ─────────────────────────────────────────────────────────
wanderer = Monster("Wanderer", 2, 22,  5, 3, 15,  5, 15, 0.40)
dark_elf = Monster("Dark Elf", 2, 18,  6, 2, 15,  5, 12, 0.45,
                   status_effects=[("weakened", 0.30, 3)])

# ── Tier 3: Bosses ────────────────────────────────────────────────────────────
hill_giant  = Monster("Hill Giant",  3, 45,  8, 4, 50, 20, 40, 0.70,
                      status_effects=[("stunned", 0.20, 1)])
dark_wizard = Monster("Dark Wizard", 3, 35, 10, 2, 50, 20, 40, 0.70,
                      status_effects=[("poison", 0.40, 3), ("weakened", 0.30, 3)])

NORMAL_POOL   = [goblin, imp, skeleton, cow, unicorn]
WANDERER_POOL = [wanderer, dark_elf]
BOSS_POOL     = [hill_giant, dark_wizard]


def spawn(tier, boss_index=0):
    if tier == 1:
        return random.choice(NORMAL_POOL).copy()
    elif tier == 2:
        return random.choice(WANDERER_POOL).copy()
    else:
        return BOSS_POOL[boss_index % len(BOSS_POOL)].copy()


def calc_damage(atk, def_):
    '''atk² / (atk + def), ±20% random variance, minimum 1'''
    raw = atk ** 2 / max(1, atk + def_)
    return max(1, int(raw * random.uniform(0.8, 1.2)))
