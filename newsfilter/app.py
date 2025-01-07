import logging
import os
from typing import Optional
from pprint import pprint
from dataclasses import dataclass
from datetime import datetime
from dataclasses_json import dataclass_json
from .poster import Poster
from .scorer import Scorer
from .loader import Loader, NewsArticle


@dataclass_json
@dataclass
class Settings:
    last_processed: Optional[datetime]


class App:
    SETTINGS_PATH = os.getenv("SETTINGS_PATH")
    CUTOFF = 7

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        if os.path.exists(self.SETTINGS_PATH):
            with open(self.SETTINGS_PATH) as f:
                self.config = Settings.from_json(f.read())
        else:
            self.config = Settings(last_processed=None)

    def run(self):
        self.logger.info("Getting new news")

        new_news = self._get_new_news()

        scorer = Scorer()
        poster = Poster()

        for article in new_news:
            self.logger.info("Scoring article %s", article.title)

            scored = scorer.score(article)

            self.logger.info('Scored at %d because "%s"', scored.score, scored.reason)

            if scored and scored.score >= self.CUTOFF:
                self.logger.info("Publishing as tweet")

                poster.post(scored)
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

    def _get_new_news(self) -> list[NewsArticle]:
        articles = list(Loader().load(self.config.last_processed))

        if len(articles) > 0:
            self.config.last_processed = articles[0].published
            # self._save()

        return articles
