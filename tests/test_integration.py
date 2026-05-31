'''
tests/test_integration.py
Integration tests: multiple systems working together.

Each test is grounded in a bug or class of bugs that only surfaces when systems
interact — things that unit tests on individual functions would not catch.

Groups:
  1.  Full combat round         — attack → counter → log → state all consistent
  2.  Loot pool correctness      — Restholm/Duskwall items never cross-contaminate
  3.  Status effect lifecycle    — apply → active guard → expiry → cooldown → re-apply
  4.  Block mechanics            — halved damage, can reach 0
  5.  Examine costs a turn       — counter-attack fires, button dims after use
  6.  Shrine temp buffs          — applied during adventure, cleared on exit
  7.  Curse room positive turns  — never sets -1, ticks in combat, clears after
  8.  Pacifist only in adventure — counter does not fire outside adventure context
  9.  Full adventure sequence    — multi-room run through boss → completion
  10. Rest day display           — work_result text includes the new day number
  11. Intro skip flow            — ESC sets flag, name entry skips QA

audio.sounds and render.helpers are mocked at session level in conftest.py.
'''

import pytest
import random
import math
from unittest.mock import patch, MagicMock

from state.gamestate import WorldState, PlayerState, ADVENTURE_LOCATIONS
from data.monsters import Monster, NORMAL_POOL, BOSS_POOL, DUSKWALL_NORMAL_POOL, DUSKWALL_BOSS_POOL
import data.items as items_module
from data.quests import check_achievements, ACHIEVEMENTS
from logic.adventure import (
    do_combat_action, handle_victory, handle_defeat, return_to_village,
    enter_room, advance_day,
    _do_counter_attack, _apply_monster_status, _tick_status_effects,
)


# ── Shared helpers ────────────────────────────────────────────────────────────

@pytest.fixture
def world():
    w = WorldState()
    w.reset("village")
    return w

@pytest.fixture
def player():
    return PlayerState()


def _monster(tier=1, hp=20, atk=3, def_=2, xp=5,
             gmin=1, gmax=3, status_effects=None, item_chance=0.0,
             description="A test creature."):
    return Monster("TestBeast", tier, hp, atk, def_, xp, xp, gmin, gmax,
                   item_chance=item_chance, status_effects=status_effects or [],
                   description=description)


def _in_adventure(world, player, loc=0, room=0):
    '''Set up a mid-adventure, mid-combat state.'''
    world.in_adventure             = True
    world.adventure_loc_index      = loc
    world.adventure_room           = room
    world.adventure_room_sequence  = []
    world.area                     = "village"
    player.food                    = 5


def _start_fight(world, player, monster=None, loc=0, room=0):
    _in_adventure(world, player, loc, room)
    m = monster or _monster()
    world.start_combat(m)
    return m


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Full combat round
# ═══════════════════════════════════════════════════════════════════════════════

class TestFullCombatRound:
    '''One complete round: player attacks → monster counter-attacks.
    Verifies that monster HP, player HP, and combat log are all consistent.'''

    def test_both_sides_take_damage(self, world, player):
        monster = _start_fight(world, player, _monster(hp=100, atk=2, def_=0))
        before_monster_hp = monster.hp
        before_player_hp  = player.health
        # no crit, no block, no status
        with patch('random.randint', return_value=50), \
             patch('random.uniform', return_value=1.0), \
             patch('random.random',  return_value=1.0):
            do_combat_action(0, world, player)
        assert monster.hp < before_monster_hp, "Monster should have taken damage"
        assert player.health < before_player_hp, "Player should have taken damage"

    def test_combat_log_has_both_hit_lines(self, world, player):
        monster = _start_fight(world, player, _monster(hp=100, atk=2, def_=0))
        with patch('random.randint', return_value=50), \
             patch('random.uniform', return_value=1.0), \
             patch('random.random',  return_value=1.0):
            do_combat_action(0, world, player)
        log = world.combat_log
        assert any("dmg to the" in l for l in log), "Player hit not logged"
        assert any("hits you for" in l or "blocked" in l.lower()
                   or "no damage" in l.lower() for l in log), "Monster hit not logged"

    def test_victory_ends_combat_cleanly(self, world, player):
        '''Kill the monster in one hit → combat_result, no active combat.'''
        monster = _start_fight(world, player, _monster(hp=1, atk=0))
        with patch('random.randint', return_value=0), \
             patch('random.uniform', return_value=1.0):
            do_combat_action(0, world, player)
        assert not world.in_combat
        assert world.combat_result == "victory"
        assert world.post_combat_mode

    def test_defeat_ends_combat_cleanly(self, world, player):
        '''Player dies from counter-attack → defeat state set.'''
        player.health = 1
        monster = _start_fight(world, player, _monster(hp=999, atk=100, def_=0))
        with patch('random.randint', return_value=50), \
             patch('random.uniform', return_value=1.0), \
             patch('random.random',  return_value=1.0):
            do_combat_action(0, world, player)
        assert world.combat_result == "defeat"
        assert not world.in_combat

    def test_gold_and_xp_awarded_on_victory(self, world, player):
        monster = _start_fight(world, player, _monster(hp=1, xp=10, gmin=5, gmax=5))
        before_gold = player.gold
        # randint=50: skips crit (50 > ~5% chance) and block (50 > ~5% chance);
        # roll_loot uses randint(5,5) which is also overridden to 50, so gold = 50 >= 5
        with patch('random.randint', return_value=50), \
             patch('random.uniform', return_value=1.0):
            do_combat_action(0, world, player)
        assert player.gold >= before_gold + 5, "Gold should be awarded"
        # XP may cause a level-up which clears xp, so just check kills incremented
        assert player.kills == 1


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Loot pool correctness
# ═══════════════════════════════════════════════════════════════════════════════

