'''
tests/test_adventure.py
Integration tests for adventure logic: handle_victory, handle_defeat,
handle_flee, return_to_village, advance_day, and food room mechanics.

audio.sounds and render.helpers are mocked at session level in conftest.py.
'''

import math
import pytest
import random
from unittest.mock import patch
from state.gamestate import WorldState, PlayerState, ADVENTURE_LOCATIONS
from logic.adventure import (
    handle_victory, handle_defeat, handle_flee,
    return_to_village, advance_day, enter_room,
)
from data.monsters import Monster


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def world():
    w = WorldState()
    w.reset("village")
    return w

@pytest.fixture
def player():
    return PlayerState()


def _make_monster(tier=1, hp=10, attack=3, defense=1, xp=5, gold_min=2, gold_max=5):
    '''Build a minimal monster for testing.'''
    return Monster("TestBeast", tier, hp, attack, defense, xp, xp, gold_min, gold_max,
                   item_chance=0.0)  # no item drops → deterministic


def _setup_non_boss_fight(world, player, room=0):
    '''Put world/player in a mid-adventure combat scenario.'''
    world.in_adventure = True
    world.adventure_loc_index = 0   # Dark Forest
    world.adventure_room = room
    world.adventure_room_sequence = []
    player.food = 5
    monster = _make_monster()
    world.start_combat(monster)
    return monster


def _setup_boss_fight(world, player):
    '''Put world/player in a boss fight (last room of Dark Forest = room 9).'''
    world.in_adventure = True
    world.adventure_loc_index = 0
    boss_room = ADVENTURE_LOCATIONS[0]["total_rooms"] - 1  # 9
    world.adventure_room = boss_room
    monster = _make_monster(tier=3, xp=50)
    world.start_combat(monster)
    return monster, boss_room


# ── handle_victory: basic loot / state ────────────────────────────────────────

def test_handle_victory_increments_kills(world, player):
    _setup_non_boss_fight(world, player)
    handle_victory(world, player)
    assert player.kills == 1

def test_handle_victory_awards_gold(world, player):
    _setup_non_boss_fight(world, player)
    handle_victory(world, player)
    assert player.gold >= 2   # gold_min = 2

def test_handle_victory_sets_post_combat_mode(world, player):
    _setup_non_boss_fight(world, player)
    handle_victory(world, player)
    assert world.post_combat_mode is True

def test_handle_victory_clears_in_combat(world, player):
    _setup_non_boss_fight(world, player)
    handle_victory(world, player)
    assert world.in_combat is False

def test_handle_victory_stores_loot(world, player):
    _setup_non_boss_fight(world, player)
    handle_victory(world, player)
    gold, loot_label = world.post_combat_loot
    assert gold >= 0

def test_handle_victory_records_levelups(world, player):
    '''Gain enough XP to level up.'''
    _setup_non_boss_fight(world, player)
    # Give a monster with huge XP so we level up
    world.combat_monster.xp_min = 10_000
    world.combat_monster.xp_max = 10_000
    handle_victory(world, player)
    assert len(world.post_combat_levelups) >= 1

def test_handle_victory_tracks_kill_counts(world, player):
    _setup_non_boss_fight(world, player)
    handle_victory(world, player)
    assert player.kill_counts.get("TestBeast", 0) == 1


# ── handle_victory: boss fight ────────────────────────────────────────────────

def test_handle_victory_boss_marks_complete(world, player):
    monster, _ = _setup_boss_fight(world, player)
    handle_victory(world, player)
    assert 0 in world.adventure_locations_complete

def test_handle_victory_boss_ends_adventure(world, player):
    _setup_boss_fight(world, player)
    handle_victory(world, player)
    assert world.in_adventure is False
    assert world.adventure_complete is True

def test_handle_victory_boss_increments_boss_kills(world, player):
    _setup_boss_fight(world, player)
    handle_victory(world, player)
    assert player.boss_kills == 1

def test_handle_victory_boss_advances_day(world, player):
    _setup_boss_fight(world, player)
    day_before = world.day
    handle_victory(world, player)
    assert world.day == day_before + 1

def test_handle_victory_boss_survivalist_no_potion(world, player):
    _setup_boss_fight(world, player)
    player.used_potion_this_run = False
    before = player.survivalist_completions
    handle_victory(world, player)
    assert player.survivalist_completions == before + 1

