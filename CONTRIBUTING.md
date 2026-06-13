# Contributing to The Walking Dev

Thanks for your interest! This project is designed so anyone can clone it and run
their own daily podcast. Contributions that keep that "clone-and-run" promise
intact are very welcome.

## Getting set up

```bash
git clone https://github.com/RSanges/the-walking-dev && cd the-walking-dev
uv sync
uv pip install -e ".[dev]"     # pytest + ruff
cp .env.example .env
cp config.example.yaml config.yaml
```

Run the offline checks before pushing:

```bash
ruff check walkingdev scripts tests
pytest -q
```

Both run in CI on every push and pull request (Python 3.12).

## Ground rules

- **No personal data in the source.** Anything user-specific (names, emails,
  hostnames, focus areas, vault paths) belongs in `config.yaml` / `.env`, never
  in code or example files. The example configs must stay generic.
- **Keep adapters swappable.** New backends implement an existing interface
  (`MessagingChannel`, `KnowledgeProvider`, `StateStore`, `ScriptWriter`,
  `AudioHosting`, `TTSEngine`) and register in the matching `make_*` factory.
- **Tests stay offline.** Unit tests must not hit the network, a GPU, Telegram,
  or remote hosting. Mock at the boundary (see `tests/test_news.py` for the
  pattern). Add tests for new behavior.
- **Lint clean.** `ruff` config lives in `pyproject.toml`. Heavy imports
  (`torch`, `telegram`, `boto3`, `paramiko`) stay lazy (imported inside the
  function that needs them) so the default install stays light.
- **Match the surrounding style.** Code comments and docstrings in English;
  user-facing bot strings can stay French (they are what the narrator/bot says).

## Adding a backend

1. Implement the interface in the relevant package (e.g. a new
   `walkingdev/hosting/<name>.py`).
2. Wire it into the factory (`make_hosting`, `make_channel`, ...).
3. Document its config keys in `config.example.yaml` and any env vars in
   `.env.example`.
4. Add unit tests that exercise it without external services.

## Commit / PR

- Keep commits focused; describe the "why" in the body.
- Open a PR against `main`. CI must be green.
- For larger changes, open an issue first to discuss the approach.

## Reporting issues

Include your OS, Python version, the relevant `config.yaml` section (redact
secrets), and the output of `walkingdev doctor`.
