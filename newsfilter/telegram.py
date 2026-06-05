import logging

import requests

log = logging.getLogger(__name__)


class Telegram:
    """The slice of the Telegram Bot API used to post an article to a chat."""

    def __init__(self, token):
        self.base = f"https://api.telegram.org/bot{token}"

    def send_message(self, chat_id, text):
        """Send a plain text message to a chat."""
        response = requests.post(
            f"{self.base}/sendMessage",
            data={"chat_id": chat_id, "text": text},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["result"]["message_id"]

    def send_photo(self, chat_id, photo, caption):
        """Send a photo (referenced by URL) with a caption to a chat. Telegram
        fetches the URL itself, so no local download is needed."""
        response = requests.post(
            f"{self.base}/sendPhoto",
            data={"chat_id": chat_id, "photo": photo, "caption": caption},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["result"]["message_id"]
