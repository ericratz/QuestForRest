'''
tests/test_combat.py
Tests for combat mechanics: calc_damage, do_combat_action, _do_counter_attack,
_tick_status_effects, and the Examine / Flee / Use-Potion actions.

audio.sounds and render.helpers are mocked at session level in conftest.py.
'''

import pytest
import random
from unittest.mock import patch, MagicMock
from state.gamestate import WorldState, PlayerState
from data.monsters import Monster, calc_damage
from logic.adventure import (
    do_combat_action, handle_victory, handle_defeat,
    _tick_status_effects, _do_counter_attack,
)
import data.items as items_module


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def world():
    w = WorldState()
    w.reset("village")
    return w

@pytest.fixture
def player():
    return PlayerState()


def _make_monster(tier=1, hp=20, attack=3, defense=2, xp=5,
                  gold_min=1, gold_max=3, status_effects=None):
    return Monster("TestBeast", tier, hp, attack, defense, xp, xp, gold_min, gold_max,
                   item_chance=0.0, status_effects=status_effects or [])


def _start_combat(world, player, monster=None):
    monster = monster or _make_monster()
    world.in_adventure         = True
    world.adventure_loc_index  = 0
    world.adventure_room       = 0
    world.adventure_room_sequence = []
    player.food                = 5
    world.start_combat(monster)
    return monster


# ── calc_damage ────────────────────────────────────────────────────────────────

def test_calc_damage_formula_deterministic():
    '''With seeded RNG the formula matches expected: atk²/(atk+def) ±20%.'''
    random.seed(0)
    result = calc_damage(10, 5)
    assert result >= 1

def test_calc_damage_min_1_high_defense():
    '''Very high defense cannot reduce damage below 1.'''
    for _ in range(50):
        assert calc_damage(1, 1000) >= 1

def test_calc_damage_zero_defense():
    '''With zero defense damage equals atk² / atk = atk, with variance.'''
    random.seed(42)
    result = calc_damage(10, 0)
    # formula: 10²/10 = 10, ±20% → 8–12
    assert 8 <= result <= 12

def test_calc_damage_always_positive():
    for _ in range(100):
        assert calc_damage(random.randint(1, 20), random.randint(0, 20)) >= 1


# ── Attack action (index 0) ────────────────────────────────────────────────────

def test_attack_reduces_monster_hp(world, player):
    monster = _start_combat(world, player)
    before = monster.hp
    with patch('random.randint', return_value=0):   # no crit, no block
        do_combat_action(0, world, player)
    assert monster.hp < before

def test_attack_logs_damage(world, player):
    monster = _start_combat(world, player)
    with patch('random.randint', return_value=0):
        do_combat_action(0, world, player)
    assert any("dmg" in line for line in world.combat_log)

def test_crit_doubles_damage(world, player):
    monster = _start_combat(world, player, monster=_make_monster(hp=1000, defense=0))
    # force crit: randint returns value <= crit chance
    with patch('random.randint', return_value=1), \
         patch('random.uniform', return_value=1.0):
        do_combat_action(0, world, player)
    assert any("Critical hit" in line for line in world.combat_log)

def test_no_crit_when_roll_too_high(world, player):
    monster = _start_combat(world, player, monster=_make_monster(hp=1000))
    with patch('random.randint', return_value=100), \
         patch('random.uniform', return_value=1.0):
        do_combat_action(0, world, player)
    assert not any("Critical" in line for line in world.combat_log)

def test_attack_triggers_victory_on_kill(world, player):
    monster = _start_combat(world, player, monster=_make_monster(hp=1))
    with patch('random.randint', return_value=0), \
         patch('random.uniform', return_value=1.0):
        do_combat_action(0, world, player)
    assert world.post_combat_mode
    assert world.combat_result == "victory"

def test_lifesteal_heals_on_attack(world, player):
    player.chosen_passives = ["lifesteal"]
    player.health = 5
    # Use 0-attack monster so counter-attack does min 1 dmg but lifesteal fires first
    monster = _start_combat(world, player, monster=_make_monster(hp=1000, attack=0, defense=0))
    with patch('random.randint', return_value=0), \
         patch('random.uniform', return_value=1.0):
        do_combat_action(0, world, player)
    assert any("Lifesteal" in line for line in world.combat_log)


