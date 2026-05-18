'''
quests.py
Quest definitions and progress tracking
'''

import random

QUESTS = [
    {"id": "debt",        "name": "Settle Your Debt",
     "desc": "Pay off your 100g debt to the innkeeper.",
     "type": "debt",   "target": 100, "reward": 0},
    {"id": "kill_3",      "name": "First Blood",
     "desc": "Defeat 3 monsters.",
     "type": "kills",  "target": 3,   "reward": 30},
    {"id": "kill_10",     "name": "Monster Hunter",
     "desc": "Defeat 10 monsters.",
     "type": "kills",  "target": 10,  "reward": 75},
    {"id": "kill_20",     "name": "Monster Slayer",
     "desc": "Defeat 20 monsters.",
     "type": "kills",  "target": 20,  "reward": 150},
    {"id": "rusty_sword", "name": "Humble Beginnings",
     "desc": "Equip the Rusty Sword.",
     "type": "equip",  "target": "Rusty Sword", "reward": 10},
    {"id": "kill_boss",   "name": "Giant Killer",
     "desc": "Defeat a boss monster.",
     "type": "bosses", "target": 1,   "reward": 100},
    {"id": "all_slots",   "name": "Well Equipped",
     "desc": "Fill all 7 equipment slots.",
     "type": "slots",  "target": 7,   "reward": 80},
]


def quest_progress(quest, pState):
    t   = quest["type"]
    qid = quest["id"]
    if t == "debt":
        return min(100 - pState.debt, 100), 100
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
    return 0, 1


def check_new_completions(pState):
    '''Check active quests; award gold for newly completed ones. Returns list of quest names.'''
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
                pState.gold += quest["reward"]
            newly_done.append(quest["name"])
    return newly_done


def refresh_questboard(wState, pState):
    '''Pick a new random quest for the board if the day has changed.'''
    if wState.questboard_day == wState.day:
        return
    eligible = [q for q in QUESTS
                if q["id"] not in pState.active_quests
                and q["id"] not in pState.quests_complete
                and q["id"] != "debt"]
    wState.questboard_quest_id = random.choice(eligible)["id"] if eligible else None
    wState.questboard_day      = wState.day