def test_handle_victory_boss_survivalist_used_potion(world, player):
    _setup_boss_fight(world, player)
    player.used_potion_this_run = True
    before = player.survivalist_completions
    handle_victory(world, player)
    assert player.survivalist_completions == before  # no increment


# ── handle_victory: Iron Will achievement ────────────────────────────────────

def _setup_boss_fight_no_xp(world, player):
    '''Boss fight that gives 0 XP — prevents level-up from restoring HP before achievement check.'''
    world.in_adventure = True
    world.adventure_loc_index = 0
    boss_room = ADVENTURE_LOCATIONS[0]["total_rooms"] - 1
    world.adventure_room = boss_room
    monster = _make_monster(tier=3, xp=0)
    world.start_combat(monster)
    return monster

def test_iron_will_triggers_at_exactly_1_hp(world, player):
    '''Finishing a dungeon at exactly 1 HP earns Iron Will.'''
    _setup_boss_fight_no_xp(world, player)
    player.health = 1
    handle_victory(world, player)
    assert "Iron Will" in world.achievement_popup

def test_iron_will_does_not_trigger_at_2_hp(world, player):
    '''Iron Will requires exactly 1 HP — 2 HP is not enough.'''
    _setup_boss_fight_no_xp(world, player)
    player.health = 2
    handle_victory(world, player)
    assert "Iron Will" not in world.achievement_popup

def test_iron_will_does_not_trigger_at_5_hp(world, player):
    '''Old threshold (<=5) should no longer count; only exactly 1 HP qualifies.'''
    _setup_boss_fight_no_xp(world, player)
    player.health = 5
    handle_victory(world, player)
    assert "Iron Will" not in world.achievement_popup


# ── Boss pool assignments ─────────────────────────────────────────────────────

def test_dark_forest_boss_is_dark_wizard(world, player):
    '''Dark Forest boss_index 1 → BOSS_POOL[1] = Dark Wizard.'''
    from data.monsters import BOSS_POOL, spawn
    loc = ADVENTURE_LOCATIONS[0]
    boss = spawn(3, boss_index=loc["boss_index"])
    assert boss.name == "Dark Wizard"

def test_deep_caverns_boss_is_hill_giant(world, player):
    '''Deep Caverns boss_index 0 → BOSS_POOL[0] = Hill Giant.'''
    from data.monsters import BOSS_POOL, spawn
    loc = ADVENTURE_LOCATIONS[1]
    boss = spawn(3, boss_index=loc["boss_index"])
    assert boss.name == "Hill Giant"


# ── handle_victory: Duskwall unlock ──────────────────────────────────────────

def test_handle_victory_caverns_boss_unlocks_duskwall(world, player):
    '''Beating Deep Caverns (index 1) should set duskwall_unlocked.'''
    world.in_adventure = True
    world.adventure_loc_index = 1
    boss_room = ADVENTURE_LOCATIONS[1]["total_rooms"] - 1
    world.adventure_room = boss_room
    monster = _make_monster(tier=3, xp=50)
    world.start_combat(monster)
    handle_victory(world, player)
    assert world.duskwall_unlocked is True
    assert world.duskwall_just_unlocked is True

def test_handle_victory_forest_boss_does_not_unlock_duskwall(world, player):
    _setup_boss_fight(world, player)   # Dark Forest
    handle_victory(world, player)
    assert world.duskwall_unlocked is False


# ── handle_victory: passive milestone detection ───────────────────────────────

def test_handle_victory_sets_pending_milestone_at_level_5(world, player):
    '''If level-up reaches a milestone, passive_pending_milestone is set.'''
    # Give xp to reach level 5
    player.level = 4
    player.xp = player.xp_to_next() - 1
    world.in_adventure = True
    world.adventure_loc_index = 0
    world.adventure_room = 0
    monster = _make_monster(xp=5)
    world.start_combat(monster)
    handle_victory(world, player)
    # If we leveled to 5 and milestone 5 not done, should be pending
    if player.level >= 5 and 5 not in player.passive_milestones_done:
        assert world.passive_pending_milestone == 5
    # Otherwise just confirm it's not incorrectly set to a non-milestone
    if world.passive_pending_milestone is not None:
        assert world.passive_pending_milestone in (5, 10, 15)

