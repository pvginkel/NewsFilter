from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from newsfilter import dedupe
from newsfilter.dedupe import Deduper
from newsfilter.loader import NewsArticle
from newsfilter.scorer import ScoredArticle

# Cosine 0.9 between the two petrol stories, 0.0 against the unrelated one.
VECTORS = {
    "Benzineprijs breekt alle records": [1.0, 0.0, 0.0],
    "Aanbieders verhogen de benzineprijs": [0.9, 0.436, 0.0],
    "Serval ontsnapt in Tilburg": [0.0, 1.0, 0.0],
}


class FakeClient:
    def __init__(self):
        self.embeddings = SimpleNamespace(create=self.create)
        self.fail = False

    def create(self, model, dimensions, input):
        if self.fail:
            raise RuntimeError("embeddings are having a bad minute")

        title = input.split("\n")[0]

        return SimpleNamespace(data=[SimpleNamespace(embedding=VECTORS[title])])


@pytest.fixture
def client(monkeypatch, tmp_path):
    client = FakeClient()
    monkeypatch.setattr(dedupe, "OpenAI", lambda: client)
    monkeypatch.setattr(Deduper, "STATE_PATH", str(tmp_path / "posted.json"))

    return client


def scored(title):
    article = NewsArticle(
        link=f"https://nos.nl/{title}",
        title=title,
        published=datetime.now(tz=UTC),
        summary="",
        image_url=None,
    )

    return ScoredArticle(article=article, summary="", score=7, reason="")


def test_lets_an_unrelated_story_through(client):
    deduper = Deduper()
    deduper.remember(scored("Benzineprijs breekt alle records"))

    assert deduper.duplicate_of(scored("Serval ontsnapt in Tilburg")) is None


def test_suppresses_the_same_story_told_twice(client):
    deduper = Deduper()
    deduper.remember(scored("Benzineprijs breekt alle records"))

    duplicate = deduper.duplicate_of(scored("Aanbieders verhogen de benzineprijs"))

    assert duplicate is not None
    assert duplicate.title == "Benzineprijs breekt alle records"


def test_remembers_across_runs(client):
    # Every run is a fresh process, so suppression only works if what went out
    # is on disk rather than in memory.
    Deduper().remember(scored("Benzineprijs breekt alle records"))

    assert Deduper().duplicate_of(scored("Aanbieders verhogen de benzineprijs"))


def test_forgets_stories_older_than_the_window(client):
    deduper = Deduper()
    deduper.remember(scored("Benzineprijs breekt alle records"))
    deduper.posted.stories[0].posted = datetime.now(tz=UTC) - timedelta(hours=49)

    assert deduper.duplicate_of(scored("Aanbieders verhogen de benzineprijs")) is None


def test_prunes_the_window_when_saving(client):
    deduper = Deduper()
    deduper.remember(scored("Benzineprijs breekt alle records"))
    deduper.posted.stories[0].posted = datetime.now(tz=UTC) - timedelta(hours=49)
    deduper.remember(scored("Serval ontsnapt in Tilburg"))

    assert [s.title for s in Deduper().posted.stories] == ["Serval ontsnapt in Tilburg"]


def test_posts_the_article_when_embedding_fails(client):
    # A duplicate is an annoyance; an article dropped because the embeddings
    # API had a bad minute is news that never arrives.
    deduper = Deduper()
    deduper.remember(scored("Benzineprijs breekt alle records"))
    client.fail = True
    deduper.embeddings.clear()

    assert deduper.duplicate_of(scored("Aanbieders verhogen de benzineprijs")) is None


def test_starts_clean_when_the_state_file_is_damaged(client, tmp_path):
    (tmp_path / "posted.json").write_text("{not json", encoding="utf-8")

    assert Deduper().posted.stories == []
