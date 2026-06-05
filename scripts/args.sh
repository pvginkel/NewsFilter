mkdir -p $(pwd)/tmp

NAME=newsfilter
ARGS="
    --user 1000:1000
    -e STORE_PATH=/app/store
    -e OPENAI_API_KEY=$OPENAI_API_KEY
    -e TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
    -e TELEGRAM_CHAT_IDS=$TELEGRAM_CHAT_IDS
    -v $(pwd)/tmp:/app/store
"