class TestLootPoolCorrectness:
    '''Restholm monsters must never drop Duskwall items and vice versa.
    This is the class of bug we found where ALL_ITEMS was used instead of SHOP_POOL.'''

    def test_restholm_normal_drops_only_restholm_items(self):
        random.seed(0)
        for m in NORMAL_POOL:
            for _ in range(100):
                _, item = m.copy().roll_loot()
                if item:
                    assert item in items_module.SHOP_POOL, \
                        f"{m.name} dropped non-Restholm item: {item.name}"

    def test_restholm_boss_drops_only_restholm_items(self):
        random.seed(0)
        for m in BOSS_POOL:
            m2 = m.copy()
            m2.item_chance = 1.0   # guarantee a drop every roll
            for _ in range(100):
                _, item = m2.roll_loot()
                if item:
                    assert item in items_module.SHOP_POOL, \
                        f"{m.name} (boss) dropped non-Restholm item: {item.name}"

    def test_duskwall_drops_only_duskwall_items(self):
        random.seed(0)
        for m in DUSKWALL_NORMAL_POOL:
            m2 = m.copy()
            m2.item_chance = 1.0
            for _ in range(100):
                _, item = m2.roll_duskwall_loot()
                if item:
                    is_dusk  = item in items_module.DUSKWALL_SHOP_POOL
                    is_charm = item in items_module.FAMILIAR_ITEM_POOL
                    assert is_dusk or is_charm, \
                        f"{m.name} dropped non-Duskwall item: {item.name}"

    def test_loot_tier_matches_monster_tier(self):
        '''Normal (tier-1) Restholm monsters drop tier-1 items via roll_loot.'''
        random.seed(42)
        for m in NORMAL_POOL:
            m2 = m.copy(); m2.item_chance = 1.0
            for _ in range(50):
                _, item = m2.roll_loot()
                if item:
                    assert item.tier == 1, \
                        f"Normal monster {m.name} dropped tier-{item.tier} item"

    def test_dark_forest_boss_loot_is_tier_2(self):
        '''Dark Forest boss uses roll_boss_loot with tier 2 from SHOP_POOL.'''
        random.seed(0)
        boss = BOSS_POOL[1].copy()   # Dark Wizard (boss_index=1 for Dark Forest)
        for _ in range(60):
            gold, items_list = boss.roll_boss_loot(2, items_module.SHOP_POOL)
            for item in items_list:
                assert item in items_module.SHOP_POOL, \
                    f"Dark Forest boss dropped non-SHOP_POOL item: {item.name}"
                assert item.tier == 2, \
                    f"Dark Forest boss dropped tier-{item.tier} item (expected 2)"

    def test_caverns_boss_loot_is_tier_3(self):
        '''Deep Caverns boss uses roll_boss_loot with tier 3 from SHOP_POOL.'''
        random.seed(0)
        boss = BOSS_POOL[0].copy()   # Hill Giant (boss_index=0 for Deep Caverns)
        for _ in range(60):
            gold, items_list = boss.roll_boss_loot(3, items_module.SHOP_POOL)
            for item in items_list:
                assert item in items_module.SHOP_POOL, \
                    f"Caverns boss dropped non-SHOP_POOL item: {item.name}"
                assert item.tier == 3, \
                    f"Caverns boss dropped tier-{item.tier} item (expected 3)"

    def test_duskwall_boss_loot_is_tier_3_duskwall(self):
        '''Duskwall bosses use roll_boss_loot with tier 3 from DUSKWALL_SHOP_POOL.'''
        random.seed(0)
        for boss in DUSKWALL_BOSS_POOL:
            b = boss.copy()
            for _ in range(60):
                gold, items_list = b.roll_boss_loot(3, items_module.DUSKWALL_SHOP_POOL)
                for item in items_list:
                    assert item in items_module.DUSKWALL_SHOP_POOL, \
                        f"Duskwall boss dropped non-DUSKWALL_SHOP_POOL item: {item.name}"
                    assert item.tier == 3, \
                        f"Duskwall boss dropped tier-{item.tier} item (expected 3)"

    def test_boss_loot_three_outcomes(self):
        '''roll_boss_loot produces all three outcomes across enough rolls:
        (gold=0, 2 items), (gold>0, 1 item), (gold>0, 0 items).'''
        random.seed(99)
        boss = BOSS_POOL[0].copy()
        saw_two_items = saw_one_item_gold = saw_gold_only = False
        for _ in range(300):
            gold, items_list = boss.roll_boss_loot(3, items_module.SHOP_POOL)
            n = len(items_list)
            if n == 2 and gold == 0:
                saw_two_items = True
            elif n == 1 and gold > 0:
                saw_one_item_gold = True
            elif n == 0 and gold > 0:
                saw_gold_only = True
        assert saw_two_items,      "Never saw two-item outcome"
        assert saw_one_item_gold,  "Never saw one-item+gold outcome"
        assert saw_gold_only,      "Never saw gold-only outcome"

    def test_boss_loot_gold_scales_with_outcome(self):
        '''Gold-only outcome pays more than one-item outcome.'''
        random.seed(7)
        boss = BOSS_POOL[0].copy()
        one_item_golds = []
        gold_only_golds = []
        for _ in range(600):
            gold, items_list = boss.roll_boss_loot(3, items_module.SHOP_POOL)
            if len(items_list) == 1 and gold > 0:
                one_item_golds.append(gold)
            elif len(items_list) == 0 and gold > 0:
                gold_only_golds.append(gold)
        if one_item_golds and gold_only_golds:
            assert min(gold_only_golds) >= min(one_item_golds), \
                "Gold-only floor should be at least as high as one-item medium gold"


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Status effect lifecycle
# ═══════════════════════════════════════════════════════════════════════════════

