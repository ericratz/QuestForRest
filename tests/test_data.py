'''
tests/test_data.py
Data-integrity / regression tests.
Verifies that area definitions, NPC references, intro/ending content,
item definitions, and passive data are internally consistent.
'''

import pytest
import data.areas as areas_module
import data.dialogue as dialogue_module
import data.passives as passives_data
import data.items as items_module
import data.intro as intro_module
from state.gamestate import EQUIPMENT_SLOTS, WorldState, PlayerState


# ── Areas ─────────────────────────────────────────────────────────────────────

EXPECTED_AREAS = [
    "start_screen", "village", "inn", "shop",
    "duskwall", "duskwall_tavern", "duskwall_shop",
]

def test_all_expected_areas_registered():
    for area_id in EXPECTED_AREAS:
        assert area_id in areas_module.areas, f"area '{area_id}' missing from areas dict"

def test_area_objects_have_required_attrs():
    for area_id, area in areas_module.areas.items():
        assert hasattr(area, "name"),    f"{area_id} missing 'name'"
        assert hasattr(area, "text"),    f"{area_id} missing 'text'"
        assert hasattr(area, "image"),   f"{area_id} missing 'image'"
        assert hasattr(area, "choices"), f"{area_id} missing 'choices'"
        assert isinstance(area.choices, dict), f"{area_id}.choices is not a dict"


# ── talk: destinations reference valid NPC ids ─────────────────────────────────

def test_talk_destinations_have_known_npcs():
    '''Every "talk:<npc_id>" destination in any area must exist in NPCS.'''
    for area_id, area in areas_module.areas.items():
        for key, (dest, label) in area.choices.items():
            if dest.startswith("talk:"):
                npc_id = dest[5:]
                assert npc_id in dialogue_module.NPCS, (
                    f"area '{area_id}' choice '{key}' references unknown NPC '{npc_id}'"
                )


# ── Dialogue NPC structure ─────────────────────────────────────────────────────

def test_all_npcs_have_name():
    for npc_id, npc in dialogue_module.NPCS.items():
        assert "name" in npc, f"NPC '{npc_id}' missing 'name'"

def test_all_npcs_have_dialogue_list():
    for npc_id, npc in dialogue_module.NPCS.items():
        assert "dialogue" in npc, f"NPC '{npc_id}' missing 'dialogue'"
        assert isinstance(npc["dialogue"], list), f"NPC '{npc_id}' dialogue is not a list"

def test_all_npcs_have_default_fallback():
    '''Each NPC must end with a condition=None fallback so get_lines never returns "...".'''
    for npc_id, npc in dialogue_module.NPCS.items():
        last = npc["dialogue"][-1]
        assert last["condition"] is None, (
            f"NPC '{npc_id}' last entry has condition={last['condition']!r}; expected None"
        )

def test_npc_lines_are_non_empty():
    for npc_id, npc in dialogue_module.NPCS.items():
        for entry in npc["dialogue"]:
            assert len(entry["lines"]) > 0, f"NPC '{npc_id}' has empty lines list"

def test_get_lines_default_returns_list(monkeypatch):
    '''get_lines on unknown NPC returns the fallback (["..."], None).'''
    lines, action = dialogue_module.get_lines("nonexistent_npc", WorldState(), PlayerState())
    assert lines == ["..."]
    assert action is None

def test_get_name_unknown_returns_question_marks():
    assert dialogue_module.get_name("nonexistent_npc") == "???"


# ── Dialogue conditions are callable ─────────────────────────────────────────

def test_dialogue_conditions_callable_or_none():
    for npc_id, npc in dialogue_module.NPCS.items():
        for entry in npc["dialogue"]:
            cond = entry["condition"]
            assert cond is None or callable(cond), (
                f"NPC '{npc_id}' condition is not None or callable: {cond!r}"
            )


# ── Items ─────────────────────────────────────────────────────────────────────

def test_all_items_have_required_fields():
    for name, item in items_module.ALL_ITEMS.items():
        assert hasattr(item, "name"),       f"item '{name}' missing 'name'"
        assert hasattr(item, "slot"),       f"item '{name}' missing 'slot'"
        assert hasattr(item, "consumable"), f"item '{name}' missing 'consumable'"
        assert hasattr(item, "stats"),      f"item '{name}' missing 'stats'"

