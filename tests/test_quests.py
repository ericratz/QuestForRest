'''
tests/test_quests.py
Unit tests for quest_progress, check_new_completions, and check_achievements.
'''

import pytest
from state.gamestate import PlayerState, WorldState
from data.quests import (
    QUESTS, quest_progress, check_new_completions,
    check_achievements, unlock_achievement,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def player():
    return PlayerState()

@pytest.fixture
def world():
    return WorldState()


def _quest(qid):
    '''Return the quest dict for a given id.'''
    return next(q for q in QUESTS if q["id"] == qid)


# ── quest_progress: debt ──────────────────────────────────────────────────────

def test_debt_progress_full_debt(player):
    player.debt = 100
    prog, target = quest_progress(_quest("debt"), player)
    assert prog == 0
    assert target == 100

def test_debt_progress_partial(player):
    player.debt = 40
    prog, target = quest_progress(_quest("debt"), player)
    assert prog == 60
    assert target == 100

def test_debt_progress_paid(player):
    player.debt = 0
    prog, target = quest_progress(_quest("debt"), player)
    assert prog == 100
    assert target == 100

def test_debt_progress_capped_at_target(player):
    '''Overpaying should not exceed target.'''
    player.debt = -10
    prog, target = quest_progress(_quest("debt"), player)
    assert prog <= target


# ── quest_progress: second_debt ───────────────────────────────────────────────

def test_second_debt_progress_full(player):
    player.debt = 200
    prog, target = quest_progress(_quest("second_debt"), player)
    assert prog == 0
    assert target == 200

def test_second_debt_progress_partial(player):
    player.debt = 100
    prog, target = quest_progress(_quest("second_debt"), player)
    assert prog == 100
    assert target == 200

def test_second_debt_paid(player):
    player.debt = 0
    prog, target = quest_progress(_quest("second_debt"), player)
    assert prog == 200
    assert target == 200


# ── quest_progress: kills ─────────────────────────────────────────────────────

def test_kills_no_baseline(player):
    player.kills = 5
    player.quest_snapshots = {}   # no snapshot → baseline defaults to current kills
    prog, target = quest_progress(_quest("kill_3"), player)
    # baseline = kills = 5, progress = 5-5 = 0
    assert prog == 0

def test_kills_with_baseline(player):
    player.kills = 8
    player.quest_snapshots = {"kill_3": 5}
    prog, target = quest_progress(_quest("kill_3"), player)
    assert prog == 3
    assert target == 3

def test_kills_completed(player):
    player.kills = 10
    player.quest_snapshots = {"kill_10": 0}
    prog, target = quest_progress(_quest("kill_10"), player)
    assert prog >= target


# ── quest_progress: bosses ────────────────────────────────────────────────────

def test_bosses_no_kills(player):
    player.boss_kills = 0
    player.quest_snapshots = {"kill_boss": 0}
    prog, target = quest_progress(_quest("kill_boss"), player)
    assert prog == 0
    assert target == 1

def test_bosses_one_kill(player):
    player.boss_kills = 1
    player.quest_snapshots = {"kill_boss": 0}
    prog, target = quest_progress(_quest("kill_boss"), player)
    assert prog == 1
    assert target == 1


# ── quest_progress: equip ─────────────────────────────────────────────────────

def test_equip_not_equipped(player):
    prog, target = quest_progress(_quest("rusty_sword"), player)
    assert prog == 0

def test_equip_is_equipped(player):
    import data.items as items_module
    player.equipment["weapon"] = items_module.ALL_ITEMS["Rusty Sword"]
    prog, target = quest_progress(_quest("rusty_sword"), player)
    assert prog == 1
    assert target == 1


# ── quest_progress: slots ─────────────────────────────────────────────────────

def test_slots_empty(player):
    prog, target = quest_progress(_quest("all_slots"), player)
    assert prog == 0
    assert target == 7

def test_slots_partial(player):
    import data.items as items_module
    player.equipment["weapon"] = items_module.ALL_ITEMS["Rusty Sword"]
    prog, target = quest_progress(_quest("all_slots"), player)
    assert prog == 1

def test_slots_full(player):
    import data.items as items_module
    from state.gamestate import EQUIPMENT_SLOTS
    items = [i for i in items_module.ALL_ITEMS.values()
             if not i.consumable]
    slot_map = {}
    for item in items:
        if item.slot not in slot_map:
            slot_map[item.slot] = item
    for slot in EQUIPMENT_SLOTS:
        if slot in slot_map:
            player.equipment[slot] = slot_map[slot]
    prog, target = quest_progress(_quest("all_slots"), player)
    assert prog == target


# ── quest_progress: stash_count ───────────────────────────────────────────────

def test_stash_count_empty(player):
    player.stash = []
    prog, target = quest_progress(_quest("collector"), player)
    assert prog == 0

def test_stash_count_ten(player):
    import data.items as items_module
    potion = items_module.ALL_ITEMS["Potion"]
    player.stash = [potion] * 10
    prog, target = quest_progress(_quest("collector"), player)
    assert prog == 10
    assert target == 10


# ── quest_progress: exterminator ─────────────────────────────────────────────

def test_exterminator_no_kills(player):
    player.kill_counts = {}
    prog, target = quest_progress(_quest("exterminator"), player)
    assert prog == 0

def test_exterminator_with_kills(player):
    player.kill_counts = {"Goblin": 5, "Bat": 2}
    player.quest_snapshots = {"exterminator": {"Goblin": 0, "Bat": 0}}
    prog, target = quest_progress(_quest("exterminator"), player)
    assert prog == 5
    assert target == 5

def test_exterminator_baseline_subtracted(player):
    player.kill_counts = {"Goblin": 7}
    player.quest_snapshots = {"exterminator": {"Goblin": 3}}
    prog, target = quest_progress(_quest("exterminator"), player)
    assert prog == 4


# ── check_new_completions ─────────────────────────────────────────────────────

def test_check_new_completions_debt_paid(player):
    player.debt = 0
    player.active_quests = {"debt"}
    player.quests_complete = set()
    newly = check_new_completions(player)
    assert any("Debt" in n or "debt" in n.lower() or n == "Settle Your Debt" for n in newly)

def test_check_new_completions_awards_gold(player):
    player.debt = 0
    player.active_quests = {"debt"}
    player.quests_complete = set()
    before = player.gold
    check_new_completions(player)
    assert player.gold >= before   # reward gold added

def test_check_new_completions_does_not_double_award(player):
    player.debt = 0
    player.active_quests = {"debt"}
    player.quests_complete = {"debt"}   # already done
    before = player.gold
    check_new_completions(player)
    assert player.gold == before

def test_check_new_completions_inactive_quest_ignored(player):
    player.kills = 999
    player.active_quests = set()   # kill quests not active
    player.quests_complete = set()
    newly = check_new_completions(player)
    # None of the kill quest names should appear
    assert newly == []

def test_check_new_completions_marks_complete(player):
    player.debt = 0
    player.active_quests = {"debt"}
    player.quests_complete = set()
    check_new_completions(player)
    assert "debt" in player.quests_complete


# ── check_achievements ────────────────────────────────────────────────────────

def test_pacifist_triggers_at_6_rooms(player, world):
    world.in_adventure = True
    player.consecutive_peaceful_rooms = 6
    newly = check_achievements(world, player)
    assert "Pacifist" in newly

def test_pacifist_not_triggered_at_5_rooms(player, world):
    world.in_adventure = True
    player.consecutive_peaceful_rooms = 5
    newly = check_achievements(world, player)
    assert "Pacifist" not in newly

def test_pacifist_not_triggered_outside_adventure(player, world):
    world.in_adventure = False
    player.consecutive_peaceful_rooms = 6
    newly = check_achievements(world, player)
    assert "Pacifist" not in newly

def test_merchants_friend_triggers_at_150g(player, world):
    player.total_spent_gold = 150
    newly = check_achievements(world, player)
    assert "Merchant's Friend" in newly

def test_merchants_friend_not_triggered_below_150g(player, world):
    player.total_spent_gold = 149
    newly = check_achievements(world, player)
    assert "Merchant's Friend" not in newly

def test_achievement_not_awarded_twice(player, world):
    player.consecutive_peaceful_rooms = 6
    check_achievements(world, player)
    before = player.gold
    world.achievement_popup.clear()
    check_achievements(world, player)
    assert player.gold == before   # second call adds no gold


# ── unlock_achievement ────────────────────────────────────────────────────────

def test_unlock_achievement_adds_gold(player, world):
    before = player.gold
    unlock_achievement("iron_will", world, player)
    assert player.gold > before

def test_iron_will_reward_is_25g(player, world):
    before = player.gold
    unlock_achievement("iron_will", world, player)
    assert player.gold - before == 25

def test_unlock_achievement_queues_popup(player, world):
    unlock_achievement("iron_will", world, player)
    assert "Iron Will" in world.achievement_popup

def test_unlock_achievement_is_idempotent(player, world):
    unlock_achievement("iron_will", world, player)
    gold_after_first = player.gold
    unlock_achievement("iron_will", world, player)
    assert player.gold == gold_after_first


# ── check_achievements: additional cases ──────────────────────────────────────

def test_speed_run_not_triggered_by_check_achievements(player, world):
    '''speed_run is unlocked in handle_victory directly, not via check_achievements.'''
    newly = check_achievements(world, player)
    assert "Speed Run" not in newly

def test_iron_will_not_triggered_by_check_achievements(player, world):
    '''iron_will is unlocked in handle_victory directly, not via check_achievements.'''
    player.health = 1
    newly = check_achievements(world, player)
    assert "Iron Will" not in newly

def test_collector_not_triggered_by_check_achievements(player, world):
    '''collector achievement doesn't exist in check_achievements; stash count is a quest type.'''
    player.stash = [None] * 20
    newly = check_achievements(world, player)
    assert "Collector" not in newly


# ── refresh_questboard ────────────────────────────────────────────────────────

from data.quests import refresh_questboard, QUESTS

def test_refresh_questboard_picks_available_quest(world, player):
    world.questboard_day = -1   # force refresh
    refresh_questboard(world, player)
    assert world.questboard_quest_id is not None

def test_refresh_questboard_excludes_active_quests(world, player):
    world.questboard_day = -1
    all_ids = {q["id"] for q in QUESTS
               if q["id"] not in ("debt", "second_debt")
               and not q.get("area")}
    player.active_quests  = all_ids.copy()
    player.quests_complete = set()
    refresh_questboard(world, player)
    # Only Duskwall quests remain (require duskwall_unlocked) → None
    assert world.questboard_quest_id is None

def test_refresh_questboard_no_duskwall_quests_without_unlock(world, player):
    world.questboard_day    = -1
    world.duskwall_unlocked = False
    refresh_questboard(world, player)
    if world.questboard_quest_id:
        chosen = next(q for q in QUESTS if q["id"] == world.questboard_quest_id)
        assert not chosen.get("area")

def test_refresh_questboard_allows_duskwall_quests_when_unlocked(world, player):
    world.questboard_day    = -1
    world.duskwall_unlocked = True
    # Mark all non-duskwall quests as complete to force a duskwall pick
    non_dusk = {q["id"] for q in QUESTS
                if q["id"] not in ("debt", "second_debt") and not q.get("area")}
    player.quests_complete = non_dusk
    refresh_questboard(world, player)
    if world.questboard_quest_id:
        chosen = next(q for q in QUESTS if q["id"] == world.questboard_quest_id)
        assert chosen.get("area") == "duskwall"

def test_refresh_questboard_same_day_no_change(world, player):
    world.questboard_day    = world.day   # already refreshed today
    world.questboard_quest_id = "kill_3"
    refresh_questboard(world, player)
    assert world.questboard_quest_id == "kill_3"   # unchanged


# ── Dialogue condition selection ──────────────────────────────────────────────

import data.dialogue as dialogue_module

def test_dialogue_mystic_familiar_found_branch(world, player):
    player.familiar.found = True
    lines, _ = dialogue_module.get_lines("duskwall_mystic", world, player)
    assert any("companion" in l.lower() or "bond" in l.lower() or "watches" in l.lower()
               for l in lines)

def test_dialogue_mystic_ruins_complete_branch(world, player):
    player.familiar.found = False
    world.adventure_locations_complete = [2]
    lines, _ = dialogue_module.get_lines("duskwall_mystic", world, player)
    assert any("Ruins" in l or "creature" in l.lower() or "waiting" in l.lower()
               for l in lines)

def test_dialogue_mystic_default_branch(world, player):
    player.familiar.found = False
    world.adventure_locations_complete = []
    lines, _ = dialogue_module.get_lines("duskwall_mystic", world, player)
    assert any("Ruins" in l or "proven" in l.lower() for l in lines)

def test_dialogue_innkeeper_debt_paid_branch(world, player):
    player.debt = 0
    world.adventure_locations_complete = []
    lines, _ = dialogue_module.get_lines("restholm_innkeeper", world, player)
    assert any("paid" in l.lower() or "welcome" in l.lower() for l in lines)

def test_dialogue_innkeeper_default_branch(world, player):
    player.debt = 50
    world.day   = 1
    world.adventure_locations_complete = []
    lines, _ = dialogue_module.get_lines("restholm_innkeeper", world, player)
    assert isinstance(lines, list) and len(lines) > 0

def test_dialogue_unknown_npc_returns_ellipsis(world, player):
    lines, _ = dialogue_module.get_lines("fake_npc_xyz", world, player)
    assert lines == ["..."]


# ── Duskwall marks regression ─────────────────────────────────────────────────

def test_second_debt_reward_goes_to_marks(player):
    '''Completing second_debt quest awards marks, not gold.'''
    player.debt = 0
    player.active_quests = {"second_debt"}
    player.quests_complete = set()
    gold_before  = player.gold
    marks_before = player.marks
    check_new_completions(player)
    assert player.gold  == gold_before,       "second_debt should NOT award gold"
    assert player.marks == marks_before + 50, "second_debt should award 50 marks"

def test_duskwall_quest_reward_goes_to_marks(player):
    '''Duskwall-tagged bounty quests reward marks.'''
    dusk_quest = next(q for q in QUESTS if q.get("area") == "duskwall" and q["reward"] > 0
                      and q["id"] not in ("second_debt",))
    player.active_quests  = {dusk_quest["id"]}
    player.quests_complete = set()
    # Force quest progress to completion
    if dusk_quest["type"] == "kills":
        player.kills = dusk_quest["target"] * 10
        player.quest_snapshots[dusk_quest["id"]] = 0
    elif dusk_quest["type"] == "bosses":
        player.boss_kills = dusk_quest["target"]
        player.quest_snapshots[dusk_quest["id"]] = 0
    elif dusk_quest["type"] == "survivalist":
        player.survivalist_completions = 1
        player.quest_snapshots[dusk_quest["id"]] = 0
    elif dusk_quest["type"] == "exterminator":
        player.kill_counts = {"Crumbled Knight": dusk_quest["target"]}
        player.quest_snapshots[dusk_quest["id"]] = {}
    gold_before  = player.gold
    marks_before = player.marks
    check_new_completions(player)
    assert player.gold  == gold_before,  "Duskwall bounty should NOT award gold"
    assert player.marks >  marks_before, "Duskwall bounty should award marks"

def test_restholm_quest_reward_goes_to_gold(player):
    '''Non-Duskwall quests still award gold.'''
    player.debt = 0
    player.active_quests  = {"debt"}
    player.quests_complete = set()
    gold_before  = player.gold
    marks_before = player.marks
    check_new_completions(player)
    assert player.gold  > gold_before,   "Restholm quest should award gold"
    assert player.marks == marks_before, "Restholm quest should NOT award marks"

def test_check_new_completions_second_debt_idempotent(player):
    '''second_debt does not double-award marks.'''
    player.debt = 0
    player.active_quests  = {"second_debt"}
    player.quests_complete = {"second_debt"}   # already complete
    marks_before = player.marks
    check_new_completions(player)
    assert player.marks == marks_before

def test_duskwall_bounty_board_shows_dusk_quests_only(world, player):
    '''refresh_questboard in Duskwall only picks duskwall-tagged quests.'''
    from data.quests import refresh_questboard
    world.area          = "duskwall"
    world.questboard_day = -1
    refresh_questboard(world, player)
    if world.questboard_quest_id:
        chosen = next(q for q in QUESTS if q["id"] == world.questboard_quest_id)
        assert chosen.get("area") == "duskwall"

def test_duskwall_bounty_board_excludes_npc_story_quests(world, player):
    '''NPC story quests (guildmaster, mystic) never appear on the bounty board.'''
    from data.quests import refresh_questboard
    _story = {"innkeeper_quest", "guildmaster_quest", "mystic_quest"}
    world.area          = "duskwall"
    world.questboard_day = -1
    for _ in range(20):   # run many times to catch random picks
        world.questboard_day = -1
        player.active_quests  = set()
        player.quests_complete = set()
        refresh_questboard(world, player)
        assert world.questboard_quest_id not in _story

def test_second_debt_quest_has_duskwall_area_tag():
    '''second_debt must be tagged area=duskwall so rewards route to marks.'''
    q = next(q for q in QUESTS if q["id"] == "second_debt")
    assert q.get("area") == "duskwall"

def test_dialogue_get_lines_returns_tuple(world, player):
    '''get_lines returns (lines, post_action) tuple.'''
    result = dialogue_module.get_lines("restholm_innkeeper", world, player)
    assert isinstance(result, tuple) and len(result) == 2
    lines, action = result
    assert isinstance(lines, list)

def test_dialogue_merchant_exists(world, player):
    '''duskwall_merchant NPC is defined and returns lines.'''
    lines, _ = dialogue_module.get_lines("duskwall_merchant", world, player)
    assert isinstance(lines, list) and len(lines) > 0