def test_handle_victory_milestone_not_set_twice(world, player):
    '''If milestone already done, passive_pending_milestone stays None.'''
    player.level = 4
    player.xp = player.xp_to_next() - 1
    player.passive_milestones_done = {5}   # already done level 5
    world.in_adventure = True
    world.adventure_loc_index = 0
    world.adventure_room = 0
    monster = _make_monster(xp=5)
    world.start_combat(monster)
    handle_victory(world, player)
    # milestone 5 is done, so should not be set again
    if player.level == 5:
        assert world.passive_pending_milestone != 5


# ── handle_victory: Prospector gold bonus ────────────────────────────────────

def test_prospector_increases_gold(world, player):
    player.chosen_passives = ["prospector"]
    world.in_adventure = True
    world.adventure_loc_index = 0
    world.adventure_room = 0
    # Force deterministic gold
    monster = _make_monster(gold_min=10, gold_max=10)
    world.start_combat(monster)
    handle_victory(world, player)
    gold, _ = world.post_combat_loot
    assert gold >= 13   # 10 + 30% = 13


# ── handle_defeat ─────────────────────────────────────────────────────────────

def test_handle_defeat_sets_post_combat_mode(world, player):
    _setup_non_boss_fight(world, player)
    handle_defeat(world, player)
    assert world.post_combat_mode is True

def test_handle_defeat_ends_adventure(world, player):
    _setup_non_boss_fight(world, player)
    handle_defeat(world, player)
    assert world.in_adventure is False
    assert world.in_combat is False

def test_handle_defeat_calls_die(world, player):
    player.gold = 100
    player.inventory = []
    _setup_non_boss_fight(world, player)
    handle_defeat(world, player)
    # die() halves gold
    assert player.gold == 50

def test_handle_defeat_advances_day(world, player):
    _setup_non_boss_fight(world, player)
    day_before = world.day
    handle_defeat(world, player)
    assert world.day == day_before + 1

def test_handle_defeat_clears_loot(world, player):
    _setup_non_boss_fight(world, player)
    handle_defeat(world, player)
    gold, label = world.post_combat_loot
    assert gold == 0
    assert label is None


# ── handle_flee ───────────────────────────────────────────────────────────────

def test_handle_flee_sets_fled_result(world, player):
    _setup_non_boss_fight(world, player)
    handle_flee(world, player)
    assert world.combat_result == "fled"

def test_handle_flee_ends_combat(world, player):
    _setup_non_boss_fight(world, player)
    handle_flee(world, player)
    assert world.in_combat is False

def test_handle_flee_no_loot(world, player):
    _setup_non_boss_fight(world, player)
    handle_flee(world, player)
    gold, label = world.post_combat_loot
    assert gold == 0
    assert label is None


# ── return_to_village ─────────────────────────────────────────────────────────

def test_return_to_village_goes_to_origin(world, player):
    world.adventure_origin = "village"
    return_to_village(world, player)
    assert world.area == "village"

def test_return_to_village_goes_to_duskwall_origin(world, player):
    world.adventure_origin = "duskwall"
    return_to_village(world, player)
    assert world.area == "duskwall"

def test_return_to_village_clears_adventure_flags(world, player):
    world.in_adventure = True
    world.adventure_complete = True
    world.adventure_origin = "village"
    return_to_village(world, player)
    assert world.in_adventure is False
    assert world.adventure_complete is False
    assert world.post_combat_mode is False

def test_return_to_village_resets_nav_index(world, player):
    world.nav_index = 3
    world.adventure_origin = "village"
    return_to_village(world, player)
    assert world.nav_index == 0

def test_return_to_village_clears_status_effects(world, player):
    player.status_effects = {"cursed": -1, "poison": 2}
    world.adventure_origin = "village"
    return_to_village(world, player)
    assert player.status_effects == {}

def test_return_to_village_resets_temp_attack_bonus(world, player):
    player.temp_attack_bonus = 5
    world.adventure_origin = "village"
    return_to_village(world, player)
    assert player.temp_attack_bonus == 0


# ── advance_day ───────────────────────────────────────────────────────────────

def test_advance_day_increments_day(world, player):
    world.day = 3
    advance_day(world, player)
    assert world.day == 4

def test_advance_day_resets_adventured_today(world, player):
    world.adventured_today = True
    advance_day(world, player)
    assert world.adventured_today is False

def test_advance_day_14_game_over_if_debt(world, player):
    world.day = 13
    player.debt = 50
    advance_day(world, player)
    assert world.game_over == "debt_expired"

