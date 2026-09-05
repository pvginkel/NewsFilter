import datetime
from pathlib import Path

import pytest
import yaml

from newsfilter.loader import NewsArticle
from newsfilter.scorer import Scorer

CASES = yaml.safe_load(
    (Path(__file__).parent / "score-cases.yaml").read_text(encoding="utf-8")
)


@pytest.fixture(scope="module")
def scorer():
    return Scorer()


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_score(case, scorer):
    # `published=now` puts every run past the scorer's on-disk cache, so a
    # regression cannot hide behind a hit. That makes this suite a live call
    # per case -- slow and not free, which is the price of testing the thing
    # that actually varies.
    article = NewsArticle(
        link="",
        title=case["title"],
        published=datetime.datetime.now(tz=datetime.UTC),
        summary=case["summary"],
        image_url="",
    )

    scored = scorer.score(article)

    assert scored, "the model's response did not parse"
    assert case["min"] <= scored.score <= case["max"], (
        f"scored {scored.score}, wanted {case['min']}-{case['max']}\n\n"
        f"why this case exists: {case['why']}\n\n"
        f"the model's reasoning: {scored.reason}"
    )
