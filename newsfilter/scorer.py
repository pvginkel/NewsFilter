import datetime
import hashlib
import json
import logging
import os
from dataclasses import dataclass
from typing import ClassVar

from dataclasses_json import dataclass_json
from openai import OpenAI

from .config import DATA_PATH, STORE_PATH
from .loader import NewsArticle
from .utils import html_to_text


@dataclass_json
@dataclass
class ScoredArticle:
    article: NewsArticle
    summary: str
    score: int
    reason: str


class Scorer:
    MODEL = "gpt-5.4-mini"
    SUMMARY_LENGTH = 2000
    CACHE_PATH = os.path.join(STORE_PATH, "cache", MODEL)
    # See https://community.openai.com/t/cheat-sheet-mastering-temperature-and-top-p-in-chatgpt-api/172683
    TEMPERATURE = 0.2
    MONTHS: ClassVar[list[str]] = [
        "januari",
        "februari",
        "maart",
        "april",
        "mei",
        "juni",
        "juli",
        "augustus",
        "september",
        "oktober",
        "november",
        "december",
    ]

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = OpenAI()

        with open(os.path.join(DATA_PATH, "prompt.txt"), encoding="utf-8") as f:
            self.prompt = f.read()

    def score(self, article: NewsArticle) -> ScoredArticle | None:
        summary = html_to_text(article.summary)
        if len(summary) > self.SUMMARY_LENGTH:
            summary = summary[: (self.SUMMARY_LENGTH - 3)] + "..."

        if self.CACHE_PATH:
            cache_key = hashlib.sha1(f"{self.prompt}:::{article}".encode()).hexdigest()
            cache_file = os.path.join(self.CACHE_PATH, cache_key)
            if os.path.exists(cache_file):
                with open(cache_file, encoding="utf-8") as f:
                    scored = ScoredArticle.from_json(f.read())
                    scored.article = article

                    return scored
        else:
            cache_file = None

        temperature = 1 if self.MODEL.startswith("o") else self.TEMPERATURE

        response = self.client.chat.completions.create(
            model=self.MODEL,
            temperature=temperature,
            messages=[
                {
                    "role": "developer",
                    "content": self.prompt.replace("%DATE%", self.get_date()),
                },
                {
                    "role": "user",
                    "content": f"{article.title}\n\n{summary}",
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "news_schema",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "nieuwswaardigheid": {
                                "description": "Interesse niveau van het artikel",
                                "type": "number",
                            },
                            "samenvatting": {
                                "description": "Samenvatting van het nieuwsartikel van maximaal 400 karakters",
                                "type": "string",
                            },
                            "onderbouwing": {
                                "description": "Onderbouwing van de gegeven score",
                                "type": "string",
                            },
                            "additionalProperties": False,
                        },
                    },
                },
            },
        )

        try:
            obj = json.loads(response.choices[0].message.content)

            scored = ScoredArticle(
                article=article,
                summary=obj["samenvatting"],
                score=int(obj["nieuwswaardigheid"]),
                reason=obj["onderbouwing"],
            )
        except Exception:
            self.logger.exception("Failed to score article")

            scored = None

        if cache_file and scored:
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)

            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(scored.to_json())

        return scored

    def get_date(self):
        date = datetime.datetime.now(tz=datetime.UTC).date()
        month = self.MONTHS[date.month - 1]

        return f"{date.day} {month} {date.year}"