def test_advance_day_14_no_auto_debt_if_paid(world, player):
    '''Day 14 no longer auto-assigns second debt; debt is set on Duskwall arrival.'''
    world.day = 13
    player.debt = 0
    advance_day(world, player)
    assert player.debt == 0          # no second debt added automatically
    assert world.game_over is None   # no game over either

def test_advance_day_28_game_over_if_second_debt(world, player):
    world.day = 27
    player.debt = 500
    player.active_quests = {"second_debt"}
    advance_day(world, player)
    assert world.game_over == "debt_expired"

def test_advance_day_expired_quest_penalises_gold(world, player):
    player.gold = 100
    player.quest_due_dates = {"kill_3": 1}
    player.active_quests = {"kill_3"}
    player.quests_complete = set()
    world.day = 1   # advance to day 2, quest was due day 1
    advance_day(world, player)
    assert player.gold < 100   # penalty applied


# ── enter_room: food room ─────────────────────────────────────────────────────

def test_enter_room_food_default_gives_1(world, player):
    '''Without forager, food room gives +1.'''
    world.in_adventure = True
    world.adventure_loc_index = 1   # Deep Caverns has "food" room type
    world.adventure_room = 0
    world.adventure_room_sequence = ["food"]  # force food room
    before = player.food
    enter_room(1, 0, world, player)
    assert player.food == before + 1

def test_enter_room_food_forager_gives_2(world, player):
    '''Forager passive adds +1 to food room yield.'''
    player.chosen_passives = ["forager"]
    world.in_adventure = True
    world.adventure_loc_index = 1
    world.adventure_room = 0
    world.adventure_room_sequence = ["food"]
    before = player.food
    enter_room(1, 0, world, player)
    assert player.food == before + 2


# ── enter_room: other room types ─────────────────────────────────────────────

def _setup_room(world, player, room_type, loc_index=0):
    world.in_adventure = True
    world.adventure_loc_index = loc_index
    world.adventure_room = 0
    world.adventure_room_sequence = [room_type]
    player.food = 3

def test_enter_room_combat_starts_fight(world, player):
    loc = ADVENTURE_LOCATIONS[0]
    world.in_adventure = True
    world.adventure_loc_index = 0
    world.adventure_room = 0
    world.adventure_room_sequence = ["monster"]
    player.food = 3
    enter_room(0, 0, world, player)
    assert world.in_combat
    assert world.combat_monster is not None

def test_enter_room_boss_room_starts_fight(world, player):
    '''Last room of any dungeon should start a boss fight.'''
    loc   = ADVENTURE_LOCATIONS[0]
    boss_room = loc["total_rooms"] - 1
    world.in_adventure = True
    world.adventure_loc_index = 0
    world.adventure_room = boss_room
    world.adventure_room_sequence = []
    player.food = 3
    enter_room(0, boss_room, world, player)
    assert world.in_combat
    assert world.combat_monster is not None

def test_enter_room_campfire_sets_prompt(world, player):
    _setup_room(world, player, "campfire")
    enter_room(0, 0, world, player)
    assert world.campfire_prompt
    assert world.campfire_pending_heal >= 1

def test_enter_room_trapped_chest_sets_mode(world, player):
    _setup_room(world, player, "trapped_chest")
    enter_room(0, 0, world, player)
    assert world.trapped_chest_mode

def test_enter_room_wanderer_trade_sets_mode(world, player):
    _setup_room(world, player, "wanderer")
    with patch('random.randint', return_value=6):   # sub==6 → trade
        enter_room(0, 0, world, player)
    assert world.adventure_trade_mode
    assert world.adventure_trade_item is not None

def test_enter_room_nothing_gives_post_room(world, player):
    _setup_room(world, player, "nothing")
    enter_room(0, 0, world, player)
    assert world.post_room_mode
    assert world.post_room_lines

def test_enter_room_duskwall_spawns_duskwall_monster(world, player):
    '''Duskwall location (index 2) should spawn a Duskwall monster.'''
    from data.monsters import DUSKWALL_NORMAL_POOL
    world.in_adventure = True
    world.adventure_loc_index = 2
    world.adventure_room = 0
    world.adventure_room_sequence = ["monster"]
    player.food = 3
    enter_room(2, 0, world, player)
    assert world.in_combat
    assert world.combat_monster.name in {m.name for m in DUSKWALL_NORMAL_POOL}


# ── FamiliarState ─────────────────────────────────────────────────────────────