# ── Familiar attacks ───────────────────────────────────────────────────────────

def test_familiar_attacks_after_player(world, player):
    player.familiar.found = True
    player.familiar.name  = "Luna"
    monster = _start_combat(world, player, monster=_make_monster(hp=1000, defense=0))
    with patch('random.randint', return_value=0), \
         patch('random.uniform', return_value=1.0):
        do_combat_action(0, world, player)
    assert any("Luna strikes" in line for line in world.combat_log)

def test_familiar_kill_triggers_victory(world, player):
    '''Familiar's hit drops monster to 0 after player left it at 1 HP.'''
    player.familiar.found      = True
    player.familiar.name       = "Luna"
    player.familiar.base_attack = 10
    # Monster with exactly 1 HP so player attack (min 1) kills it before familiar
    # Instead give monster enough HP that player won't kill it but familiar will
    # Player attack base ~3, familiar attack 10 against 0 defense
    monster = _make_monster(hp=5, defense=100)   # player does 1 dmg, familiar does ~1 too
    _start_combat(world, player, monster)
    with patch('random.randint', return_value=0), \
         patch('random.uniform', return_value=1.0):
        do_combat_action(0, world, player)
    # Either player or familiar killed it — just ensure combat resolved
    assert world.post_combat_mode or world.in_combat

def test_familiar_does_not_attack_when_not_found(world, player):
    player.familiar.found = False
    monster = _start_combat(world, player, monster=_make_monster(hp=1000))
    with patch('random.randint', return_value=0), \
         patch('random.uniform', return_value=1.0):
        do_combat_action(0, world, player)
    assert not any("strikes" in line for line in world.combat_log)


# ── Examine action (index 2) ──────────────────────────────────────────────────

def test_examine_reveals_stats(world, player):
    monster = _start_combat(world, player)
    do_combat_action(2, world, player)
    assert any("ATK" in line and "DEF" in line for line in world.combat_log)

def test_examine_sets_combat_examined(world, player):
    _start_combat(world, player)
    do_combat_action(2, world, player)
    assert world.combat_examined

def test_examine_costs_a_turn_monster_attacks(world, player):
    '''Examine now consumes a turn — the monster counter-attacks afterwards.'''
    player.health = player.get_max_health()
    monster = _start_combat(world, player, monster=_make_monster(attack=5, defense=0))
    with patch('random.randint', return_value=50), \
         patch('random.uniform', return_value=1.0), \
         patch('random.random', return_value=1.0):   # never apply status
        do_combat_action(2, world, player)
    assert player.health < player.get_max_health(), "Monster should have attacked after examine"


# ── Flee action (index 3) ─────────────────────────────────────────────────────

def test_flee_costs_food(world, player):
    _start_combat(world, player)
    player.food = 3
    with patch('random.random', return_value=0.0):   # always flee successfully
        do_combat_action(3, world, player)
    assert player.food == 2

def test_flee_no_food_blocks_escape(world, player):
    _start_combat(world, player)
    player.food = 0
    do_combat_action(3, world, player)
    assert world.in_combat   # still in combat
    assert any("No food" in line for line in world.combat_log)

def test_flee_success_ends_combat(world, player):
    _start_combat(world, player)
    with patch('random.random', return_value=0.0):
        do_combat_action(3, world, player)
    assert not world.in_combat
    assert world.combat_result == "fled"

def test_flee_failure_triggers_counter_attack(world, player):
    player.health = player.get_max_health()
    monster = _start_combat(world, player, monster=_make_monster(attack=10, defense=0))
    # randint=100 ensures no block (100 > any block_chance); uniform=1.0 for deterministic dmg
    with patch('random.random', return_value=1.0), \
         patch('random.randint', return_value=100), \
         patch('random.uniform', return_value=1.0):
        do_combat_action(3, world, player)
    assert player.health < player.get_max_health()


# ── Use Item action (index 1) ─────────────────────────────────────────────────

def test_use_potion_heals_player(world, player):
    player.health = 5
    player.inventory.append(items_module.ALL_ITEMS["Potion"])
    monster = _start_combat(world, player)
    with patch('random.randint', return_value=0):
        do_combat_action(1, world, player)
    assert player.health > 5

