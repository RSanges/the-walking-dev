from .base import AudioHosting


def make_hosting(config) -> AudioHosting:
    backend = config.get("hosting", "backend", default="local")
    if backend == "local":
        from .local import LocalHosting
        return LocalHosting(config)
    if backend in ("ftp", "sftp", "ftps"):
        from .ftp import FTPHosting
        return FTPHosting(config)
    # All object-storage backends share one S3 adapter; the provider only
    # changes endpoint resolution and ACL handling.
    if backend in ("ovh", "r2", "s3", "scaleway", "minio"):
        from .s3 import S3Hosting
        return S3Hosting(config, provider=backend)
    raise NotImplementedError("hosting backend not implemented: " + str(backend))
