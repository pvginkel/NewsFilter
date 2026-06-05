# CLAUDE.md

## What this project does

NewsFilter pulls the NOS Algemeen Nieuws RSS feed, asks OpenAI to rate each new
article 1-10 against the criteria in `data/prompt.txt`, and posts the ones at
or above the cutoff (currently `7`, set in `App.CUTOFF`) to Telegram.

A single run is one-shot — there is no scheduler in the code. In production it
runs as a container that is launched periodically.

## Architecture

`App.run()` in `newsfilter/app.py` is the orchestrator:

1. `Loader.load(since)` — parses the RSS feed and yields `NewsArticle`s newer
   than `since`. The cursor (`last_processed`) is persisted to
   `$STORE_PATH/config.json` via the atomic `App._save()` (writes `-tmp`,
   rotates `-old`, then renames).
2. `Scorer.score(article)` — calls OpenAI with the prompt from `DATA_PATH/prompt.txt`
   and a JSON-schema response format. Output keys are Dutch
   (`nieuwswaardigheid`, `samenvatting`, `onderbouwing`) and are mapped onto
   `ScoredArticle`. Responses are cached on disk under
   `$STORE_PATH/cache/<MODEL>/<sha1>` keyed by `prompt + article`, so re-runs
   over the same content do not hit the API.
3. `ScoreLogger.log(scored)` — appends every scored article (regardless of
   whether it gets posted) to `$STORE_PATH/scorelog/YYYY-MM-DD.txt` as a YAML
   document. Logs older than 10 days are deleted on each call.
4. `Poster.post(scored)` — only invoked when `score >= CUTOFF`. Sends
   `summary + link` to every chat in `TELEGRAM_CHAT_IDS` via the thin
   `Telegram` client in `newsfilter/telegram.py`. When the article has an
   `image_url` (the NOS hero image, from the RSS `enclosure`) it is sent as a
   `sendPhoto` with the text as the caption — Telegram fetches the URL itself,
   so nothing is downloaded locally. Missing images and any `sendPhoto` failure
   fall back to a plain `sendMessage`.

## Environment variables

`newsfilter/__main__.py` calls `load_dotenv()` before importing the rest of
the package, so a `.env` in the working directory is picked up automatically.
Real environment variables win over `.env`. These must be set (via either
mechanism) before `App` is imported, since paths are read at class-definition
time:

- `OPENAI_API_KEY` — used by the `OpenAI` client.
- `TELEGRAM_BOT_TOKEN` — token of the Telegram bot used to post messages.
- `TELEGRAM_CHAT_IDS` — comma-separated list of chat IDs to post to (a single
  value works too; whitespace around entries is trimmed).
- `DATA_PATH` — directory containing `prompt.txt` (use `data` locally).
- `STORE_PATH` — writable directory for `config.json`, `cache/`, and
  `scorelog/`.

`App.SETTINGS_PATH` and `Scorer.CACHE_PATH` are computed at class-definition
time from `os.getenv("STORE_PATH")`, so importing the module without
`STORE_PATH` set will produce paths starting with `None/…` and fail later.

## Running and testing

Dependencies are managed by Poetry (`pyproject.toml` + `poetry.lock`). The
venv lives in `~/.cache/pypoetry/virtualenvs/` — do not create a `.venv/` at
the project root, because Poetry will silently adopt it instead of using the
out-of-project default.

- Local: `poetry run python -m newsfilter` after setting `OPENAI_API_KEY` /
  `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_IDS` (`DATA_PATH` and `STORE_PATH` come
  from `.env`). Entry point is `newsfilter/__main__.py`.
- Docker: `scripts/run.sh` builds the image and runs it with `tmp/` mounted as
  the store. The Dockerfile installs deps with Poetry into the system Python
  (`POETRY_VIRTUALENVS_CREATE=false`). The scripts read `OPENAI_API_KEY` /
  `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_IDS` from the host shell (see
  `scripts/args.sh`).
- Tests: `poetry run pytest`. The suite in `tests/test_score.py` calls the
  real OpenAI API and asserts that low-relevance articles score at or below
  `6`. The scorer's on-disk cache makes re-runs fast and cheap.

## Conventions

- Scoring criteria live in `data/prompt.txt`. The placeholder `%DATE%` is
  replaced at request time with today's date in Dutch (`Scorer.get_date()`).
- The model is set in `Scorer.MODEL`. For `o*` models, temperature is forced
  to `1`; otherwise `Scorer.TEMPERATURE` (`0.2`) is used.
- Cache invalidation is implicit: changing the prompt or switching models
  changes the cache key / directory, so old entries are simply ignored.

## Git workflow

This is a one-man shop, so keep it simple:

- Commit as you go — make small, self-contained commits as work progresses
  rather than batching everything into one big commit at the end.
- Work directly on `main`. No topic branches and no pull requests; just commit
  and push.

## Federated architecture model

We take part in a federated Architecture-as-Code model. The architecture for this repository is maintained in `docs/architecture/architecture.yaml`. Whenever a change is made in this repo that could impact an Enterprise Architecture / ArchiMate model modeling everything owned by this repo, nudge the user to spawn the `update-architecture` agent. The agent is incremental, so it's not a hard requirement that it runs on every change. Nudge a bit harder when significant changes are made (new managed host, new daemon, removed service, renamed external identity). When you are performing work unattended, feel free to invoke the agent yourself.

The tooling is installed on the operator's filesystem (not in this repo): the `/seed-architecture` skill (one-shot, authors the first artifact) and the `update-architecture` agent (permanent, incremental). Generated producers — those whose `docs/architecture/*.yaml` is a build output from a generator + annotation layer — use the `update-architecture-generated` agent instead, which edits the annotations and never the output. The producer manual at `~/.claude/architecture/producer-manual.md` is the authoritative vocabulary reference; the skill and agents read it from the operator's filesystem on startup.
