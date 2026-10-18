from datetime import UTC, datetime
from types import SimpleNamespace

import httpx
import pytest
from openai import RateLimitError

from newsfilter import scorer
from newsfilter.loader import NewsArticle
from newsfilter.scorer import Scorer

CONTENT = '{"nieuwswaardigheid": 7, "samenvatting": "Samenvatting", "onderbouwing": "Onderbouwing"}'


class FakeClient:
    def __init__(self):
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))
        self.failing_tiers = set()
        self.tiers = []

    def create(self, service_tier, **kwargs):
        self.tiers.append(service_tier)

        if service_tier in self.failing_tiers:
            request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")

            raise RateLimitError(
                "Resource Unavailable",
                response=httpx.Response(429, request=request),
                body=None,
            )

        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=CONTENT))])


@pytest.fixture
def client(monkeypatch, tmp_path):
    client = FakeClient()
    monkeypatch.setattr(scorer, "OpenAI", lambda **kwargs: client)
    monkeypatch.setattr(Scorer, "CACHE_PATH", str(tmp_path))

    return client


def article():
    return NewsArticle(
        link="https://nos.nl/artikel",
        title="Benzineprijs breekt alle records",
        published=datetime.now(tz=UTC),
        summary="",
        image_url=None,
    )


def test_scores_on_the_flex_tier(client):
    scored = Scorer().score(article())

    assert scored.score == 7
    assert client.tiers == ["flex"]


def test_falls_back_to_the_standard_tier_when_flex_has_no_capacity(client):
    client.failing_tiers = {"flex"}

    scored = Scorer().score(article())

    assert scored.score == 7
    assert client.tiers == ["flex", "auto"]


def test_a_429_on_the_standard_tier_too_propagates(client):
    # Exhausted credits fail on every tier; the run must still fail loudly.
    client.failing_tiers = {"flex", "auto"}

    with pytest.raises(RateLimitError):
        Scorer().score(article())
