'''
tests/test_save_load.py
Round-trip tests for save_game / load_game.
Uses a temporary save directory so tests never touch real saves.
'''

import os
import json
import pytest
from state.gamestate import WorldState, PlayerState
import state.save as save_module
import data.items as items_module


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def tmp_save_dir(tmp_path, monkeypatch):
    '''Redirect the save directory to a temp location for every test.'''
    monkeypatch.setattr(save_module, "_SAVE_DIR", str(tmp_path))
    # Also patch _save_path to use tmp_path
    def _tmp_save_path(slot):
        return os.path.join(str(tmp_path), f"save_{slot}.json")
    monkeypatch.setattr(save_module, "_save_path", _tmp_save_path)
    return tmp_path


@pytest.fixture
def world():
    w = WorldState()
    w.reset("village")
    return w

@pytest.fixture
def player():
    return PlayerState()


# ── Basic round-trip ──────────────────────────────────────────────────────────

def test_save_creates_file(world, player, tmp_path):
    world.save_slot = 1
    save_module.save_game(world, player)
    assert os.path.exists(os.path.join(str(tmp_path), "save_1.json"))

def test_save_load_day(world, player):
    world.day = 7
    world.save_slot = 1
    save_module.save_game(world, player)
    w2, p2 = WorldState(), PlayerState()
    assert save_module.load_game(w2, p2, 1)
    assert w2.day == 7

def test_save_load_player_name(world, player):
    player.name = "Aldric"
    world.save_slot = 1
    save_module.save_game(world, player)
    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, 1)
    assert p2.name == "Aldric"

def test_save_load_gold(world, player):
    player.gold = 250
    world.save_slot = 1
    save_module.save_game(world, player)
    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, 1)
    assert p2.gold == 250

def test_save_load_health(world, player):
    player.health = 13
    world.save_slot = 1
    save_module.save_game(world, player)
    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, 1)
    assert p2.health == 13

def test_save_load_level_and_xp(world, player):
    player.level = 4
    player.xp = 22
    world.save_slot = 1
    save_module.save_game(world, player)
    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, 1)
    assert p2.level == 4
    assert p2.xp == 22

def test_save_load_debt(world, player):
    player.debt = 75
    world.save_slot = 1
    save_module.save_game(world, player)
    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, 1)
    assert p2.debt == 75

def test_save_load_kills(world, player):
    player.kills = 12
    player.boss_kills = 1
    world.save_slot = 1
    save_module.save_game(world, player)
    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, 1)
    assert p2.kills == 12
    assert p2.boss_kills == 1


# ── Passives round-trip ───────────────────────────────────────────────────────

def test_save_load_chosen_passives(world, player):
    player.chosen_passives = ["iron_skin", "might"]
    world.save_slot = 1
    save_module.save_game(world, player)
    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, 1)
    assert p2.chosen_passives == ["iron_skin", "might"]

def test_save_load_passive_milestones_done(world, player):
    player.passive_milestones_done = {5, 10}
    world.save_slot = 1
    save_module.save_game(world, player)
    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, 1)
    assert p2.passive_milestones_done == {5, 10}

def test_passive_milestones_done_is_a_set_after_load(world, player):
    player.passive_milestones_done = {5}
    world.save_slot = 1
    save_module.save_game(world, player)
    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, 1)
    assert isinstance(p2.passive_milestones_done, set)


# ── Duskwall unlock round-trip ────────────────────────────────────────────────

def test_save_load_duskwall_unlocked_true(world, player):
    world.duskwall_unlocked = True
    world.save_slot = 1
    save_module.save_game(world, player)
    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, 1)
    assert w2.duskwall_unlocked is True

def test_save_load_duskwall_unlocked_false(world, player):
    world.duskwall_unlocked = False
    world.save_slot = 1
    save_module.save_game(world, player)
    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, 1)
    assert w2.duskwall_unlocked is False


# ── Inventory / equipment round-trip ─────────────────────────────────────────

def test_save_load_inventory(world, player):
    potion = items_module.ALL_ITEMS["Potion"]
    player.inventory = [potion]
    world.save_slot = 1
    save_module.save_game(world, player)
    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, 1)
    assert len(p2.inventory) == 1
    assert p2.inventory[0].name == "Potion"

def test_save_load_equipment(world, player):
    rusty = items_module.ALL_ITEMS["Rusty Sword"]
    player.equipment["weapon"] = rusty
    world.save_slot = 1
    save_module.save_game(world, player)
    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, 1)
    assert p2.equipment["weapon"] is not None
    assert p2.equipment["weapon"].name == "Rusty Sword"