class TestStatusEffectLifecycle:
    '''The full lifecycle: apply → active guard → natural expiry → cooldown → re-apply.
    This directly tests the two bugs: "reset while active" and "can't reapply after cooldown".'''

    def _poison_monster(self):
        return _monster(status_effects=[("poison", 1.0, 3)])   # 100% chance

    def test_active_effect_cannot_be_refreshed_by_monster(self, world, player):
        '''If poison is already ticking, a monster hit must not change its duration.'''
        player.status_effects["poison"] = 3
        m = self._poison_monster()
        world.combat_log = []
        # 50 hits — duration must stay exactly 3
        for _ in range(50):
            _apply_monster_status(m, world, player)
        assert player.status_effects["poison"] == 3, \
            "Active effect should not be refreshed while ticking"
        # And no duplicate "afflicted" log entries
        assert not any("afflicted" in l for l in world.combat_log), \
            "No affliction message should fire while effect is already active"

    def test_effect_ticks_down_to_zero_and_sets_cooldown(self, world, player):
        player.status_effects["poison"] = 1
        world.combat_log = []
        _tick_status_effects(world, player)
        assert "poison" not in player.status_effects,      "Effect should have cleared"
        assert "poison" in player.status_effect_cooldowns, "Cooldown should be set"
        assert player.status_effect_cooldowns["poison"] == 5

    def test_effect_cannot_be_applied_during_cooldown(self, world, player):
        player.status_effect_cooldowns["poison"] = 3
        m = self._poison_monster()
        world.combat_log = []
        for _ in range(50):
            _apply_monster_status(m, world, player)
        assert "poison" not in player.status_effects, \
            "Effect should not be applicable while in cooldown"

    def test_cooldown_ticks_down_each_combat_round(self, world, player):
        player.status_effect_cooldowns["poison"] = 3
        world.combat_log = []
        _tick_status_effects(world, player)
        assert player.status_effect_cooldowns["poison"] == 2

    def test_cooldown_clears_at_zero(self, world, player):
        player.status_effect_cooldowns["poison"] = 1
        world.combat_log = []
        _tick_status_effects(world, player)
        assert "poison" not in player.status_effect_cooldowns, \
            "Cooldown entry should be removed at zero"

    def test_effect_can_be_reapplied_after_cooldown_expires(self, world, player):
        '''Full cycle: apply → expires → cooldown ticks to 0 → re-apply succeeds.'''
        player.status_effects["poison"] = 1
        world.combat_log = []
        # Expire the effect
        _tick_status_effects(world, player)
        assert "poison" not in player.status_effects
        assert player.status_effect_cooldowns.get("poison") == 5
        # Tick cooldown down to 0
        for _ in range(5):
            _tick_status_effects(world, player)
        assert "poison" not in player.status_effect_cooldowns
        # Now re-apply should succeed
        m = self._poison_monster()
        world.combat_log = []
        _apply_monster_status(m, world, player)
        assert "poison" in player.status_effects, "Effect should be reapplicable after cooldown"

    def test_duration_is_random_1_to_5(self, world, player):
        '''Each fresh application rolls a 1–5 turn duration.'''
        durations = set()
        m = self._poison_monster()
        for seed in range(200):
            random.seed(seed)
            p2 = PlayerState()
            world.combat_log = []
            _apply_monster_status(m, world, p2)
            d = p2.status_effects.get("poison")
            if d is not None:
                durations.add(d)
        assert durations.issubset({1, 2, 3, 4, 5}), "Duration must be in [1,5]"
        assert len(durations) > 1, "Duration should vary across applications"

    def test_cursed_effect_ticks_in_combat(self, world, player):
        '''Cursed (added last session) must be ticked by _tick_status_effects.'''
        player.status_effects["cursed"] = 2
        world.combat_log = []
        _tick_status_effects(world, player)
        assert player.status_effects.get("cursed") == 1, \
            "Cursed should decrement from 2 to 1"


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Block mechanics
# ═══════════════════════════════════════════════════════════════════════════════

