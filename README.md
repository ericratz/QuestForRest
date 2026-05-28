# Quest For Rest

A keyboard-driven RPG built with Python and Pygame. Explore dungeons, fight monsters, manage equipment, complete quests, and pay off your ever-growing debt before the deadline.

---

## Gameplay

You start in a village with a 100 gold debt to the innkeeper. Each day you choose how to spend your time:

- **Inn** — Pay off your debt, rest to restore HP, or access your stash
- **Shop** — Buy and sell equipment and supplies
- **Quest Board** — Take on quests for gold rewards, or work odd jobs
- **Adventure** — Explore dangerous locations, fight monsters, and find loot

Fail to pay by the deadline and it's game over.

---

## Controls

| Key | Action |
|---|---|
| Arrow Keys | Navigate menus and choices |
| Enter | Confirm / Select |
| ESC | Back / Open pause menu |
| I | Open inventory |
| Q | Open quest log |

---

## Features

- Adventure
- Equipment
- Quests & Achievements
- Save and Load
- Audio & SFX

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

## Project Structure

```
questforrest.py     — Entry point and main loop
state/              — Game state (world, player, save/load)
logic/              — Input handling and game logic
data/               — Areas, items, monsters, quests
render/             — All rendering (display dispatcher, adventure, village)
audio/              — Sound effects and music
assets/             — Images, music, sfx
```
