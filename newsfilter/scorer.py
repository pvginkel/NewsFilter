from dataclasses import dataclass
import logging
from typing import Optional
from openai import OpenAI
import os
from .loader import NewsArticle
import json
import re
import hashlib
from dataclasses_json import dataclass_json
from .utils import html_to_text


@dataclass_json
@dataclass
class ScoredArticle:
    article: NewsArticle
    summary: str
    score: int
    reason: str


class Scorer:
    MODEL = "gpt-4o-mini"
    SUMMARY_LENGTH = 2000
    DATA_PATH = os.getenv("DATA_PATH")
    CACHE_PATH = os.getenv("CACHE_PATH")
    # See https://community.openai.com/t/cheat-sheet-mastering-temperature-and-top-p-in-chatgpt-api/172683
    TEMPERATURE = 0.2

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = OpenAI()

        with open(os.path.join(self.DATA_PATH, "prompt.txt")) as f:
            self.prompt = f.read()

    def score(self, article: NewsArticle) -> Optional[ScoredArticle]:
        summary = html_to_text(article.summary)
        if len(summary) > self.SUMMARY_LENGTH:
            summary = summary[: (self.SUMMARY_LENGTH - 3)] + "..."

        if self.CACHE_PATH:
            cache_key = hashlib.sha1(f"{self.prompt}:::{article}".encode()).hexdigest()
            cache_file = os.path.join(self.CACHE_PATH, cache_key)
            if os.path.exists(cache_file):
                with open(cache_file) as f:
                    scored = ScoredArticle.from_json(f.read())
                    scored.article = article

                    return scored
        else:
            cache_file = None

        response = self.client.chat.completions.create(
            model=self.MODEL,
            temperature=self.TEMPERATURE,
            messages=[
                {
                    "role": "developer",
                    "content": self.prompt,
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
                                "description": "Samenvatting van het nieuwsartikel van maximaal 250 karakters",
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
        except:
            self.logger.exception("Failed to score article")

            scored = None

        if cache_file and scored:
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)

            with open(cache_file, "w") as f:
                f.write(scored.to_json())

        return scored
