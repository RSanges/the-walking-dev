"""S3Hosting: push MP3 + feed.xml to any S3-compatible object storage.

Works with OVHcloud Object Storage (French datacenters), Cloudflare R2,
Scaleway, MinIO, AWS S3... The only differences are the endpoint, region, and
whether objects are exposed via ACL (OVH/Scaleway/MinIO) or a public bucket /
custom domain (R2). The provider just resolves a default endpoint; everything
else is plain S3 via boto3.

Credentials come from generic S3_* env vars (with R2_* kept as a fallback for
existing setups). Public URLs are built from ``public_base_url``.
"""
from ..config import Config
from .base import AudioHosting


class S3Hosting(AudioHosting):
    def __init__(self, config, provider: str = "s3"):
        h = config.section("hosting", provider)
        region = h.get("region") or Config.env("S3_REGION") or "auto"

        endpoint = h.get("endpoint_url") or Config.env("S3_ENDPOINT_URL")
        if not endpoint:
            if provider == "ovh":
                # e.g. https://s3.gra.io.cloud.ovh.net (gra = Gravelines, FR)
                endpoint = "https://s3.%s.io.cloud.ovh.net" % region
            elif provider == "r2":
                endpoint = "https://%s.r2.cloudflarestorage.com" % Config.env(
                    "R2_ACCOUNT_ID")
        if not endpoint:
            raise RuntimeError(
                "S3 endpoint not found: set hosting.%s.endpoint_url or "
                "S3_ENDPOINT_URL." % provider)

        self.bucket = (h.get("bucket") or Config.env("S3_BUCKET")
                       or Config.env("R2_BUCKET", "walkingdev"))
        self.base = (h.get("public_base_url") or Config.env("S3_PUBLIC_BASE_URL")
                     or Config.env("R2_PUBLIC_BASE_URL", "")).rstrip("/")
        # R2 serves via a public bucket/custom domain and rejects ACLs; OVH and
        # other S3 providers need objects flagged public-read.
        self.acl = None if provider == "r2" else h.get("acl", "public-read")

        key = Config.env("S3_ACCESS_KEY_ID") or Config.env("R2_ACCESS_KEY_ID")
        secret = (Config.env("S3_SECRET_ACCESS_KEY")
                  or Config.env("R2_SECRET_ACCESS_KEY"))

        import boto3
        self._s3 = boto3.client(
            "s3", endpoint_url=endpoint, region_name=region,
            aws_access_key_id=key, aws_secret_access_key=secret)

    def publish(self, mp3_path: str, date: str) -> str:
        key = "episodes/" + date + ".mp3"
        self._put_file(mp3_path, key, "audio/mpeg")
        return self.base + "/" + key

    def feed_url(self) -> str:
        return self.base + "/feed.xml"

    def put_feed(self, xml: bytes) -> None:
        self._put_bytes("feed.xml", xml, "application/rss+xml")

    def put_asset(self, name: str, data: bytes, content_type: str) -> str:
        self._put_bytes(name, data, content_type)
        return self.base + "/" + name

    # --- helpers ---
    def _put_file(self, path: str, key: str, content_type: str) -> None:
        extra = {"ContentType": content_type}
        if self.acl:
            extra["ACL"] = self.acl
        self._s3.upload_file(path, self.bucket, key, ExtraArgs=extra)

    def _put_bytes(self, key: str, data: bytes, content_type: str) -> None:
        kw = dict(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
        if self.acl:
            kw["ACL"] = self.acl
        self._s3.put_object(**kw)
