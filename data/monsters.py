'''
monsters.py
Monster definitions and combat math
'''

import random
import data.items as items_module


class Monster:
    def __init__(self, name, tier, hp, attack, defense, xp_min, xp_max,
                 gold_min, gold_max, item_chance=0.25, status_effects=None,
                 description=""):
        self.name           = name
        self.tier           = tier      # 1=normal, 2=wanderer, 3=boss
        self.max_hp         = hp
        self.hp             = hp
        self.attack         = attack
        self.defense        = defense
        self.xp_min         = xp_min
        self.xp_max         = xp_max
        self.gold_min       = gold_min
        self.gold_max       = gold_max
        self.item_chance    = item_chance
        # list of (effect_name, chance, duration); duration -1 = permanent
        self.status_effects = status_effects or []
        self.description    = description

    def copy(self):
        m = Monster(self.name, self.tier, self.max_hp, self.attack, self.defense,
                    self.xp_min, self.xp_max, self.gold_min, self.gold_max,
                    self.item_chance, list(self.status_effects), self.description)
        return m

    def roll_xp(self):
        return random.randint(self.xp_min, self.xp_max)

    def roll_loot(self):
        gold = random.randint(self.gold_min, self.gold_max)
        item = None
        if random.random() < self.item_chance:
            loot_tier = self.tier   # tier 1 → t1 items, tier 2 → t2 items
            pool = [i for i in items_module.SHOP_POOL
                    if i.tier == loot_tier and i.slot != "familiar"]
            if pool:
                item = random.choice(pool)
        return gold, item

    def roll_boss_loot(self, loot_tier, pool):
        '''Boss-specific 3-way loot roll (always called for tier-3 monsters).
        Outcome 1: two items of loot_tier, no gold.
        Outcome 2: one item of loot_tier + medium gold (gold_max – gold_max*2).
        Outcome 3: high gold only (gold_max*2 – gold_max*4), no items.
        Falls back to high gold if the pool has no matching items.
        '''
        item_pool = [i for i in pool if i.tier == loot_tier and i.slot != "familiar"]
        roll = random.randint(1, 3)
        if roll == 1 and item_pool:   # two items
            return 0, [random.choice(item_pool), random.choice(item_pool)]
        elif roll == 2 and item_pool:  # one item + standard gold
            return random.randint(self.gold_min, self.gold_max), [random.choice(item_pool)]
        else:                          # gold only (capped at 2× gold_max)
            return random.randint(self.gold_max, self.gold_max * 2), []

    def roll_duskwall_loot(self):
        '''Like roll_loot, but drops Duskwall-tier items; bosses can drop familiar charms.'''
        gold = random.randint(self.gold_min, self.gold_max)
        item = None
        if random.random() < self.item_chance:
            charm_chance = 0.30 if self.tier == 3 else 0.08
            if random.random() < charm_chance:
                charm_tier = 3 if self.tier == 3 else 2
                charm_pool = [i for i in items_module.FAMILIAR_ITEM_POOL if i.tier <= charm_tier]
                if charm_pool:
                    return gold, random.choice(charm_pool)
            loot_tier = 3 if self.tier == 3 else 2
            pool = [i for i in items_module.DUSKWALL_SHOP_POOL if i.tier == loot_tier]
            if not pool:
                pool = list(items_module.DUSKWALL_SHOP_POOL)
            if pool:
                item = random.choice(pool)
        return gold, item


# ── Restholm Tier 1: Normal ───────────────────────────────────────────────────
goblin   = Monster("Goblin",   1,  8, 3, 1,  3,  6,  1,  5, 0.20,
                   status_effects=[("weakened", 0.25, 3)],
                   description="A small, green-skinned creature with a rusty blade. Mean-spirited and unpredictable.")
imp      = Monster("Imp",      1,  6, 4, 0,  3,  6,  1,  4, 0.15,
                   status_effects=[("poison", 0.30, 3)],
                   description="A winged demon that darts and bites with venomous precision.")
skeleton = Monster("Skeleton", 1, 10, 2, 3,  3,  6,  1,  5, 0.25,
                   description="Animated bones marching forward by old magic alone. It feels no pain.")
cow      = Monster("Cow",      1, 15, 1, 2,  3,  6,  2,  8, 0.10,
                   description="A large, deeply unsettled cow. You're not sure how it got here.")
unicorn  = Monster("Unicorn",  1, 12, 2, 2,  3,  6,  3, 10, 0.20,
                   description="Its coat has gone grey. Whatever this was, it isn't anymore.")

# ── Restholm Tier 2: Wanderers ────────────────────────────────────────────────
wanderer = Monster("Wanderer", 2, 15, 4, 3,  6, 15,  5, 15, 0.40,
                   description="A road-hardened stranger with a blade and no interest in talking.")