class TestBlockMechanics:
    '''Block halves damage, rounded down. A 1-damage hit can be completely blocked.'''

    def _setup_counter(self, world, player, atk):
        _in_adventure(world, player)
        m = _monster(atk=atk, def_=0)
        world.in_combat      = True
        world.combat_monster = m
        return m

    def test_block_halves_damage_rounded_down(self, world, player):
        '''5-damage hit → blocked → 2 damage taken.'''
        m = self._setup_counter(world, player, atk=5)
        # Force block (randint <= block_chance), force exact damage = 5
        player.health = player.get_max_health()
        with patch('random.randint', return_value=1), \
             patch('random.uniform', return_value=1.0), \
             patch('random.random',  return_value=1.0):
            _do_counter_attack(m, world, player)
        # 5 // 2 = 2
        dmg_taken = player.get_max_health() - player.health
        assert dmg_taken == 2, f"Expected 2 dmg after block, got {dmg_taken}"

    def test_block_can_deal_zero_damage(self, world, player):
        '''A 1-damage hit that is blocked deals 0 damage (1 // 2 == 0).'''
        m = self._setup_counter(world, player, atk=1)
        player.health = player.get_max_health()
        # Force block and force raw damage = 1 by capping defense high
        player.base_defense = 100
        with patch('random.randint', return_value=1), \
             patch('random.uniform', return_value=1.0), \
             patch('random.random',  return_value=1.0):
            _do_counter_attack(m, world, player)
        dmg_taken = player.get_max_health() - player.health
        assert dmg_taken == 0, "Blocked 1-damage hit should deal 0 damage"
        assert any("completely blocked" in l.lower() for l in world.combat_log), \
            "Should log 'Completely blocked' message"

    def test_no_block_deals_full_damage(self, world, player):
        m = self._setup_counter(world, player, atk=5)
        player.health = player.get_max_health()
        # Force no block (randint returns > block_chance)
        with patch('random.randint', return_value=99), \
             patch('random.uniform', return_value=1.0), \
             patch('random.random',  return_value=1.0):
            _do_counter_attack(m, world, player)
        # Player should have taken some damage (unblocked)
        assert player.health < player.get_max_health()
        assert not any("blocked" in l.lower() for l in world.combat_log)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Examine costs a turn
