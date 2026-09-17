from dataclasses import dataclass


@dataclass
class Video:
    id: str
    title: str
    channel: str = ""
    duration: str = ""
    thumbnail_url: str = ""

    @property
    def url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.id}"
