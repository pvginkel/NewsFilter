# CLAUDE.md

## What this project does

NewsFilter pulls the NOS Algemeen Nieuws RSS feed, asks OpenAI to rate each
new article 1-10 against the criteria in `data/prompt.txt`, and posts the
ones at or above the cutoff (currently `7`, set in `App.CUTOFF`) to Telegram,
suppressing duplicates of a story that already went out.

A single run is one-shot — there is no scheduler in the code. In production it
runs as a container that is launched periodically.

## Architecture

`App.run()` in `newsfilter/app.py` is the orchestrator:

1. `Loader.load(since)` — parses the feeds in `Loader.RSS_FEEDS`, which is
   just NOS Algemeen Nieuws, and yields `NewsArticle`s newer than `since`,
   newest first. More than one feed can be listed: they are merged on the
   article `link`, keeping the first occurrence, so a story two feeds both
   carry is still scored once. The cursor
   (`last_processed`) is persisted to `$STORE_PATH/config.json` via the
   atomic `App._save()` (writes `-tmp`, rotates `-old`, then renames).
2. `Scorer.score(article)` — calls OpenAI with the prompt from `DATA_PATH/prompt.txt`
   and a JSON-schema response format. Output keys are Dutch
   (`nieuwswaardigheid`, `samenvatting`, `onderbouwing`) and are mapped onto
   `ScoredArticle`. Responses are cached on disk under
   `$STORE_PATH/cache/<MODEL>/<sha1>` keyed by `prompt + article`, so re-runs
   over the same content do not hit the API.
3. `ScoreLogger.log(scored)` — appends every scored article (regardless of
   whether it gets posted) to `$STORE_PATH/scorelog/YYYY-MM-DD.txt` as a YAML
   document. Logs older than 10 days are deleted on each call.
4. `Deduper.duplicate_of(scored)` — for any article at or above `CUTOFF`,
   checks whether it is the same story as one already posted in the last 48
   hours, by embedding title + summary and comparing cosine similarity
   against everything `Deduper.remember(scored)` has recorded in that window.
   Only when it returns nothing does `App.run()` go on to post.
5. `Poster.post(scored)` — only invoked when `score >= CUTOFF` and
   `duplicate_of` found no match. Sends `summary + link` to every chat in
   `TELEGRAM_CHAT_IDS` via the thin `Telegram` client in
   `newsfilter/telegram.py`. When the article has an `image_url` (the NOS
   hero image, from the RSS `enclosure`) it is sent as a `sendPhoto` with the
   text as the caption — Telegram fetches the URL itself, so nothing is
   downloaded locally. Missing images and any `sendPhoto` failure fall back
   to a plain `sendMessage`. After a successful post, `deduper.remember(scored)`
   records the story so later duplicates can be caught.

## Environment variables

`newsfilter/__main__.py` calls `load_dotenv()` before importing the rest of
the package, so a `.env` in the working directory is picked up automatically.
Real environment variables win over `.env`. `OPENAI_API_KEY`,
`TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_IDS` must be set (via either
mechanism) before `App` is imported. `DATA_PATH` and `STORE_PATH` are
optional and fall back to defaults:

- `OPENAI_API_KEY` — used by the `OpenAI` client.
- `TELEGRAM_BOT_TOKEN` — token of the Telegram bot used to post messages.
- `TELEGRAM_CHAT_IDS` — comma-separated list of chat IDs to post to (a single
  value works too; whitespace around entries is trimmed).
- `DATA_PATH` — directory containing `prompt.txt`. Defaults to `data`.
- `STORE_PATH` — writable directory for `config.json`, `cache/`,
  `scorelog/`, and `posted.json`. Defaults to `store`.

The defaults live in `newsfilter/config.py`. They are still read at
class-definition time, so changing `DATA_PATH` or `STORE_PATH` at runtime
after import has no effect. In the KubeCoder environment `OPENAI_API_KEY` is
projected automatically from the deployment's secret catalog; the Telegram
variables are deliberately left unset, so a run scores and logs articles but
posts nothing.

## Running and testing

