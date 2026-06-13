from .base import MessagingChannel


def make_channel(config) -> MessagingChannel:
    backend = config.get("channel", "backend", default="telegram")
    if backend == "telegram":
        from .telegram import TelegramChannel
        return TelegramChannel(config)
    raise NotImplementedError("channel backend not implemented: " + str(backend))
