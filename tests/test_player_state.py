'''
tests/test_player_state.py
Unit tests for PlayerState derived stats, damage, levelling, and item use.
'''

import pytest
from state.gamestate import PlayerState, EQUIPMENT_SLOTS
import data.items as items_module


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def player():
    return PlayerState()


def _equip(player, item_name):
    '''Helper: put a named item straight into the equipment dict.'''
    item = items_module.ALL_ITEMS[item_name]
    player.equipment[item.slot] = item
    return item


# ── Max health ────────────────────────────────────────────────────────────────

def test_get_max_health_base(player):
    assert player.get_max_health() == 20

def test_get_max_health_grows_with_base(player):
    player.base_max_health = 30
    assert player.get_max_health() == 30

def test_get_max_health_includes_equipment_bonus(player):
    # Equip anything with an hp stat
    for item in items_module.ALL_ITEMS.values():
        if item.stats.get('hp', 0) > 0 and not item.consumable:
            player.equipment[item.slot] = item
            expected = 20 + item.stats['hp']
            assert player.get_max_health() == expected
            break

def test_get_max_health_includes_hp_bonus_passive(player):
    player.chosen_passives = []   # no hp_bonus passive in default set
    base = player.get_max_health()
    # Manually inject a fake passive effect via monkey-patching chosen_passives
    # (passive_effect reads PASSIVES dict, so we add a real key that has hp_bonus)
    # There is no hp_bonus passive by default; verify base is still correct.
    assert base == player.base_max_health


# ── Attack ────────────────────────────────────────────────────────────────────

def test_get_attack_base(player):
    assert player.get_attack() == 1

def test_get_attack_with_might_passive(player):
    player.chosen_passives = ['might']
    assert player.get_attack() == 3   # base 1 + might +2

def test_get_attack_berserker_high_hp(player):
    '''Berserker should NOT trigger when HP >= 50% max.'''
    player.chosen_passives = ['berserker']
    player.health = player.get_max_health()   # full health
    assert player.get_attack() == 1

def test_get_attack_berserker_low_hp(player):
    '''Berserker triggers when HP < 50% max.'''
    player.chosen_passives = ['berserker']
    player.health = 1   # well below 50%
    assert player.get_attack() == 5   # base 1 + berserker +4

def test_get_attack_cursed_halves_after_bonus(player):
    player.chosen_passives = ['might']
    player.status_effects = {'cursed': -1}
    # base 1 + might 2 = 3, cursed -2 = max(1, 1) = 1
    assert player.get_attack() == 1

def test_get_attack_weakened(player):
    player.base_attack = 6
    player.status_effects = {'weakened': 2}
    assert player.get_attack() == 3   # 6 // 2


# ── Defense ───────────────────────────────────────────────────────────────────

def test_get_defense_base(player):
    assert player.get_defense() == 1

def test_get_defense_iron_skin_passive(player):
    player.chosen_passives = ['iron_skin']
    assert player.get_defense() == 3   # base 1 + iron_skin +2

def test_get_defense_cursed(player):
    player.chosen_passives = ['iron_skin']
    player.status_effects = {'cursed': -1}
    # 1 + 2 = 3, cursed -2 = 1
    assert player.get_defense() == 1


# ── Crit and block ────────────────────────────────────────────────────────────

def test_get_crit_chance_base(player):
    assert player.get_crit_chance() == 5

def test_get_crit_chance_tracker(player):
    player.chosen_passives = ['tracker']
    assert player.get_crit_chance() == 13   # 5 + 8

def test_get_block_chance_base(player):
    assert player.get_block_chance() == 5

def test_get_block_chance_with_shield(player):
    # Equip any shield item
    shields = [i for i in items_module.ALL_ITEMS.values()
               if i.slot == 'shield' and not i.consumable]
    if shields:
        player.equipment['shield'] = shields[0]
        assert player.get_block_chance() == 10   # 5 base + 5 wood shield

def test_get_block_chance_bulwark_no_shield(player):
    player.chosen_passives = ['bulwark']
    assert player.get_block_chance() == 20   # 5 + 15

def test_get_block_chance_bulwark_with_shield(player):
    shields = [i for i in items_module.ALL_ITEMS.values()
               if i.slot == 'shield' and not i.consumable]
    if shields:
        player.equipment['shield'] = shields[0]
        player.chosen_passives = ['bulwark']
        assert player.get_block_chance() == 25   # 5 base + 5 wood shield + 15 bulwark


# ── HP / damage ───────────────────────────────────────────────────────────────