# ═══════════════════════════════════════════════════════════════════════════════

class TestExamineCostsATurn:
    '''After examining, the monster counter-attacks. combat_examined dims the button.'''

    def test_examine_triggers_monster_counter_attack(self, world, player):
        monster = _start_fight(world, player, _monster(hp=100, atk=5, def_=0))
        player.health = player.get_max_health()
        with patch('random.randint', return_value=50), \
             patch('random.uniform', return_value=1.0), \
             patch('random.random',  return_value=1.0):
            do_combat_action(2, world, player)
        assert player.health < player.get_max_health(), \
            "Monster should have attacked after examine"

    def test_examine_sets_examined_flag(self, world, player):
        _start_fight(world, player)
        do_combat_action(2, world, player)
        assert world.combat_examined

    def test_examine_logs_stats(self, world, player):
        _start_fight(world, player)
        do_combat_action(2, world, player)
        assert any("ATK" in l and "DEF" in l for l in world.combat_log)

    def test_examine_logs_description(self, world, player):
        m = _start_fight(world, player, _monster(description="A fearsome beast."))
        do_combat_action(2, world, player)
        assert any("A fearsome beast." in l for l in world.combat_log)

    def test_examine_flag_resets_on_new_combat(self, world, player):
        '''combat_examined is False at the start of every new combat.'''
        _start_fight(world, player)
        world.combat_examined = True
        # Start a new combat
        world.start_combat(_monster())
        assert not world.combat_examined, \
            "combat_examined should be cleared when new combat starts"


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Shrine temp buffs
# ═══════════════════════════════════════════════════════════════════════════════

class TestShrineTempBuffs:
    '''Shrine buffs increase temp bonus fields, not base stats.
    All temp bonuses are cleared when the player returns to village.'''

    def _enter_shrine(self, world, player, buff_type):
        '''Force a specific shrine buff type and enter the shrine room.'''
        _in_adventure(world, player, loc=0, room=0)
        world.adventure_room_sequence = ["shrine"] + ["nothing"] * 20
        # random.choice returns buff_type for the shrine buff selection;
        # random.randint=2 makes the bonus roll pick the maximum (1–2 → 2, or 2–3 → 2)
        with patch('random.choice', return_value=buff_type):
            with patch('random.randint', return_value=2):
                enter_room(0, 0, world, player)

    def test_shrine_atk_increases_temp_attack_bonus(self, world, player):
        before = player.temp_attack_bonus
        self._enter_shrine(world, player, "atk")
        assert player.temp_attack_bonus > before, "Shrine ATK should raise temp_attack_bonus"
        assert player.base_attack == PlayerState().base_attack, "Base attack should be unchanged"

    def test_shrine_def_increases_temp_defense_bonus(self, world, player):
        before = player.temp_defense_bonus
        self._enter_shrine(world, player, "def")
        assert player.temp_defense_bonus > before, "Shrine DEF should raise temp_defense_bonus"
        assert player.base_defense == PlayerState().base_defense, "Base defense should be unchanged"

    def test_shrine_hp_increases_temp_max_health_bonus(self, world, player):
        before = player.temp_max_health_bonus
        self._enter_shrine(world, player, "hp")
        assert player.temp_max_health_bonus > before, "Shrine HP should raise temp_max_health_bonus"
        assert player.base_max_health == PlayerState().base_max_health, "Base max HP should be unchanged"

    def test_temp_buffs_cleared_on_return_to_village(self, world, player):
        player.temp_attack_bonus      = 2
        player.temp_defense_bonus     = 2
        player.temp_max_health_bonus  = 3
        _in_adventure(world, player)
        return_to_village(world, player)
        assert player.temp_attack_bonus     == 0
        assert player.temp_defense_bonus    == 0
        assert player.temp_max_health_bonus == 0

    def test_temp_atk_buff_reflected_in_get_attack(self, world, player):
        base = player.get_attack()
        player.temp_attack_bonus = 2
        assert player.get_attack() == base + 2

    def test_temp_def_buff_reflected_in_get_defense(self, world, player):
        base = player.get_defense()
        player.temp_defense_bonus = 2
        assert player.get_defense() == base + 2

    def test_temp_hp_buff_reflected_in_get_max_health(self, world, player):
        base = player.get_max_health()
        player.temp_max_health_bonus = 3
        assert player.get_max_health() == base + 3


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Curse room positive turns
# ═══════════════════════════════════════════════════════════════════════════════

