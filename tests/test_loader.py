import calendar
from datetime import UTC, datetime
from types import SimpleNamespace

import feedparser

from newsfilter.loader import Loader


def entry(link, title, published):
    return SimpleNamespace(
        link=link,
        title=title,
        published_parsed=published.utctimetuple(),
        summary=f"<p>{title}</p>",
        enclosures=[],
    )


def at(day, hour):
    return datetime(2026, 9, day, hour, tzinfo=UTC)


FEEDS = {
    "https://feeds.nos.nl/nosnieuwsalgemeen": [
        entry("/l/1", "nieuwste", at(5, 12)),
        entry("/l/2", "gedeeld", at(5, 10)),
        entry("/l/3", "oudste", at(4, 9)),
    ],
    # Same story, carried by two feeds, and one the first feed does not have.
    "https://feeds.nos.nl/nosnieuwspolitiek": [
        entry("/l/2", "gedeeld", at(5, 10)),
        entry("/l/4", "alleen politiek", at(5, 11)),
    ],
}


def fake_parse(url):
    return SimpleNamespace(entries=FEEDS.get(url, []))


def load(monkeypatch, since, feeds=tuple(FEEDS)):
    monkeypatch.setattr(feedparser, "parse", fake_parse)
    monkeypatch.setattr(Loader, "RSS_FEEDS", list(feeds))

    return list(Loader().load(since))


def test_merges_feeds_without_duplicating(monkeypatch):
    articles = load(monkeypatch, None)

    assert [a.link for a in articles] == ["/l/1", "/l/4", "/l/2", "/l/3"]


def test_orders_newest_first_across_feeds(monkeypatch):
    # App takes the cursor from the newest article and posts in this order, so
    # merging feeds must not leave them grouped per feed.
    articles = load(monkeypatch, None)

    assert all(
        articles[i].published >= articles[i + 1].published
        for i in range(len(articles) - 1)
    )


def test_skips_articles_at_or_before_the_cursor(monkeypatch):
    articles = load(monkeypatch, at(5, 10))

    assert [a.link for a in articles] == ["/l/1", "/l/4"]


def test_converts_the_feed_timestamp_as_utc(monkeypatch):
    article = load(monkeypatch, None)[0]

    assert article.published == at(5, 12)
    assert calendar.timegm(at(5, 12).utctimetuple()) == article.published.timestamp()
