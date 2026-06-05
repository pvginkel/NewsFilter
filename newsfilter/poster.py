import logging
import os

import requests

from .scorer import ScoredArticle
from .telegram import Telegram

# Telegram limits captions (sendPhoto) to 1024 chars and messages
# (sendMessage) to 4096. The summary is already capped at ~250 chars by the
# scorer, so the caption limit is the only one we can realistically hit.
CAPTION_LENGTH = 1024


class Poster:
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    CHAT_IDS = os.getenv("TELEGRAM_CHAT_IDS")

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.telegram = Telegram(self.BOT_TOKEN)
        self.chat_ids = [
            chat_id.strip()
            for chat_id in (self.CHAT_IDS or "").split(",")
            if chat_id.strip()
        ]

    def post(self, article: ScoredArticle):
        text = f"{article.summary}\n\n{article.article.link}"
        image_url = article.article.image_url

        for chat_id in self.chat_ids:
            self._post_to_chat(chat_id, text, image_url)

    def _post_to_chat(self, chat_id, text, image_url):
        if image_url:
            try:
                self.telegram.send_photo(chat_id, image_url, text[:CAPTION_LENGTH])
                return
            except requests.RequestException:
                # The hero image is best-effort; if Telegram can't fetch it,
                # still post the article as a plain message.
                self.logger.warning(
                    "Failed to post photo to chat %s, falling back to text",
                    chat_id,
                    exc_info=True,
                )

        self.telegram.send_message(chat_id, text)