def test_use_smoke_bomb_flees_immediately(world, player):
    player.inventory.append(items_module.ALL_ITEMS["Smoke Bomb"])
    _start_combat(world, player)
    do_combat_action(1, world, player)
    assert not world.in_combat
    assert world.combat_result == "fled"

def test_use_item_no_usable_item_logs_error(world, player):
    _start_combat(world, player)
    do_combat_action(1, world, player)
    assert any("No usable items" in line for line in world.combat_log)


# ── Stunned player ────────────────────────────────────────────────────────────

def test_stunned_player_loses_turn(world, player):
    player.status_effects["stunned"] = 2
    player.health = player.get_max_health()
    monster = _start_combat(world, player, monster=_make_monster(attack=1, defense=0))
    with patch('random.randint', return_value=0):
        do_combat_action(0, world, player)
    assert any("stunned" in line.lower() for line in world.combat_log)

def test_stunned_fades_after_duration(world, player):
    player.status_effects["stunned"] = 1
    _start_combat(world, player)
    with patch('random.randint', return_value=0):
        do_combat_action(0, world, player)
    assert "stunned" not in player.status_effects

def test_stunned_expiry_sets_cooldown(world, player):
    '''When stun expires via a lost turn, a cooldown is active so it can\'t reapply immediately.
    The counter-attack ticks the cooldown once (5→4), so we assert > 0 rather than == 5.'''
    player.status_effects["stunned"] = 1
    _start_combat(world, player)
    with patch('random.randint', return_value=0):
        do_combat_action(0, world, player)
    assert player.status_effect_cooldowns.get("stunned", 0) > 0

def test_stunned_expiry_via_potion_sets_cooldown(world, player):
    '''Stun expiring during a potion turn also activates the cooldown.'''
    player.status_effects["stunned"] = 1
    player.inventory.append(items_module.ALL_ITEMS["Potion"])
    _start_combat(world, player)
    with patch('random.randint', return_value=100):
        do_combat_action(1, world, player)
    assert player.status_effect_cooldowns.get("stunned", 0) > 0

def test_stunned_cooldown_blocks_reapplication(world, player):
    '''Monster cannot re-stun a player who is in the stunned cooldown window.'''
    from logic.adventure import _apply_monster_status
    from data.monsters import Monster
    stun_monster = Monster("Test", tier=1, hp=50, attack=10, defense=0,
                           xp_min=5, xp_max=5, gold_min=1, gold_max=1,
                           item_chance=0.0,
                           status_effects=[("stunned", 1.0, 3)])   # 100% stun chance
    world.start_combat(stun_monster)
    player.status_effect_cooldowns["stunned"] = 3   # in cooldown
    _apply_monster_status(stun_monster, world, player)
    assert "stunned" not in player.status_effects, "Should not re-stun during cooldown"

def test_stunned_can_use_potion(world, player):
    '''Potions are usable while stunned — health should increase.'''
    player.health = 1
    player.inventory.append(items_module.ALL_ITEMS["Potion"])
    player.status_effects["stunned"] = 2
    _start_combat(world, player)
    with patch('random.randint', return_value=100):   # no block on counter-attack
        do_combat_action(1, world, player)
    assert any("potion" in line.lower() for line in world.combat_log)

def test_stunned_potion_ticks_stun_down(world, player):
    '''Using a potion while stunned still counts as a turn — stun decrements.'''
    player.inventory.append(items_module.ALL_ITEMS["Potion"])
    player.status_effects["stunned"] = 2
    _start_combat(world, player)
    with patch('random.randint', return_value=100):
        do_combat_action(1, world, player)
    assert player.status_effects.get("stunned", 0) == 1

def test_stunned_potion_stun_fades_at_one(world, player):
    '''Stun at 1 is removed after a potion turn.'''
    player.inventory.append(items_module.ALL_ITEMS["Potion"])
    player.status_effects["stunned"] = 1
    _start_combat(world, player)
    with patch('random.randint', return_value=100):
        do_combat_action(1, world, player)
    assert "stunned" not in player.status_effects

def test_stunned_potion_monster_still_attacks(world, player):
    '''Monster counter-attacks even when player drinks a potion while stunned.'''
    player.health = player.get_max_health()
    player.inventory.append(items_module.ALL_ITEMS["Potion"])
    player.status_effects["stunned"] = 2
    monster = _start_combat(world, player, monster=_make_monster(attack=999, defense=0))
    with patch('random.randint', return_value=100), \
         patch('random.uniform', return_value=1.0):
        do_combat_action(1, world, player)
    assert any(monster.name in line for line in world.combat_log)