def test_familiar_gain_xp_no_levelup(player):
    player.familiar.level = 1
    player.familiar.xp    = 0
    levels = player.familiar.gain_xp(3)
    assert levels == []
    assert player.familiar.xp == 3

def test_familiar_gain_xp_triggers_levelup(player):
    player.familiar.level = 1
    player.familiar.xp    = 0
    needed = player.familiar.xp_to_next()
    levels = player.familiar.gain_xp(needed)
    assert player.familiar.level == 2
    assert levels == [2]

def test_familiar_gain_xp_resets_xp_after_levelup(player):
    player.familiar.level = 1
    needed = player.familiar.xp_to_next()
    player.familiar.gain_xp(needed + 5)
    assert player.familiar.xp == 5

def test_familiar_gain_xp_multiple_levels(player):
    levels = player.familiar.gain_xp(100_000)
    assert len(levels) > 1
    assert player.familiar.level > 2

def test_familiar_get_attack_base(player):
    player.familiar.base_attack = 2
    player.familiar.equipment   = None
    assert player.familiar.get_attack() == 2

def test_familiar_get_attack_includes_charm(player):
    from data.items import ALL_ITEMS
    player.familiar.base_attack = 2
    player.familiar.equipment   = ALL_ITEMS['Worn Collar']   # +1 atk
    assert player.familiar.get_attack() == 3

def test_familiar_xp_to_next_grows_with_level(player):
    player.familiar.level = 1
    low  = player.familiar.xp_to_next()
    player.familiar.level = 5
    high = player.familiar.xp_to_next()
    assert high > low


# ── handle_victory: Duskwall path ────────────────────────────────────────────

def _setup_duskwall_fight(world, player, room=0):
    from state.gamestate import ADVENTURE_LOCATIONS
    world.in_adventure         = True
    world.adventure_loc_index  = 2   # Outer Ruins
    world.adventure_room       = room
    world.adventure_room_sequence = []
    player.food = 3
    monster = _make_monster(xp=10, tier=1)
    world.start_combat(monster)
    return monster

def test_handle_victory_duskwall_gives_duskwall_loot(world, player):
    '''Duskwall location uses roll_duskwall_loot (higher gold range than tier 1).'''
    _setup_duskwall_fight(world, player)
    with patch('random.randint', return_value=5), \
         patch('random.random', return_value=1.0):   # no item drop
        handle_victory(world, player)
    gold, _ = world.post_combat_loot
    assert gold >= 1

def test_handle_victory_familiar_gains_xp(world, player):
    player.familiar.found = True
    player.familiar.name  = "Luna"
    before_xp = player.familiar.xp
    _setup_duskwall_fight(world, player)
    with patch('random.random', return_value=1.0):
        handle_victory(world, player)
    assert player.familiar.xp > before_xp or player.familiar.level > 1

def test_handle_victory_outer_ruins_boss_unlocks_castle(world, player):
    '''Defeating boss of Outer Ruins (loc 2) sets duskwall_locations_unlocked=2.'''
    loc = ADVENTURE_LOCATIONS[2]
    boss_room = loc["total_rooms"] - 1
    _setup_duskwall_fight(world, player, room=boss_room)
    world.duskwall_locations_unlocked = 1
    with patch('random.random', return_value=1.0):
        handle_victory(world, player)
    assert world.duskwall_locations_unlocked == 2


# ── handle_trapped_chest ──────────────────────────────────────────────────────

from logic.adventure import handle_trapped_chest_open, handle_trapped_chest_leave

def _setup_chest(world, player):
    world.in_adventure        = True
    world.adventure_loc_index = 0
    world.adventure_room      = 2
    world.adventure_room_sequence = []
    world.trapped_chest_mode  = True
    player.food               = 3

def test_trapped_chest_leave_clears_mode(world, player):
    _setup_chest(world, player)
    handle_trapped_chest_leave(world, player)
    assert not world.trapped_chest_mode
    assert world.post_room_mode

def test_trapped_chest_open_clears_mode(world, player):
    _setup_chest(world, player)
    with patch('random.random', return_value=1.0), \
         patch('random.randint', return_value=5):
        handle_trapped_chest_open(world, player)
    assert not world.trapped_chest_mode

def test_trapped_chest_open_result_is_post_room_or_combat(world, player):
    '''After opening, state is either post_room or post_combat (if damage killed).'''
    _setup_chest(world, player)
    player.health = player.get_max_health()
    with patch('random.random', return_value=0.5), \
         patch('random.randint', return_value=5):
        handle_trapped_chest_open(world, player)
    # Any of these is valid depending on random outcome
    assert world.post_room_mode or world.post_combat_mode or not world.trapped_chest_mode


