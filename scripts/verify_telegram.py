"""Verify Telegram credentials without printing them.

Checks that TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID are set, validates the token
via get_me(), and sends a test message to the chat. Prints only safe info.
"""
import asyncio

from walkingdev.config import Config


async def main():
    Config.load("config.yaml")  # loads .env into os.environ
    token = Config.env("TELEGRAM_BOT_TOKEN")
    chat = Config.env("TELEGRAM_CHAT_ID")
    print("token rempli:", bool(token), "| chat_id rempli:", bool(chat))
    if not token or not chat:
        print("ECHEC: complete .env (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID)")
        return
    from telegram import Bot
    bot = Bot(token)
    me = await bot.get_me()
    print("Bot authentifie -> @%s (id %s)" % (me.username, me.id))
    await bot.send_message(
        chat_id=chat,
        text="The Walking Dev est connecte. Si tu lis ceci, tout fonctionne. "
             "Tape /start pour lancer l'onboarding.")
    print("Message de test envoye au chat", chat)


if __name__ == "__main__":
    asyncio.run(main())