Dependencies are managed by Poetry (`pyproject.toml` + `poetry.lock`). The
venv lives in `~/.cache/pypoetry/virtualenvs/` — do not create a `.venv/` at
the project root, because Poetry will silently adopt it instead of using the
out-of-project default.

Poetry and Ruff live in the `python` toolchain sidecar, not in the dev
container, so every Python command takes a `cexec python` prefix here. The
unprefixed forms below are what a checkout outside the environment uses.

- Setup: `kc project setup` → `cexec python poetry install`.
- Run: `cexec python poetry run python -m newsfilter`. Entry point is
  `newsfilter/__main__.py`. Nothing listens on a port — the run processes the
  articles published since the last one and exits.
- Build: `kc project build` → `kaniko --no-push`, which proves the Dockerfile
  without pushing. To push a scratch image,
  `kaniko --destination registry:5000/newsfilter:dev` — Jenkins owns `:latest`
  and the numbered tags, so a local build must not use them.
- Tests: `kc project test` → `cexec python poetry run pytest`. The suite in
  `tests/test_score.py` calls the real OpenAI API and guards both ends of the
  scale: low-relevance articles must stay at or below their `max`, and the two
  high-side cases must reach `7`, so a model or prompt change that quietly
  drops everything under `CUTOFF` fails the build instead of going unnoticed.
  Every case builds its article with `published=now`, so the on-disk cache
  never hides a regression. `tests/test_loader.py` covers feed merging,
  deduplication, newest-first ordering, and cursor filtering — by
  monkeypatching `feedparser.parse` and `RSS_FEEDS`, so it makes no network
  calls.
  `tests/test_dedupe.py` covers suppression, the 48-hour window, persistence
  across runs, pruning, the fail-open path, and a damaged state file, by
  faking the OpenAI client, so it too makes no network calls.
- Lint: `kc project lint` → `cexec python ruff check .` and
  `./scripts/arch-validate.py docs/architecture/*.yaml`.

## Conventions

- Scoring criteria live in `data/prompt.txt`: an anchor per band from 1 to 10,
  with the 7 — the band `App.CUTOFF` cuts against — spelled out as four kinds
  of article: something to watch out for or act on, a national rule that
  changes what is allowed or owed (with or without a price tag), something
  felt in the wallet, and a national turning point worth knowing even when it
  costs you nothing. The 7 deliberately does not require an ingangsdatum or
  that everyone is affected — demanding either is what used to leave box 3,
  windmill norms and new intelligence-service powers stranded at 6. Band 6 is
  therefore narrow on purpose: genuinely vague plans, and changes that reach
  only a small group.
- Two rules hold the volume down. Only the article that breaks an event can
  reach 7; the reactions, analyses, polls and reconstructies after it cap at
  5, which is what keeps one event from becoming ten messages. And transient
  local disruption caps at 4, weather at 3 — immediate is not the same as
  important. Bands and cutoff are calibrated together, so change them
  together. The placeholder `%DATE%` is replaced at request time with today's
  date in Dutch (`Scorer.get_date()`).
- Calibrate against production, not against a feed snapshot. The RSS feed only
  holds ~20 items, so any single fetch is an unrepresentative slice — it is
  entirely possible to draw a window with no Dutch policy news in it at all
  and conclude the wrong thing. The real corpus is on the prd volume:
  `$STORE_PATH/scorelog/` has 10 days of scored articles and
  `$STORE_PATH/cache/<MODEL>/` holds the original article text. Copy both out
  of the `samba` pod in `newsfilter-prd` (`kubectl --kubeconfig
  ~/.kube/config-prd-write -n newsfilter-prd exec ...`, `kubectl` lives in the
  `iac` toolchain), re-score them with the candidate prompt and replay
  `Deduper` over the result in publication order. That measures the change in
  messages per day directly. The current prompt lands at ~1.8 a day over 13
  replayed days, against 2.9 for what production was sending.
- The model is set in `Scorer.MODEL` (currently `gpt-5.6-sol`). Reasoning
  models — the prefixes in `Scorer.REASONING_PREFIXES`, i.e. `o*` and
  `gpt-5.5` and up — reject any temperature but the default, so those get `1`;
  the older chat models get `Scorer.TEMPERATURE` (`0.2`).
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
