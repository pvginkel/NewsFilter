import json
import tempfile
from pprint import pprint
import tweepy
from .scorer import ScoredArticle
import os
import urllib.request
import os


class Poster:
    api: tweepy.API
    newapi: tweepy.Client

    API_KEY = os.getenv("TWITTER_API_KEY")
    TWEET_LENGTH = 280
    SHORT_URL_LENGTH = 23

    def __init__(self):
        self.api_key = json.loads(self.API_KEY)

        auth = tweepy.OAuth1UserHandler(
            self.api_key["api_key"],
            self.api_key["api_key_secret"],
            self.api_key["access_token"],
            self.api_key["access_token_secret"],
        )

        self.api = tweepy.API(auth)

        self.newapi = tweepy.Client(
            bearer_token=self.api_key["bearer_token"],
            access_token=self.api_key["access_token"],
            access_token_secret=self.api_key["access_token_secret"],
            consumer_key=self.api_key["api_key"],
            consumer_secret=self.api_key["api_key_secret"],
        )

    def post(self, article: ScoredArticle):
        return
        media_ids = None

        if False and article.article.image_url:
            with tempfile.NamedTemporaryFile() as tf:
                tf.close()

                urllib.request.urlretrieve(article.article.image_url, filename=tf.name)

                media = self.api.media_upload(tf.name)

                media_ids = [media.media_id]

        max_summary_length = self.TWEET_LENGTH - self.SHORT_URL_LENGTH - 5
        summary = article.summary
        if len(summary) > max_summary_length:
            summary = summary[: (max_summary_length - 3)] + "..."

        tweet = f"{summary} {article.article.link}"

        post_result = self.newapi.create_tweet(text=tweet, media_ids=media_ids)

        pprint(post_result)
