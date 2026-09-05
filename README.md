# NewsFilter

Filters articles from four NOS RSS feeds ([Algemeen Nieuws](https://feeds.nos.nl/nosnieuwsalgemeen),
[Binnenland](https://feeds.nos.nl/nosnieuwsbinnenland), [Politiek](https://feeds.nos.nl/nosnieuwspolitiek)
and [Economie](https://feeds.nos.nl/nosnieuwseconomie)) using OpenAI and posts the ones that pass
a relevance threshold to Telegram.

For each new article, the model is asked to rate how relevant the news is on a
scale of 1-10 according to the criteria in [`data/prompt.txt`](data/prompt.txt).
Articles scoring at or above the cutoff (currently `7`) are posted to one or more
Telegram chats with a short summary and a link to the original article. When the
article includes a hero image it is sent as a photo with the summary as the
caption; otherwise a plain text message is sent. Every scored article is also
written to a daily YAML log under `$STORE_PATH/scorelog/`.

## Requirements

- Python 3.11+
- [Poetry](https://python-poetry.org/) for dependency management
- An OpenAI API key (the model used is set in `Scorer.MODEL`)
- A Telegram bot token and one or more chat IDs to post to (only required if you
  actually want to post messages)

## Configuration

NewsFilter is configured entirely through environment variables.

| Variable             | Required     | Purpose                                                                                                                             |
|----------------------|--------------|-------------------------------------------------------------------------------------------------------------------------------------|
| `OPENAI_API_KEY`     | yes          | Used by the OpenAI client to score articles.                                                                                        |
| `TELEGRAM_BOT_TOKEN` | only to post | The token of the Telegram bot used to post messages.                                                                                |
| `TELEGRAM_CHAT_IDS`  | only to post | Comma-separated list of chat IDs to post qualifying articles to. With none set, the app scores and logs articles but posts nothing. |
| `DATA_PATH`          | no           | Directory containing `prompt.txt`. Defaults to `data`.                                                                              |
| `STORE_PATH`         | no           | Writable directory for `config.json`, the score log, and the response cache. Defaults to `store`.                                   |

`TELEGRAM_CHAT_IDS` is a comma-separated list, so a single value works too:

```sh
export TELEGRAM_CHAT_IDS='123456789'
export TELEGRAM_CHAT_IDS='123456789,-1009876543210'   # multiple chats
```

On startup the app loads a `.env` file from the working directory via
`python-dotenv`, if one is present. The repo does not ship a `.env` — `DATA_PATH`
and `STORE_PATH` already default to `data` and `store`, so you only need a
`.env` (or exported variables) for `OPENAI_API_KEY`, and `TELEGRAM_BOT_TOKEN` /
`TELEGRAM_CHAT_IDS` if you want the app to post. Real environment variables
take precedence over `.env`.

## Running locally

Install dependencies with Poetry. By default Poetry creates the virtual
environment outside the project tree (under `~/.cache/pypoetry/virtualenvs/`):

```sh
poetry install
```

Export the required secrets and run the module:

```sh
export OPENAI_API_KEY='sk-...'
export TELEGRAM_BOT_TOKEN='123456:ABC-...'
export TELEGRAM_CHAT_IDS='123456789,-1009876543210'

poetry run python -m newsfilter
```

In the KubeCoder environment Poetry lives in a toolchain sidecar rather than
alongside the checkout, so the commands take a `cexec python` prefix:

```sh
cexec python poetry install                        # or: kc project setup
cexec python poetry run python -m newsfilter
```

`DATA_PATH` and `STORE_PATH` default to `data` and `store` and do not need to
be set for a plain checkout.

Each invocation processes any articles published after the last run (tracked in
`$STORE_PATH/config.json`), so on the first run it will score everything that
is currently in the feeds.

A VS Code launch configuration named **Run NewsFilter** is also provided in
`.vscode/launch.json`.

### Running the tests

The test suite calls the real OpenAI API to verify scoring behaviour, so it
needs `OPENAI_API_KEY` set. The scorer caches responses on disk under
`$STORE_PATH/cache`, so re-runs are cheap — but the first run after a prompt
or model change is not.

```sh
poetry run pytest
```

or, in the KubeCoder environment:

```sh
kc project test
```

### Building the container image

Images are built with `kaniko`, from the repository root:

```sh
kaniko --no-push                                   # build only, to prove the Dockerfile
kaniko --destination registry:5000/newsfilter:dev  # build and push a scratch image
```

Use the `:dev` tag for local pushes — Jenkins owns
`registry:5000/newsfilter:latest` and the numbered tags, and a local build
must not clobber them. Jenkins itself builds via `helmCharts.kaniko(...)` in
the `Jenkinsfile`.

### Linting

```sh
kc project lint
```

Runs Ruff over the whole tree and validates `docs/architecture/*.yaml`
against the architecture validation service — the same check the
`AaC/NewsFilter` pipeline runs.

## Project layout

```
newsfilter/        Application package (entry point: python -m newsfilter)
  app.py           Orchestrates the run: load → score → log → post
  loader.py        Reads and merges the four NOS RSS feeds
  scorer.py        Calls OpenAI and parses the JSON response
  scorelogger.py   Appends every scored article to a daily YAML log
  poster.py        Posts qualifying articles to Telegram
  telegram.py      Thin Telegram Bot API client (sendMessage / sendPhoto)
  config.py        DATA_PATH / STORE_PATH defaults
data/prompt.txt    System prompt used by the scorer
pyproject.toml     Poetry project + dependency definitions
scripts/           arch-validate.py, run by Jenkinsfile.architecture
tests/             Pytest suite (hits the live OpenAI API)
```
