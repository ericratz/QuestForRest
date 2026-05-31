'''
tests/conftest.py
Session-level setup: mock out the modules that require pygame or display
initialisation so all game-logic modules can be imported cleanly.
'''

import sys
from unittest.mock import MagicMock

# ── Mock pygame ───────────────────────────────────────────────────────────────
# Only fake what doesn't exist yet; leave real pygame if already installed.
if 'pygame' not in sys.modules:
    sys.modules['pygame'] = MagicMock()

# ── Mock audio.sounds ─────────────────────────────────────────────────────────
_sfx = MagicMock()
_sfx.play           = MagicMock()
_sfx.play_delayed   = MagicMock()
_sfx.play_exclusive = MagicMock()
_sfx.set_music      = MagicMock()
_sfx.stop_music     = MagicMock()
_sfx.set_sfx_volume = MagicMock()
_sfx.set_music_volume = MagicMock()
sys.modules['audio']        = MagicMock()
sys.modules['audio.sounds'] = _sfx

# ── Mock render.helpers ───────────────────────────────────────────────────────
_rh = MagicMock()
_rh.trigger_fade_in = MagicMock()
sys.modules['render']          = MagicMock()
sys.modules['render.helpers']  = _rh
