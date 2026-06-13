# The Walking Dev

A self-hosted, open-source generator for a **daily personal podcast** you listen
to on your morning walk. Every night it gathers your world (news on your themes,
project/objective progress, a summary of useful mail, today's calendar), writes a
spoken script, turns it into audio with a local voice, and publishes a private
podcast RSS feed. You wake up, hit play, and walk.

Built to be **cloned and run by anyone**: every moving part is a swappable
adapter, with sensible zero-account defaults.

```
Evening (~21:30)   a Telegram bot asks you a few short questions  ->  stored locally
Night              gather -> write script -> synthesize -> publish -> trace
Morning            your podcast app fetches the new episode via RSS
```

Audio order: intro, news, projects/objectives, challenge of the day, mail,
agenda (last), outro.

## What it sounds like

A brief is a single spoken track. 🔊 **[Listen to a 10s sample](demo/sample.mp3)**
(neutral default voice, generic content). Here's a generic excerpt of the kind of
script it produces (your real one is built from your own news, projects and answers):

> Good morning. It's seven o'clock, here's your brief for the day. Let's get moving.
>
> On the news front: a new open-weights model dropped this week, and it matters for
> anyone keeping their stack on their own machine, it closes a lot of the gap with the
> hosted options. Worth thirty minutes this weekend to try it on something real.
>
> On your projects: the API refactor is the one marked active, so that's today, ship the
> auth endpoint before you touch anything else. The dashboard is still on hold, leave it there.
>
> Challenge of the day, on focus: you started three things this week and finished none.
> Which one would actually move the needle if it were done by Friday, and what are you
> avoiding by staying busy?
>
> That's it. One thing at a time. Enjoy the walk.

## Adapters

Every concern is an interface with a default and swappable backends. Pick them in
`config.yaml`; put secrets in `.env`.

| Concern          | Interface          | Default                | Other backends |
|------------------|--------------------|------------------------|----------------|
| Chat / Q&A       | `MessagingChannel` | Telegram               | CLI (terminal, no network) |
| Knowledge source | `KnowledgeProvider`| Local store            | Obsidian vault |
| State storage    | `StateStore`       | SQLite (one file)      | (Supabase: planned) |
| Script writer    | `ScriptWriter`     | Claude Code (headless) | **Local LLM** (Ollama, LM Studio, llama.cpp, vLLM), Anthropic API |
| Audio hosting    | `AudioHosting`     | Local folder           | FTP/SFTP, OVH, Cloudflare R2, Scaleway, MinIO, S3 |
| Text-to-speech   | `TTSEngine`        | OmniVoice (local GPU)  | — |

## Requirements

- **Python 3.12** (managed with [uv](https://docs.astral.sh/uv/), recommended)
- A **messaging channel**: a [Telegram bot token](https://t.me/BotFather) (free),
  or the **CLI channel** for a no-network terminal check-in
- A **script writer**, one of:
  - the [Claude Code](https://docs.anthropic.com/claude/docs/claude-code) CLI
    (default, covered by a Claude Max plan; adds web search + Gmail/Calendar),
  - a **local LLM** via any OpenAI-compatible server (Ollama, LM Studio,
    llama.cpp, vLLM) — fully offline,
  - or an `ANTHROPIC_API_KEY`
- **For local TTS**: an NVIDIA GPU (validated on an RTX 2070 Super, 8 GB).
  No GPU? You can still develop everything else; only the audio synthesis step
  needs it (or set `tts.omnivoice.device: cpu`, much slower).

## Privacy / fully-local mode

Every component can run on your machine. For a setup where **nothing leaves your
computer**, in `config.yaml`:

```yaml
channel:   { backend: cli }          # terminal check-in, no Telegram
knowledge: { backend: local }        # or obsidian (your local vault)
state:     { backend: sqlite }       # one local file
writer:
  backend: local                     # local LLM, no cloud
  local: { base_url: "http://localhost:11434/v1", model: "llama3.1" }
hosting:   { backend: local }        # files on disk; serve with a local server/tunnel
tts:       { backend: omnivoice }    # local GPU voice
news:      { enabled: false }        # skip the web RSS fetch entirely
```

With this profile there is **zero outbound traffic**. If you keep `news.enabled:
true`, the only network calls are read-only fetches of the public RSS feeds you
list (they carry nothing personal). The local writer has no mail/calendar
connectors, so those segments are simply skipped.

Run it with:

```bash
# 1. start your local model server, e.g.:
ollama serve & ollama pull llama3.1
# 2. onboard / nightly / evening check-in, all local:
uv run walkingdev bot        # onboarding (first run), then evening check-in
uv run walkingdev nightly    # generate today's episode
```

## Quick start

```bash
git clone https://github.com/RSanges/the-walking-dev && cd the-walking-dev
uv sync                                   # Python 3.12 venv + core deps

cp .env.example .env                      # add your Telegram bot token + chat id
cp config.example.yaml config.yaml        # edit to taste

# Optional extras, install only what your config uses:
uv pip install -e ".[sftp]"               # FTP/SFTP hosting
uv pip install -e ".[s3]"                 # OVH / R2 / S3 hosting
uv pip install -e ".[api]"                # Anthropic API writer (instead of Claude Code)

# Local GPU voice (NVIDIA). Run once, then validate the voice:
powershell -ExecutionPolicy Bypass -File scripts/install_omnivoice.ps1   # Windows
uv run python scripts/spike_omnivoice.py

uv run walkingdev doctor                   # check environment & config
uv run walkingdev bot                      # onboarding + evening questions
uv run walkingdev nightly                  # generate one episode now
```

> Run commands from the repo root: paths (`config.yaml`, `.env`, `audio/`,
> `data/`) resolve relative to the project folder. You can override the root with
> the `WALKINGDEV_HOME` environment variable.

## Commands

```
walkingdev bot                  start the messaging bot (onboarding + evening flow)
walkingdev nightly [--day D]    generate one episode now (used by the scheduler)
walkingdev doctor               check environment, config and connectors
```

Common options: `--config PATH`, `--force` (regenerate today's episode), `-v`.

## Scheduling the nightly run

**Windows (Task Scheduler):**

```powershell
powershell -ExecutionPolicy Bypass -File scripts/schedule_task.ps1 -At 05:30
powershell -ExecutionPolicy Bypass -File scripts/schedule_bot.ps1   # bot at logon
```

**Linux/macOS (cron):** add a line with `crontab -e`:

```cron
30 5 * * *  cd /path/to/the-walking-dev && /path/to/.venv/bin/walkingdev nightly
```

Run the bot continuously with your process manager of choice (systemd, `tmux`,
`pm2`, ...): `walkingdev bot`.

## Hosting the feed

- **local** (default): writes `public/episodes/<date>.mp3` + `public/feed.xml`.
  Serve `public/` with any static server, or expose it with a tunnel
  (e.g. `cloudflared`).
- **ftp / sftp**: drop files on classic shared web hosting; a subdomain folder
  maps to `public_base_url`. Needs `FTP_USER` / `FTP_PASSWORD` in `.env`.
- **ovh / r2 / s3 / scaleway / minio**: any S3-compatible object storage. Generic
  `S3_ACCESS_KEY_ID` / `S3_SECRET_ACCESS_KEY` in `.env` (R2 also needs
  `R2_ACCOUNT_ID`).

Add the feed URL (`<public_base_url>/feed.xml`) to your podcast app. Keeping the
base URL unguessable (a secret folder name) is the simplest way to keep a
personal feed private.

## How the brief is written

The nightly pipeline ([`walkingdev/pipeline/nightly.py`](walkingdev/pipeline/nightly.py))
hands the script writer fresh, dated RSS items (no stale training-data news), your
projects/objectives, last night's answers, yesterday's task follow-through, and
optionally your whole Obsidian vault as background context. With the default
Claude Code writer it can also call connected MCP tools (Gmail, Calendar) during
the run. The personal "challenge of the day" focus areas and any private context
are configured in `config.yaml` (`podcast.challenge`), so nothing personal lives
in the source.

## Development

```bash
uv pip install -e ".[dev]"     # pytest + ruff
pytest -q                      # offline test suite (no network, no GPU)
ruff check walkingdev scripts tests
```

CI (GitHub Actions) runs ruff + pytest on every push and PR. See
[CONTRIBUTING.md](CONTRIBUTING.md).

## Project layout

```
walkingdev/
  channels/    MessagingChannel (Telegram)
  knowledge/   KnowledgeProvider (local store, Obsidian)
  state/       StateStore (SQLite)
  writer/      ScriptWriter (Claude Code, API) + prompt builder
  tts/         TTSEngine (OmniVoice)
  hosting/     AudioHosting (local, FTP/SFTP, S3) + RSS feed builder
  news.py      curated-RSS gathering
  pipeline/    the nightly orchestration
scripts/       install, scheduling and one-off helper utilities
tests/         offline unit tests
```

## License

[MIT](LICENSE). The "The Walking Dev" name and artwork are a playful nod to a
well-known series; if you redistribute, consider your own branding.