def test_non_consumable_slots_are_valid():
    valid_slots = set(EQUIPMENT_SLOTS) | {"familiar"}
    for name, item in items_module.ALL_ITEMS.items():
        if not item.consumable:
            assert item.slot in valid_slots, (
                f"item '{name}' has invalid slot '{item.slot}'"
            )

def test_consumable_items_have_use_effect():
    for name, item in items_module.ALL_ITEMS.items():
        if item.consumable:
            assert hasattr(item, "use_effect") and item.use_effect, (
                f"consumable item '{name}' has empty or missing use_effect"
            )

def test_potion_in_all_items():
    assert "Potion" in items_module.ALL_ITEMS

def test_rusty_sword_in_all_items():
    assert "Rusty Sword" in items_module.ALL_ITEMS

def test_shop_pool_items_have_tier():
    for item in items_module.SHOP_POOL:
        assert hasattr(item, "tier"), f"SHOP_POOL item '{item.name}' missing 'tier'"

def test_perm_shop_items_in_all_items():
    from state.gamestate import PERM_SHOP_ITEMS
    for item in PERM_SHOP_ITEMS:
        assert item.name in items_module.ALL_ITEMS


# ── Passive data ──────────────────────────────────────────────────────────────

def test_all_milestone_passives_exist():
    for lvl, opts in passives_data.MILESTONE_OPTIONS.items():
        for pid in opts:
            assert pid in passives_data.PASSIVES, (
                f"milestone {lvl} references missing passive '{pid}'"
            )

def test_each_passive_effect_key_is_string():
    for pid, passive in passives_data.PASSIVES.items():
        for key in passive["effect"]:
            assert isinstance(key, str), f"passive '{pid}' has non-string effect key"


# ── Intro / ending content ────────────────────────────────────────────────────

def test_opening_lines_not_empty():
    assert len(intro_module.OPENING_LINES) > 0

def test_closing_lines_not_empty():
    assert len(intro_module.CLOSING_LINES) > 0

def test_ending_lines_not_empty():
    assert len(intro_module.ENDING_LINES) > 0

def test_qa_options_not_empty():
    assert len(intro_module.QA_OPTIONS) > 0

def test_qa_options_have_done_option():
    '''There must be a "done" option to exit the QA phase.'''
    assert any(key == "qa_done" for _, key in intro_module.QA_OPTIONS)

def test_qa_responses_cover_all_non_done_options():
    for label, key in intro_module.QA_OPTIONS:
        if key == "qa_done":
            continue
        assert key in intro_module.QA_RESPONSES, (
            f"QA option '{key}' has no response in QA_RESPONSES"
        )

def test_qa_responses_are_non_empty_lists():
    for key, lines in intro_module.QA_RESPONSES.items():
        assert isinstance(lines, list) and len(lines) > 0, (
            f"QA_RESPONSES['{key}'] is empty or not a list"
        )


# ── PlayerState has consecutive_peaceful_rooms field ─────────────────────────

def test_player_has_consecutive_peaceful_rooms_field():
    '''Regression: field used by Pacifist achievement must exist.'''
    p = PlayerState()
    assert hasattr(p, "consecutive_peaceful_rooms")
    assert p.consecutive_peaceful_rooms == 0


# ── WorldState has all expected new fields ────────────────────────────────────

def test_world_state_has_ending_fields():
    w = WorldState()
    assert hasattr(w, "ending_mode")
    assert hasattr(w, "ending_line_index")

def test_world_state_has_intro_fields():
    w = WorldState()
    assert hasattr(w, "intro_mode")
    assert hasattr(w, "intro_phase")
    assert hasattr(w, "intro_line_index")
    assert hasattr(w, "intro_qa_index")

def test_world_state_has_passive_select_fields():
    w = WorldState()
    assert hasattr(w, "passive_select_mode")
    assert hasattr(w, "passive_select_options")
    assert hasattr(w, "passive_select_index")
    assert hasattr(w, "passive_pending_milestone")

def test_world_state_has_duskwall_fields():
    w = WorldState()
    assert hasattr(w, "duskwall_unlocked")
    assert hasattr(w, "duskwall_just_unlocked")
    assert hasattr(w, "duskwall_arrival_pending")

def test_world_state_has_adventure_origin():
    w = WorldState()
    assert hasattr(w, "adventure_origin")
    assert w.adventure_origin == "village"