def test_save_load_equipment_empty_slots(world, player):
    world.save_slot = 1
    save_module.save_game(world, player)
    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, 1)
    from state.gamestate import EQUIPMENT_SLOTS
    for slot in EQUIPMENT_SLOTS:
        assert slot in p2.equipment


# ── Status effects ────────────────────────────────────────────────────────────

def test_save_load_status_effects(world, player):
    player.status_effects = {"poisoned": 3, "cursed": -1}
    world.save_slot = 1
    save_module.save_game(world, player)
    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, 1)
    assert p2.status_effects == {"poisoned": 3, "cursed": -1}


# ── Missing field defaults ────────────────────────────────────────────────────

def test_load_missing_chosen_passives_defaults_to_empty(world, player, tmp_path):
    '''Simulate an old save file that has no chosen_passives field.'''
    world.save_slot = 1
    save_module.save_game(world, player)
    path = os.path.join(str(tmp_path), "save_1.json")
    with open(path) as f:
        data = json.load(f)
    del data["player"]["chosen_passives"]
    with open(path, "w") as f:
        json.dump(data, f)

    w2, p2 = WorldState(), PlayerState()
    assert save_module.load_game(w2, p2, 1)
    assert p2.chosen_passives == []

def test_load_missing_duskwall_unlocked_defaults_false(world, player, tmp_path):
    '''Simulate an old save that has no duskwall_unlocked field.'''
    world.save_slot = 1
    save_module.save_game(world, player)
    path = os.path.join(str(tmp_path), "save_1.json")
    with open(path) as f:
        data = json.load(f)
    del data["world"]["duskwall_unlocked"]
    with open(path, "w") as f:
        json.dump(data, f)

    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, 1)
    assert w2.duskwall_unlocked is False

def test_load_missing_passive_milestones_defaults_empty_set(world, player, tmp_path):
    world.save_slot = 1
    save_module.save_game(world, player)
    path = os.path.join(str(tmp_path), "save_1.json")
    with open(path) as f:
        data = json.load(f)
    del data["player"]["passive_milestones_done"]
    with open(path, "w") as f:
        json.dump(data, f)

    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, 1)
    assert p2.passive_milestones_done == set()


# ── load_game return value ────────────────────────────────────────────────────

def test_load_nonexistent_returns_false(world, player):
    w2, p2 = WorldState(), PlayerState()
    result = save_module.load_game(w2, p2, 99)
    assert result is False

def test_load_corrupted_json_returns_false(tmp_path):
    path = os.path.join(str(tmp_path), "save_1.json")
    with open(path, "w") as f:
        f.write("{not valid json")
    w2, p2 = WorldState(), PlayerState()
    result = save_module.load_game(w2, p2, 1)
    assert result is False


# ── Auto slot assignment ──────────────────────────────────────────────────────

def test_save_assigns_slot_if_none(world, player):
    world.save_slot = None
    save_module.save_game(world, player)
    assert world.save_slot is not None

def test_save_uses_existing_slot(world, player, tmp_path):
    world.save_slot = 3
    save_module.save_game(world, player)
    assert os.path.exists(os.path.join(str(tmp_path), "save_3.json"))


# ── Duskwall new fields ───────────────────────────────────────────────────────

def test_save_load_duskwall_currency_converted(world, player):
    world.duskwall_currency_converted = True
    save_module.save_game(world, player)
    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, world.save_slot)
    assert w2.duskwall_currency_converted is True

def test_save_load_duskwall_currency_converted_false(world, player):
    world.duskwall_currency_converted = False
    save_module.save_game(world, player)
    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, world.save_slot)
    assert w2.duskwall_currency_converted is False

def test_save_load_duskwall_locations_unlocked(world, player):
    world.duskwall_locations_unlocked = 2
    save_module.save_game(world, player)
    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, world.save_slot)
    assert w2.duskwall_locations_unlocked == 2


# ── Familiar save/load ────────────────────────────────────────────────────────

def test_save_load_familiar_found(world, player):
    player.familiar.found = True
    player.familiar.name  = "Luna"
    save_module.save_game(world, player)
    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, world.save_slot)
    assert p2.familiar.found is True
    assert p2.familiar.name == "Luna"

