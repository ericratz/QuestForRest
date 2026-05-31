'''
data/passives.py
Passive skill definitions and milestone configuration.

Each passive has:
  name    — display name
  desc    — one-line description shown in the selection screen
  effect  — dict of effect keys used by PlayerState.passive_effect()
  tier    — 1 / 2 / 3 (matches milestone level // 5)

Effect keys used across the codebase:
  atk_bonus     int   added to get_attack()
  def_bonus     int   added to get_defense()
  hp_bonus      int   added to get_max_health()
  crit_bonus    int   added to get_crit_chance()  (%)
  block_bonus   int   added to get_block_chance() (%)
  berserker_atk int   added to get_attack() when HP < 50%
  lifesteal     int   HP healed per successful player attack
  second_wind   int   1 = can survive one lethal hit per adventure
  gold_mult     float fraction added to gold loot (0.30 = +30%)
  food_bonus    int   extra food from food rooms; also reduces Caverns entry cost
'''

PASSIVES = {

    # ── Tier 1 — unlocked at level 5 ──────────────────────────────────────────
    "iron_skin": {
        "name":   "Iron Skin",
        "desc":   "Permanently gain +2 Defense.",
        "effect": {"def_bonus": 2},
        "tier":   1,
    },
    "tracker": {
        "name":   "Tracker",
        "desc":   "+8% critical hit chance.",
        "effect": {"crit_bonus": 8},
        "tier":   1,
    },
    "forager": {
        "name":   "Forager",
        "desc":   "Food drops yield +1. Costs 1 less food to enter the Caverns.",
        "effect": {"food_bonus": 1},
        "tier":   1,
    },

    # ── Tier 2 — unlocked at level 10 ─────────────────────────────────────────
    "might": {
        "name":   "Might",
        "desc":   "Permanently gain +2 Attack.",
        "effect": {"atk_bonus": 2},
        "tier":   2,
    },
    "second_wind": {
        "name":   "Second Wind",
        "desc":   "Once per adventure, survive a lethal blow with 1 HP.",
        "effect": {"second_wind": 1},
        "tier":   2,
    },
    "prospector": {
        "name":   "Prospector",
        "desc":   "Gold drops from monsters are increased by 30%.",
        "effect": {"gold_mult": 0.30},
        "tier":   2,
    },

    # ── Tier 3 — unlocked at level 15 ─────────────────────────────────────────
    "berserker": {
        "name":   "Berserker",
        "desc":   "While below 50% HP, gain +4 Attack.",
        "effect": {"berserker_atk": 4},
        "tier":   3,
    },
    "lifesteal": {
        "name":   "Lifesteal",
        "desc":   "Heal 1 HP with each successful attack.",
        "effect": {"lifesteal": 1},
        "tier":   3,
    },
    "bulwark": {
        "name":   "Bulwark",
        "desc":   "+15% block chance.",
        "effect": {"block_bonus": 15},
        "tier":   3,
    },
}

# Options shown at each level milestone: list of 3 passive IDs to pick from.
MILESTONE_OPTIONS = {
    5:  ["iron_skin",  "tracker",     "forager"],
    10: ["might",      "second_wind", "prospector"],
    15: ["berserker",  "lifesteal",   "bulwark"],
}

MILESTONES = frozenset(MILESTONE_OPTIONS)   # {5, 10, 15}

# Base combat chances (percent) — before passives / equipment.
BASE_CRIT_CHANCE  = 5
BASE_BLOCK_CHANCE = 5
