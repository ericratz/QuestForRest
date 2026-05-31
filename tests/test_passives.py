'''
tests/test_passives.py
Tests for data/passives.py structure and PlayerState.passive_effect integration.
'''

import pytest
from data.passives import PASSIVES, MILESTONE_OPTIONS, MILESTONES, BASE_CRIT_CHANCE, BASE_BLOCK_CHANCE
from state.gamestate import PlayerState


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def player():
    return PlayerState()


# ── PASSIVES dict integrity ───────────────────────────────────────────────────

def test_all_passives_have_name():
    for pid, p in PASSIVES.items():
        assert "name" in p, f"{pid} missing 'name'"

def test_all_passives_have_desc():
    for pid, p in PASSIVES.items():
        assert "desc" in p, f"{pid} missing 'desc'"

def test_all_passives_have_effect():
    for pid, p in PASSIVES.items():
        assert "effect" in p and isinstance(p["effect"], dict), f"{pid} missing/bad 'effect'"

def test_all_passives_have_tier():
    for pid, p in PASSIVES.items():
        assert p["tier"] in (1, 2, 3), f"{pid} has unexpected tier {p['tier']}"


# ── MILESTONE_OPTIONS integrity ───────────────────────────────────────────────

def test_milestone_keys_are_5_10_15():
    assert set(MILESTONE_OPTIONS.keys()) == {5, 10, 15}

def test_milestone_options_each_have_3():
    for lvl, opts in MILESTONE_OPTIONS.items():
        assert len(opts) == 3, f"milestone {lvl} should have 3 options"

def test_milestone_options_all_valid_passive_ids():
    for lvl, opts in MILESTONE_OPTIONS.items():
        for pid in opts:
            assert pid in PASSIVES, f"milestone {lvl} references unknown passive '{pid}'"

def test_milestone_options_no_duplicates_across_tiers():
    all_ids = [pid for opts in MILESTONE_OPTIONS.values() for pid in opts]
    assert len(all_ids) == len(set(all_ids)), "duplicate passive IDs across milestones"

def test_milestones_frozenset_matches_keys():
    assert MILESTONES == frozenset({5, 10, 15})


# ── Tier assignments ──────────────────────────────────────────────────────────

def test_tier1_passives_are_in_milestone_5():
    for pid in MILESTONE_OPTIONS[5]:
        assert PASSIVES[pid]["tier"] == 1

def test_tier2_passives_are_in_milestone_10():
    for pid in MILESTONE_OPTIONS[10]:
        assert PASSIVES[pid]["tier"] == 2

def test_tier3_passives_are_in_milestone_15():
    for pid in MILESTONE_OPTIONS[15]:
        assert PASSIVES[pid]["tier"] == 3


# ── Base constants ────────────────────────────────────────────────────────────

def test_base_crit_chance():
    assert BASE_CRIT_CHANCE == 5

def test_base_block_chance():
    assert BASE_BLOCK_CHANCE == 5


# ── passive_effect integration ────────────────────────────────────────────────

def test_passive_effect_returns_zero_with_no_passives(player):
    assert player.passive_effect("atk_bonus") == 0

def test_passive_effect_iron_skin(player):
    player.chosen_passives = ["iron_skin"]
    assert player.passive_effect("def_bonus") == 2

def test_passive_effect_tracker(player):
    player.chosen_passives = ["tracker"]
    assert player.passive_effect("crit_bonus") == 8

def test_passive_effect_forager(player):
    player.chosen_passives = ["forager"]
    assert player.passive_effect("food_bonus") == 1

def test_passive_effect_might(player):
    player.chosen_passives = ["might"]
    assert player.passive_effect("atk_bonus") == 2

def test_passive_effect_second_wind(player):
    player.chosen_passives = ["second_wind"]
    assert player.passive_effect("second_wind") == 1

def test_passive_effect_prospector(player):
    player.chosen_passives = ["prospector"]
    assert abs(player.passive_effect("gold_mult") - 0.30) < 1e-9

def test_passive_effect_berserker(player):
    player.chosen_passives = ["berserker"]
    assert player.passive_effect("berserker_atk") == 4

def test_passive_effect_lifesteal(player):
    player.chosen_passives = ["lifesteal"]
    assert player.passive_effect("lifesteal") == 1

def test_passive_effect_bulwark(player):
    player.chosen_passives = ["bulwark"]
    assert player.passive_effect("block_bonus") == 15

def test_passive_effect_unknown_key_returns_zero(player):
    player.chosen_passives = ["might", "tracker"]
    assert player.passive_effect("nonexistent") == 0

def test_passive_effect_unknown_passive_id_is_safe(player):
    # Should not raise; unknown IDs are skipped
    player.chosen_passives = ["fake_passive"]
    assert player.passive_effect("atk_bonus") == 0


# ── second_wind_available resets ──────────────────────────────────────────────

def test_second_wind_fires_once(player):
    player.chosen_passives = ["second_wind"]
    player.second_wind_available = True
    dead1 = player.take_damage(9999)
    assert dead1 is False
    assert player.health == 1
    assert player.second_wind_available is False

def test_second_wind_does_not_fire_twice(player):
    player.chosen_passives = ["second_wind"]
    player.second_wind_available = True
    player.take_damage(9999)   # survives
    dead2 = player.take_damage(9999)
    assert dead2 is True

def test_second_wind_requires_passive(player):
    '''Flag set but no passive chosen — should not save player.'''
    player.second_wind_available = True
    dead = player.take_damage(9999)
    assert dead is True
