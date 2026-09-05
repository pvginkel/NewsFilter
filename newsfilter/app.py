import logging
import os
from dataclasses import dataclass
from datetime import datetime

from dataclasses_json import dataclass_json

from .config import STORE_PATH
from .dedupe import Deduper
from .loader import Loader, NewsArticle
from .poster import Poster
from .scorelogger import ScoreLogger
from .scorer import Scorer


@dataclass_json
@dataclass
class Settings:
    last_processed: datetime | None


class App:
    SETTINGS_PATH = os.path.join(STORE_PATH, "config.json")
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
        score_logger = ScoreLogger()
        deduper = Deduper()

        for article in new_news:
            self.logger.info("Scoring article %s", article.title)

            scored = scorer.score(article)

            # `Scorer.score` returns None when the model's response does not
            # parse. Everything below reads `scored`, so there is nothing left
            # to do with this article.
            if not scored:
                continue

            self.logger.info('Scored at %d because "%s"', scored.score, scored.reason)

            score_logger.log(scored)

            if scored.score >= self.CUTOFF and not deduper.duplicate_of(scored):
                self.logger.info("Publishing to Telegram")

                poster.post(scored)
                deduper.remember(scored)

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
            self.config.last_processed = max(a.published for a in articles)
            self._save()

        return articles
