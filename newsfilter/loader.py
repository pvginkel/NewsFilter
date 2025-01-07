from dataclasses import dataclass
from datetime import datetime
from typing import Generator, Iterator, Optional
import feedparser
import time


@dataclass
class NewsArticle:
    link: str
    title: str
    published: datetime
    summary: str
    image_url: Optional[str]


class Loader:
    RSS_FEED = "https://feeds.nos.nl/nosnieuwsalgemeen"

    def load(self, since: Optional[datetime]) -> Iterator[NewsArticle]:
        feed = feedparser.parse(self.RSS_FEED)

        for entry in feed.entries:
            article = NewsArticle(
                link=entry.link,
                title=entry.title,
                published=datetime.fromtimestamp(time.mktime(entry.published_parsed)),
                summary=entry.summary,
                image_url=(
                    entry.enclosures[0].href if len(entry.enclosures) > 0 else None
                ),
            )

            # Only include new articles.

            if since:
                if article.published <= since.replace(tzinfo=None):
                    break

            yield article
