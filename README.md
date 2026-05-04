# NewsFilter

Filters articles from the [NOS Algemeen Nieuws](https://feeds.nos.nl/nosnieuwsalgemeen)
RSS feed using OpenAI and posts the ones that pass a relevance threshold to Twitter/X.

For each new article, the model is asked to rate how relevant the news is on a
scale of 1-10 according to the criteria in [`data/prompt.txt`](data/prompt.txt).
Articles scoring at or above the cutoff (currently `7`) are posted as a tweet
with a short summary and a link to the original article. Every scored article
is also written to a daily YAML log under `$STORE_PATH/scorelog/`.

## Requirements

- Python 3.11+
- [Poetry](https://python-poetry.org/) for dependency management
- An OpenAI API key (the scorer uses the `o4-mini` model)
- A Twitter/X developer app with OAuth 1.0a user-context credentials (only
  required if you actually want to post tweets)

## Configuration

NewsFilter is configured entirely through environment variables.

| Variable          | Required | Purpose                                                                      |
|-------------------|----------|------------------------------------------------------------------------------|
| `OPENAI_API_KEY`  | yes      | Used by the OpenAI client to score articles.                                 |
| `TWITTER_API_KEY` | yes      | A JSON blob with the Twitter credentials (see below).                        |
| `DATA_PATH`       | yes      | Directory containing `prompt.txt`. Use `data` when running from the repo.    |
| `STORE_PATH`      | yes      | Writable directory for `config.json`, the score log, and the response cache. |

`TWITTER_API_KEY` must be a JSON object with the following keys:

```json
{
  "api_key": "...",
  "api_key_secret": "...",
  "access_token": "...",
  "access_token_secret": "...",
  "bearer_token": "..."
}
```

On startup the app loads a `.env` file from the working directory via
`python-dotenv`. The repo ships with one that sets `DATA_PATH=data` and
`STORE_PATH=store`, so for local runs you only need to export
`OPENAI_API_KEY` and `TWITTER_API_KEY` yourself. Real environment variables
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
export TWITTER_API_KEY='{"api_key":"...","api_key_secret":"...","access_token":"...","access_token_secret":"...","bearer_token":"..."}'

poetry run python -m newsfilter
```

(`DATA_PATH` and `STORE_PATH` come from the bundled `.env`.)

Each invocation processes any articles published after the last run (tracked in
`$STORE_PATH/config.json`), so on the first run it will score everything that
is currently in the feed.

A VS Code launch configuration named **Run NewsFilter** is also provided in
`.vscode/launch.json`.

### Running the tests

The test suite calls the real OpenAI API to verify scoring behaviour, so it
needs the same `OPENAI_API_KEY`, `DATA_PATH`, and `STORE_PATH` environment
variables to be set.

```sh
poetry run pytest
```

### Running with Docker

The included scripts wrap `docker build` / `docker run` and mount `tmp/` as the
store directory. Set `OPENAI_API_KEY` and `TWITTER_API_KEY` in your shell
first, then:

```sh
./scripts/run.sh    # build, run in the background, and tail the logs
./scripts/stop.sh   # stop the running container
./scripts/push.sh   # build and push to registry:5000/newsfilter
```

## Project layout

```
newsfilter/        Application package (entry point: python -m newsfilter)
  app.py           Orchestrates the run: load → score → log → post
  loader.py        Reads the NOS RSS feed
  scorer.py        Calls OpenAI and parses the JSON response
  scorelogger.py   Appends every scored article to a daily YAML log
  poster.py        Posts qualifying articles to Twitter/X
data/prompt.txt    System prompt used by the scorer
pyproject.toml     Poetry project + dependency definitions
scripts/           Docker helper scripts (build, run, stop, push)
tests/             Pytest suite (hits the live OpenAI API)
```
