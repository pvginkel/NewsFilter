import logging
import math
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from dataclasses_json import dataclass_json
from openai import OpenAI

from .config import STORE_PATH
from .scorer import ScoredArticle


@dataclass_json
@dataclass
class PostedStory:
    link: str
    title: str
    posted: datetime
    embedding: list[float]


@dataclass_json
@dataclass
class PostedStories:
    stories: list[PostedStory] = field(default_factory=list)


class Deduper:
    """Keeps one story from arriving twice.

    Several NOS feeds carry the same development from different angles, and
    the scorer sees one article at a time, so it cannot know it just sent the
    same news. Over a measured day, eight articles above the cutoff covered
    six stories: the petrol price rise arrived twice and the begrotingsakkoord
    arrived twice.
    """

    STATE_PATH = os.path.join(STORE_PATH, "posted.json")
    MODEL = "text-embedding-3-small"
    # 256 of the model's 1536 dimensions ranks stories just as well and keeps
    # the state file to a few kilobytes.
    DIMENSIONS = 256
    # Measured over 8515 pairs of real scored articles: every pair at or above
    # this was one story told twice, and the two the cutoff actually sent twice
    # sit at 0.787 (the petrol price) and 0.759 (the begrotingsakkoord). That
    # second one is close to the line, and it moves with the summary the model
    # happens to write, so this has less margin than it looks. Lowering it is
    # not free either: just below sit pairs that only look alike, the
    # Polarsteps tracking story against the Polarsteps data leak at 0.746. The
    # bias is deliberate -- a duplicate is an annoyance, a suppressed article
    # is news that never arrives.
    THRESHOLD = 0.75
    # Long enough to cover a story's follow-ups, short enough that a genuinely
    # new development in the same dossier is not swallowed.
    WINDOW = timedelta(hours=48)

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = OpenAI()
        self.embeddings: dict[str, list[float]] = {}
        self.posted = self._load()

    def duplicate_of(self, scored: ScoredArticle) -> PostedStory | None:
        """The recently posted story this one repeats, if there is one."""

        embedding = self._embedding(scored)
        if embedding is None:
            # Posting a duplicate beats dropping an article because the
            # embeddings API had a bad minute.
            return None

        cutoff = datetime.now(tz=UTC) - self.WINDOW
        best, best_similarity = None, self.THRESHOLD

        for story in self.posted.stories:
            if story.posted < cutoff:
                continue

            similarity = self._similarity(embedding, story.embedding)
            if similarity >= best_similarity:
                best, best_similarity = story, similarity

        if best:
            self.logger.info(
                'Suppressing "%s" as a repeat of "%s" (%.3f)',
                scored.article.title,
                best.title,
                best_similarity,
            )

        return best

    def remember(self, scored: ScoredArticle) -> None:
        """Record that this story went out, so its follow-ups do not."""

        embedding = self._embedding(scored)
        if embedding is None:
            return

        self.posted.stories.append(
            PostedStory(
                link=scored.article.link,
                title=scored.article.title,
                posted=datetime.now(tz=UTC),
                embedding=embedding,
            )
        )
        self._save()

    def _embedding(self, scored: ScoredArticle) -> list[float] | None:
        link = scored.article.link

        if link not in self.embeddings:
            try:
                response = self.client.embeddings.create(
                    model=self.MODEL,
                    dimensions=self.DIMENSIONS,
                    input=f"{scored.article.title}\n\n{scored.summary}",
                )
            except Exception:
                self.logger.exception("Failed to embed article")

                return None

            self.embeddings[link] = response.data[0].embedding

        return self.embeddings[link]

    def _similarity(self, left: list[float], right: list[float]) -> float:
        # Truncated embeddings are not necessarily unit length, so this is a
        # full cosine rather than a dot product.
        norm = math.sqrt(sum(x * x for x in left)) * math.sqrt(
            sum(y * y for y in right)
        )

        return sum(x * y for x, y in zip(left, right)) / norm if norm else 0.0

    def _load(self) -> PostedStories:
        if not os.path.exists(self.STATE_PATH):
            return PostedStories()

        try:
            with open(self.STATE_PATH, encoding="utf-8") as f:
                return PostedStories.from_json(f.read())
        except (OSError, ValueError, KeyError):
            # The file is a cache of what went out, not a record anything
            # depends on, so a damaged one is worth no more than a warning.
            self.logger.warning("Ignoring unreadable %s", self.STATE_PATH, exc_info=True)

            return PostedStories()

    def _save(self) -> None:
        cutoff = datetime.now(tz=UTC) - self.WINDOW
        self.posted.stories = [s for s in self.posted.stories if s.posted >= cutoff]

        os.makedirs(os.path.dirname(self.STATE_PATH), exist_ok=True)

        with open(self.STATE_PATH + "-tmp", "w", encoding="utf-8") as f:
            f.write(self.posted.to_json())

        os.replace(self.STATE_PATH + "-tmp", self.STATE_PATH)
