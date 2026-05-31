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
| `svc:openai-api,2ea6d65c-42cf-4de4-9450-f2769b9e8fc0` | OpenAI API | external ApplicationService | `stats.homepage: https://openai.com/`; no «SoftwareProduct» |
| `svc:twitter-api,03d46e49-8971-47ba-aeab-9739f6cb561c` | Twitter/X API | external ApplicationService | `stats.homepage: https://developer.x.com/` |
| `svc:nos-rss-feed,83b382b5-0fcc-4aa6-8dbd-3533c485f605` | NOS Algemeen Nieuws RSS feed | external ApplicationService | `stats.homepage: https://nos.nl/` |

## Relations

- `app:newsfilter —Association→ svc:openai-api` (`rel:newsfilter-consumes-openai`)
- `app:newsfilter —Association→ svc:twitter-api` (`rel:newsfilter-consumes-twitter`)
- `app:newsfilter —Association→ svc:nos-rss-feed` (`rel:newsfilter-consumes-nos-rss`)

## Outbound-dependency survey

`grep -rIi '://'` over `newsfilter/` + `tests/` plus an env-var/config scan.
Three genuine runtime calls, all with **hardcoded base URLs** — so no `boundBy`
on any edge (the env vars carry auth, not endpoints):

1. **OpenAI** — `OpenAI()` client in `newsfilter/scorer.py:47`, default base
   URL. Auth via `OPENAI_API_KEY` (credential, not endpoint). → `svc:openai-api`.
2. **Twitter/X** — `tweepy.API` / `tweepy.Client` in `newsfilter/poster.py:29-37`,
   default endpoint. Auth via `TWITTER_API_KEY` JSON blob (credentials, not
   endpoint). → `svc:twitter-api`.
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

None. All three external services are third-party SaaS / public feeds declared
locally here; no edges resolve to another producer's UUID, so nothing dangles.

## Open questions (would have asked a human)

- **Should the NOS RSS feed be a modelled dependency, or is it "just a data
  source"?** Decided **in** — it is a genuine, hardcoded outbound HTTP call the
  app makes every run, matching the "external service you actually call → `svc:`"
  convention. Easy to drop if you'd rather not track public content feeds.
- **Twitter/X homepage** — used the developer-portal URL (`developer.x.com`)
  since the dependency is the API, not the consumer site. Swap to `https://x.com/`
  if you prefer the brand homepage.
- **Image is registered in `stats` only.** If/when a v0.1 home for image identity
  appears, this moves out of `stats`.
