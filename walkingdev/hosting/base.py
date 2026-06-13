"""AudioHosting: publish the MP3 and the RSS feed at a public URL the podcast
app can reach. ``local`` (default) writes to a folder; ``ftp`` pushes to classic
web hosting over FTPS/SFTP; the S3 backend covers OVH, R2, Scaleway, MinIO, AWS.
"""
from abc import ABC, abstractmethod


class AudioHosting(ABC):
    @abstractmethod
    def publish(self, mp3_path: str, date: str) -> str:
        """Upload the episode MP3, return its public URL.

        The episode is stored under ``episodes/<date>.mp3`` relative to the feed
        location so the feed and the files always agree.
        """

    @abstractmethod
    def feed_url(self) -> str:
        """Public URL of the RSS feed to add to a podcast app."""

    @abstractmethod
    def put_feed(self, xml: bytes) -> None:
        """Store/refresh the RSS feed (feed.xml) at the public location."""

    @abstractmethod
    def put_asset(self, name: str, data: bytes, content_type: str) -> str:
        """Store an arbitrary asset (e.g. cover.jpg) next to the feed; return URL."""
