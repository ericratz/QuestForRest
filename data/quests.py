'''
quests.py
Quest definitions and progress tracking
'''

import random

QUESTS = [
    {"id": "debt",        "name": "Settle Your Debt",
     "desc": "Pay off your 100g debt to the innkeeper.",
     "type": "debt",        "target": 100,  "reward": 25,  "days": None},
    {"id": "second_debt", "name": "The Greater Debt",
     "desc": "Pay off your 200 mark debt to the Guildmaster.",
     "type": "second_debt", "target": 200,  "reward": 50,  "days": None, "area": "duskwall"},
    {"id": "kill_3",      "name": "First Blood",
     "desc": "Defeat 3 monsters.",
     "type": "kills",       "target": 3,    "reward": 15,  "days": 2},
    {"id": "kill_10",     "name": "Monster Hunter",
     "desc": "Defeat 10 monsters.",
     "type": "kills",       "target": 10,   "reward": 50,  "days": 4},
    {"id": "kill_20",     "name": "Monster Slayer",
     "desc": "Defeat 20 monsters.",
     "type": "kills",       "target": 20,   "reward": 100, "days": 7},
    {"id": "rusty_sword", "name": "Humble Beginnings",
     "desc": "Equip the Rusty Sword.",
     "type": "equip",       "target": "Rusty Sword", "reward": 10, "days": 3},
    {"id": "kill_boss",   "name": "Giant Killer",
     "desc": "Defeat a boss monster.",
     "type": "bosses",      "target": 1,    "reward": 50,  "days": 7},
    {"id": "all_slots",   "name": "Well Equipped",
     "desc": "Fill all 7 equipment slots.",
     "type": "slots",       "target": 7,    "reward": 50,  "days": 7},
    {"id": "survivalist", "name": "Survivalist",
     "desc": "Complete a dungeon without using any potions.",
     "type": "survivalist", "target": 1,    "reward": 30,  "days": 5},
    {"id": "collector",   "name": "Collector",
     "desc": "Store 10 items in your stash.",
     "type": "stash_count", "target": 10,   "reward": 50,  "days": 5},
    {"id": "exterminator","name": "Exterminator",
     "desc": "Kill 5 monsters of the same type.",
     "type": "exterminator","target": 5,    "reward": 40,  "days": 5},

    # ── Duskwall bounty board quests ──────────────────────────────────────────
    {"id": "dusk_kill_5",    "name": "Ruins Raider",
     "desc": "Kill 5 more enemies beyond Duskwall's walls.",
     "type": "kills",        "target": 5,   "reward": 8,  "days": 3,  "area": "duskwall"},
    {"id": "dusk_kill_15",   "name": "Ruins Veteran",
     "desc": "Kill 15 more enemies in the ruins.",
     "type": "kills",        "target": 15,  "reward": 18, "days": 6,  "area": "duskwall"},
    {"id": "dusk_boss",      "name": "Giant Slayer",
     "desc": "Defeat a Duskwall dungeon boss.",
     "type": "bosses",       "target": 1,   "reward": 25, "days": 7,  "area": "duskwall"},
    {"id": "dusk_survivor",  "name": "Ghost",
     "desc": "Complete a Duskwall dungeon without using any potions.",
     "type": "survivalist",  "target": 1,   "reward": 15, "days": 6,  "area": "duskwall"},
    {"id": "dusk_plague",    "name": "Pest Control",
     "desc": "Kill 5 Plague Rats.",
     "type": "exterminator", "target": 5,   "reward": 10, "days": 4,  "area": "duskwall"},
    {"id": "dusk_knight",    "name": "Dismantle the Knights",
     "desc": "Destroy 5 Crumbled Knights.",
     "type": "exterminator", "target": 5,   "reward": 12, "days": 5,  "area": "duskwall"},

    # ── NPC story quests (no deadline; activated by dialogue) ─────────────────
    {"id": "innkeeper_quest", "name": "Into the Dark Forest",
     "desc": "Innkeeper Bram asked you to clear the Dark Forest of its beasts.",
     "type": "complete_loc",  "target": 0,   "reward": 20, "days": None},
    {"id": "guildmaster_quest", "name": "Cleanse the Outer Ruins",
     "desc": "Guildmaster Rook wants the Outer Ruins cleared.",
     "type": "complete_loc",  "target": 2,   "reward": 0,  "days": None, "area": "duskwall"},
    {"id": "mystic_quest",    "name": "The Mystic's Test",
     "desc": "Prove yourself in the Outer Ruins to earn the Mystic's trust.",
     "type": "complete_loc",  "target": 2,   "reward": 0,  "days": None, "area": "duskwall"},
]

