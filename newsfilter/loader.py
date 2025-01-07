from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import feedparser
import time


@dataclass
class NewsArticle:
    link: str
    title: str
    published: datetime
    summary: str


class Loader:
    RSS_FEED = "https://feeds.nos.nl/nosnieuwsalgemeen"

    def load(self, since: Optional[datetime]) -> list[NewsArticle]:
        feed = feedparser.parse(self.RSS_FEED)

        for entry in feed.entries:
            article = NewsArticle(
                link=entry.link,
                title=entry.title,
                published=datetime.fromtimestamp(time.mktime(entry.published_parsed)),
                summary=entry.summary,
            )

            # Only include new articles.

            if since:
                if article.published <= since.replace(tzinfo=None):
                    break

            yield article
