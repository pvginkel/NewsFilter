import os
import datetime
import re
import yaml

from .scorer import ScoredArticle


class ScoreLogger:
    STORE_PATH = os.getenv("STORE_PATH")
    MAX_LOG_DAYS = 10

    def __init__(self):
        self.log_path = os.path.join(self.STORE_PATH, "scorelog")

        os.makedirs(self.log_path, exist_ok=True)

    def log(self, article: ScoredArticle) -> None:
        self._delete_old_logs()

        now = datetime.datetime.now().date()

        with open(
            os.path.join(
                self.log_path, f"{now.year:04}-{now.month:02}-{now.day:02}.txt"
            ),
            "a",
            encoding="utf-8",
        ) as f:
            f.write("---\n")
            f.write(
                yaml.dump(
                    {
                        "title": article.article.title,
                        "score": article.score,
                        "reason": article.reason,
                        "summary": article.summary,
                        "link": article.article.link,
                    },
                    allow_unicode=True,
                )
            )

    def _delete_old_logs(self) -> None:
        now = datetime.datetime.now().date()

        for name in os.listdir(self.log_path):
            match = re.search(r"^(\d+)-(\d+)-(\d+)\.txt$", name)
            if match:
                date = datetime.date(
                    int(match.group(1)), int(match.group(2)), int(match.group(3))
                )

                if now - date > datetime.timedelta(days=self.MAX_LOG_DAYS):
                    os.unlink(os.path.join(self.log_path, name))
