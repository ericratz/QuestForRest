'''
data/dialogue.py
NPC dialogue data. Each NPC has an ordered list of dialogue entries.
The first entry whose condition passes is used.
condition=None means "always" / default fallback.

To add a new NPC:
  1. Add an entry to NPCS with a unique id key.
  2. Add a "talk:<npc_id>" destination to the relevant area in areas.py.
'''


# ── NPC definitions ───────────────────────────────────────────────────────────

NPCS = {

    # ── Restholm ──────────────────────────────────────────────────────────────

    "restholm_innkeeper": {
        "name": "Innkeeper Bram",
        "portrait": "assets/images/Innkeeper Bram.jpeg",
        "dialogue": [
            {
                "condition": lambda w, p: p.debt == 0 and 1 in w.adventure_locations_complete,
                "lines": [
                    "Debt paid. Caverns cleared. I don't know what you are,",
                    "but you're not like the others who've passed through here.",
                    "Stay as long as you like. First drink's on me.",
                ]
            },
            {
                "condition": lambda w, p: 1 in w.adventure_locations_complete,
                "lines": [
                    "The Deep Caverns. You actually made it back.",
                    "I've sent stronger men in there. Didn't see them again.",
                    "...You still owe me, mind you. Survival doesn't clear a debt.",
                ]
            },
            {
                "condition": lambda w, p: 0 in w.adventure_locations_complete,
                "lines": [
                    "The Dark Forest — not many walk out of there.",
                    "Word travels fast in a small town. People are talking.",
                    "Don't let it go to your head. Debt doesn't care how brave you are.",
                ]
            },
            {
                "condition": lambda w, p: p.debt == 0,
                "lines": [
                    "Paid in full. I'll admit, I didn't think you had it in you.",
                    "You're welcome here as long as you like.",
                ]
            },
            {
                "condition": lambda w, p: w.day >= 10,
                "lines": [
                    "Ten days already. Time moves fast when you owe someone money.",
                    "I'm not unreasonable, but I am a businessman.",
                    "Don't make me collect.",
                ]
            },
            {
                "condition": None,
                "lines": [
                    "You need something? I'm a busy man.",
                    "You're new here — that much is obvious.",
                    "Get yourself sorted. Restholm isn't a bad place to start over.",
                    "...Actually, the Dark Forest has been causing trouble.",
                    "Clear it out and I'll consider us on better terms.",
                ],
                "post_action": "activate_quest_innkeeper",
            },
        ]
    },

    "restholm_shopkeeper": {
        "name": "Mira",
        "portrait": "assets/images/Mira.jpeg",
        "dialogue": [
            {
                "condition": lambda w, p: p.total_spent_gold >= 150,
                "lines": [
                    "You've kept me in business these past few days.",
                    "Honest work, honest trade. I respect that.",
                    "If you need anything, I'll see what I can do.",
                ]
            },
            {
                "condition": lambda w, p: 1 in w.adventure_locations_complete,
                "lines": [
                    "The Caverns. Most folk won't even look in that direction.",
                    "I've got some new stock that might suit someone like you.",
                    "Don't be shy — I don't bite. Much.",
                ]
            },
            {
                "condition": lambda w, p: 0 in w.adventure_locations_complete,
                "lines": [
                    "Cleared the Dark Forest? Then you'll be needing better gear.",
                    "I hear the things deeper in the woods don't stay dead.",
                    "Come back if you need supplies. I'll be here.",
                ]
            },
            {
                "condition": lambda w, p: p.level >= 5,
                "lines": [
                    "You've got that look about you. Seen a few fights.",
                    "The good stuff's in the back. Ask nicely and I might show you.",
                ]
            },
            {
                "condition": None,
                "lines": [
                    "Everything you see is for sale.",
                    "Some things that aren't, too, if you ask nicely.",
                    "Where'd you come from? Not around here, that's for sure.",
                ]
            },
        ]
    },

    # ── Duskwall ──────────────────────────────────────────────────────────────

    "duskwall_mystic": {
        "name": "The Mystic",
        "portrait": "assets/images/The Mystic.jpeg",
        "dialogue": [
            {
                "condition": lambda w, p: p.familiar.found,
                "lines": [
                    "She watches your companion with quiet approval.",
                    "The bond between you two is already taking root.",
                    "Treat her well. Creatures like her don't choose lightly.",
                    "If you find a Worn Collar, Silver Charm, or Arcane Collar",
                    "in the ruins, equip it on her — she grows stronger with them.",
                ]
            },
            {
                "condition": lambda w, p: 2 in w.adventure_locations_complete,
                "lines": [
                    "You've been to the Outer Ruins and back.",
                    "I found this creature there, weeks ago. She's been waiting ever since.",
                    "I think she was waiting for you.",
                    "Give her a name. She'll follow you now.",
                    "Charms drop from monsters in the ruins. Equip one on her to strengthen her.",
                ],
                "post_action": "give_familiar",
            },
            {
                "condition": None,
                "lines": [
                    "You're new. I can tell.",
                    "I have something for you — when you've proven yourself out there.",
                    "Clear the Outer Ruins first. Then come back.",
                ],
                "post_action": "activate_quest_mystic",
            },
        ]
    },

    "duskwall_guild": {
        "name": "Guildmaster Rook",
        "portrait": "assets/images/Guildmaster Rook.jpeg",
        "dialogue": [
            {
                "condition": lambda w, p: p.familiar.found and 3 in w.adventure_locations_complete,
                "lines": [
                    "Castle cleared, debt gone, and a companion at your side.",
                    "You've done more in Duskwall than most manage in a lifetime.",
                    "The Guild remembers names like yours.",
                ]
            },
            {
                "condition": lambda w, p: 3 in w.adventure_locations_complete,
                "lines": [
                    "The Abandoned Castle. You actually did it.",
                    "I've sent people in there before. Never saw them again.",
                    "Whatever's left in there — it's yours. You've earned it.",
                ]
            },
            {
                "condition": lambda w, p: p.debt == 0 and 2 in w.adventure_locations_complete,
                "lines": [
                    "Outer Ruins cleared. Debt settled. Not bad.",
                    "Most people who come to Duskwall don't last a fortnight.",
                    "You can stay. There's always work for someone like you.",
                ]
            },
            {
                "condition": lambda w, p: p.familiar.found,
                "lines": [
                    "You've got a familiar now. The Mystic's work, I'd wager.",
                    "Creatures like that are rare. Don't lose it.",
                    "The Castle might be worth attempting. With backup.",
                ]
            },
            {
                "condition": lambda w, p: 2 in w.adventure_locations_complete,
                "lines": [
                    "You came back from the Ruins. Respect.",
                    "The Castle's still out there. Nobody's touched it in years.",
                    "Figure out your finances first. Then we'll talk.",
                ]
            },
            {
                "condition": lambda w, p: 0 < p.debt <= 20,
                "lines": [
                    "Almost there. Just a little more.",
                    "I've seen people give up when the end was in sight.",
                    "Don't be one of them.",
                ]
            },
            {
                "condition": lambda w, p: p.debt > 0 and w.day >= 5,
                "lines": [
                    "You still owe me, outsider.",
                    "The debt clock doesn't stop because you're tired.",
                    "The ruins are where the money is. Get moving.",
                ]
            },
            {
                "condition": None,
                "lines": [
                    "Welcome to Duskwall. Rates here aren't what you're used to.",
                    "You've got a debt to work off. That's why you're here.",
                    "The Outer Ruins are close. Don't get killed on your first run.",
                    "Do that, and I'll consider giving you more work.",
                ],
                "post_action": "activate_quest_guildmaster",
            },
        ]
    },

    "duskwall_merchant": {
        "name": "The Merchant",
        "portrait": "assets/images/The Merchant.jpeg",
        "dialogue": [
            {
                "condition": lambda w, p: p.marks > 0,
                "lines": [
                    "You've figured out the marks system. Good.",
                    "Keeps things moving here. Gold's useless in Duskwall.",
                    "Need to convert? The exchange is open.",
                ],
            },
            {
                "condition": None,
                "lines": [
                    "Restholm traveller. Rare sight.",
                    "I'll be straight — we don't accept gold here.",
                    "Marks are the currency of Duskwall. Always have been.",
                    "I can exchange what you have, but the rate isn't in your favour.",
                    "Twenty-five gold to the mark. That's the going rate.",
                ],
            },
        ]
    },

    "duskwall_barkeep": {
        "name": "The Barkeep",
        "portrait": "assets/images/The Barkeep.jpeg",
        "dialogue": [
            {
                "condition": lambda w, p: 3 in w.adventure_locations_complete,
                "lines": [
                    "The Abandoned Castle. Word reached us even in here.",
                    "People have been buying drinks all night on that news.",
                    "This one's on me. Genuinely.",
                ]
            },
            {
                "condition": lambda w, p: p.familiar.found,
                "lines": [
                    "Nice creature you've got there.",
                    "Saw it through the window. Thought I was seeing things.",
                    "The Mystic's been right about strangers before. Apparently.",
                ]
            },
            {
                "condition": lambda w, p: p.kills >= 30,
                "lines": [
                    "You've got a reputation here now.",
                    "People talk. Especially about someone who keeps walking back in.",
                    "Drink's on the house. Don't make it a habit.",
                ]
            },
            {
                "condition": lambda w, p: 0 < p.debt <= 20,
                "lines": [
                    "Heard you're almost square with Rook.",
                    "That's no small thing in Duskwall.",
                    "One more run should do it.",
                ]
            },
            {
                "condition": lambda w, p: 1 in w.adventure_locations_complete,
                "lines": [
                    "You came through the Caverns.",
                    "Most don't.",
                    "Whatever you're running from — it didn't catch you. Not yet.",
                ]
            },
            {
                "condition": lambda w, p: w.day >= 5,
                "lines": [
                    "Still here.",
                    "Most newcomers don't last a week in Duskwall.",
                    "You're either tough or stupid. Maybe both.",
                ]
            },
            {
                "condition": None,
                "lines": [
                    "You look lost.",
                    "Most people who end up in Duskwall are.",
                    "What'll it be?",
                ]
            },
        ]
    },

}


# ── Public API ────────────────────────────────────────────────────────────────

def get_lines(npc_id: str, wState, pState):
    '''Return (lines, post_action) for this NPC given current game state.'''
    npc = NPCS.get(npc_id)
    if not npc:
        return ["..."], None
    for entry in npc["dialogue"]:
        if entry["condition"] is None or entry["condition"](wState, pState):
            return list(entry["lines"]), entry.get("post_action")
    return ["..."], None


def get_name(npc_id: str) -> str:
    npc = NPCS.get(npc_id)
    return npc["name"] if npc else "???"


def get_portrait(npc_id: str):
    '''Return the portrait path string for this NPC, or None.'''
    npc = NPCS.get(npc_id)
    return npc["portrait"] if npc else None
