"""Telegram implementation of MessagingChannel.

Default channel: free, no approval, token via @BotFather. Drives two flows with
a ConversationHandler:
  - ONBOARDING: triggered by /start the first time, calibrates the profile.
  - EVENING: a daily JobQueue prompt (configurable time) or manual /soir.
Answers are written to the StateStore. Voice notes are downloaded; transcription
is a pluggable step (TODO) so text works fully today.

Authorization: when TELEGRAM_CHAT_ID is set, the bot only answers that chat, so a
publicly-cloned bot does not respond to strangers who find it.

Commands: /start /soir /episode /taches /pause /help /annuler
"""
import asyncio
import logging
from datetime import date as _date
from datetime import time as _time

from ..config import Config
from ..questions import ONBOARDING, Question
from ..state import make_state
from .base import MessagingChannel

log = logging.getLogger(__name__)

ASKING = 0


class TelegramChannel(MessagingChannel):
    def __init__(self, config: Config):
        self.config = config
        self.state = make_state(config)
        self.token = Config.env("TELEGRAM_BOT_TOKEN")
        self.chat_id = Config.env("TELEGRAM_CHAT_ID")
        if not self.token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN missing from .env")
        self._bot = None  # set in run()

    # --- MessagingChannel API ---
    async def send(self, text: str) -> None:
        from telegram import Bot
        await (self._bot or Bot(self.token)).send_message(
            chat_id=self.chat_id, text=text)

    def run(self) -> None:
        from telegram.ext import (
            ApplicationBuilder,
            CallbackQueryHandler,
            CommandHandler,
            ConversationHandler,
            MessageHandler,
            filters,
        )

        log.info("bot starting")
        app = ApplicationBuilder().token(self.token).build()
        self._bot = app.bot

        async def _err(update, context):
            log.error("handler error: %r", context.error, exc_info=context.error)
        app.add_error_handler(_err)

        # Restrict every handler to the configured chat when one is set.
        auth = filters.Chat(int(self.chat_id)) if self.chat_id else None
        answer_filter = (filters.TEXT & ~filters.COMMAND) | filters.VOICE
        if auth:
            answer_filter = answer_filter & auth

        conv = ConversationHandler(
            entry_points=[
                CommandHandler("start", self._cmd_start, filters=auth),
                CommandHandler("soir", self._cmd_evening, filters=auth),
            ],
            states={ASKING: [MessageHandler(answer_filter, self._on_answer)]},
            fallbacks=[
                CommandHandler("annuler", self._cancel, filters=auth),
                CommandHandler("passer", self._skip, filters=auth),
            ],
        )
        app.add_handler(conv)
        app.add_handler(CommandHandler("episode", self._cmd_episode, filters=auth))
        app.add_handler(CommandHandler("taches", self._cmd_tasks, filters=auth))
        app.add_handler(CommandHandler("pause", self._cmd_pause, filters=auth))
        app.add_handler(CommandHandler("help", self._cmd_help, filters=auth))
        app.add_handler(CallbackQueryHandler(self._on_task_toggle, pattern=r"^t:"))

        # Daily evening prompt via JobQueue (bot must run continuously).
        hh, mm = _parse_hhmm(self.config.get(
            "schedule", "evening_questions_at", default="21:30"))
        tz = self._tzinfo()
        if app.job_queue:
            app.job_queue.run_daily(self._job_evening, time=_time(hh, mm, tzinfo=tz))

        app.run_polling()

    def _tzinfo(self):
        name = self.config.get("podcast", "timezone", default="Europe/Paris")
        try:
            from zoneinfo import ZoneInfo
            return ZoneInfo(name)
        except Exception:
            return None

    def _authorized(self, update) -> bool:
        if not self.chat_id:
            return True
        chat = update.effective_chat
        return chat is not None and str(chat.id) == str(self.chat_id)

    # --- flow helpers ---
    async def _begin(self, update, context, flow, questions):
        context.user_data.update(flow=flow, questions=questions, idx=0, answers={})
        await self._ask_current(update, context)
        return ASKING

    async def _ask_current(self, update, context):
        q: Question = context.user_data["questions"][context.user_data["idx"]]
        suffix = "\n(facultatif, /passer pour sauter)" if q.optional else ""
        await update.effective_message.reply_text(q.text + suffix)

    async def _record_and_advance(self, update, context, answer):
        from telegram.ext import ConversationHandler
        q: Question = context.user_data["questions"][context.user_data["idx"]]
        context.user_data["answers"][q.key] = answer
        context.user_data["idx"] += 1
        if context.user_data["idx"] < len(context.user_data["questions"]):
            await self._ask_current(update, context)
            return ASKING
        await self._finish(update, context)
        return ConversationHandler.END

    async def _on_answer(self, update, context):
        msg = update.effective_message
        if msg.voice:
            tg_file = await msg.voice.get_file()
            path = str(self.config.root / "data" / ("voice_%s.ogg" % msg.message_id))
            await tg_file.download_to_drive(path)
            answer = "[vocal a transcrire: %s]" % path  # TODO: transcription
        else:
            answer = (msg.text or "").strip()
        return await self._record_and_advance(update, context, answer)

    async def _skip(self, update, context):
        q: Question = context.user_data["questions"][context.user_data["idx"]]
        if not q.optional:
            await update.effective_message.reply_text(
                "Cette question n'est pas facultative.")
            return ASKING
        return await self._record_and_advance(update, context, "")

    async def _finish(self, update, context):
        flow = context.user_data["flow"]
        answers = context.user_data["answers"]
        if flow == "onboarding":
            self.state.save_onboarding(answers)
            await update.effective_message.reply_text(
                "C'est calibre. Ton premier brief sera pret demain matin. "
                "Chaque soir je te poserai quelques questions (/soir maintenant).")
        else:
            self.state.save_evening(_date.today().isoformat(), answers)
            await update.effective_message.reply_text(
                "Note. Bonne nuit, le brief de demain en tiendra compte.")

    # --- commands ---
    async def _cmd_start(self, update, context):
        from telegram.ext import ConversationHandler
        if self.state.is_onboarded():
            await update.effective_message.reply_text(
                "Deja configure. /soir pour le point du jour, /episode pour le "
                "dernier brief, /help pour tout.")
            return ConversationHandler.END
        await update.effective_message.reply_text(
            "Bienvenue dans The Walking Dev. Quelques questions pour tout calibrer.")
        return await self._begin(update, context, "onboarding", ONBOARDING)

    async def _cmd_evening(self, update, context):
        from .. import evening_questions
        await update.effective_message.reply_text(
            "Je prepare tes questions du soir...")
        questions = await asyncio.to_thread(
            evening_questions.generate, self.config, _date.today().isoformat())
        return await self._begin(update, context, "evening", questions)

    async def _job_evening(self, context):
        await context.bot.send_message(
            chat_id=self.chat_id,
            text="C'est l'heure du point du soir. Tape /soir quand tu es pret.")

    async def _cmd_episode(self, update, context):
        day = _date.today().isoformat()
        url = next((e["url"] for e in self.state.list_episodes()
                    if e["date"] == day), None)
        await update.effective_message.reply_text(
            url or "Pas encore d'episode pour aujourd'hui.")

    # --- tasks checklist ---
    # Full task text goes in the message BODY (it wraps); the buttons stay
    # compact (checkbox + number) because inline-button labels can't wrap.
    async def send_tasks(self, date: str, tasks: list[dict]) -> None:
        from telegram import Bot
        if not tasks:
            return
        bot = self._bot or Bot(self.token)
        await bot.send_message(
            chat_id=self.chat_id, text=self._tasks_text(date, tasks),
            reply_markup=self._task_keyboard(date, tasks))

    def _tasks_text(self, date: str, tasks: list[dict]) -> str:
        lines = ["\U0001F5D2 Tes taches du " + date + " :", ""]
        for t in tasks:
            mark = "✅" if t["done"] else "⬜"
            lines.append("%s %d. %s" % (mark, t["idx"] + 1, t["text"]))
        lines += ["", "Tape un numero ci-dessous pour cocher / decocher."]
        return "\n".join(lines)

    def _task_keyboard(self, date: str, tasks: list[dict]):
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        btns = [
            InlineKeyboardButton(
                ("✅" if t["done"] else "⬜") + " %d" % (t["idx"] + 1),
                callback_data="t:%s:%d" % (date, t["idx"]))
            for t in tasks
        ]
        rows = [btns[i:i + 4] for i in range(0, len(btns), 4)]  # 4 per row
        return InlineKeyboardMarkup(rows)

    async def _cmd_tasks(self, update, context):
        date = _date.today().isoformat()
        tasks = self.state.get_tasks(date)
        if not tasks:
            await update.effective_message.reply_text(
                "Pas de taches pour aujourd'hui (le brief du matin les genere).")
            return
        await update.effective_message.reply_text(
            self._tasks_text(date, tasks),
            reply_markup=self._task_keyboard(date, tasks))

    async def _on_task_toggle(self, update, context):
        q = update.callback_query
        if not self._authorized(update):
            await q.answer()
            return
        await q.answer()  # stop the spinner immediately
        try:
            _, date, idx = q.data.split(":")
            new = self.state.toggle_task(date, int(idx))
            if new is None:
                await q.answer("Liste obsolete, retape /taches.", show_alert=False)
                return
            log.info("toggle %s idx=%s -> done=%s", date, idx, new)
            tasks = self.state.get_tasks(date)
            await q.edit_message_text(
                self._tasks_text(date, tasks),
                reply_markup=self._task_keyboard(date, tasks))
        except Exception as e:
            log.error("toggle failed: %r", e, exc_info=e)

    async def _cmd_pause(self, update, context):
        await update.effective_message.reply_text(
            "Pause notee. (Gestion fine des jours OFF a venir.)")

    async def _cmd_help(self, update, context):
        await update.effective_message.reply_text(
            "/start configurer | /soir questions du soir | /taches checklist du jour "
            "| /episode dernier brief | /pause suspendre | /annuler interrompre")

    async def _cancel(self, update, context):
        from telegram.ext import ConversationHandler
        await update.effective_message.reply_text("Interrompu.")
        return ConversationHandler.END


def _parse_hhmm(s):
    try:
        hh, mm = str(s).split(":")
        return int(hh), int(mm)
    except Exception:
        return 21, 30
