'''
tests/test_world_state.py
Unit tests for WorldState initialisation, updateArea, restock_shop.
'''

import pytest
from state.gamestate import WorldState, PlayerState
import data.items as items_module


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def world():
    return WorldState()


@pytest.fixture
def player():
    return PlayerState()


# ── Default field values ──────────────────────────────────────────────────────

def test_initial_area(world):
    assert world.area == "start_screen"

def test_initial_day(world):
    assert world.day == 1

def test_initial_duskwall_unlocked(world):
    assert world.duskwall_unlocked is False

def test_initial_duskwall_just_unlocked(world):
    assert world.duskwall_just_unlocked is False

def test_initial_duskwall_arrival_pending(world):
    assert world.duskwall_arrival_pending is False

def test_initial_adventure_origin(world):
    assert world.adventure_origin == "village"

def test_initial_map_open(world):
    assert world.map_open is False

def test_initial_map_cursor(world):
    assert world.map_cursor == 0

def test_initial_intro_mode(world):
    assert world.intro_mode is False

def test_initial_intro_phase(world):
    assert world.intro_phase == "opening"

def test_initial_ending_mode(world):
    assert world.ending_mode is False

def test_initial_ending_line_index(world):
    assert world.ending_line_index == 0

def test_initial_game_over(world):
    assert world.game_over is None

def test_initial_passive_select_mode(world):
    assert world.passive_select_mode is False

def test_initial_passive_pending_milestone(world):
    assert world.passive_pending_milestone is None

def test_initial_passive_select_options(world):
    assert world.passive_select_options == []

def test_initial_nav_index(world):
    assert world.nav_index == 0

def test_initial_adventure_locations_unlocked(world):
    assert world.adventure_locations_unlocked == 1

def test_initial_adventure_locations_complete(world):
    assert world.adventure_locations_complete == []

def test_initial_music_volume(world):
    assert world.music_volume == 0.5

def test_initial_sfx_volume(world):
    assert world.sfx_volume == 0.5


# ── updateArea ────────────────────────────────────────────────────────────────

def test_update_area_changes_area(world):
    world.updateArea("village")
    assert world.area == "village"

def test_update_area_resets_nav_index(world):
    world.nav_index = 3
    world.updateArea("inn")
    assert world.nav_index == 0

def test_update_area_shop_restocks_when_stale(world):
    world.day = 5
    world.shop_last_stocked_day = 1
    world.updateArea("shop")
    assert world.shop_last_stocked_day == 5

def test_update_area_duskwall_shop_restocks_when_stale(world):
    world.day = 5
    world.shop_last_stocked_day = 1
    world.updateArea("duskwall_shop")
    assert world.shop_last_stocked_day == 5

def test_update_area_non_shop_does_not_restock(world):
    world.day = 5
    world.shop_last_stocked_day = 1
    world.updateArea("village")
    # shop_last_stocked_day should be unchanged
    assert world.shop_last_stocked_day == 1

def test_update_area_shop_no_restock_same_day(world):
    world.day = 5
    world.shop_last_stocked_day = 5   # already stocked today
    world.updateArea("shop")
    assert world.shop_last_stocked_day == 5


# ── updateDay / getDay / getArea ──────────────────────────────────────────────

def test_update_day(world):
    world.updateDay()
    assert world.day == 2

def test_get_day(world):
    assert world.getDay() == 1

def test_get_area(world):
    assert world.getArea() == "start_screen"


# ── restock_shop ──────────────────────────────────────────────────────────────

def test_restock_shop_sets_day(world):
    world.day = 3
    world.restock_shop()
    assert world.shop_last_stocked_day == 3

def test_restock_shop_has_items(world):
    world.restock_shop()
    assert len(world.shop_inventory) > 0

def test_restock_shop_before_caverns_tier1_and_tier2(world):
    world.adventure_locations_complete = []
    world.restock_shop()
    tiers = {i.tier for i in world.shop_inventory if hasattr(i, 'tier')}
    # Before Forest cleared: tier 1 + tier 2 equipment (SHOP_POOL)
    # At minimum should not contain tier 3 equip from SHOP_POOL
    assert 3 not in tiers or all(
        i.consumable for i in world.shop_inventory if i.tier == 3
    )

def test_restock_shop_after_caverns_tier2_and_tier3(world):
    world.adventure_locations_complete = [0]  # Dark Forest done
    world.restock_shop()
    tiers = {i.tier for i in world.shop_inventory if not i.consumable}
    # After Forest: pool_a = tier 2, pool_b = tier 3
    assert 1 not in tiers


# ── reset ─────────────────────────────────────────────────────────────────────

def test_reset_returns_to_start_screen_by_default(world):
    world.day = 10
    world.reset("start_screen")
    assert world.area == "start_screen"
    assert world.day == 1

def test_reset_to_village_restocks(world):
    world.reset("village")
    assert world.shop_last_stocked_day == 1

def test_reset_to_start_screen_no_restock(world):
    world.reset("start_screen")
    assert world.shop_last_stocked_day == -1
