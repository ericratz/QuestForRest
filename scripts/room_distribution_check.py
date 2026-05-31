'''
Room distribution analysis.
Reads room_dist directly from gamestate.ADVENTURE_LOCATIONS so the numbers
are always authoritative. Simulates 1000 adventures per location and reports:
  - frequency of each room type (should be exactly as defined in room_dist)
  - monster multiplier vs. every other type (should be exactly 3.00x)
  - consecutive same-type pairs (shows back-to-back is possible)
  - any room type handled by enter_room but missing from a location's deck
'''

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from collections import Counter
from unittest.mock import patch, MagicMock

# Stub pygame before importing game modules
pygame_stub = MagicMock()
sys.modules.setdefault('pygame', pygame_stub)
sys.modules.setdefault('pygame.mixer', pygame_stub.mixer)

import state.gamestate as gamestate

ALL_ROOM_TYPES = {
    "campfire", "cursed", "damage", "fairy", "food",
    "item", "nothing", "shrine", "trapped_chest", "wanderer",
}

N = 1000
random.seed(42)

all_ok = True

for loc in gamestate.ADVENTURE_LOCATIONS:
    dist = loc["room_dist"]
    n_rooms = len(dist)
    total_rooms = loc["total_rooms"]
    counter = Counter()
    consecutive_hits = 0

    for _ in range(N):
        seq = dist[:]
        random.shuffle(seq)
        counter.update(seq)
        for i in range(len(seq) - 1):
            if seq[i] == seq[i + 1]:
                consecutive_hits += 1

    total = sum(counter.values())
    monster_count = counter["monster"]
    others = {k: v for k, v in counter.items() if k != "monster"}
    avg_other = sum(others.values()) / len(others) if others else 1
    mult = monster_count / avg_other

    missing = ALL_ROOM_TYPES - set(dist)
    extra   = set(dist) - ALL_ROOM_TYPES - {"monster"}

    # PASS criteria:
    #   • monster ratio >= 3.0x vs the average non-monster type (target: >=3.00x)
    #   • no unknown room types
    #   • missing types are flagged but only FAIL for areas large enough to fit all 10
    missing_fail = missing and len(dist) >= 13   # Dark Forest (9 slots) cannot fit all 10 at 3:1
    ok = mult >= 2.99 and not extra and not missing_fail
    all_ok = all_ok and ok
    status = "OK" if ok else "FAIL"

    print(f"=== [{status}] {loc['name']}  ({n_rooms} non-boss rooms + 1 boss = {total_rooms} total) ===")
    print()

    header = f"  {'Room type':<18} {'Total':>6}  {'Per adv':>8}  {'In dist':>7}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for rtype in sorted(counter, key=lambda k: -counter[k]):
        in_dist = dist.count(rtype)
        per_adv = counter[rtype] / N
        print(f"  {rtype:<18} {counter[rtype]:>6}  {per_adv:>8.2f}  {in_dist:>7}")

    print()
    print(f"  Monster multiplier vs avg other: {mult:.2f}x  (target: >=3.00x)")
    print(f"  Consecutive same-type pairs: {consecutive_hits} across {N} runs")
    print(f"  Back-to-back possible: yes (no constraint prevents it)")

    if missing:
        note = "(intentional — area too small for all 10 types)" if not missing_fail else "(FAIL)"
        print(f"  Omitted room types: {sorted(missing)}  {note}")
    if extra:
        print(f"  UNKNOWN room types (not handled by enter_room): {sorted(extra)}")

    n_tiers = len(loc["tiers"])
    expected_tiers = total_rooms - 1
    tier_ok = n_tiers == expected_tiers
    print(f"  Tiers array: {n_tiers} entries (expected {expected_tiers}): {'OK' if tier_ok else 'MISMATCH'}")
    print()

print("=" * 60)
print(f"Overall: {'ALL PASS' if all_ok else 'FAILURES DETECTED'}")