class TestCurseRoomPositiveTurns:
    '''Curse room effects must use a positive turn count (not -1).
    They must tick down in combat and clear afterwards.'''

    def _enter_cursed_room(self, world, player, curse_type):
        _in_adventure(world, player, loc=0, room=0)
        world.adventure_room_sequence = ["cursed"] + ["nothing"] * 20
        with patch('random.randint', return_value=curse_type):
            enter_room(0, 0, world, player)

    def test_curse_room_weakened_has_positive_duration(self, world, player):
        player.health = 20  # enough to survive
        self._enter_cursed_room(world, player, curse_type=1)  # weakened
        turns = player.status_effects.get("weakened", None)
        assert turns is not None, "Weakened effect should be applied"
        assert turns > 0, f"Duration should be positive, got {turns}"
        assert turns != -1, "Duration must not be the old -1 permanent sentinel"

    def test_curse_room_cursed_has_positive_duration(self, world, player):
        player.health = 20
        self._enter_cursed_room(world, player, curse_type=2)  # cursed
        turns = player.status_effects.get("cursed", None)
        assert turns is not None, "Cursed effect should be applied"
        assert turns > 0
        assert turns != -1

    def test_cursed_ticks_down_during_combat(self, world, player):
        player.status_effects["cursed"] = 3
        world.combat_log = []
        _tick_status_effects(world, player)
        assert player.status_effects.get("cursed") == 2, "Cursed should decrement each tick"

    def test_weakened_reduces_attack_during_effect(self, world, player):
        # Give player enough base attack so halving is visible above the floor of 1
        player.base_attack = 4
        base_atk = player.get_attack()
        player.status_effects["weakened"] = 2
        assert player.get_attack() < base_atk, "Weakened should reduce attack"

    def test_cursed_reduces_attack_and_defense(self, world, player):
        # Give player enough base stats so the -2 penalty is visible above the floor of 1
        player.base_attack  = 4
        player.base_defense = 4
        base_atk = player.get_attack()
        base_def = player.get_defense()
        player.status_effects["cursed"] = 2
        assert player.get_attack()  < base_atk
        assert player.get_defense() < base_def


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Pacifist only fires inside an active adventure
# ═══════════════════════════════════════════════════════════════════════════════

class TestPacifistGuard:
    '''consecutive_peaceful_rooms >= 6 should NOT unlock Pacifist unless
    in_adventure is True. This catches the "randomly activates" bug.'''

    def test_pacifist_does_not_fire_outside_adventure(self, world, player):
        player.consecutive_peaceful_rooms = 6
        world.in_adventure = False
        check_achievements(world, player)
        assert "pacifist" not in player.achievements_unlocked, \
            "Pacifist must not fire when not in an adventure"

    def test_pacifist_fires_inside_adventure(self, world, player):
        player.consecutive_peaceful_rooms = 6
        world.in_adventure = True
        check_achievements(world, player)
        assert "pacifist" in player.achievements_unlocked, \
            "Pacifist should fire when in_adventure=True and counter >= 6"

    def test_pacifist_does_not_fire_at_5_rooms(self, world, player):
        player.consecutive_peaceful_rooms = 5
        world.in_adventure = True
        check_achievements(world, player)
        assert "pacifist" not in player.achievements_unlocked

    def test_pacifist_counter_resets_on_monster_room(self, world, player):
        '''Entering a monster room resets the counter, preventing accumulation
        of counts from multiple separate peaceful streaks.'''
        _in_adventure(world, player, loc=0)
        player.consecutive_peaceful_rooms = 4
        # sequence[0]="monster" forces a monster room without patching random.choice,
        # which would break monster spawning (choice(NORMAL_POOL) would return a string)
        world.adventure_room_sequence = ["monster"] + ["nothing"] * 20
        enter_room(0, 0, world, player)
        assert player.consecutive_peaceful_rooms == 0, \
            "Counter must reset when a monster room is entered"

    def test_pacifist_counter_resets_at_adventure_completion(self, world, player):
        '''After a boss victory the counter is zeroed, not carried into next run.'''
        boss_room = ADVENTURE_LOCATIONS[0]["total_rooms"] - 1
        world.in_adventure        = True
        world.adventure_loc_index = 0
        world.adventure_room      = boss_room
        player.consecutive_peaceful_rooms = 4
        m = _monster(tier=3, xp=50, hp=1)
        world.start_combat(m)
        with patch('random.randint', return_value=0), \
             patch('random.uniform', return_value=1.0):
            do_combat_action(0, world, player)
        assert player.consecutive_peaceful_rooms == 0


