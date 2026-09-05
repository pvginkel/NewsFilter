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
    # Just the general feed. Any single fetch of it can look narrow -- all
    # incidents and foreign news, not a Dutch policy or price story in sight --
    # but a feed only holds ~20 items while the job runs hourly, so what counts
    # is the ~40 articles a day passing through it. Eleven days of production
    # scorelog show every policy and price story in there: box 3, de gasprijs,
    # de huren, de benzineprijs, het begrotingsakkoord, Prinsjesdag. Reading
    # binnenland, politiek and economie alongside it re-reads those same stories
    # under different headlines at three times the scoring calls.
    #
    # Do not re-decide this from one fetch of the feed -- that snapshot is what
    # made the case for six feeds look obvious, and it was wrong. `load` still
    # merges and dedupes on link, so adding one back is a one-line change.
    RSS_FEEDS: ClassVar[list[str]] = [
        "https://feeds.nos.nl/nosnieuwsalgemeen",
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
