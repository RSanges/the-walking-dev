"""FTPHosting: publish MP3 + feed.xml to classic web hosting over FTPS or SFTP.

Ideal when you already have shared web hosting (e.g. an OVH mutualise plan):
files dropped in the web root are served directly over HTTPS, and a subdomain
maps to a folder with no extra infra.

config hosting.ftp:
  protocol: sftp | ftps
  host: ssh.<host>            (sftp)  | ftp.<host> (ftps)
  port: 22 (sftp) | 21 (ftps)
  remote_dir: "www/podcast"     # folder served at public_base_url
  public_base_url: "https://podcast.example.com"
env: FTP_USER, FTP_PASSWORD (and optionally FTP_HOST, FTP_PUBLIC_BASE_URL)

Privacy note: when the public base URL is unguessable (a secret folder name),
the feed is effectively private. The uploaded .htaccess only disables directory
listing (Options -Indexes); it must NOT add `X-Robots-Tag: noindex`, because a
noindex header on an RSS feed makes Apple/Google Podcasts refuse to ingest it.
"""
import io
import posixpath
import socket

from ..config import Config
from .base import AudioHosting

_HTACCESS = b"Options -Indexes\n"
_TIMEOUT = 60


class FTPHosting(AudioHosting):
    def __init__(self, config):
        h = config.section("hosting", "ftp")
        self.protocol = (h.get("protocol") or "ftps").lower()
        self.host = h.get("host") or Config.env("FTP_HOST")
        self.port = int(h.get("port") or (22 if self.protocol == "sftp" else 21))
        self.remote_dir = (h.get("remote_dir") or "www/podcast").strip("/")
        self.base = (h.get("public_base_url")
                     or Config.env("FTP_PUBLIC_BASE_URL", "")).rstrip("/")
        self.user = Config.env("FTP_USER")
        self.password = Config.env("FTP_PASSWORD")
        if not (self.host and self.user and self.password):
            raise RuntimeError(
                "FTP hosting needs host + FTP_USER + FTP_PASSWORD (set them in "
                ".env and hosting.ftp in config.yaml).")

    # --- public API ---
    def publish(self, mp3_path: str, date: str) -> str:
        key = "episodes/" + date + ".mp3"
        with open(mp3_path, "rb") as f:
            self._upload(key, f.read())
        return self.base + "/" + key

    def feed_url(self) -> str:
        return self.base + "/feed.xml"

    def put_feed(self, xml: bytes) -> None:
        self._upload(".htaccess", _HTACCESS)
        self._upload("feed.xml", xml)

    def put_asset(self, name: str, data: bytes, content_type: str) -> str:
        self._upload(name, data)
        return self.base + "/" + name

    # --- transport ---
    def _upload(self, rel_key: str, data: bytes) -> None:
        remote_path = posixpath.join(self.remote_dir, rel_key)
        if self.protocol == "sftp":
            self._upload_sftp(remote_path, data)
        else:
            self._upload_ftps(remote_path, data)

    def _upload_ftps(self, remote_path: str, data: bytes) -> None:
        from ftplib import FTP_TLS
        ftp = FTP_TLS()
        try:
            ftp.connect(self.host, self.port, timeout=_TIMEOUT)
            ftp.login(self.user, self.password)
            ftp.prot_p()
            _ftps_makedirs(ftp, posixpath.dirname(remote_path))
            ftp.storbinary("STOR " + remote_path, io.BytesIO(data))
        finally:
            try:
                ftp.quit()
            except Exception:
                ftp.close()

    def _upload_sftp(self, remote_path: str, data: bytes) -> None:
        import paramiko
        sock = socket.create_connection((self.host, self.port), timeout=_TIMEOUT)
        transport = paramiko.Transport(sock)
        try:
            transport.connect(username=self.user, password=self.password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            _sftp_makedirs(sftp, posixpath.dirname(remote_path))
            with sftp.open(remote_path, "wb") as f:
                f.write(data)
            sftp.close()
        finally:
            transport.close()


def _ftps_makedirs(ftp, path: str) -> None:
    parts, cur = [p for p in path.split("/") if p], ""
    for p in parts:
        cur = cur + "/" + p if cur else p
        try:
            ftp.mkd(cur)
        except Exception:
            pass  # already exists


def _sftp_makedirs(sftp, path: str) -> None:
    parts, cur = [p for p in path.split("/") if p], ""
    for p in parts:
        cur = cur + "/" + p if cur else p
        try:
            sftp.stat(cur)
        except OSError:
            sftp.mkdir(cur)