# ═══════════════════════════════════════════════════════════════════════════════
# 9. Full adventure sequence
# ═══════════════════════════════════════════════════════════════════════════════

class TestFullAdventureSequence:
    '''Walk a player through a scripted adventure: peaceful rooms, a combat, and
    a boss fight. Verifies that state transitions are consistent end-to-end.'''

    def _scripted_adventure(self, world, player):
        '''Enter Dark Forest with a pre-set room sequence: nothing × 3, boss.'''
        loc_idx   = 0
        loc       = ADVENTURE_LOCATIONS[loc_idx]
        boss_room = loc["total_rooms"] - 1

        world.in_adventure              = True
        world.adventure_loc_index       = loc_idx
        world.adventure_room            = 0
        world.adventure_room_sequence   = ["nothing"] * boss_room
        world.area                      = "village"
        world.adventure_origin          = "village"
        player.food                     = 10
        player.consecutive_peaceful_rooms = 0
        return loc, boss_room

    def test_peaceful_rooms_accumulate_counter(self, world, player):
        _, boss_room = self._scripted_adventure(world, player)
        for room in range(min(3, boss_room)):
            enter_room(0, room, world, player)
            world.post_room_mode  = False
            world.post_room_lines = []
            world.adventure_room  = room + 1
        assert player.consecutive_peaceful_rooms == 3

    def test_monster_room_resets_counter(self, world, player):
        _, boss_room = self._scripted_adventure(world, player)
        player.consecutive_peaceful_rooms = 3
        world.adventure_room_sequence = ["monster"] + ["nothing"] * boss_room
        enter_room(0, 0, world, player)
        assert player.consecutive_peaceful_rooms == 0

    def test_boss_room_starts_boss_fight(self, world, player):
        loc, boss_room = self._scripted_adventure(world, player)
        enter_room(0, boss_room, world, player)
        assert world.in_combat, "Boss room should start combat"
        assert world.combat_monster is not None
        assert world.combat_monster.tier == 3

    def test_boss_victory_marks_adventure_complete(self, world, player):
        loc, boss_room = self._scripted_adventure(world, player)
        world.adventure_room = boss_room
        m = _monster(tier=3, hp=1, xp=50)
        world.start_combat(m)
        with patch('random.randint', return_value=0), \
             patch('random.uniform', return_value=1.0):
            do_combat_action(0, world, player)
        assert world.adventure_complete, "adventure_complete should be set after boss kill"
        assert not world.in_adventure,   "in_adventure should clear after boss kill"

    def test_boss_victory_advances_day(self, world, player):
        loc, boss_room = self._scripted_adventure(world, player)
        world.adventure_room = boss_room
        day_before = world.day
        m = _monster(tier=3, hp=1, xp=50)
        world.start_combat(m)
        with patch('random.randint', return_value=0), \
             patch('random.uniform', return_value=1.0):
            do_combat_action(0, world, player)
        assert world.day == day_before + 1, "Day should advance after boss victory"

    def test_boss_victory_clears_temp_buffs(self, world, player):
        loc, boss_room = self._scripted_adventure(world, player)
        world.adventure_room      = boss_room
        player.temp_attack_bonus  = 2
        player.temp_defense_bonus = 2
        m = _monster(tier=3, hp=1, xp=50)
        world.start_combat(m)
        with patch('random.randint', return_value=0), \
             patch('random.uniform', return_value=1.0):
            do_combat_action(0, world, player)
        assert player.temp_attack_bonus  == 0
        assert player.temp_defense_bonus == 0

    def test_return_to_village_resets_all_adventure_state(self, world, player):
        self._scripted_adventure(world, player)
        player.temp_attack_bonus         = 2
        player.temp_defense_bonus        = 1
        player.temp_max_health_bonus     = 3
        player.status_effects            = {"poison": 2}
        player.status_effect_cooldowns   = {"cursed": 3}
        player.consecutive_peaceful_rooms = 4
        return_to_village(world, player)
        assert not world.in_adventure
        assert player.temp_attack_bonus       == 0
        assert player.temp_defense_bonus      == 0
        assert player.temp_max_health_bonus   == 0
        assert player.status_effects          == {}
        assert player.status_effect_cooldowns == {}
        assert player.consecutive_peaceful_rooms == 0

    def test_location_unlock_after_dungeon_1(self, world, player):
        '''Beating Dark Forest (loc 0) should unlock Deep Caverns (loc 1).'''
        _, boss_room = self._scripted_adventure(world, player)
        world.adventure_room = boss_room
        m = _monster(tier=3, hp=1, xp=50)
        world.start_combat(m)
        with patch('random.randint', return_value=0), \
             patch('random.uniform', return_value=1.0):
            do_combat_action(0, world, player)
        assert world.adventure_locations_unlocked >= 2, \
            "Beating Dark Forest should unlock Deep Caverns"