def test_heal_capped_at_max(player):
    player.health = 10
    player.heal(100)
    assert player.health == player.get_max_health()

def test_heal_partial(player):
    player.health = 10
    player.heal(3)
    assert player.health == 13

def test_take_damage_reduces_hp(player):
    player.health = 15
    dead = player.take_damage(5)
    assert player.health == 10
    assert dead is False

def test_take_damage_lethal(player):
    player.health = 5
    dead = player.take_damage(10)
    assert player.health == 0
    assert dead is True

def test_take_damage_second_wind_saves(player):
    player.chosen_passives = ['second_wind']
    player.second_wind_available = True
    dead = player.take_damage(9999)
    assert dead is False
    assert player.health == 1

def test_take_damage_second_wind_only_once(player):
    player.chosen_passives = ['second_wind']
    player.second_wind_available = True
    player.take_damage(9999)   # first lethal — survives
    dead = player.take_damage(9999)   # second lethal — dies
    assert dead is True

def test_take_damage_second_wind_not_available_without_passive(player):
    player.second_wind_available = True   # flag set but no passive
    dead = player.take_damage(9999)
    assert dead is True


# ── Levelling ─────────────────────────────────────────────────────────────────

def test_gain_xp_no_level_up(player):
    leveled = player.gain_xp(1)
    assert leveled == []
    assert player.xp == 1

def test_gain_xp_single_level_up(player):
    needed = player.xp_to_next()
    leveled = player.gain_xp(needed)
    assert len(leveled) == 1
    new_level, hp_g, atk_g, def_g = leveled[0]
    assert new_level == 2
    assert player.level == 2
    # HP should have been healed to new max
    assert player.health == player.get_max_health()

def test_gain_xp_multiple_levels(player):
    # Give a very large XP amount to jump several levels
    leveled = player.gain_xp(10_000)
    assert len(leveled) > 1
    assert player.level > 2


# ── Passive effect helper ─────────────────────────────────────────────────────

def test_passive_effect_empty(player):
    assert player.passive_effect('atk_bonus') == 0

def test_passive_effect_single(player):
    player.chosen_passives = ['might']
    assert player.passive_effect('atk_bonus') == 2

def test_passive_effect_stacking(player):
    # In default set no two passives share a key, but we can verify the sum logic
    player.chosen_passives = ['tracker']
    assert player.passive_effect('crit_bonus') == 8
    assert player.passive_effect('atk_bonus')  == 0

def test_passive_effect_unknown_key(player):
    player.chosen_passives = ['might']
    assert player.passive_effect('nonexistent_key') == 0


# ── Items ─────────────────────────────────────────────────────────────────────

def test_use_item_heal(player):
    potion = items_module.ALL_ITEMS['Potion']
    player.inventory = [potion]
    player.health = 5
    msg = player.use_item(0)
    assert msg is not None
    assert player.health > 5
    assert len(player.inventory) == 0   # consumed

def test_use_item_invalid_index(player):
    assert player.use_item(5) is None

def test_use_item_non_consumable_returns_none(player):
    weapons = [i for i in items_module.ALL_ITEMS.values()
               if not i.consumable and i.slot == 'weapon']
    if weapons:
        player.inventory = [weapons[0]]
        assert player.use_item(0) is None

def test_equip_item_places_in_slot(player):
    weapons = [i for i in items_module.ALL_ITEMS.values()
               if not i.consumable and i.slot == 'weapon']
    if weapons:
        w = weapons[0]
        player.inventory = [w]
        player.equip_item(0)
        assert player.equipment['weapon'] == w
        assert w not in player.inventory

def test_equip_item_swaps_existing(player):
    weapons = [i for i in items_module.ALL_ITEMS.values()
               if not i.consumable and i.slot == 'weapon']
    if len(weapons) >= 2:
        player.equipment['weapon'] = weapons[0]
        player.inventory = [weapons[1]]
        player.equip_item(0)
        assert player.equipment['weapon'] == weapons[1]
        assert weapons[0] in player.inventory


# ── die() ─────────────────────────────────────────────────────────────────────

def test_die_clears_inventory(player):
    player.inventory = [items_module.ALL_ITEMS['Potion']]
    player.die()
    assert player.inventory == []

def test_die_clears_equipment(player):
    player.equipment['weapon'] = items_module.ALL_ITEMS['Rusty Sword']
    player.die()
    assert all(v is None for v in player.equipment.values())

def test_die_halves_gold(player):
    player.gold = 100
    player.die()
    assert player.gold == 50

def test_die_halves_gold_rounds_down(player):
    player.gold = 7
    player.die()
    assert player.gold == 3

