'''
save.py
Handles saving and loading game state to disk
'''

import json
import os
import glob
import items as items_module

_SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saves")

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
        except (ValueError, json.JSONDecodeError, KeyError):
            pass
    return saves

def save_exists():
    return len(list_saves()) > 0

def save_game(wState, pState):
    if wState.save_slot is None:
        used = {slot for slot, _ in list_saves()}
        wState.save_slot = next(i for i in range(1, 100) if i not in used)
    data = {
        "world": {"day": wState.day},
        "player": {
            "health":       pState.health,
            "gold":         pState.gold,
            "base_attack":  pState.base_attack,
            "base_defense": pState.base_defense,
            "inventory":    [item.name for item in pState.inventory],
            "equipment":    {slot: (item.name if item else None)
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
        wState.day       = w["day"]
        wState.area      = "village"
        wState.save_slot = slot
        pState.health       = p["health"]
        pState.gold         = p["gold"]
        pState.base_attack  = p["base_attack"]
        pState.base_defense = p["base_defense"]
        pState.inventory    = [items_module.ALL_ITEMS[n] for n in p["inventory"]
                                if n in items_module.ALL_ITEMS]
        pState.equipment    = {s: (items_module.ALL_ITEMS.get(name) if name else None)
                                for s, name in p["equipment"].items()}
        return True
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        return False
