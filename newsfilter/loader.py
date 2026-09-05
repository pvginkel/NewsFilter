import calendar
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime

import feedparser


@dataclass
class NewsArticle:
    link: str
    title: str
    published: datetime
    summary: str
    image_url: str | None


class Loader:
    RSS_FEED = "https://feeds.nos.nl/nosnieuwsalgemeen"

    def load(self, since: datetime | None) -> Iterator[NewsArticle]:
        feed = feedparser.parse(self.RSS_FEED)

        for entry in feed.entries:
            article = NewsArticle(
                link=entry.link,
                title=entry.title,
                published=datetime.fromtimestamp(
                    calendar.timegm(entry.published_parsed), tz=UTC
                ),
                summary=entry.summary,
                image_url=(
                    entry.enclosures[0].href if len(entry.enclosures) > 0 else None
                ),
            )

            # Only include new articles.

            # `since` comes back from config.json as an aware datetime, so it
            # compares directly against the aware `published` above.
            if since and article.published <= since:
                break

            yield article
