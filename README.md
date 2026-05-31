# Quest For Rest

A keyboard-driven RPG built with Python and Pygame. You arrive in the town of Restholm with a debt to pay and not much else. Explore dungeons, fight monsters, manage your gear, and complete quests before your deadline runs out.

---

## Features

**Two Connected Realms**
Restholm and Duskwall are distinct regions with their own economies, shops, quests, NPCs, and dungeons.

**Dungeon Exploration**
Four procedurally-ordered dungeons across both regions.

**Turn-Based Combat**
Attack, flee, examine enemies, or use items mid-fight.

**Status Effects**
Poison, stun, weaken, and curse each behave differently.

**Equipment & Inventory**
Seven equipment slots with tiered gear across both regions.

**Quests & Achievements**
Story quests activated through NPC dialogue, bounty board jobs with deadlines, repeatable daily work, and a Duskwall smuggling job with risk of loss. Achievements unlock automatically based on playstyle — pacifism, kills, spending, and more.

**Passives System**
Level-up milestones unlock passive abilities chosen from randomised options.

**Debt Mechanic**
An outstanding debt grows if ignored. Missing the repayment deadline ends the game.

**Save & Load**
Multiple save slots with per-slot character previews on the load screen.

---

## Controls

| Key | Action |
|---|---|
| Arrow Keys | Navigate menus |
| Enter | Confirm / Select |
| ESC | Back / Close |
| I | Inventory |
| Q | Quest log |

---

## Requirements

- Python 3.10+
- Pygame 2

```
pip install pygame
```

---

## Running

```
python questforrest.py
```

---

## Tests

```
pip install pytest
pytest tests/
```

---

## Project Structure

```
assets/             - Images, music, sfx
audio/              - Music and sound effects
data/               - Areas, monsters, items, quests, dialogue
logic/              - Input handling and game logic
render/             - Display dispatcher, adventure, village
saves/              - Save game data
scripts/            - Additional testing
state/              - Game state, player, save/load screens
tests/              - Pytest test suite
questforrest.py     - Entry point and main loop

```
