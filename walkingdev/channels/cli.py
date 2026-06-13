"""CLIChannel: a fully-local messaging channel (no Telegram, no network).

Runs onboarding and the evening check-in interactively in the terminal, so your
answers never leave the machine. The daily task checklist is printed (no tappable
buttons). Use it for a 100%-local privacy profile:

  channel:
    backend: cli

`walkingdev bot` then runs onboarding the first time, and the evening check-in on
subsequent runs (schedule it with cron at your evening time).
"""
import logging
from datetime import date as _date

from ..questions import ONBOARDING
from ..state import make_state
from .base import MessagingChannel

log = logging.getLogger(__name__)


class CLIChannel(MessagingChannel):
    def __init__(self, config):
        self.config = config
        self.state = make_state(config)

    async def send(self, text: str) -> None:
        print(text)

    def run(self) -> None:
        if not self.state.is_onboarded():
            self._onboard()
        else:
            self._evening()

    # --- flows ---
    def _onboard(self) -> None:
        print("\n=== The Walking Dev: onboarding (local) ===")
        answers = self._ask(ONBOARDING)
        self.state.save_onboarding(answers)
        print("\nCalibrated. Your first brief can be generated with "
              "`walkingdev nightly`. Run `walkingdev bot` each evening for the "
              "check-in.")

    def _evening(self) -> None:
        from .. import evening_questions
        today = _date.today().isoformat()
        print("\n=== Evening check-in (local) ===")
        questions = evening_questions.generate(self.config, today)
        answers = self._ask(questions)
        self.state.save_evening(today, answers)
        print("\nNoted. Tomorrow's brief will take it into account.")

    def _ask(self, questions) -> dict:
        answers = {}
        for q in questions:
            suffix = "  (optional, Enter to skip)" if q.optional else ""
            try:
                ans = input(f"\n{q.text}{suffix}\n> ").strip()
            except EOFError:
                ans = ""
            answers[q.key] = ans
        return answers

    async def send_tasks(self, date: str, tasks: list[dict]) -> None:
        if not tasks:
            return
        print(f"\nTasks for {date}:")
        for t in tasks:
            mark = "[x]" if t["done"] else "[ ]"
            print(f"  {mark} {t['idx'] + 1}. {t['text']}")
        print("(mark them off in your own tracker)")
