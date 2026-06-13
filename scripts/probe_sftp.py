"""Probe the SFTP connection and show the directory layout (find the web root).

Reads the host/port from config.yaml (hosting.ftp) and credentials from .env.
"""
import paramiko

from walkingdev.config import Config

cfg = Config.load("config.yaml")
ftp = cfg.section("hosting", "ftp")
host = ftp.get("host") or Config.env("FTP_HOST")
port = int(ftp.get("port") or 22)
user = Config.env("FTP_USER")
pwd = Config.env("FTP_PASSWORD")
print("Connecting %s@%s:%d ..." % (user, host, port))

t = paramiko.Transport((host, port))
t.connect(username=user, password=pwd)
sftp = paramiko.SFTPClient.from_transport(t)
print("Home:", sftp.normalize("."))
print("Home contents:", sorted(sftp.listdir(".")))
for d in ("www", "public_html", "htdocs"):
    try:
        print("Contents of %s:" % d, sorted(sftp.listdir(d))[:20])
    except OSError:
        pass
sftp.close()
t.close()
print("OK")
