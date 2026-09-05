import calendar
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import ClassVar

import feedparser


@dataclass
class NewsArticle:
    link: str
    title: str
    published: datetime
    summary: str
    image_url: str | None


class Loader:
    # "Algemeen" is not all of NOS: it is a general-mix feed, and on an average
    # day it carries incidents, foreign news and human interest without a single
    # Dutch policy or price item. The news worth scoring a 7 -- begrotingen,
    # belastingen, huren, de energierekening -- only appears in `politiek` and
    # `economie`, so those are read too. Feeds overlap; `load` dedupes on link.
    RSS_FEEDS: ClassVar[list[str]] = [
        "https://feeds.nos.nl/nosnieuwsalgemeen",
        "https://feeds.nos.nl/nosnieuwsbinnenland",
        "https://feeds.nos.nl/nosnieuwspolitiek",
        "https://feeds.nos.nl/nosnieuwseconomie",
    ]

    def load(self, since: datetime | None) -> Iterator[NewsArticle]:
        articles: dict[str, NewsArticle] = {}

        for url in self.RSS_FEEDS:
            for entry in feedparser.parse(url).entries:
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

                # Only include new articles. This filters rather than stopping
                # at the first old entry: that shortcut needs every feed to be
                # strictly newest-first, and one feed breaking that rule would
                # silently swallow the rest of it.

                # `since` comes back from config.json as an aware datetime, so it
                # compares directly against the aware `published` above.
                if since and article.published <= since:
                    continue

                articles.setdefault(article.link, article)

        # Merging feeds loses the per-feed ordering, so restore it: newest
        # first, the order a single feed came in and the order App posts in.
        yield from sorted(articles.values(), key=lambda a: a.published, reverse=True)
