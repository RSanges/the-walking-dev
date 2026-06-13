"""MessagingChannel: the user-facing bot over any chat platform.

An event-driven bot owns its own conversation loop, so the interface is small:
send a message, and run the bot (which handles onboarding, the evening Q&A, and
commands). A new platform (WhatsApp, Signal...) implements these two methods plus
its own handler wiring, reusing questions.ONBOARDING / questions.EVENING.
"""
from abc import ABC, abstractmethod


class MessagingChannel(ABC):
    @abstractmethod
    async def send(self, text: str) -> None:
        """Send a plain text message to the configured user."""

    @abstractmethod
    def run(self) -> None:
        """Start the bot loop: /start onboarding, scheduled evening questions,
        and utility commands (/soir, /episode, /pause)."""

    async def send_tasks(self, date: str, tasks: list[dict]) -> None:
        """Send the day's tasks as a tappable checklist. No-op by default;
        channels that support interactive buttons override this."""
        return None
