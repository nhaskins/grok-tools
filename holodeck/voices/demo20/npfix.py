"""beats.npy/bars.npy (song-only, gitignored) are missing on this box; sets.py loads them at import. Stub them in memory."""
import numpy as np, os
_l = np.load
def _load(f, *a, **k):
    if not os.path.exists(f) and os.path.basename(str(f)) in ('beats.npy', 'bars.npy'): return np.arange(0, 600, .5)
    return _l(f, *a, **k)
np.load = _load