# ── trapped chest: damage cap (25% max HP, min 1) ────────────────────────────

def test_trapped_chest_damage_capped_at_25_percent_max_hp(world, player):
    '''roll >= 0.4 triggers damage; uniform=0.25 → exactly ceil(max_hp * 0.25).'''
    _setup_chest(world, player)
    player.health = player.get_max_health()
    max_hp = player.get_max_health()
    with patch('random.random', return_value=0.9), \
         patch('random.uniform', return_value=0.25):
        handle_trapped_chest_open(world, player)
    damage = max_hp - player.health
    assert damage == math.ceil(max_hp * 0.25)

def test_trapped_chest_damage_minimum_is_1(world, player):
    '''10% of 20 HP = ceil(2.0) = 2 ≥ 1. Confirms the max(1, ...) floor holds.'''
    _setup_chest(world, player)
    player.health = player.get_max_health()
    max_hp = player.get_max_health()
    with patch('random.random', return_value=0.9), \
         patch('random.uniform', return_value=0.10):
        handle_trapped_chest_open(world, player)
    damage = max_hp - player.health
    assert damage >= 1

def test_trapped_chest_no_damage_when_roll_below_40(world, player):
    '''roll < 0.4 → item-only outcome, no damage taken.'''
    _setup_chest(world, player)
    player.health = player.get_max_health()
    with patch('random.random', return_value=0.1):   # roll=0.1 < 0.4
        handle_trapped_chest_open(world, player)
    assert player.health == player.get_max_health(), "No trap damage when roll < 0.4"

def test_trapped_chest_restholm_gives_restholm_item(world, player):
    '''Chest in a Restholm dungeon must only drop SHOP_POOL items.'''
    from data.items import SHOP_POOL
    _setup_chest(world, player)   # adventure_loc_index=0 (Dark Forest)
    before = set(_all_held_items(player))
    with patch('random.random', return_value=0.1):   # roll < 0.4 → item-only, no damage
        handle_trapped_chest_open(world, player)
    new_items = [i for i in _all_held_items(player) if i not in before]
    assert new_items, "An item should have been awarded"
    assert new_items[0] in SHOP_POOL, (
        f"Got {new_items[0].name!r} which is not in SHOP_POOL")

def test_trapped_chest_duskwall_gives_duskwall_item(world, player):
    '''Chest in a Duskwall dungeon must only drop DUSKWALL_SHOP_POOL items.'''
    from data.items import DUSKWALL_SHOP_POOL
    world.in_adventure        = True
    world.adventure_loc_index = 2   # Outer Ruins = duskwall
    world.adventure_room      = 2
    world.adventure_room_sequence = []
    world.trapped_chest_mode  = True
    player.food = 3
    before = set(_all_held_items(player))
    with patch('random.random', return_value=0.1):   # item-only, no damage
        handle_trapped_chest_open(world, player)
    new_items = [i for i in _all_held_items(player) if i not in before]
    assert new_items, "An item should have been awarded"
    assert new_items[0] in DUSKWALL_SHOP_POOL, (
        f"Got {new_items[0].name!r} which is not in DUSKWALL_SHOP_POOL")


# ── enter_room: shrine ────────────────────────────────────────────────────────

def test_enter_room_shrine_atk_raises_temp_attack_bonus(world, player):
    _setup_room(world, player, "shrine")
    before = player.temp_attack_bonus
    with patch('random.choice', return_value="atk"), \
         patch('random.randint', return_value=2):
        enter_room(0, 0, world, player)
    assert player.temp_attack_bonus == before + 2
    assert world.post_room_mode

def test_enter_room_shrine_def_raises_temp_defense_bonus(world, player):
    _setup_room(world, player, "shrine")
    before = player.temp_defense_bonus
    with patch('random.choice', return_value="def"), \
         patch('random.randint', return_value=2):
        enter_room(0, 0, world, player)
    assert player.temp_defense_bonus == before + 2

def test_enter_room_shrine_hp_raises_temp_max_health_bonus(world, player):
    _setup_room(world, player, "shrine")
    before = player.temp_max_health_bonus
    with patch('random.choice', return_value="hp"), \
         patch('random.randint', return_value=3):
        enter_room(0, 0, world, player)
    assert player.temp_max_health_bonus == before + 3