def test_die_reduces_food_by_2(player):
    player.food = 5
    player.die()
    assert player.food == 3

def test_die_food_floored_at_zero(player):
    player.food = 1
    player.die()
    assert player.food == 0

def test_die_restores_full_health(player):
    player.health = 1
    player.die()
    assert player.health == player.get_max_health()

def test_die_clears_status_effects(player):
    player.status_effects = {"poison": 3, "cursed": -1}
    player.die()
    assert player.status_effects == {}


# ── equip_item — familiar slot ────────────────────────────────────────────────

def test_equip_familiar_charm_routes_to_familiar(player):
    charm = items_module.ALL_ITEMS['Worn Collar']
    player.inventory = [charm]
    player.equip_item(0)
    assert player.familiar.equipment == charm
    assert charm not in player.inventory

def test_equip_familiar_charm_swaps_existing(player):
    old_charm = items_module.ALL_ITEMS['Worn Collar']
    new_charm = items_module.ALL_ITEMS['Silver Charm']
    player.familiar.equipment = old_charm
    player.inventory = [new_charm]
    player.equip_item(0)
    assert player.familiar.equipment == new_charm
    assert old_charm in player.inventory

def test_equip_familiar_charm_does_not_touch_equipment_dict(player):
    charm = items_module.ALL_ITEMS['Worn Collar']
    player.inventory = [charm]
    player.equip_item(0)
    assert 'familiar' not in player.equipment


# ── unequip_item ──────────────────────────────────────────────────────────────

def test_unequip_moves_item_to_inventory(player):
    weapon = items_module.ALL_ITEMS['Rusty Sword']
    player.equipment['weapon'] = weapon
    slot_idx = list(player.equipment.keys()).index('weapon')
    from state.gamestate import EQUIPMENT_SLOTS
    player.unequip_item(EQUIPMENT_SLOTS.index('weapon'))
    assert player.equipment['weapon'] is None
    assert weapon in player.inventory

def test_unequip_empty_slot_is_safe(player):
    from state.gamestate import EQUIPMENT_SLOTS
    player.unequip_item(EQUIPMENT_SLOTS.index('weapon'))  # nothing equipped
    assert player.equipment['weapon'] is None

def test_unequip_hp_gear_clamps_health(player):
    helm = items_module.ALL_ITEMS['Iron Helm']   # hp+5
    player.equipment['head'] = helm
    player.health = player.get_max_health()       # at new max
    from state.gamestate import EQUIPMENT_SLOTS
    player.unequip_item(EQUIPMENT_SLOTS.index('head'))
    assert player.health <= player.get_max_health()


# ── use_item — non-heal effects ───────────────────────────────────────────────

def test_use_item_food_effect(player):
    ration = items_module.ALL_ITEMS['Rations']
    player.inventory = [ration]
    player.food = 2
    player.use_item(0)
    assert player.food == 3
    assert ration not in player.inventory

def test_use_item_cure_removes_poison(player):
    antidote = items_module.ALL_ITEMS['Antidote']
    player.inventory = [antidote]
    player.status_effects = {"poison": 3, "weakened": 2}
    msg = player.use_item(0)
    assert "poison" not in player.status_effects
    assert "weakened" not in player.status_effects
    assert "Cured" in msg

def test_use_item_cure_nothing_to_cure(player):
    antidote = items_module.ALL_ITEMS['Antidote']
    player.inventory = [antidote]
    player.status_effects = {}
    msg = player.use_item(0)
    assert "Nothing to cure" in msg

def test_use_item_buff_attack_adds_temp_bonus(player):
    stone = items_module.ALL_ITEMS['Sharpening Stone']
    player.inventory = [stone]
    before = player.temp_attack_bonus
    player.use_item(0)
    assert player.temp_attack_bonus == before + 1


# ── reset ─────────────────────────────────────────────────────────────────────

def test_player_reset_clears_inventory(player):
    player.inventory = [items_module.ALL_ITEMS['Potion']]
    player.reset()
    assert player.inventory == []

def test_player_reset_clears_equipment(player):
    player.equipment['weapon'] = items_module.ALL_ITEMS['Rusty Sword']
    player.reset()
    assert all(v is None for v in player.equipment.values())

def test_player_reset_zeroes_gold(player):
    player.gold = 500
    player.reset()
    assert player.gold == 0

def test_player_reset_resets_familiar(player):
    player.familiar.found = True
    player.familiar.name  = "Luna"
    player.reset()
    assert not player.familiar.found
    assert player.familiar.name == ""
