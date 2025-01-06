import os
from typing import Optional
from openai import OpenAI
import feedparser
from pprint import pprint
from dataclasses import dataclass
from datetime import datetime
import time
from dataclasses_json import dataclass_json
import re


@dataclass_json
@dataclass
class Settings:
    last_processed: Optional[datetime]


@dataclass
class NewsArticle:
    link: str
    title: str
    published: datetime
    summary: str


class App:
    SETTINGS_PATH = os.getenv("SETTINGS_PATH")
    DATA_PATH = os.getenv("DATA_PATH")
    RSS_FEED = "https://feeds.nos.nl/nosnieuwsalgemeen"
    CUTOFF = 7
    MODEL = "gpt-4o-mini"
    SUMMARY_LENGTH = 1000

    def __init__(self):
        self.client = OpenAI()

        if os.path.exists(self.SETTINGS_PATH):
            with open(self.SETTINGS_PATH) as f:
                self.config = Settings.from_json(f.read())
        else:
            self.config = Settings(last_processed=None)

        with open(os.path.join(self.DATA_PATH, "prompt.txt")) as f:
            self.prompt = self._clean_prompt(f.read())

    def run(self):
        new_news = self._get_new_news()
        forward = []

        for article in new_news:
            processed = self._process(article)
            return

    def _save(self):
        os.makedirs(os.path.dirname(self.SETTINGS_PATH), exist_ok=True)

        with open(self.SETTINGS_PATH + "-tmp", "w") as f:
            f.write(self.config.to_json())

        if os.path.exists(self.SETTINGS_PATH + "-old"):
            os.unlink(self.SETTINGS_PATH + "-old")
        if os.path.exists(self.SETTINGS_PATH):
            os.rename(self.SETTINGS_PATH, self.SETTINGS_PATH + "-old")
        os.rename(self.SETTINGS_PATH + "-tmp", self.SETTINGS_PATH)

    def _get_new_news(self):
        articles = []

        feed = feedparser.parse(self.RSS_FEED)

        for entry in feed.entries:
            article = NewsArticle(
                link=entry.link,
                title=entry.title,
                published=datetime.fromtimestamp(time.mktime(entry.published_parsed)),
                summary=entry.summary,
            )

            # Only include new articles.

            if self.config.last_processed:
                if article.published <= self.config.last_processed.replace(tzinfo=None):
                    break

            articles.append(article)

        if len(articles) > 0:
            self.config.last_processed = articles[0].published
            # self._save()

        return articles

    def _process(self, article: NewsArticle) -> NewsArticle:
        summary = (
            article.summary[: (self.SUMMARY_LENGTH - 3)] + "..."
            if len(article.summary) > self.SUMMARY_LENGTH
            else article.summary
        )

        response = self.client.chat.completions.create(
            model=self.MODEL,
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
                                "description": "Samenvatting van het nieuwsartikel",
                                "type": "string",
                            },
                            "additionalProperties": False,
                        },
                    },
                },
            },
        )

        print(response.choices[0].message.content)

    def _clean_prompt(self, prompt):
        result = []

        for line in re.split(r"\r?\n\r?\n", prompt):
            result.append(re.sub(r"\s+", " ", line).strip())

        return "\n\n".join(result)
