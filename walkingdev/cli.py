"""Command line entry point.

  walkingdev bot                  start the messaging bot (onboarding + evening)
  walkingdev nightly [--day D]    run the nightly generation once (scheduler)
  walkingdev doctor               check environment, config and connectors

Common options: --config PATH, --force (nightly), -v/--verbose.
"""
import argparse
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def _setup_logging(verbose: bool = False) -> None:
    """Configure root logging once: a rotating file under data/ plus the console
    when one is attached (the bot runs under pythonw with no console)."""
    level = logging.DEBUG if verbose else logging.INFO
    root = logging.getLogger()
    if root.handlers:  # already configured
        root.setLevel(level)
        return
    root.setLevel(level)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    try:
        data_dir = Path.cwd() / "data"
        data_dir.mkdir(exist_ok=True)
        fh = RotatingFileHandler(
            data_dir / "walkingdev.log", maxBytes=2_000_000, backupCount=3,
            encoding="utf-8")
        fh.setFormatter(fmt)
        root.addHandler(fh)
    except OSError:
        pass
    if sys.stdout is not None:
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        root.addHandler(ch)


def _alert_nightly_failure(config_path: str, day: str | None, exc: Exception) -> None:
    """Best-effort heads-up over the messaging channel when the nightly run dies.

    The brief is generated unattended, so a crash would otherwise be silent until
    someone notices the podcast went quiet. Any failure here is swallowed (logged
    only): the alert must never mask the original error or change the exit code.
    """
    from datetime import date as _date
    try:
        import asyncio

        from .channels import make_channel
        from .config import Config
        cfg = Config.load(config_path)
        when = day or _date.today().isoformat()
        text = (
            "⚠️ The Walking Dev : la generation du brief a echoue (%s).\n"
            "%s: %s\n\n"
            "Aucun nouvel episode ne sera publie. Le planificateur reessaiera "
            "demain matin." % (when, type(exc).__name__, str(exc)[:600])
        )
        asyncio.run(make_channel(cfg).send(text))
    except Exception:
        logging.getLogger("walkingdev.cli").warning(
            "could not send nightly failure alert", exc_info=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="walkingdev", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default="config.yaml", help="path to config.yaml")
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("bot", help="start the messaging bot")
    p_nightly = sub.add_parser("nightly", help="generate one episode now")
    p_nightly.add_argument("--day", help="YYYY-MM-DD (default: today)")
    p_nightly.add_argument("--force", action="store_true",
                           help="regenerate even if today's episode exists")
    sub.add_parser("doctor", help="check environment and config")

    args = parser.parse_args(argv)
    _setup_logging(args.verbose)

    if args.command == "nightly":
        from .pipeline.nightly import run
        try:
            run(config_path=args.config, day=args.day, force=args.force)
        except Exception as exc:
            logging.getLogger("walkingdev.cli").exception("nightly run failed")
            _alert_nightly_failure(args.config, args.day, exc)
            raise  # keep a non-zero exit so the scheduler records the failure
        return 0
    if args.command == "bot":
        from .channels import make_channel
        from .config import Config
        make_channel(Config.load(args.config)).run()
        return 0
    if args.command == "doctor":
        from .doctor import check
        return check(args.config)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