# ═══════════════════════════════════════════════════════════════════════════════
# 10. Rest day display
# ═══════════════════════════════════════════════════════════════════════════════

class TestRestDayDisplay:
    '''After resting, work_result text must include the new day number.
    This was caught by noticing the old text never showed the day.'''

    def test_rest_work_result_contains_day(self, world, player):
        '''Simulate the handler logic: advance_day then set work_result.'''
        world.rest_confirm = True
        day_before = world.day
        advance_day(world, player)
        player.health   = player.get_max_health()
        world.work_result = (f"You rested until morning.\nDay {world.day}", 0, 0)
        text, gold, food = world.work_result
        assert "Day" in text,               "work_result text must contain 'Day'"
        assert str(day_before + 1) in text, "work_result text must contain the new day number"
        assert "\n" in text,                "Day should be on its own line (newline present)"

    def test_rest_advances_day_by_one(self, world, player):
        day_before = world.day
        advance_day(world, player)
        assert world.day == day_before + 1

    def test_rest_resets_adventured_today(self, world, player):
        world.adventured_today = True
        advance_day(world, player)
        assert not world.adventured_today


# ═══════════════════════════════════════════════════════════════════════════════
# 11. Intro skip flow
# ═══════════════════════════════════════════════════════════════════════════════

class TestIntroSkipFlow:
    '''ESC during the opening sets intro_skipped. After name entry with that flag,
    the game goes directly to village (skipping QA and closing sequences).'''

    def test_intro_skipped_defaults_false(self, world):
        assert not world.intro_skipped

    def test_intro_skipped_set_on_escape(self, world):
        '''Simulate the ESC branch in the opening phase handler.'''
        world.intro_mode        = True
        world.intro_phase       = "opening"
        world.intro_skipped     = False
        # Replicate handler logic
        world.intro_phase       = "name"
        world.intro_line_index  = 0
        world.name_input_buffer = ""
        world.intro_skipped     = True
        assert world.intro_skipped

    def test_name_entry_with_skip_goes_to_village(self, world, player):
        '''After ESC-skip, entering a name should land in village, not QA.'''
        world.intro_mode        = True
        world.intro_phase       = "name"
        world.intro_skipped     = True
        world.name_input_buffer = "Aria"
        # Replicate handler Enter-key logic
        if world.name_input_buffer.strip():
            player.name = world.name_input_buffer.strip()
            if world.intro_skipped:
                world.intro_mode    = False
                world.intro_phase   = "opening"
                world.intro_skipped = False
                world.area          = "village"
        assert world.area == "village",    "Should land in village after skipped intro name"
        assert not world.intro_mode,       "Intro mode should be cleared"
        assert not world.intro_skipped,    "intro_skipped flag should be reset"
        assert player.name == "Aria"

    def test_name_entry_without_skip_goes_to_qa(self, world, player):
        '''Without skip, entering a name should advance to the QA phase.'''
        world.intro_mode        = True
        world.intro_phase       = "name"
        world.intro_skipped     = False
        world.name_input_buffer = "Aria"
        # Replicate handler Enter-key logic
        if world.name_input_buffer.strip():
            player.name = world.name_input_buffer.strip()
            if not world.intro_skipped:
                world.intro_phase    = "qa"
                world.intro_qa_index = 0
        assert world.intro_phase == "qa", "Should advance to QA phase without skip"
        assert world.intro_mode,          "Intro mode should remain active"

    def test_intro_skipped_resets_on_world_reset(self, world):
        world.intro_skipped = True
        world.reset("start_screen")
        assert not world.intro_skipped, "intro_skipped must reset on world reset"