ACHIEVEMENTS = [
    {"id": "iron_will",        "name": "Iron Will",
     "desc": "Leave a dungeon with exactly 1 HP remaining.",         "reward": 25},
    {"id": "pacifist",         "name": "Pacifist",
     "desc": "Complete 5 consecutive rooms without fighting.",        "reward": 30},
    {"id": "speed_run",        "name": "Speed Run",
     "desc": "Complete Dark Forest on Day 1.",                       "reward": 40},
    {"id": "merchants_friend", "name": "Merchant's Friend",
     "desc": "Spend 150g total at the shop.",                        "reward": 25},
]


def quest_progress(quest, pState):
    t   = quest["type"]
    qid = quest["id"]
    if t == "debt":
        return min(100 - pState.debt, 100), 100
    elif t == "second_debt":
        return min(200 - pState.debt, 200), 200
    elif t == "complete_loc":
        done = 1 if quest["target"] in getattr(pState, "locations_complete", set()) else 0
        return done, 1
    elif t == "kills":
        baseline = pState.quest_snapshots.get(qid, pState.kills)
        return pState.kills - baseline, quest["target"]
    elif t == "bosses":
        baseline = pState.quest_snapshots.get(qid, pState.boss_kills)
        return pState.boss_kills - baseline, quest["target"]
    elif t == "equip":
        hit = any(i and i.name == quest["target"] for i in pState.equipment.values())
        return (1 if hit else 0), 1
    elif t == "slots":
        filled = sum(1 for i in pState.equipment.values() if i)
        return filled, quest["target"]
    elif t == "survivalist":
        baseline = pState.quest_snapshots.get(qid, pState.survivalist_completions)
        return max(0, pState.survivalist_completions - baseline), 1
    elif t == "stash_count":
        return len(pState.stash), quest["target"]
    elif t == "exterminator":
        baseline = pState.quest_snapshots.get(qid, {})
        if not isinstance(baseline, dict):
            baseline = {}
        if not pState.kill_counts:
            return 0, quest["target"]
        best = max(
            pState.kill_counts.get(name, 0) - baseline.get(name, 0)
            for name in pState.kill_counts
        )
        return max(0, best), quest["target"]
    return 0, 1


def check_new_completions(pState):
    '''Check active quests; award gold or marks for newly completed ones. Returns list of quest names.'''
    newly_done = []
    for quest in QUESTS:
        qid = quest["id"]
        if qid not in pState.active_quests:
            continue
        if qid in pState.quests_complete:
            continue
        progress, target = quest_progress(quest, pState)
        if progress >= target:
            pState.quests_complete.add(qid)
            if quest["reward"] > 0:
                if quest.get("area") == "duskwall":
                    pState.marks += quest["reward"]
                else:
                    pState.gold  += quest["reward"]
            newly_done.append(quest["name"])
    return newly_done


def unlock_achievement(aid, wState, pState):
    '''Unlock an achievement if not already done. Grants reward gold. Queues popup.'''
    if aid in pState.achievements_unlocked:
        return False
    ach = next((a for a in ACHIEVEMENTS if a["id"] == aid), None)
    if ach:
        pState.achievements_unlocked.add(aid)
        wState.achievement_popup.append(ach["name"])
        reward = ach.get("reward", 0)
        if reward > 0:
            pState.gold += reward
        return True
    return False


def check_achievements(wState, pState):
    '''Check polled achievements (Pacifist, Merchant's Friend). Returns newly unlocked names.'''
    newly = []
    if ("pacifist" not in pState.achievements_unlocked
            and pState.consecutive_peaceful_rooms >= 6
            and wState.in_adventure):
        unlock_achievement("pacifist", wState, pState)
        newly.append("Pacifist")
    if "merchants_friend" not in pState.achievements_unlocked and pState.total_spent_gold >= 150:
        unlock_achievement("merchants_friend", wState, pState)
        newly.append("Merchant's Friend")
    return newly


def refresh_questboard(wState, pState):
    '''Pick a new random quest for the board if the day has changed.'''
    if wState.questboard_day == wState.day:
        return
    _npc_quests = {"innkeeper_quest", "guildmaster_quest", "mystic_quest"}
    _dusk_areas = {"duskwall", "duskwall_tavern", "duskwall_shop"}
    in_duskwall = wState.area in _dusk_areas
    if in_duskwall:
        # Bounty board: only Duskwall-tagged quests, no NPC story quests
        eligible = [q for q in QUESTS
                    if q.get("area") == "duskwall"
                    and q["id"] not in pState.active_quests
                    and q["id"] not in pState.quests_complete
                    and q["id"] not in _npc_quests]
    else:
        # Restholm quest board: no duskwall-specific or NPC story quests
        eligible = [q for q in QUESTS
                    if not q.get("area")
                    and q["id"] not in pState.active_quests
                    and q["id"] not in pState.quests_complete
                    and q["id"] not in ("debt", "second_debt")
                    and q["id"] not in _npc_quests]
    wState.questboard_quest_id = random.choice(eligible)["id"] if eligible else None
    wState.questboard_day      = wState.day
