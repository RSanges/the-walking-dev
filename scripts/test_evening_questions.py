"""Show the adaptive evening questions Claude generates for a given day."""
import sys

from walkingdev import evening_questions
from walkingdev.config import Config

day = sys.argv[1] if len(sys.argv) > 1 else "2026-06-04"
qs = evening_questions.generate(Config.load("config.yaml"), day)
print("=== Questions du soir (", len(qs), ") ===")
for i, q in enumerate(qs, 1):
    print("%d. [%s] %s" % (i, q.kind, q.text))