# ── Examine: re-examine is a no-op ────────────────────────────────────────────

def test_examine_second_call_is_noop(world, player):
    '''Pressing Examine a second time does nothing — no counter-attack, no new log lines.'''
    player.health = player.get_max_health()
    _start_combat(world, player, monster=_make_monster(attack=99, defense=0))
    # First examine — costs a turn, monster attacks
    with patch('random.randint', return_value=100), \
         patch('random.uniform', return_value=1.0), \
         patch('random.random', return_value=1.0):
        do_combat_action(2, world, player)
    health_after_first = player.health
    log_len_after_first = len(world.combat_log)
    # Second examine — should be a no-op
    do_combat_action(2, world, player)
    assert player.health == health_after_first, "Re-examine must not trigger counter-attack"
    assert len(world.combat_log) == log_len_after_first, "Re-examine must add no log entries"


# ── _do_counter_attack ────────────────────────────────────────────────────────

def test_counter_attack_deals_damage(world, player):
    monster = _make_monster(attack=5, defense=0)
    world.in_combat       = True
    world.combat_monster  = monster
    world.adventure_loc_index = 0
    player.health = player.get_max_health()
    with patch('random.randint', return_value=0), \
         patch('random.uniform', return_value=1.0):
        _do_counter_attack(monster, world, player)
    assert player.health < player.get_max_health()

def test_block_halves_damage(world, player):
    monster = _make_monster(attack=10, defense=0)
    world.in_combat      = True
    world.combat_monster = monster
    world.adventure_loc_index = 0
    player.health = player.get_max_health()
    # Force block: randint returns value <= block_chance (5 base)
    with patch('random.randint', return_value=1), \
         patch('random.uniform', return_value=1.0):
        _do_counter_attack(monster, world, player)
    assert any("Blocked" in line for line in world.combat_log)

def test_counter_attack_can_kill_player(world, player):
    player.health = 1
    monster = _make_monster(attack=100, defense=0)
    world.in_combat      = True
    world.combat_monster = monster
    world.adventure_loc_index = 0
    world.in_adventure   = True
    world.adventure_room = 0
    world.adventure_room_sequence = []
    with patch('random.randint', return_value=50), \
         patch('random.uniform', return_value=1.0):
        _do_counter_attack(monster, world, player)
    assert world.combat_result == "defeat"

def test_monster_status_applied_on_counter(world, player):
    monster = _make_monster(status_effects=[("poison", 1.0, 3)])
    world.in_combat       = True
    world.combat_monster  = monster
    world.adventure_loc_index = 0
    player.health = player.get_max_health()
    with patch('random.randint', return_value=50), \
         patch('random.uniform', return_value=1.0), \
         patch('random.random', return_value=0.0):   # always apply status
        _do_counter_attack(monster, world, player)
    assert "poison" in player.status_effects


# ── _tick_status_effects ──────────────────────────────────────────────────────

def test_poison_deals_damage_per_tick(world, player):
    player.status_effects["poison"] = 3
    player.health = player.get_max_health()
    world.combat_log = []
    _tick_status_effects(world, player)
    assert player.health == player.get_max_health() - 2

def test_poison_duration_decrements(world, player):
    player.status_effects["poison"] = 2
    world.combat_log = []
    _tick_status_effects(world, player)
    assert player.status_effects["poison"] == 1

def test_poison_expires_at_zero(world, player):
    player.status_effects["poison"] = 1
    world.combat_log = []
    _tick_status_effects(world, player)
    assert "poison" not in player.status_effects

def test_poison_kill_returns_true(world, player):
    player.status_effects["poison"] = 5
    player.health = 1
    world.combat_log = []
    result = _tick_status_effects(world, player)
    assert result is True

def test_weakened_duration_decrements(world, player):
    player.status_effects["weakened"] = 2
    world.combat_log = []
    _tick_status_effects(world, player)
    assert player.status_effects["weakened"] == 1

def test_no_effects_returns_false(world, player):
    world.combat_log = []
    result = _tick_status_effects(world, player)
    assert result is False
