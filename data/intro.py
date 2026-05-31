'''
data/intro.py
Intro sequence — the robed man scene played on New Game.
'''

# Lines the robed man speaks before asking for a name.
OPENING_LINES = [
    "You find yourself sitting at a small table in a white room.",
    "Across from you sits a man in a white robe.",
    "He looks up from his notes.",
    '"Hey. You\'re finally awake."',
    '"You probably have questions. That\'s fine."',
    '"But first — I\'ll need your name."',
]

# Q&A menu options shown after name is entered.
# Each entry: (display label, internal key)
QA_OPTIONS = [
    ("Where am I?",            "qa_where"),
    ("Who are you?",           "qa_who"),
    ("How did I die?",         "qa_how"),
    ("What's the world like?", "qa_world"),
    ("I'm ready to go.",       "qa_done"),
]

# Robed man's responses to each question.
QA_RESPONSES = {
    "qa_where": [
        '"This is where we process arrivals."',
        '"Normally we\'d show a summary of your life, but..."',
        '"...there\'s really not much to review."',
        '"Anyway. Not important."',
    ],
    "qa_who": [
        '"Me? I\'m just the greeter."',
        '"Someone has to explain the situation."',
        '"The man upstairs handles the bigger decisions."',
    ],
    "qa_how": [
        '"Sleep deprivation, technically."',
        '"You kept telling yourself you\'d fix your schedule."',
        '"You didn\'t."',
    ],
    "qa_world": [
        '"Simpler than what you\'re used to."',
        '"Less connected. Harder. More honest."',
        '"Your old way of living won\'t translate — at all."',
        '"But you\'ll find your footing. Most do."',
    ],
}

# Lines shown after the player chooses to enter the world.
# First half: robed man farewell. Second half: arrival narration.
CLOSING_LINES = [
    'The man smiles. "Have fun."',
    "For a moment, he almost seems familiar.",
    "",
    "Everything goes dark.",
    "...",
    "",
    "You're lying on the ground next to a stone fountain.",
    "You get up. Brush yourself off.",
    "Old buildings. Cobblestone streets. Candlelight in windows.",
    "",
    "An innkeeper has a room available.",
    "He'll need 100 gold. You don't have any.",
    "You work something out — fourteen days to pay it back.",
    "",
    "He doesn't seem worried.",
    "You are.",
]

# Lines shown in the ending sequence (robed man's farewell after the second debt is cleared).
ENDING_LINES = [
    "A familiar light fills the room.",
    "",
    "The robed man is there.",
    "Of course he is.",
    "",
    '"Well."',
    '"That took longer than I expected."',
    "",
    '"But you did it."',
    "",
    "He sets down his notebook.",
    "",
    '"Both debts. Cleared."',
    '"Both dungeons."',
    '"You actually built something there."',
    "",
    '"Most people who come through this office..."',
    '"...they go through the motions. Survive. Call it enough."',
    "",
    '"You did more than survive."',
    "",
    "He stands.",
    "",
    '"Restholm. Duskwall. They\'ll remember you."',
    "",
    '"The door is open, if you want to see what\'s next."',
    '"Or stay. Rest a while."',
    '"You\'ve earned it."',
    "",
    "He almost smiles.",
    "",
    "For the last time —",
    "he almost seems familiar.",
    "",
    "...",
]