def test_enter_room_shrine_hp_also_heals_player(world, player):
    _setup_room(world, player, "shrine")
    player.health = 5
    with patch('random.choice', return_value="hp"), \
         patch('random.randint', return_value=3):
        enter_room(0, 0, world, player)
    assert player.health > 5

def test_enter_room_shrine_does_not_modify_base_stats(world, player):
    '''Shrine uses temp bonuses — base stats must remain unchanged.'''
    base_atk = player.base_attack
    base_def = player.base_defense
    base_hp  = player.base_max_health
    _setup_room(world, player, "shrine")
    with patch('random.choice', return_value="atk"), \
         patch('random.randint', return_value=2):
        enter_room(0, 0, world, player)
    assert player.base_attack     == base_atk
    assert player.base_defense    == base_def
    assert player.base_max_health == base_hp


# ── enter_room: damage ────────────────────────────────────────────────────────

def test_enter_room_damage_reduces_health(world, player):
    _setup_room(world, player, "damage")
    player.health = player.get_max_health()
    with patch('random.randint', return_value=10):   # 10% of max HP
        enter_room(0, 0, world, player)
    assert player.health < player.get_max_health()
    assert world.post_room_mode

def test_enter_room_damage_minimum_1(world, player):
    '''1% of 20 HP = 0.2 → int(0.2)=0 → max(1,0)=1.'''
    _setup_room(world, player, "damage")
    player.health = player.get_max_health()
    before = player.health
    with patch('random.randint', return_value=1):
        enter_room(0, 0, world, player)
    assert before - player.health >= 1

def test_enter_room_damage_lethal_triggers_defeat(world, player):
    _setup_room(world, player, "damage")
    player.health = 1
    with patch('random.randint', return_value=15):
        enter_room(0, 0, world, player)
    assert world.combat_result == "defeat" or not world.in_adventure


# ── enter_room: fairy ─────────────────────────────────────────────────────────

def test_enter_room_fairy_heals_to_full(world, player):
    _setup_room(world, player, "fairy")
    player.health = 5
    enter_room(0, 0, world, player)
    assert player.health == player.get_max_health()
    assert world.post_room_mode

def test_enter_room_fairy_full_health_logs_message(world, player):
    _setup_room(world, player, "fairy")
    player.health = player.get_max_health()
    enter_room(0, 0, world, player)
    assert world.post_room_mode
    assert any("full" in l.lower() for l in world.post_room_lines)


# ── enter_room: item sub-cases ────────────────────────────────────────────────

def test_enter_room_item_gold_awards_gold(world, player):
    _setup_room(world, player, "item")
    before = player.gold
    # First randint = roll (1 → gold), second = gold amount (7)
    with patch('random.randint', side_effect=[1, 7]):
        enter_room(0, 0, world, player)
    assert player.gold == before + 7

def test_enter_room_item_potion_adds_to_inventory(world, player):
    _setup_room(world, player, "item")
    with patch('random.randint', return_value=3):   # roll=3 → potion
        enter_room(0, 0, world, player)
    assert any(i.name == "Potion" for i in player.inventory)

def test_enter_room_item_empty_gives_nothing(world, player):
    _setup_room(world, player, "item")
    before_gold = player.gold
    before_inv  = len(player.inventory)
    with patch('random.randint', return_value=4):   # roll=4 → nothing inside
        enter_room(0, 0, world, player)
    assert player.gold == before_gold
    assert len(player.inventory) == before_inv
    assert world.post_room_mode

def _all_held_items(player):
    '''Return every item the player holds: inventory + all equipped slots.'''
    equipped = [v for v in player.equipment.values() if v]
    return player.inventory + equipped

def test_enter_room_item_restholm_gives_restholm_item(world, player):
    '''Item room in a Restholm location (index 0) must only drop SHOP_POOL items.'''
    from data.items import SHOP_POOL
    _setup_room(world, player, "item", loc_index=0)
    before = set(_all_held_items(player))
    with patch('random.randint', return_value=2):   # roll=2 → equipment drop
        enter_room(0, 0, world, player)
    new_items = [i for i in _all_held_items(player) if i not in before]
    assert new_items, "An item should have been awarded"
    assert new_items[0] in SHOP_POOL, (
        f"Got {new_items[0].name!r} which is not in SHOP_POOL")

