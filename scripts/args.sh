mkdir -p $(pwd)/tmp

NAME=newsfilter
ARGS="
    -e STORE_PATH=/app/store
    -e OPENAI_API_KEY=$OPENAI_API_KEY
    -e TWITTER_API_KEY=$TWITTER_API_KEY
    -v $(pwd)/tmp:/app/store
"
