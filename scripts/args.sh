mkdir -p $(pwd)/tmp

NAME=newsfilter
ARGS="
    -e SETTINGS_PATH=/app/store/config.json
    -e CACHE_PATH=/app/store/cache
    -e OPENAI_API_KEY=$OPENAI_API_KEY
    -e TWITTER_API_KEY=$TWITTER_API_KEY
    -v $(pwd)/tmp:/app/store
"