def test_enter_room_item_duskwall_gives_duskwall_item(world, player):
    '''Item room in a Duskwall location (index 2) must only drop DUSKWALL_SHOP_POOL items.'''
    from data.items import DUSKWALL_SHOP_POOL
    _setup_room(world, player, "item", loc_index=2)   # Outer Ruins = duskwall
    before = set(_all_held_items(player))
    with patch('random.randint', return_value=2):   # roll=2 → equipment drop
        enter_room(2, 0, world, player)
    new_items = [i for i in _all_held_items(player) if i not in before]
    assert new_items, "An item should have been awarded"
    assert new_items[0] in DUSKWALL_SHOP_POOL, (
        f"Got {new_items[0].name!r} which is not in DUSKWALL_SHOP_POOL")


# ── enter_room: wanderer sub-cases ────────────────────────────────────────────

def test_wanderer_steals_gold_when_rich(world, player):
    _setup_room(world, player, "wanderer")
    player.gold = 10
    with patch('random.randint', side_effect=[1, 4]):   # sub=1, stolen=4
        enter_room(0, 0, world, player)
    assert player.gold == 6
    assert world.post_room_mode

def test_wanderer_steals_nothing_when_broke(world, player):
    _setup_room(world, player, "wanderer")
    player.gold = 0
    with patch('random.randint', return_value=1):   # sub=1, but gold==0
        enter_room(0, 0, world, player)
    assert player.gold == 0
    assert world.post_room_mode

def test_wanderer_gifts_gold(world, player):
    _setup_room(world, player, "wanderer")
    player.gold = 0   # gold==0 → gains from randint(1, 20)
    with patch('random.randint', side_effect=[2, 15]):  # sub=2, gained=15
        enter_room(0, 0, world, player)
    assert player.gold == 15

def test_wanderer_scary_no_effect(world, player):
    _setup_room(world, player, "wanderer")
    before_gold = player.gold
    before_hp   = player.health
    with patch('random.randint', return_value=3):   # sub=3 → scary wanderer
        enter_room(0, 0, world, player)
    assert player.gold   == before_gold
    assert player.health == before_hp
    assert world.post_room_mode

def test_wanderer_steals_food(world, player):
    _setup_room(world, player, "wanderer")
    player.food = 3
    with patch('random.randint', return_value=4):   # sub=4 → hungry
        enter_room(0, 0, world, player)
    assert player.food == 2

def test_wanderer_steals_food_gracefully_when_none(world, player):
    _setup_room(world, player, "wanderer")
    player.food = 0
    with patch('random.randint', return_value=4):   # sub=4, nothing to steal
        enter_room(0, 0, world, player)
    assert player.food == 0
    assert world.post_room_mode

def test_wanderer_steals_item(world, player):
    import data.items as items_module
    _setup_room(world, player, "wanderer")
    player.inventory = [items_module.ALL_ITEMS["Potion"]]
    with patch('random.randint', return_value=5), \
         patch('random.randrange', return_value=0):  # sub=5, steal index 0
        enter_room(0, 0, world, player)
    assert player.inventory == []
    assert world.post_room_mode

def test_wanderer_steals_item_gracefully_when_empty(world, player):
    _setup_room(world, player, "wanderer")
    player.inventory = []
    with patch('random.randint', return_value=5):   # sub=5, nothing to steal
        enter_room(0, 0, world, player)
    assert world.post_room_mode

def test_wanderer_ambush_starts_combat(world, player):
    _setup_room(world, player, "wanderer")
    with patch('random.randint', return_value=7):   # sub=7 → ambush
        enter_room(0, 0, world, player)
    assert world.in_combat


# ── return_to_village: new temp bonus / cooldown fields ──────────────────────

def test_return_to_village_clears_temp_defense_bonus(world, player):
    player.temp_defense_bonus = 2
    world.adventure_origin = "village"
    return_to_village(world, player)
    assert player.temp_defense_bonus == 0

def test_return_to_village_clears_temp_max_health_bonus(world, player):
    player.temp_max_health_bonus = 3
    world.adventure_origin = "village"
    return_to_village(world, player)
    assert player.temp_max_health_bonus == 0

def test_return_to_village_clears_status_effect_cooldowns(world, player):
    player.status_effect_cooldowns = {"poison": 3, "cursed": 1}
    world.adventure_origin = "village"
    return_to_village(world, player)
    assert player.status_effect_cooldowns == {}
