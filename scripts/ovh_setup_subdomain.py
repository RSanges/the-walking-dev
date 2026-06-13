"""Create a subdomain on an OVH shared-hosting plan, via the OVH API.

Attaches a subdomain to the folder your feed is published to (hosting.ftp
remote_dir), with SSL, then ensures the DNS record exists and triggers a
Let's Encrypt certificate. Idempotent: existing domain/record/SSL are skipped.

Everything personal is read from config.yaml + .env (nothing hardcoded):
  config hosting.ftp.public_base_url  -> the subdomain (e.g. https://podcast.example.com)
  config hosting.ftp.remote_dir       -> the web docroot the subdomain points to

Prerequisites (.env):
  OVH_ENDPOINT=ovh-eu
  OVH_APP_KEY=...
  OVH_APP_SECRET=...
  OVH_CONSUMER_KEY=...
  OVH_SERVICE_NAME=<your-hosting>.hosting.ovh.net   # the web hosting service name

Run:  python scripts/ovh_setup_subdomain.py
"""
import os
import sys
from urllib.parse import urlparse

try:
    import ovh
except ImportError:
    sys.exit("Missing the OVH client:  pip install ovh")

from walkingdev.config import Config

cfg = Config.load("config.yaml")  # also loads .env into the environment

base_url = cfg.get("hosting", "ftp", "public_base_url", default="")
host = urlparse(base_url).hostname
if not host:
    sys.exit("Set hosting.ftp.public_base_url in config.yaml (e.g. https://podcast.example.com)")
DOMAIN = host                                  # podcast.example.com
parts = host.split(".")
SUB = parts[0]                                 # podcast
ZONE = ".".join(parts[1:])                     # example.com
DOCROOT = (cfg.get("hosting", "ftp", "remote_dir", default="www/podcast")).strip("/")
SERVICE = os.environ["OVH_SERVICE_NAME"]

client = ovh.Client(
    endpoint=os.environ.get("OVH_ENDPOINT", "ovh-eu"),
    application_key=os.environ["OVH_APP_KEY"],
    application_secret=os.environ["OVH_APP_SECRET"],
    consumer_key=os.environ["OVH_CONSUMER_KEY"],
)


def step(msg):
    print("\n==>", msg)


# 1. Attach the subdomain -> docroot, with SSL
step("Attach %s -> /%s (SSL)" % (DOMAIN, DOCROOT))
existing = client.get("/hosting/web/%s/attachedDomain" % SERVICE)
if DOMAIN in existing:
    print("   already attached, skipping.")
else:
    client.post("/hosting/web/%s/attachedDomain" % SERVICE,
                domain=DOMAIN, path=DOCROOT, ssl=True)
    print("   created (OVH task queued).")

# 2. DNS: CNAME <sub> -> service (when the zone is hosted at OVH and missing)
step("Check DNS record %s in zone %s" % (SUB, ZONE))
try:
    ids = client.get("/domain/zone/%s/record" % ZONE, subDomain=SUB)
    if ids:
        print("   record already present, skipping.")
    else:
        target = SERVICE if SERVICE.endswith(".") else SERVICE + "."
        client.post("/domain/zone/%s/record" % ZONE,
                    fieldType="CNAME", subDomain=SUB, target=target)
        client.post("/domain/zone/%s/refresh" % ZONE)
        print("   CNAME %s -> %s created + zone refreshed." % (SUB, target))
except ovh.exceptions.ResourceNotFoundError:
    print("   zone %s not at OVH: add the CNAME at your registrar." % ZONE)

# 3. Let's Encrypt SSL for the hosting
step("Let's Encrypt SSL for the hosting")
try:
    client.post("/hosting/web/%s/ssl" % SERVICE, provider="LETS_ENCRYPT")
    print("   SSL creation requested.")
except ovh.exceptions.APIError as e:
    print("   SSL already present (%s), regenerating..." % e)
    try:
        client.post("/hosting/web/%s/ssl/regenerate" % SERVICE)
        print("   regeneration requested.")
    except ovh.exceptions.APIError as e2:
        print("   regeneration not triggered:", e2)

print("\nDone. OVH propagation ~15-30 min. Then verify with:")
print("  python scripts/verify_urls.py")
