from .base import MessagingChannel


def make_channel(config) -> MessagingChannel:
    backend = config.get("channel", "backend", default="telegram")
    if backend == "telegram":
        from .telegram import TelegramChannel
        return TelegramChannel(config)
    if backend == "cli":
        from .cli import CLIChannel
        return CLIChannel(config)
    raise NotImplementedError("channel backend not implemented: " + str(backend))