def test_save_load_familiar_level_and_xp(world, player):
    player.familiar.level = 3
    player.familiar.xp    = 42
    save_module.save_game(world, player)
    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, world.save_slot)
    assert p2.familiar.level == 3
    assert p2.familiar.xp    == 42

def test_save_load_familiar_equipment(world, player):
    charm = items_module.ALL_ITEMS['Worn Collar']
    player.familiar.equipment = charm
    save_module.save_game(world, player)
    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, world.save_slot)
    assert p2.familiar.equipment is not None
    assert p2.familiar.equipment.name == "Worn Collar"

def test_save_load_familiar_no_equipment(world, player):
    player.familiar.equipment = None
    save_module.save_game(world, player)
    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, world.save_slot)
    assert p2.familiar.equipment is None

def test_load_old_save_missing_familiar_fields_defaults_safely(world, player, tmp_path):
    '''Old saves without familiar block should not crash and give fresh FamiliarState.'''
    save_module.save_game(world, player)
    path = os.path.join(str(tmp_path), f"save_{world.save_slot}.json")
    with open(path) as f:
        data = json.load(f)
    data["player"].pop("familiar", None)
    with open(path, "w") as f:
        json.dump(data, f)
    w2, p2 = WorldState(), PlayerState()
    assert save_module.load_game(w2, p2, world.save_slot)
    assert not p2.familiar.found
    assert p2.familiar.name == ""


# ── New session fields: temp bonuses and status_effect_cooldowns ──────────────

def test_save_load_temp_defense_bonus(world, player):
    player.temp_defense_bonus = 2
    world.save_slot = 1
    save_module.save_game(world, player)
    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, 1)
    assert p2.temp_defense_bonus == 2

def test_save_load_temp_max_health_bonus(world, player):
    player.temp_max_health_bonus = 3
    world.save_slot = 1
    save_module.save_game(world, player)
    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, 1)
    assert p2.temp_max_health_bonus == 3

def test_save_load_status_effect_cooldowns(world, player):
    player.status_effect_cooldowns = {"poison": 4, "cursed": 2}
    world.save_slot = 1
    save_module.save_game(world, player)
    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, 1)
    assert p2.status_effect_cooldowns == {"poison": 4, "cursed": 2}

def test_save_load_status_effect_cooldowns_empty(world, player):
    player.status_effect_cooldowns = {}
    world.save_slot = 1
    save_module.save_game(world, player)
    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, 1)
    assert p2.status_effect_cooldowns == {}

def test_load_missing_temp_defense_bonus_defaults_to_zero(world, player, tmp_path):
    '''Old saves without temp_defense_bonus should load cleanly as 0.'''
    world.save_slot = 1
    save_module.save_game(world, player)
    path = os.path.join(str(tmp_path), "save_1.json")
    with open(path) as f:
        data = json.load(f)
    data["player"].pop("temp_defense_bonus", None)
    with open(path, "w") as f:
        json.dump(data, f)
    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, 1)
    assert p2.temp_defense_bonus == 0

def test_load_missing_temp_max_health_bonus_defaults_to_zero(world, player, tmp_path):
    '''Old saves without temp_max_health_bonus should load cleanly as 0.'''
    world.save_slot = 1
    save_module.save_game(world, player)
    path = os.path.join(str(tmp_path), "save_1.json")
    with open(path) as f:
        data = json.load(f)
    data["player"].pop("temp_max_health_bonus", None)
    with open(path, "w") as f:
        json.dump(data, f)
    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, 1)
    assert p2.temp_max_health_bonus == 0

def test_load_missing_status_effect_cooldowns_defaults_empty(world, player, tmp_path):
    '''Old saves without status_effect_cooldowns should load cleanly as {}.'''
    world.save_slot = 1
    save_module.save_game(world, player)
    path = os.path.join(str(tmp_path), "save_1.json")
    with open(path) as f:
        data = json.load(f)
    data["player"].pop("status_effect_cooldowns", None)
    with open(path, "w") as f:
        json.dump(data, f)
    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, 1)
    assert p2.status_effect_cooldowns == {}

def test_temp_bonuses_zero_on_fresh_load(world, player):
    '''Temp bonuses should default to 0 — they are adventure-session-only.'''
    world.save_slot = 1
    save_module.save_game(world, player)
    w2, p2 = WorldState(), PlayerState()
    save_module.load_game(w2, p2, 1)
    assert p2.temp_attack_bonus     == 0
    assert p2.temp_defense_bonus    == 0
    assert p2.temp_max_health_bonus == 0
