import os
import sqlite3

p = "data/walkingdev.db"
print("db existe:", os.path.exists(p))
if os.path.exists(p):
    c = sqlite3.connect(p)
    ob = c.execute("SELECT 1 FROM kv WHERE k='onboarding'").fetchone()
    print("onboarding present:", bool(ob))
    ev = c.execute("SELECT COUNT(*) FROM evening").fetchone()[0]
    print("reponses du soir enregistrees:", ev)
