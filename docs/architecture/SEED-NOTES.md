# Seed notes — `newsfilter` producer

First architecture artifact for the NewsFilter repo. Hand-authored mode (no
generator; the YAML is the source of truth). All `introduced` dates are this
repo's first commit, **2025-01-06**.

## Mode & role

- **Hand-authored.** uuid4 minted once per element; never re-mint.
- **Role: standalone app.** A one-shot batch container launched periodically in
  production (`App.run()` in `newsfilter/app.py`). There is no scheduler in the
  code and **no inbound network API** — so no `ApplicationService`/
  `ApplicationInterface` is realized *by* the product, and it realizes no
  capability.

## Elements (minted uuid4s)

| id | label | kind | notes |
|---|---|---|---|
| `app:newsfilter,22a90359-073c-4b89-a80f-87b4f1adb4b5` | NewsFilter | «SoftwareProduct» ApplicationComponent | `sourceRepository: git:pvginkel/NewsFilter`; `stats.image: registry:5000/newsfilter` |
| `svc:openai-api,b4e2a983-5c32-4ed1-94a1-6231a2112ccb` | OpenAI API | shared external ApplicationService (architecture base set) | referenced by UUID; not declared locally |
| `svc:telegram-bot-api,6708ef33-aaf7-4acd-a10d-560d7a7e1d48` | Telegram Bot API | shared external ApplicationService (architecture base set) | referenced by UUID; not declared locally |
| `svc:nos-rss-feed,83b382b5-0fcc-4aa6-8dbd-3533c485f605` | NOS Algemeen Nieuws RSS feed | external ApplicationService | `stats.homepage: https://nos.nl/` |

## Relations

- `app:newsfilter —Association→ svc:openai-api` (`rel:newsfilter-consumes-openai`)
- `app:newsfilter —Association→ svc:telegram-bot-api` (`rel:newsfilter-consumes-telegram`)
- `app:newsfilter —Association→ svc:nos-rss-feed` (`rel:newsfilter-consumes-nos-rss`)

## Outbound-dependency survey

`grep -rIi '://'` over `newsfilter/` + `tests/` plus an env-var/config scan.
Three genuine runtime calls, all with **hardcoded base URLs** — so no `boundBy`
on any edge (the env vars carry auth, not endpoints):

1. **OpenAI** — `OpenAI()` client in `newsfilter/scorer.py:47`, default base
   URL. Auth via `OPENAI_API_KEY` (credential, not endpoint). → `svc:openai-api`.
2. **Telegram** — `Telegram` client in `newsfilter/telegram.py` hitting the
   hardcoded `https://api.telegram.org/bot{token}` base, driven by
   `newsfilter/poster.py`. Auth via `TELEGRAM_BOT_TOKEN` (credential, not
   endpoint). → shared `svc:telegram-bot-api`.
3. **NOS RSS feed** — hardcoded `RSS_FEED = "https://feeds.nos.nl/nosnieuwsalgemeen"`
   in `newsfilter/loader.py:18`, parsed each run via `feedparser`. → `svc:nos-rss-feed`.

The only other `://` hit is a comment link in `scorer.py:28` (a forum cheat
sheet) — triaged **out** (documentation URL).

## Inclusion decisions (excluded / borderline)

- **Container image `registry:5000/newsfilter`** — not modelled as an element
  (images are build artifacts, v0.2 concern). Recorded as a non-load-bearing
  `stats.image` fact on the product.
- **On-disk store (`$STORE_PATH`: `config.json`, `cache/`, `scorelog/`)** — local
  filesystem state with no external identity reachable by name. **Out** (identity
  fence: runtime state, not a named surface).
- **`data/prompt.txt`** — internal config file, not a reachable surface. **Out.**
- **No `cap:` realization** — the app provides no substitutable capability; it is
  a pure consumer.
- **`environment` / `cluster`** — left unset on all elements. The product is a
  logical, type-level surface spanning every deployed env; per-env placement is
  the deploying producer's job. The external `svc:` elements legitimately span
  environments too.

## Cross-producer references

OpenAI and Telegram are shared external services declared in the `architecture`
base set (`external-services.yaml`) and referenced here by UUID
(`svc:openai-api,b4e2a983-…`, `svc:telegram-bot-api,6708ef33-…`) — both resolve
cross-producer at merge. The NOS RSS feed is single-consumer and stays declared
locally.

## Open questions (would have asked a human)

- **Should the NOS RSS feed be a modelled dependency, or is it "just a data
  source"?** Decided **in** — it is a genuine, hardcoded outbound HTTP call the
  app makes every run, matching the "external service you actually call → `svc:`"
  convention. Easy to drop if you'd rather not track public content feeds.
- **Telegram (corrected 2026-07-11)** — the initial seed mis-modelled a Twitter/X
  dependency (`svc:twitter-api`) the code never had; NewsFilter posts to Telegram
  (`newsfilter/telegram.py`), having been migrated off Twitter. Replaced with a
  reference to the shared `svc:telegram-bot-api`.
- **Image is registered in `stats` only.** If/when a v0.1 home for image identity
  appears, this moves out of `stats`.