dark_elf = Monster("Dark Elf", 2, 18, 3, 4,  6, 15,  5, 12, 0.45,
                   status_effects=[("weakened", 0.30, 3)],
                   description="Quick and cruel. It would rather leave you weakened than dead — at first.")

# ── Restholm Tier 3: Bosses ───────────────────────────────────────────────────
hill_giant  = Monster("Hill Giant",  3, 30,  6, 6, 25, 50, 25, 40, 0.70,
                      status_effects=[("stunned", 0.25, 1)],
                      description="Each step shakes the ground. This thing hits like a falling tree.")
dark_wizard = Monster("Dark Wizard", 3, 20,  8, 3, 20, 40, 20, 30, 0.70,
                      status_effects=[("poison", 0.50, 3), ("weakened", 0.40, 3)],
                      description="Robed in shadow and spite. The poison is intentional. So is everything else.")

# ── Duskwall Tier 1: Outer Ruins ──────────────────────────────────────────────
crumbled_knight = Monster("Crumbled Knight", 1, 25, 3,  7, 10, 18, 2, 6, 0.12,
                          description="Old armor with something still inside it, driven by forgotten duty.")
feral_hound     = Monster("Feral Hound",     1, 20, 6,  4, 10, 15, 2, 5, 0.07,
                          status_effects=[("weakened", 0.30, 2)],
                          description="A wild dog warped by the ruins. It tears at whatever it can reach.")
plague_rat      = Monster("Plague Rat",      1, 16, 4,  4,  8, 14, 1, 3, 0.05,
                          status_effects=[("poison", 0.55, 3)],
                          description="Diseased and desperate. The bite is the least of your worries.")
grave_robber    = Monster("Grave Robber",    1, 20, 5,  5, 10, 18, 2, 6, 0.12,
                          description="A scavenger gone feral. Knows these ruins better than you do.")

# ── Duskwall Tier 2: Wanderers ────────────────────────────────────────────────
shadow_elf   = Monster("Shadow Elf",   2, 28,  8, 6, 15, 25, 5, 12, 0.20,
                       status_effects=[("stunned", 0.30, 1)],
                       description="A Duskwall elf soaked in curse-craft. The stun hits before you see it coming.")
thorny_devil = Monster("Thorny Devil", 2, 30, 10, 4, 15, 25, 5, 12, 0.20,
                       description="A barbed lizard that shreds with every hit. Moving carefully doesn't help.")

# ── Duskwall Tier 3: Bosses ───────────────────────────────────────────────────
ruins_guardian = Monster("Ruins Guardian", 3,  50,  6, 24,  60, 120, 20, 40, 0.70,
                         status_effects=[("poison", 0.35, 3)],
                         description="Heavy, relentless, and furious. Whatever it was built to protect, it still is.")
death_knight   = Monster("Death Knight",   3,  60, 15, 10,  80, 150, 30, 55, 0.70,
                         status_effects=[("weakened", 0.30, 3), ("poison", 0.35, 3), ("stunned", 0.40, 1)],
                         description="An undead knight bound by a will not its own. It has killed many times before.")

# ── Pools ─────────────────────────────────────────────────────────────────────
NORMAL_POOL   = [goblin, imp, skeleton, cow, unicorn]
WANDERER_POOL = [wanderer, dark_elf]
BOSS_POOL     = [hill_giant, dark_wizard]

DUSKWALL_NORMAL_POOL   = [crumbled_knight, feral_hound, plague_rat, grave_robber]
DUSKWALL_WANDERER_POOL = [shadow_elf, thorny_devil]
DUSKWALL_BOSS_POOL     = [ruins_guardian, death_knight]


def spawn(tier, boss_index=0):
    '''Spawn a Restholm monster.'''
    if tier == 1:
        return random.choice(NORMAL_POOL).copy()
    elif tier == 2:
        return random.choice(WANDERER_POOL).copy()
    else:
        return BOSS_POOL[boss_index % len(BOSS_POOL)].copy()


def duskwall_spawn(tier, boss_index=0):
    '''Spawn a Duskwall monster.'''
    if tier == 1:
        return random.choice(DUSKWALL_NORMAL_POOL).copy()
    elif tier == 2:
        return random.choice(DUSKWALL_WANDERER_POOL).copy()
    else:
        return DUSKWALL_BOSS_POOL[boss_index % len(DUSKWALL_BOSS_POOL)].copy()


def calc_damage(atk, def_):
    '''atk² / (atk + def), ±20% random variance, minimum 1'''
    raw = atk ** 2 / max(1, atk + def_)
    return max(1, int(raw * random.uniform(0.8, 1.2)))
