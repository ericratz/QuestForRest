'''
save.py
Save / load game state
'''

import json
import os
import glob
import data.items as items_module

_SAVE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saves")


def _save_path(slot):
    return os.path.join(_SAVE_DIR, f"save_{slot}.json")


def list_saves():
    saves = []
    for path in sorted(glob.glob(os.path.join(_SAVE_DIR, "save_*.json"))):
        try:
            slot = int(os.path.basename(path)[5:-5])
            with open(path) as f:
                data = json.load(f)
            saves.append((slot, data))
        except (ValueError, json.JSONDecodeError):
            pass
    return saves


def save_exists():
    return len(list_saves()) > 0


def save_game(wState, pState):
    os.makedirs(_SAVE_DIR, exist_ok=True)
    if wState.save_slot is None:
        used = {slot for slot, _ in list_saves()}
        wState.save_slot = next(i for i in range(1, 100) if i not in used)

    data = {
        "world": {
            "day":                          wState.day,
            "adventure_locations_unlocked": wState.adventure_locations_unlocked,
            "adventure_locations_complete": wState.adventure_locations_complete,
            "music_volume":                 wState.music_volume,
            "sfx_volume":                   wState.sfx_volume,
        },
        "player": {
            "name":             pState.name,
            "health":           pState.health,
            "base_max_health":  pState.base_max_health,
            "gold":             pState.gold,
            "base_attack":      pState.base_attack,
            "base_defense":     pState.base_defense,
            "level":            pState.level,
            "xp":               pState.xp,
            "food":             pState.food,
            "debt":             pState.debt,
            "kills":            pState.kills,
            "boss_kills":       pState.boss_kills,
            "kill_counts":      pState.kill_counts,
            "quests_complete":    list(pState.quests_complete),
            "quests_active":      list(pState.active_quests),
            "quests_snapshots":   pState.quest_snapshots,
            "quests_due_dates":   pState.quest_due_dates,
            "achievements_unlocked":   list(pState.achievements_unlocked),
            "survivalist_completions": pState.survivalist_completions,
            "consecutive_peaceful_rooms": pState.consecutive_peaceful_rooms,
            "total_spent_gold":        pState.total_spent_gold,
            "temp_attack_bonus":       pState.temp_attack_bonus,
            "status_effects":   pState.status_effects,
            "inventory":        [item.name for item in pState.inventory],
            "stash":            [item.name for item in pState.stash],
            "equipment":        {slot: (item.name if item else None)
                                 for slot, item in pState.equipment.items()},
        }
    }
    with open(_save_path(wState.save_slot), "w") as f:
        json.dump(data, f, indent=2)


def load_game(wState, pState, slot):
    try:
        with open(_save_path(slot)) as f:
            data = json.load(f)
        w = data["world"]
        p = data["player"]

        wState.day                          = w.get("day", 1)
        wState.adventure_locations_unlocked = w.get("adventure_locations_unlocked", 1)
        wState.adventure_locations_complete = w.get("adventure_locations_complete", [])
        wState.music_volume                 = w.get("music_volume", 0.5)
        wState.sfx_volume                   = w.get("sfx_volume",   0.5)
        wState.area      = "village"
        wState.save_slot = slot

        pState.name            = p.get("name", "")
        pState.health          = p.get("health", 20)
        pState.base_max_health = p.get("base_max_health", 20)
        pState.gold            = p.get("gold", 0)
        pState.base_attack     = p.get("base_attack", 1)
        pState.base_defense    = p.get("base_defense", 1)
        pState.level           = p.get("level", 1)
        pState.xp              = p.get("xp", 0)
        pState.food            = p.get("food", 5)
        pState.debt            = p.get("debt", 100)
        pState.kills           = p.get("kills", 0)
        pState.boss_kills      = p.get("boss_kills", 0)
        pState.kill_counts     = p.get("kill_counts", {})
        pState.quests_complete  = set(p.get("quests_complete",  []))
        pState.active_quests    = set(p.get("quests_active",    ["debt"]))
        pState.quest_snapshots  = p.get("quests_snapshots",     {})
        pState.quest_due_dates  = p.get("quests_due_dates",     {})
        pState.status_effects          = p.get("status_effects",           {})
        pState.achievements_unlocked        = set(p.get("achievements_unlocked", []))
        pState.survivalist_completions      = p.get("survivalist_completions",       0)
        pState.consecutive_peaceful_rooms   = p.get("consecutive_peaceful_rooms",    0)
        pState.total_spent_gold             = p.get("total_spent_gold",              0)
        pState.temp_attack_bonus       = p.get("temp_attack_bonus",         0)

        def resolve(name):
            return items_module.ALL_ITEMS.get(name)

        pState.inventory = [resolve(n) for n in p.get("inventory", []) if resolve(n)]
        pState.stash     = [resolve(n) for n in p.get("stash",     []) if resolve(n)]
        pState.equipment = {
            slot: resolve(name) if name else None
            for slot, name in p.get("equipment", {}).items()
        }
        # fill any missing slots (in case new slots were added)
        from state.gamestate import EQUIPMENT_SLOTS
        for slot in EQUIPMENT_SLOTS:
            if slot not in pState.equipment:
                pState.equipment[slot] = None

        return True
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        return False
