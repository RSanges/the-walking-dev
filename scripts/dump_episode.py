import os
import sqlite3

import soundfile as sf

c = sqlite3.connect("data/walkingdev.db")
row = c.execute(
    "SELECT date, url, script FROM episodes ORDER BY created_at DESC LIMIT 1"
).fetchone()
if not row:
    print("Aucun episode enregistre.")
    raise SystemExit
d, url, script = row
print("=== EPISODE", d, "===")
print("url:", url)
print("longueur script:", len(script or ""), "caracteres")
wav = "audio/%s.wav" % d
if os.path.exists(wav):
    a, sr = sf.read(wav)
    print("audio:", wav, "| duree=%.1fs (%.1f min)" % (len(a) / sr, len(a) / sr / 60))
else:
    print("audio absent:", wav)
print("\n===== SCRIPT =====\n")
print(script)
